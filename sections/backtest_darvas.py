# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae

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
    activo = activos_predef[activo_nombre]

    timeframes = ["1d", "1h", "15m"]
    timeframe = st.selectbox("Temporalidad", timeframes)

    start = st.date_input("Desde",  value=pd.to_datetime("2023-01-01"), key="darvas_start")
    end   = st.date_input("Hasta", value=pd.to_datetime("today"),     key="darvas_end")

    # slider para boxp
    DARVAS_WINDOW = st.slider(
        "Largo del Darvas Box (boxp)",
        min_value=1, max_value=50, value=5, step=1, key="darvas_window"
    )

    if not st.button("Ejecutar Backtest Darvas", key="run_darvas"):
        return

    # 2) Parámetros fijos para indicadores
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

    # 4) Formatear y mostrar tabla histórica
    df_hist = df.reset_index().rename(columns={"index":"Date"})
    df_hist["Date"] = pd.to_datetime(df_hist["Date"]).dt.tz_localize(None)

    st.dataframe(
        df_hist,
        use_container_width=True,
        column_config={
            "Date": st.column_config.DateColumn("Fecha", format="DD-MM-YYYY"),
            "Open": st.column_config.NumberColumn("Apertura", format=", .2f"),
            "High": st.column_config.NumberColumn("Máximo",   format=", .2f"),
            "Low":  st.column_config.NumberColumn("Mínimo",   format=", .2f"),
            "Close":st.column_config.NumberColumn("Cierre",   format=", .2f"),
            "Volume":st.column_config.NumberColumn("Volumen", format=","),
        },
        hide_index=True
    )

    # 5) Normalizar y limpiar
    df = df_hist.copy()
    df = df.dropna(subset=["Close", "High", "Low"])

    # 6) Cálculo Darvas Box
    df["darvas_high"]      = df["High"].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
    df["darvas_low"]       = df["Low"].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
    df["prev_darvas_high"] = df["darvas_high"].shift(1)
    df["prev_darvas_low"]  = df["darvas_low"].shift(1)
    df["prev_close"]       = df["Close"].shift(1)

    # 7) Señales Darvas (primer cruce)
    df["buy_signal"]  = (df["Close"] > df["prev_darvas_high"]) & (df["prev_close"] <= df["prev_darvas_high"])
    df["sell_signal"] = (df["Close"] < df["prev_darvas_low"])  & (df["prev_close"] >= df["prev_darvas_low"])

    # 8) Filtro MavilimW (tendencia)
    df["mavilimw"]    = calc_mavilimw(df)
    df["trend_up"]    = df["Close"] > df["mavilimw"].shift(2)
    df["trend_down"]  = df["Close"] < df["mavilimw"].shift(2)

    # 9) Filtro WAE (fuerza)
    df = calc_wae(
        df,
        sensitivity   = SENSITIVITY,
        fastLength    = FAST_EMA,
        slowLength    = SLOW_EMA,
        channelLength = CHANNEL_LEN,
        mult          = BB_MULT
    )
    # momentum bajista adicional
    fastMA     = df["Close"].ewm(span=FAST_EMA, adjust=False).mean()
    slowMA     = df["Close"].ewm(span=SLOW_EMA, adjust=False).mean()
    macd       = fastMA - slowMA
    macd_shift = macd.shift(1)
    t1         = (macd - macd_shift) * SENSITIVITY
    df["wae_trendDown"] = np.where(t1 < 0, -t1, 0)

    df["wae_filter_buy"]  = (df["wae_trendUp"]   > df["wae_e1"]) & (df["wae_trendUp"]   > df["wae_deadzone"])
    df["wae_filter_sell"] = (df["wae_trendDown"] > df["wae_e1"]) & (df["wae_trendDown"] > df["wae_deadzone"])

    # 10) Señales finales (todas)
    df["buy_final"]  = df["buy_signal"]  & df["trend_up"]   & df["wae_filter_buy"]
    df["sell_final"] = df["sell_signal"] & df["trend_down"] & df["wae_filter_sell"]

    # 11) Mostrar tabla de señales
    cols_signals = [
        "Date","Close","darvas_high","darvas_low","mavilimw",
        "wae_trendUp","wae_e1","wae_deadzone","wae_trendDown",
        "buy_signal","trend_up","wae_filter_buy","buy_final",
        "sell_signal","trend_down","wae_filter_sell","sell_final"
    ]
    df_signals = df.loc[df["buy_final"] | df["sell_final"], cols_signals].copy()

    st.success(f"Número de señales detectadas: {len(df_signals)}")
    st.dataframe(
        df_signals,
        use_container_width=True,
        column_config={
            "Date":            st.column_config.DateColumn("Fecha", format="DD-MM-YYYY"),
            "Close":           st.column_config.NumberColumn("Cierre",    format=", .2f"),
            "darvas_high":     st.column_config.NumberColumn("Darvas High", format=", .2f"),
            "darvas_low":      st.column_config.NumberColumn("Darvas Low",  format=", .2f"),
            "mavilimw":        st.column_config.NumberColumn("MavilimW",    format=", .2f"),
            "wae_trendUp":     st.column_config.NumberColumn("WAE↑",        format=", .2f"),
            "wae_e1":          st.column_config.NumberColumn("Explosion",   format=", .2f"),
            "wae_deadzone":    st.column_config.NumberColumn("DeadZone",    format=", .2f"),
            "wae_trendDown":   st.column_config.NumberColumn("WAE↓",        format=", .2f"),
        },
        hide_index=True
    )

    # 12) Gráfico de Backtest
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["Date"], df["Close"],      label="Precio Close", color="black", zorder=1)
    ax.plot(df["Date"], df["darvas_high"],label="Darvas High", linestyle="--", zorder=1)
    ax.plot(df["Date"], df["darvas_low"], label="Darvas Low",  linestyle="--", zorder=1)
    ax.plot(df["Date"], df["mavilimw"],   label="MavilimW",    linewidth=2, zorder=2)

    buy_idx  = df.index[df["buy_final"]]
    sell_idx = df.index[df["sell_final"]]
    ax.scatter(df.loc[buy_idx, "Date"],  df.loc[buy_idx,  "Close"],
               marker="^", color="green", s=100, label="Señal Compra", zorder=3)
    ax.scatter(df.loc[sell_idx,"Date"],  df.loc[sell_idx, "Close"],
               marker="v", color="red",   s=100, label="Señal Venta",  zorder=3)

    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    plt.xticks(rotation=15)
    st.pyplot(fig)
