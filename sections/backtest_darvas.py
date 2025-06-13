import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

from utils.indicators import calc_mavilimw, calc_wae
from utils.backtest_helpers import run_darvas_backtest, robust_trend_filter


def backtest_darvas():
    # Título y configuración
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros fijos de los indicadores
    SENSITIVITY = 150
    FAST_EMA = 20
    SLOW_EMA = 40
    CHANNEL_LEN = 20
    BB_MULT = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # ==== SELECCIÓN DE ACTIVO Y RANGO ====  
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

    fecha_inicio = st.date_input("Desde", value=pd.to_datetime("2023-01-01").date())
    fecha_fin = st.date_input("Hasta", value=pd.Timestamp.today().date())

    if not st.button("Ejecutar Backtest Darvas"):
        return

    # ==== DESCARGA DE DATOS ====  
    st.info("Descargando datos históricos...")
    df = yf.download(
        activo,
        start=fecha_inicio,
        end=fecha_fin + pd.Timedelta(days=1),
        interval=timeframe,
        progress=False
    )

    if df.empty:
        st.error("No se encontraron datos para ese activo y timeframe. Prueba otra combinación.")
        return

    # normalize dataframe
    df = df.reset_index()
    df.columns = [str(col).capitalize() for col in df.columns]
    df = df.dropna(subset=["Close", "High", "Low"])

    # ==== DARVAS BOX ====  
    df['darvas_high'] = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
    df['darvas_low']  = df['Low'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
    df['prev_darvas_high'] = df['darvas_high'].shift(1)
    df['prev_close']       = df['Close'].shift(1)

    df['buy_signal']  = (df['Close'] > df['prev_darvas_high']) & (df['prev_close'] <= df['prev_darvas_high'])
    df['sell_signal'] = (df['Close'] < df['darvas_low'].shift(1)) & (df['prev_close'] >= df['darvas_low'].shift(1))

    # ==== MAVILIMW (Tendencia) ====  
    df['mavilimw'] = calc_mavilimw(df)
    # trend filter para compra (precio > mavilimw)
    df['trend_filter'] = df['Close'] > df['mavilimw']
    # trend filter para venta (precio < mavilimw)
    df['trend_filter_sell'] = df['Close'] < df['mavilimw']

    # ==== WAE (Fuerza) ====  
    df = calc_wae(
        df,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    # wea_filter para compra (t1 positivo sobre umbrales)
    df['wae_filter']      = (df['wae_trendUp'] > df['wae_e1']) & (df['wae_trendUp'] > df['wae_deadzone'])
    # calcula tendencia bajista para venta
    df['wae_trendDown']   = np.where(df['wae_trendUp'] < 0, -df['wae_trendUp'], 0)
    # wae_filter para venta (histograma bajista sobre umbrales)
    df['wae_filter_sell'] = (df['wae_trendDown'] > df['wae_e1']) & (df['wae_trendDown'] > df['wae_deadzone'])

    # ==== SEÑALES FINALES ====  
    df['buy_final']  = df['buy_signal']  & df['trend_filter']      & df['wae_filter']
    df['sell_final'] = df['sell_signal'] & df['trend_filter_sell'] & df['wae_filter_sell']

    # Conserva solo la PRIMERA señal de cada tipo
    first_buy_idx  = df.index[df['buy_final']].min()
    first_sell_idx = df.index[df['sell_final']].min()
    df['buy_final']  = df.index == first_buy_idx
    df['sell_final'] = df.index == first_sell_idx

    # ==== TABLA DE SEÑALES ====  
    cols = [
        'Close','Darvas_high','Darvas_low','Mavilimw',
        'Wae_trendUp','Wae_e1','Wae_deadzone',
        'Buy_signal','Trend_filter','Wae_filter','Buy_final',
        'Sell_signal','Trend_filter_sell','Wae_filter_sell','Sell_final'
    ]
    df_signals = df.loc[df['buy_final'] | df['sell_final'], cols]
    st.success(f"Número de señales finales detectadas: {len(df_signals)}")
    st.dataframe(df_signals)

    # ==== PLOT ====  
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(df['Close'], label='Precio Close', color='black', zorder=1)
    ax.plot(df['darvas_high'], '--', label='Darvas High', color='green', zorder=1)
    ax.plot(df['darvas_low'],  '--', label='Darvas Low', color='red',   zorder=1)
    ax.plot(df['mavilimw'],   linewidth=2, label='MavilimW (Tendencia)', color='white', zorder=2)

    # marcadores de primeras señales
    if not np.isnan(first_buy_idx):
        ax.scatter(first_buy_idx, df.at[first_buy_idx,'Close'], marker='^', color='lime', s=120, label='Buy', zorder=3)
    if not np.isnan(first_sell_idx):
        ax.scatter(first_sell_idx, df.at[first_sell_idx,'Close'], marker='v', color='magenta', s=120, label='Sell', zorder=3)

    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)

# Exporta la función para importación
