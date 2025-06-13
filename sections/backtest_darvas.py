# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data   import cargar_precio_historico
from utils.indicators    import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # --- UI de parámetros ---
    activos_predef = {
        "BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL", "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN", "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Elige activo", list(activos_predef.keys()))
    activo        = activos_predef[activo_nombre]

    timeframes = ["1d","1h","15m","5m"]
    timeframe  = st.selectbox("Temporalidad", timeframes)

    start = st.date_input("Desde", value=pd.to_datetime("2023-01-01"), key="darvas_start")
    end   = st.date_input("Hasta", value=pd.to_datetime("today"),      key="darvas_end")

    # <<< ESTE ES EL CAMBIO >>> 
    DARVAS_WINDOW = st.number_input(
        "Largo del Darvas Box (boxp)",
        min_value=1, max_value=100, value=5, step=1,
        help="Número de barras para máximos/mínimos de Darvas (en TradingView usan 5)"
    )

    if not st.button("Ejecutar Backtest Darvas", key="run_darvas"):
        return

    # --- parámetros fijos ---
    SENSITIVITY = 150
    FAST_EMA    = 20
    SLOW_EMA    = 40
    CHANNEL_LEN = 20
    BB_MULT     = 2.0

    st.info("Descargando datos históricos…")
    df = cargar_precio_historico(activo, timeframe, start, end)
    if df is None or df.empty:
        st.error("No hay datos para esa configuración.")
        return

    st.success(f"Datos: {len(df)} filas")
    df = df.reset_index().dropna(subset=["Close","High","Low"])

    # 1) Darvas Box
    df['darvas_high']      = df['High'].rolling(DARVAS_WINDOW).max()
    df['darvas_low']       = df['Low'].rolling(DARVAS_WINDOW).min()
    df['prev_darvas_high'] = df['darvas_high'].shift(1)
    df['prev_darvas_low']  = df['darvas_low'].shift(1)
    df['prev_close']       = df['Close'].shift(1)

    # 2) Señales Darvas
    df['buy_signal']  = (df['Close'] > df['prev_darvas_high']) & (df['prev_close'] <= df['prev_darvas_high'])
    df['sell_signal'] = (df['Close'] < df['prev_darvas_low'])  & (df['prev_close'] >= df['prev_darvas_low'])

    # 3) Tendencia con MavilimW (pendiente)
    df['mavilimw']   = calc_mavilimw(df)
    df['trend_up']   = df['mavilimw'] > df['mavilimw'].shift(1)
    df['trend_down'] = df['mavilimw'] < df['mavilimw'].shift(1)

    # 4) Fuerza con WAE
    df = calc_wae(df, sensitivity=SENSITIVITY,
                     fastLength=FAST_EMA, slowLength=SLOW_EMA,
                     channelLength=CHANNEL_LEN, mult=BB_MULT)
    fastMA     = df['Close'].ewm(span=FAST_EMA).mean()
    slowMA     = df['Close'].ewm(span=SLOW_EMA).mean()
    macd       = fastMA - slowMA
    macd_prev  = macd.shift(1)
    t1         = (macd - macd_prev) * SENSITIVITY
    df['wae_trendDown'] = np.where(t1<0, -t1, 0)

    df['wae_filter_buy']  = (df['wae_trendUp']   > df['wae_e1']) & (df['wae_trendUp']   > df['wae_deadzone'])
    df['wae_filter_sell'] = (df['wae_trendDown'] > df['wae_e1']) & (df['wae_trendDown'] > df['wae_deadzone'])

    # 5) Señales finales
    df['buy_final']  = df['buy_signal']  & df['trend_up']   & df['wae_filter_buy']
    df['sell_final'] = df['sell_signal'] & df['trend_down'] & df['wae_filter_sell']

    # Sólo la primera de cada tipo
    if df['buy_final'].any():
        idx = df['buy_final'].idxmax()
        df.loc[:, 'buy_final'] = False
        df.at[idx, 'buy_final'] = True
    if df['sell_final'].any():
        idx = df['sell_final'].idxmax()
        df.loc[:, 'sell_final'] = False
        df.at[idx, 'sell_final'] = True

    # 6) Mostrar tabla
    cols = [
        'Date','Close','darvas_high','darvas_low','mavilimw',
        'wae_trendUp','wae_e1','wae_deadzone','wae_trendDown',
        'buy_signal','trend_up','wae_filter_buy','buy_final',
        'sell_signal','trend_down','wae_filter_sell','sell_final'
    ]
    df_signals = df.loc[df['buy_final']|df['sell_final'], cols]
    st.success(f"Número de señales: {len(df_signals)}")
    st.dataframe(df_signals)

    # 7) Gráfico
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(df['Date'], df['Close'], label="Close")
    ax.plot(df['Date'], df['darvas_high'], '--', label="Darvas High")
    ax.plot(df['Date'], df['darvas_low'],  '--', label="Darvas Low")
    ax.plot(df['Date'], df['mavilimw'],    label="MavilimW", linewidth=2)

    buys  = df['Date'][df['buy_final']]
    sells = df['Date'][df['sell_final']]
    ax.scatter(buys,  df.loc[df['buy_final'],  'Close'], marker="^", color="green", s=100)
    ax.scatter(sells, df.loc[df['sell_final'], 'Close'], marker="v", color="red",   s=100)

    ax.set_title(f"Darvas Box Backtest — {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
