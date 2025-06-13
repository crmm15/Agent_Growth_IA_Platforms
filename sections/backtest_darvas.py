import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae


def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # ======== UI de entrada ========
    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Elige activo", list(activos_predef.keys()))
    activo = activos_predef[activo_nombre]

    timeframes = ["1d", "1h", "15m", "5m"]
    timeframe = st.selectbox("Temporalidad", timeframes)

    start = st.date_input("Desde", value=pd.to_datetime("2023-01-01"), key="darvas_start")
    end = st.date_input("Hasta", value=pd.to_datetime("today"), key="darvas_end")

    # Slider para el largo del Darvas Box
    boxp = st.number_input(
        "Largo del Darvas Box (boxp)",
        min_value=1,
        max_value=200,
        value=20,
        step=1,
        help="Número de barras previas a usar para techo/suelo Darvas"
    )

    if not st.button("Ejecutar Backtest Darvas", key="run_darvas"):
        return

    # ======== Descargar y validar datos ========
    st.info("Descargando datos históricos...")
    df = cargar_precio_historico(activo, timeframe, start, end)
    if df is None or df.empty:
        st.error("No se encontraron datos para esa configuración.")
        return

    st.success(f"Datos descargados: {len(df)} filas")
    # st.dataframe(df)

    # Reset index para tener una columna Date
    df = df.reset_index(drop=False).rename(columns={'index': 'Date'})
    df = df.dropna(subset=["Close", "High", "Low"])

    # ======== 1) Cálculo Darvas (techo/suelo sobre boxp barras anteriores) ========
    df['darvas_high'] = (
        df['High']
        .rolling(window=boxp+1, min_periods=boxp+1)
        .max()
        .shift(1)
    )
    df['darvas_low'] = (
        df['Low']
        .rolling(window=boxp+1, min_periods=boxp+1)
        .min()
        .shift(1)
    )

    # ======== 2) Señales Darvas (primera ruptura al alza y a la baja) ========
    df['buy_signal'] = (
        (df['Close'] > df['darvas_high']) &
        (df['Close'].shift(1) <= df['darvas_high'])
    )
    df['sell_signal'] = (
        (df['Close'] < df['darvas_low']) &
        (df['Close'].shift(1) >= df['darvas_low'])
    )

    # ======== 3) Filtro tendencia MavilimW (dos barras atrás) ========
    df['mavilimw'] = calc_mavilimw(df)
    df['trend_up'] = df['Close'] > df['mavilimw'].shift(2)
    df['trend_down'] = df['Close'] < df['mavilimw'].shift(2)

    # ======== 4) Filtro fuerza WAE ========
    df = calc_wae(
        df,
        sensitivity=150,
        fastLength=20,
        slowLength=40,
        channelLength=20,
        mult=2.0
    )
    # Calcular histograma bajista
    fastMA = df['Close'].ewm(span=20, adjust=False).mean()
    slowMA = df['Close'].ewm(span=40, adjust=False).mean()
    macd = fastMA - slowMA
    macd_shift = macd.shift(1)
    t1 = (macd - macd_shift) * 150
    df['wae_trendDown'] = np.where(t1 < 0, -t1, 0)

    df['wae_filter_buy'] = (
        (df['wae_trendUp']   > df['wae_e1']) &
        (df['wae_trendUp']   > df['wae_deadzone'])
    )
    df['wae_filter_sell'] = (
        (df['wae_trendDown'] > df['wae_e1']) &
        (df['wae_trendDown'] > df['wae_deadzone'])
    )

    # ======== 5) Señales finales (solo la primera de cada tipo) ========
    df['buy_final']  = df['buy_signal']  & df['trend_up']   & df['wae_filter_buy']
    df['sell_final'] = df['sell_signal'] & df['trend_down'] & df['wae_filter_sell']

    # Asegurar solo primera compra/venta
    if df['buy_final'].any():
        idx = df.index[df['buy_final']].min()
        df.loc[:, 'buy_final'] = False
        df.at[idx, 'buy_final'] = True
    if df['sell_final'].any():
        idx = df.index[df['sell_final']].min()
        df.loc[:, 'sell_final'] = False
        df.at[idx, 'sell_final'] = True

    # ======== 6) Mostrar tabla de señales ========
    cols = [
        'Date','Close', 'darvas_high', 'darvas_low', 'mavilimw',
        'wae_trendUp', 'wae_e1', 'wae_deadzone', 'wae_trendDown',
        'buy_signal', 'trend_up', 'wae_filter_buy', 'buy_final',
        'sell_signal','trend_down','wae_filter_sell','sell_final'
    ]
    df_signals = df.loc[df['buy_final'] | df['sell_final'], cols]
    st.success(f"Número de señales: {len(df_signals)}")
    st.dataframe(df_signals)

    # ======== 7) Gráfico ========
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Date'], df['Close'], label="Close", color="black", zorder=1)
    ax.plot(df['Date'], df['darvas_high'], '--', label="Darvas High", zorder=1)
    ax.plot(df['Date'], df['darvas_low'],  '--', label="Darvas Low",  zorder=1)
    ax.plot(df['Date'], df['mavilimw'],   linewidth=2, label="MavilimW", zorder=2)

    # Señales
    buy_idx  = df['Date'][df['buy_final']]
    sell_idx = df['Date'][df['sell_final']]
    ax.scatter(buy_idx,  df.loc[df['buy_final'],  'Close'], marker='^', color='green', s=100, label='Señal Compra', zorder=3)
    ax.scatter(sell_idx, df.loc[df['sell_final'], 'Close'], marker='v', color='red',   s=100, label='Señal Venta',  zorder=3)

    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
