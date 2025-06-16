# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators   import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # 1) Parámetros UI
    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    activo        = activos_predef[activo_nombre]

    timeframe = st.selectbox("Temporalidad", ["1d", "1h", "15m", "5m"])
    start     = st.date_input("Desde", value=pd.to_datetime("2023-01-01"), key="darvas_start")
    end       = st.date_input("Hasta", value=pd.to_datetime("today"),      key="darvas_end")

    DARVAS_WINDOW = st.slider(
        "Largo del Darvas Box (boxp)",
        min_value=1, max_value=50, value=20, step=1, key="darvas_window"
    )

    if not st.button("Ejecutar Backtest Darvas", key="run_darvas"):
        return

    # 2) Parámetros fijos
    SENSITIVITY = 150
    FAST_EMA    = 20
    SLOW_EMA    = 40
    CHANNEL_LEN = 20
    BB_MULT     = 2.0

    # 3) Descarga de históricos
    st.info("Descargando datos históricos...")
    df = cargar_precio_historico(activo, timeframe, start, end)
    if df is None or df.empty:
        st.error("No se encontraron datos para esa configuración.")
        return
    st.success(f"Datos descargados: {len(df)} filas")

    # 4) Creamos la columna Date a partir del índice y limpiamos
    df = df.copy()
    df["Date"] = pd.to_datetime(df.index).tz_localize(None)
    df = df.reset_index(drop=True)
    df = df.dropna(subset=["Close","High","Low"])

    # 5) Darvas Box
    df["darvas_high"] = df["High"].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
    df["darvas_low"]  = df["Low"].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
    df["prev_dh"]     = df["darvas_high"].shift(1)
    df["prev_dl"]     = df["darvas_low"].shift(1)
    df["prev_c"]      = df["Close"].shift(1)

    # 6) Señales Darvas
    df["buy_signal"]  = (df["Close"] > df["prev_dh"]) & (df["prev_c"] <= df["prev_dh"])
    df["sell_signal"] = (df["Close"] < df["prev_dl"]) & (df["prev_c"] >= df["prev_dl"])

    # 7) Filtro de tendencia MavilimW
    df["mavilimw"]    = calc_mavilimw(df)
    df["trend_up"]    = df["Close"] > df["mavilimw"].shift(2)
    df["trend_down"]  = df["Close"] < df["mavilimw"].shift(2)

    # 8) Filtro de fuerza WAE
    df = calc_wae(
        df,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    # momentum bajista
    fast = df["Close"].ewm(span=FAST_EMA, adjust=False).mean()
    slow = df["Close"].ewm(span=SLOW_EMA, adjust=False).mean()
    macd = fast - slow
    t1   = (macd - macd.shift(1)) * SENSITIVITY
    df["wae_trendDown"] = np.where(t1 < 0, -t1, 0)

    df["wae_filter_buy"]  = (df["wae_trendUp"]   > df["wae_e1"]) & (df["wae_trendUp"]   > df["wae_deadzone"])
    df["wae_filter_sell"] = (df["wae_trendDown"] > df["wae_e1"]) & (df["wae_trendDown"] > df["wae_deadzone"])

    # 9) Señales finales
    df["buy_final"]  = df["buy_signal"]  & df["trend_up"]   & df["wae_filter_buy"]
    df["sell_final"] = df["sell_signal"] & df["trend_down"] & df["wae_filter_sell"]

    # 10) Preparamos df_signals sin perder Date
    cols = [
        "Date", "Close", "darvas_high", "darvas_low", "mavilimw",
        "wae_trendUp", "wae_e1", "wae_deadzone", "wae_trendDown",
        "buy_signal", "trend_up", "wae_filter_buy", "buy_final",
        "sell_signal", "trend_down", "wae_filter_sell", "sell_final"
    ]
    df_signals = df.loc[df["buy_final"] | df["sell_final"], cols].copy()

    st.success(f"Número de señales detectadas: {len(df_signals)}")

    # 11) Mostramos con formato
    st.dataframe(
        df_signals,
        use_container_width=True,
        column_config={
            "Date": st.column_config.DateColumn(
                "Fecha", format="DD-MM-YYYY", help="Fecha de la señal"
            ),
            "Close": st.column_config.NumberColumn(
                "Cierre", format=",.2f"
            ),
            "darvas_high": st.column_config.NumberColumn(
                "Darvas High", format=",.2f"
            ),
            "darvas_low": st.column_config.NumberColumn(
                "Darvas Low", format=",.2f"
            ),
            "mavilimw": st.column_config.NumberColumn(
                "MavilimW", format=",.2f"
            ),
            "wae_trendUp": st.column_config.NumberColumn(
                "WAE↑", format=",.2f"
            ),
            "wae_e1": st.column_config.NumberColumn(
                "Explosión", format=",.2f"
            ),
            "wae_deadzone": st.column_config.NumberColumn(
                "DeadZone", format=",.2f"
            ),
            "wae_trendDown": st.column_config.NumberColumn(
                "WAE↓", format=",.2f"
            ),
        }
    )

    # 12) Gráfico
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["Date"], df["Close"],       label="Precio Close", color="black", zorder=1)
    ax.plot(df["Date"], df["darvas_high"],  linestyle="--", label="Darvas High", zorder=1)
    ax.plot(df["Date"], df["darvas_low"],   linestyle="--", label="Darvas Low",  zorder=1)
    ax.plot(df["Date"], df["mavilimw"],     linewidth=2, label="MavilimW",    zorder=2)

    ax.scatter(
        df.loc[df["buy_final"], "Date"],
        df.loc[df["buy_final"], "Close"],
        marker="^", color="green", s=100, label="Señal Compra", zorder=3
    )
    ax.scatter(
        df.loc[df["sell_final"], "Date"],
        df.loc[df["sell_final"], "Close"],
        marker="v", color="red",   s=100, label="Señal Venta",  zorder=3
    )

    ax.set_title(f"Darvas Box Backtest – {activo_nombre} [{timeframe}]")
    ax.legend()
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Precio")
    plt.xticks(rotation=20)
    st.pyplot(fig)

    # 12) Explicación de señales
    with st.expander("ℹ️ Interpretación de las señales"):
        st.markdown("""  
        - 🔼 **Señal de compra**: se genera cuando el precio cierra por encima de la Darvas High del día anterior, la tendencia (MavilimW) es alcista y la fuerza (WAE) supera el umbral.  
        - 🔽 **Señal de venta**: se genera cuando el precio cierra por debajo de la Darvas Low del día anterior, la tendencia es bajista y la fuerza WAE también confirma impulso a la baja.  
        - 📅 **Fecha**: corresponde al día en que se rompe el canal Darvas y se cumplen ambos filtros.  
        - 📊 **Cantidad de señales**: compras y ventas detectadas en el periodo seleccionado.
        """)

    # 13) Perfil del backtest
    with st.expander("📈 Perfil del Backtest"):
        # calculamos algunos KPIs básicos
        total_ops = len(df_signals)
        compras    = df_signals['buy_final'].sum()
        ventas     = df_signals['sell_final'].sum()
        st.markdown(f"""
        - 🔄 **Operaciones totales**: {total_ops}  
        - 🟢 **Compras**: {compras}  
        - 🔴 **Ventas**: {ventas}  
        - ⏳ **Periodo analizado**: {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}  
        - ⚙️ **Parámetros**: Darvas Window = {DARVAS_WINDOW}, EMA rápida = {FAST_EMA}, EMA lenta = {SLOW_EMA}
        """)

