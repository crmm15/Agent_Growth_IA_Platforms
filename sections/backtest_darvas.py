# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

from utils.indicators import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # ------------------------------------------------------------
    # 1) Parámetros y helpers
    # ------------------------------------------------------------
    SENSITIVITY   = 150
    FAST_EMA      = 20
    SLOW_EMA      = 40
    CHANNEL_LEN   = 20
    BB_MULT       = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # ------------------------------------------------------------
    # 2) Selección de activo y rango
    # ------------------------------------------------------------
    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    timeframe     = st.selectbox("Temporalidad", ["1d", "1h", "15m", "5m"])
    start_date    = st.date_input("Desde", value=pd.to_datetime("2023-01-01"))
    end_date      = st.date_input("Hasta", value=pd.Timestamp.today())

    if not st.button("Ejecutar Backtest Darvas"):
        return

    st.info("Descargando datos históricos...")

    df = yf.download(
        activos_predef[activo_nombre],
        start=start_date,
        end=end_date + pd.Timedelta(days=1),
        interval=timeframe,
        progress=False
    )

    if df.empty:
        st.error("No se encontraron datos para ese activo/timeframe.")
        return

    st.success(f"Datos descargados: {len(df)} filas")
    st.dataframe(df)

    # ------------------------------------------------------------
    # 3) Preparación del DataFrame
    # ------------------------------------------------------------
    # Normalizar nombres de columnas (y quitar multiindex si existe)
    cols = df.columns
    if isinstance(cols[0], tuple):
        df.columns = [c[0].capitalize() for c in cols]
    else:
        df.columns = [str(c).capitalize() for c in cols]
    df = df.reset_index().dropna(subset=["Close", "High", "Low"])
    df["prev_close"]       = df["Close"].shift(1)
    df["darvas_high"]      = df["High"].rolling(DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
    df["darvas_low"]       = df["Low"].rolling(DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
    df["prev_darvas_high"] = df["darvas_high"].shift(1)
    df["prev_darvas_low"]  = df["darvas_low"].shift(1)

    # ------------------------------------------------------------
    # 4) Señales Darvas (buy_signal / sell_signal)
    # ------------------------------------------------------------
    df["buy_signal"]  = (
        (df["Close"] > df["prev_darvas_high"]) &
        (df["prev_close"] <= df["prev_darvas_high"])
    )
    df["sell_signal"] = (
        (df["Close"] < df["prev_darvas_low"]) &
        (df["prev_close"] >= df["prev_darvas_low"])
    )

    # ------------------------------------------------------------
    # 5) Indicador MavilimW (tendencia), con lag de 2 velas
    # ------------------------------------------------------------
    df["mavilimw"] = calc_mavilimw(df)["Close"].rename("mavilimw").shift(2)

    # Filtro de tendencia: close arriba/bajo de MavilimW(lag2)
    df["trend_filter_buy"]  = df["Close"] > df["mavilimw"]
    df["trend_filter_sell"] = df["Close"] < df["mavilimw"]

    # ------------------------------------------------------------
    # 6) Indicador WAE (fuerza), sin lag
    # ------------------------------------------------------------
    df = calc_wae(
        df,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    df["wae_filter_buy"]  = (df["wae_trendUp"] > df["wae_e1"]) & (df["wae_trendUp"] > df["wae_deadzone"])
    df["wae_filter_sell"] = ~df["wae_filter_buy"]  # para venta invertimos

    # ------------------------------------------------------------
    # 7) Señales finales, solo primera ocurrencia
    # ------------------------------------------------------------
    df["buy_final"]  = df["buy_signal"]  & df["trend_filter_buy"]  & df["wae_filter_buy"]
    df["sell_final"] = df["sell_signal"] & df["trend_filter_sell"] & df["wae_filter_sell"]

    # Mantengo solo la PRIMERA buy_final y la PRIMERA sell_final
    first_buy_idx  = df.index[df["buy_final"]].min()
    first_sell_idx = df.index[df["sell_final"]].min()

    df["buy_final"]  = False
    df["sell_final"] = False
    if pd.notna(first_buy_idx):
        df.at[first_buy_idx, "buy_final"] = True
    if pd.notna(first_sell_idx):
        df.at[first_sell_idx, "sell_final"] = True

    # ------------------------------------------------------------
    # 8) Mostrar tabla de señales
    # ------------------------------------------------------------
    signal_cols = [
        "Close", "darvas_high", "darvas_low",
        "mavilimw", "wae_trendUp", "wae_e1", "wae_deadzone",
        "buy_signal", "trend_filter_buy", "wae_filter_buy", "buy_final",
        "sell_signal", "trend_filter_sell", "wae_filter_sell", "sell_final",
    ]
    df_signals = df.loc[df["buy_final"] | df["sell_final"], signal_cols]
    st.success(f"Señales finales detectadas: {len(df_signals)}")
    st.dataframe(df_signals)

    # ------------------------------------------------------------
    # 9) Gráfico final con marcadores
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["Date"], df["Close"], label="Precio Close", color="black", zorder=1)
    ax.plot(df["Date"], df["darvas_high"], label="Darvas High", color="green",
            linestyle="--", alpha=0.7, zorder=1)
    ax.plot(df["Date"], df["darvas_low"],  label="Darvas Low",  color="red",
            linestyle="--", alpha=0.7, zorder=1)
    ax.plot(df["Date"], df["mavilimw"],     label="MavilimW (lag2)", color="white",
            linewidth=2, zorder=2)

    # Sólo los puntos finales
    buys  = df[df["buy_final"]]
    sells = df[df["sell_final"]]
    ax.scatter(buys["Date"],  buys["Close"],  marker="^", color="blue",
               s=120, label="Señal Compra",  zorder=3)
    ax.scatter(sells["Date"], sells["Close"], marker="v", color="orange",
               s=120, label="Señal Venta",   zorder=3)

    ax.set_title(f"Darvas Box Backtest – {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
