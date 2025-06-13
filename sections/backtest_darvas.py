# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # UI configuration
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

    timeframes = ["1d", "1h", "15m", "5m"]
    timeframe = st.selectbox("Temporalidad", timeframes)

    start_date = st.date_input("Desde", value=pd.to_datetime("2023-01-01"))
    end_date = st.date_input("Hasta", value=pd.to_datetime("today"))

    if not st.button("Ejecutar Backtest Darvas"):
        return

    # Fixed indicator parameters
    SENSITIVITY = 150
    FAST_EMA = 20
    SLOW_EMA = 40
    CHANNEL_LEN = 20
    BB_MULT = 2.0
    DARVAS_WINDOW = 20

    st.info("Descargando datos históricos...")
    df = cargar_precio_historico(activo, timeframe, start_date, end_date)
    if df is None or df.empty:
        st.error("No se encontraron datos para esa configuración.")
        return

    # Ensure tz-naive datetime index and filter by date
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.loc[start_date:end_date]

    st.success(f"Datos descargados: {len(df)} filas")
    st.dataframe(df)

    # 1) Darvas Box calculation
    df['darvas_high'] = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
    df['darvas_low']  = df['Low'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
    df['prev_darvas_high'] = df['darvas_high'].shift(1)
    df['prev_darvas_low']  = df['darvas_low'].shift(1)
    df['prev_close']       = df['Close'].shift(1)

    # 2) Darvas signals
    df['buy_signal']  = (df['Close'] > df['prev_darvas_high']) & (df['prev_close'] <= df['prev_darvas_high'])
    df['sell_signal'] = (df['Close'] < df['prev_darvas_low'])  & (df['prev_close'] >= df['prev_darvas_low'])

    # 3) MavilimW trend filter (two periods back)
    df['mavilimw']    = calc_mavilimw(df)
    df['trend_up']    = df['Close'] > df['mavilimw'].shift(2)
    df['trend_down']  = df['Close'] < df['mavilimw'].shift(2)

    # 4) WAE momentum filter
    df = calc_wae(
        df,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    # Calculate downward WAE for sell filter
    fastMA = df['Close'].ewm(span=FAST_EMA, adjust=False).mean()
    slowMA = df['Close'].ewm(span=SLOW_EMA, adjust=False).mean()
    macd = fastMA - slowMA
    macd_shift = macd.shift(1)
    t1 = (macd - macd_shift) * SENSITIVITY
    df['wae_down'] = np.where(t1 < 0, -t1, 0)

    df['wae_filter_buy']  = (df['wae_trendUp'] > df['wae_e1']) & (df['wae_trendUp'] > df['wae_deadzone'])
    df['wae_filter_sell'] = (df['wae_down']    > df['wae_e1']) & (df['wae_down']    > df['wae_deadzone'])

    # 5) Final signals (must satisfy Darvas + trend + WAE)
    df['buy_final']  = df['buy_signal']  & df['trend_up']   & df['wae_filter_buy']
    df['sell_final'] = df['sell_signal'] & df['trend_down'] & df['wae_filter_sell']

    # Only the FIRST buy and FIRST sell
    if df['buy_final'].any():
        first_buy = df['buy_final'].idxmax()
        df['buy_final'] = False
        df.at[first_buy, 'buy_final'] = True
    if df['sell_final'].any():
        first_sell = df['sell_final'].idxmax()
        df['sell_final'] = False
        df.at[first_sell, 'sell_final'] = True

    # 6) Display signals table
    cols = [
        'Close', 'darvas_high', 'darvas_low', 'mavilimw',
        'wae_trendUp', 'wae_e1', 'wae_deadzone', 'wae_down',
        'buy_signal', 'trend_up', 'wae_filter_buy', 'buy_final',
        'sell_signal', 'trend_down', 'wae_filter_sell', 'sell_final'
    ]
    df_signals = df.loc[df['buy_final'] | df['sell_final'], cols]
    st.success(f"Número de señales detectadas: {len(df_signals)}")
    st.dataframe(df_signals)

    # 7) Plot backtest
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df['Close'], label="Precio Close", color="black", zorder=1)
    ax.plot(df.index, df['darvas_high'], label="Darvas High", linestyle="--", zorder=1)
    ax.plot(df.index, df['darvas_low'],  label="Darvas Low",  linestyle="--", zorder=1)
    ax.plot(df.index, df['mavilimw'],    label="MavilimW",    linewidth=2, zorder=2)

    buy_idx  = df.index[df['buy_final']]
    sell_idx = df.index[df['sell_final']]
    ax.scatter(buy_idx,  df.loc[buy_idx,  'Close'], marker="^", color="green", s=100, label="Señal Compra", zorder=3)
    ax.scatter(sell_idx, df.loc[sell_idx, 'Close'], marker="v", color="red",   s=100, label="Señal Venta",   zorder=3)

    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
