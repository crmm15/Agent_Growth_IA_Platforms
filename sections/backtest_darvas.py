# sections/backtest_darvas.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators    import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # 1) Parámetros de la UI
    activos = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Activo", list(activos.keys()))
    simbolo       = activos[activo_nombre]
    timeframe     = st.selectbox("Temporalidad", ["1d", "1h", "15m"])
    start         = st.date_input("Desde",  pd.to_datetime("2023-01-01"))
    end           = st.date_input("Hasta",  pd.to_datetime("today"))
    boxp          = st.slider("Largo Darvas Box (boxp)", 1, 50, 5)

    if not st.button("Ejecutar Backtest"):
        return

    # 2) Parámetros fijos para los indicadores
    SENS, F_EMA, S_EMA, CH_LEN, BB_M = 150, 20, 40, 20, 2.0

    # 3) Descarga de datos históricos
    st.info("Descargando datos históricos…")
    df = cargar_precio_historico(simbolo, timeframe, start, end)
    if df is None or df.empty:
        st.error("No se encontraron datos para esa configuración.")
        return
    st.success(f"Datos descargados: {len(df)} filas")

    # 4) Formateo y muestra de la tabla de históricos usando pandas Styler
    df_hist = df.copy()
    df_hist.index = pd.to_datetime(df_hist.index).tz_localize(None)
    df_hist = df_hist.reset_index().rename(columns={"index": "Date"})
    fmt_hist = {
        "Date"  : "{:%d/%m/%Y}",
        "Open"  : "{:,.2f}",
        "High"  : "{:,.2f}",
        "Low"   : "{:,.2f}",
        "Close" : "{:,.2f}",
        "Volume": "{:,.0f}",
    }
    st.dataframe(
        df_hist.style.format(fmt_hist),
        use_container_width=True
    )

    # 5) Cálculos de la estrategia
    df = df.reset_index(drop=False).dropna(subset=["Close", "High", "Low"])
    df["darvas_high"]      = df["High"].rolling(window=boxp, min_periods=boxp).max()
    df["darvas_low"]       = df["Low"].rolling(window=boxp, min_periods=boxp).min()
    df["prev_dh"]          = df["darvas_high"].shift(1)
    df["prev_dl"]          = df["darvas_low"].shift(1)
    df["prev_c"]           = df["Close"].shift(1)

    df["buy_sig"]  = (df["Close"] > df["prev_dh"]) & (df["prev_c"] <= df["prev_dh"])
    df["sell_sig"] = (df["Close"] < df["prev_dl"]) & (df["prev_c"] >= df["prev_dl"])

    df["mav"]        = calc_mavilimw(df)
    df["trend_up"]   = df["Close"] > df["mav"].shift(2)
    df["trend_down"] = df["Close"] < df["mav"].shift(2)

    df = calc_wae(df,
                 sensitivity=SENS,
                 fastLength=F_EMA,
                 slowLength=S_EMA,
                 channelLength=CH_LEN,
                 mult=BB_M)

    fast    = df["Close"].ewm(span=F_EMA, adjust=False).mean()
    slow    = df["Close"].ewm(span=S_EMA, adjust=False).mean()
    macd    = fast - slow
    t1      = (macd - macd.shift(1)) * SENS
    df["wae_down"] = np.where(t1 < 0, -t1, 0)

    df["w_buy"]  = (df["wae_trendUp"]   > df["wae_e1"]) & (df["wae_trendUp"]   > df["wae_deadzone"])
    df["w_sell"] = (df["wae_down"]      > df["wae_e1"]) & (df["wae_down"]      > df["wae_deadzone"])

    df["buy_f"]  = df["buy_sig"]  & df["trend_up"]   & df["w_buy"]
    df["sell_f"] = df["sell_sig"] & df["trend_down"] & df["w_sell"]

    # 6) Preparar y mostrar la tabla de señales con formateo
    df_sig = (
        df.loc[df["buy_f"] | df["sell_f"]]
          .reset_index(drop=False)
          .rename(columns={"index": "Date"})
    )
    df_sig["Date"] = pd.to_datetime(df_sig["Date"]).tz_localize(None).dt.strftime("%d/%m/%Y")

    fmt_sig = {
        "Date"         : "{:%d/%m/%Y}",
        "Close"        : "{:,.2f}",
        "darvas_high"  : "{:,.2f}",
        "darvas_low"   : "{:,.2f}",
        "mav"          : "{:,.2f}",
        "wae_trendUp"  : "{:,.2f}",
        "wae_e1"       : "{:,.2f}",
        "wae_deadzone" : "{:,.2f}",
        "wae_down"     : "{:,.2f}",
    }
    st.success(f"Número de señales detectadas: {len(df_sig)}")
    st.dataframe(
        df_sig.style.format(fmt_sig),
        use_container_width=True
    )

    # 7) Gráfico de backtest
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["Close"],       label="Precio Close", color="black", zorder=1)
    ax.plot(df.index, df["darvas_high"],  "--", label="Darvas High", zorder=1)
    ax.plot(df.index, df["darvas_low"],   "--", label="Darvas Low",  zorder=1)
    ax.plot(df.index, df["mav"],          "-",  label="MavilimW",    linewidth=2, zorder=2)
    ax.scatter(df.index[df["buy_f"]],  df["Close"][df["buy_f"]],  marker="^", color="green", s=100, label="Señal Compra", zorder=3)
    ax.scatter(df.index[df["sell_f"]], df["Close"][df["sell_f"]], marker="v", color="red",   s=100, label="Señal Venta",  zorder=3)
    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
