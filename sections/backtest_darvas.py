# sections/backtest_darvas.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # ——— UI ———
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
    end   = st.date_input("Hasta", value=pd.to_datetime("today"),      key="darvas_end")

    # Slider para el largo del Darvas Box
    boxp = st.slider("Largo del Darvas Box (boxp)", min_value=2, max_value=50, value=5)

    if not st.button("Ejecutar Backtest Darvas"):
        return

    # ——— Parámetros fijos ———
    SENSITIVITY = 150
    FAST_EMA    = 20
    SLOW_EMA    = 40
    CHANNEL_LEN = 20
    BB_MULT     = 2.0

    # ——— Descarga de datos ———
    st.info("Descargando datos históricos...")
    df = cargar_precio_historico(activo, timeframe, start, end)
    if df is None or df.empty:
        st.error("No se encontraron datos para esa configuración.")
        return

    st.success(f"Datos descargados: {len(df)} filas")
    st.dataframe(df)

    # ——— Normalizar y limpiar ———
    df = df.reset_index(drop=False).dropna(subset=["Open","High","Low","Close"])

    # ——— 1) Darvas Box usando el largo boxp ———
    df["darvas_high"]      = df["High"].rolling(window=boxp, min_periods=boxp).max()
    df["darvas_low"]       = df["Low"].rolling(window=boxp, min_periods=boxp).min()
    df["prev_darvas_high"] = df["darvas_high"].shift(1)
    df["prev_darvas_low"]  = df["darvas_low"].shift(1)
    df["prev_close"]       = df["Close"].shift(1)

    # ——— 2) Señales de ruptura Darvas ———
    df["buy_signal"]  = (
        (df["Close"] > df["prev_darvas_high"]) &
        (df["prev_close"] <= df["prev_darvas_high"])
    )
    df["sell_signal"] = (
        (df["Close"] < df["prev_darvas_low"]) &
        (df["prev_close"] >= df["prev_darvas_low"])
    )

    # ——— 3) Filtro de tendencia con MavilimW (dos barras atrás) ———
    df["mavilimw"]    = calc_mavilimw(df)
    df["trend_up"]    = df["Close"] > df["mavilimw"].shift(2)
    df["trend_down"]  = df["Close"] < df["mavilimw"].shift(2)

    # ——— 4) Filtro de fuerza con WAE ———
    df = calc_wae(
        df,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    # Calculamos momentum bajista para WAE
    fastMA     = df["Close"].ewm(span=FAST_EMA, adjust=False).mean()
    slowMA     = df["Close"].ewm(span=SLOW_EMA, adjust=False).mean()
    macd       = fastMA - slowMA
    macd_shift = macd.shift(1)
    t1         = (macd - macd_shift) * SENSITIVITY
    df["wae_trendDown"] = np.where(t1 < 0, -t1, 0)

    df["wae_filter_buy"]  = (
        (df["wae_trendUp"]   > df["wae_e1"]) &
        (df["wae_trendUp"]   > df["wae_deadzone"])
    )
    df["wae_filter_sell"] = (
        (df["wae_trendDown"] > df["wae_e1"]) &
        (df["wae_trendDown"] > df["wae_deadzone"])
    )

    # ——— 5) Señales finales (solo primera de cada tipo) ———
    df["buy_final"]  = df["buy_signal"]  & df["trend_up"]   & df["wae_filter_buy"]
    df["sell_final"] = df["sell_signal"] & df["trend_down"] & df["wae_filter_sell"]

    # Solo la PRIMERA señal de cada tipo
    if df["buy_final"].any():
        idx = df["buy_final"].idxmax()
        df.loc[:, "buy_final"] = False
        df.at[idx, "buy_final"] = True
    if df["sell_final"].any():
        idx = df["sell_final"].idxmax()
        df.loc[:, "sell_final"] = False
        df.at[idx, "sell_final"] = True

    # ——— 6) Tabla de señales ———
    cols = [
        "Date", "Close",
        "darvas_high", "darvas_low", "mavilimw",
        "wae_trendUp", "wae_e1", "wae_deadzone", "wae_trendDown",
        "buy_signal", "trend_up", "wae_filter_buy", "buy_final",
        "sell_signal", "trend_down", "wae_filter_sell", "sell_final"
    ]
    df_signals = df.loc[df["buy_final"] | df["sell_final"], cols].copy()

    st.success(f"Número de señales detectadas: {len(df_signals)}")
    st.dataframe(df_signals)

    # ——— 7) Gráfico de Backtest ———
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["Date"], df["Close"],         label="Precio Close", zorder=1, color="black")
    ax.plot(df["Date"], df["darvas_high"],   "--",   label="Darvas High",  zorder=1)
    ax.plot(df["Date"], df["darvas_low"],    "--",   label="Darvas Low",   zorder=1)
    ax.plot(df["Date"], df["mavilimw"],       "-",   label="MavilimW",      zorder=2, linewidth=2)

    # Señales
    buy_idx  = df.index[df["buy_final"]]
    sell_idx = df.index[df["sell_final"]]
    ax.scatter(
        df.loc[buy_idx, "Date"],  df.loc[buy_idx, "Close"],
        marker="^", s=100, color="green", label="Señal Compra", zorder=3
    )
    ax.scatter(
        df.loc[sell_idx, "Date"], df.loc[sell_idx, "Close"],
        marker="v", s=100, color="red",   label="Señal Venta",  zorder=3
    )

    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
