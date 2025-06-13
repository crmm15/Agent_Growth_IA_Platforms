# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # ——— UI de parámetros ———
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

    start = st.date_input("Desde", value=datetime.date(2023, 1, 1), key="darvas_start")
    end   = st.date_input("Hasta", value=datetime.date.today(), key="darvas_end")

    boxp = st.number_input("Largo del Darvas Box (boxp)", 2, 100, 5,
                           help="Cantidad de barras para calcular máximo y mínimo de Darvas.")

    if not st.button("Ejecutar Backtest Darvas", key="run_darvas"):
        return

    # ——— Descarga de datos ———
    st.info("Descargando datos históricos...")
    start_str = start.strftime("%Y-%m-%d")
    end_str   = (end + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    df = cargar_precio_historico(activo, timeframe, start_str, end_str)
    if df is None or df.empty:
        st.error("No se encontraron datos para esa configuración.")
        return
    st.success(f"Datos: {len(df)} filas")

    # ——— Preparación ———
    df = df.reset_index(drop=False).dropna(subset=["Open","High","Low","Close"])
    df['prev_close'] = df['Close'].shift(1)

    # ——— 1) Darvas Box — usando boxp ———
    df['darvas_high'] = df['High'].rolling(window=boxp, min_periods=boxp).max()
    df['darvas_low']  = df['Low'].rolling( window=boxp, min_periods=boxp).min()
    df['prev_darvas_high'] = df['darvas_high'].shift(1)
    df['prev_darvas_low']  = df['darvas_low'].shift(1)

    # ——— 2) Señales de ruptura — arriba y abajo ———
    df['buy_signal']  = (df['Close'] > df['prev_darvas_high']) & (df['prev_close'] <= df['prev_darvas_high'])
    df['sell_signal'] = (df['Close'] < df['prev_darvas_low'])  & (df['prev_close'] >= df['prev_darvas_low'])

    # ——— 3) Filtro de tendencia MavilimW (2 barras atrás) ———
    df['mavilimw'] = calc_mavilimw(df)
    df['trend_up']   = df['Close'] > df['mavilimw'].shift(2)
    df['trend_down'] = df['Close'] < df['mavilimw'].shift(2)

    # ——— 4) Filtro de fuerza WAE ———
    df = calc_wae(
        df,
        sensitivity=150,
        fastLength=20,
        slowLength=40,
        channelLength=boxp,  # puedes vincular también el channelLength al mismo boxp si quieres
        mult=2.0
    )
    # calcula también la componente bajista
    fastMA = df['Close'].ewm(span=20, adjust=False).mean()
    slowMA = df['Close'].ewm(span=40, adjust=False).mean()
    macd = fastMA - slowMA
    macd_shift = macd.shift(1)
    t1 = (macd - macd_shift) * 150
    df['wae_trendDown'] = np.where(t1 < 0, -t1, 0)

    df['wae_filter_buy']  = (df['wae_trendUp']   > df['wae_e1']) & (df['wae_trendUp']   > df['wae_deadzone'])
    df['wae_filter_sell'] = (df['wae_trendDown'] > df['wae_e1']) & (df['wae_trendDown'] > df['wae_deadzone'])

    # ——— 5) Señales finales (primera de cada tipo) ———
    df['buy_final']  = df['buy_signal']  & df['trend_up']   & df['wae_filter_buy']
    df['sell_final'] = df['sell_signal'] & df['trend_down'] & df['wae_filter_sell']

    # deja solo la primera de cada una
    if df['buy_final'].any():
        i = df['buy_final'].idxmax()
        df.loc[:, 'buy_final'] = False
        df.at[i, 'buy_final'] = True
    if df['sell_final'].any():
        i = df['sell_final'].idxmax()
        df.loc[:, 'sell_final'] = False
        df.at[i, 'sell_final'] = True

    # ——— 6) Tabla de señales ———
    cols = [
        "Date", "Close", "darvas_high", "darvas_low", "mavilimw",
        "wae_trendUp", "wae_e1", "wae_deadzone", "wae_trendDown",
        "buy_signal","trend_up","wae_filter_buy","buy_final",
        "sell_signal","trend_down","wae_filter_sell","sell_final"
    ]
    df_signals = df.loc[df['buy_final'] | df['sell_final'], cols]
    st.success(f"Número de señales: {len(df_signals)}")
    st.dataframe(df_signals)

    # ——— 7) Gráfico ———
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Date'], df['Close'], label="Close", color="black", zorder=1)
    ax.plot(df['Date'], df['darvas_high'], '--', label="Darvas High", zorder=1)
    ax.plot(df['Date'], df['darvas_low'],  '--', label="Darvas Low",  zorder=1)
    ax.plot(df['Date'], df['mavilimw'],    label="MavilimW", zorder=2)

    buys  = df[df['buy_final']]
    sells = df[df['sell_final']]
    ax.scatter(buys['Date'],  buys['Close'],  marker="^", color="green", s=100, label="Señal Compra", zorder=3)
    ax.scatter(sells['Date'], sells['Close'], marker="v", color="red",   s=100, label="Señal Venta",  zorder=3)

    ax.set_title(f"Darvas Box Backtest – {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
