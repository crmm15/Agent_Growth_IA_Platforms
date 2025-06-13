# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

from utils.indicators import calc_mavilimw, calc_wae
from utils.backtest_helpers import run_darvas_backtest, robust_trend_filter

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros fijos de los indicadores
    SENSITIVITY   = 150
    FAST_EMA      = 20
    SLOW_EMA      = 40
    CHANNEL_LEN   = 20
    BB_MULT       = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # ================
    # Funciones auxiliares
    # ================
    # (Ya vienen de utils; sólo se muestran aquí para que el módulo sea autónomo)
    def calc_mavilimw(df, fmal=3, smal=5):
        M1 = df['Close'].rolling(window=fmal, min_periods=fmal).mean()
        M2 = M1.rolling(window=smal, min_periods=smal).mean()
        M3 = M2.rolling(window=fmal+smal, min_periods=fmal+smal).mean()
        M4 = M3.rolling(window=fmal+2*smal, min_periods=fmal+2*smal).mean()
        M5 = M4.rolling(window=2*fmal+2*smal, min_periods=2*fmal+2*smal).mean()
        return M5

    def calc_wae(df, sensitivity=150, fastLength=20, slowLength=40, channelLength=20, mult=2.0):
        fastMA = df['Close'].ewm(span=fastLength, adjust=False).mean()
        slowMA = df['Close'].ewm(span=slowLength, adjust=False).mean()
        macd = fastMA - slowMA
        macd_shift = macd.shift(1)
        t1 = (macd - macd_shift) * sensitivity

        basis = df['Close'].rolling(window=channelLength).mean()
        dev   = df['Close'].rolling(window=channelLength).std(ddof=0) * mult
        bb_upper = basis + dev
        bb_lower = basis - dev
        e1 = bb_upper - bb_lower

        true_range = np.maximum(df['High'] - df['Low'],
                        np.maximum(
                            np.abs(df['High'] - df['Close'].shift(1)),
                            np.abs(df['Low']  - df['Close'].shift(1))
                        ))
        deadzone = pd.Series(true_range).rolling(window=100).mean().fillna(0) * 3.7

        df['wae_trendUp']   = np.where(t1 >= 0, t1, 0)
        df['wae_e1']        = e1
        df['wae_deadzone']  = deadzone
        return df

    # ================
    # UI para selección de datos
    # ================
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

    timeframes = ["1d", "1h", "15m", "5m"]
    timeframe   = st.selectbox("Temporalidad", timeframes)

    fecha_inicio = st.date_input("Desde", value=pd.to_datetime("2023-01-01"), key="darvas_ini")
    fecha_fin    = st.date_input("Hasta", value=pd.Timestamp.today(), key="darvas_fin")

    if not st.button("Ejecutar Backtest Darvas", key="ejecutar_backtest_darvas"):
        return

    st.info("Descargando datos históricos…")
    df = yf.download(
        activo,
        start=fecha_inicio,
        end=fecha_fin + pd.Timedelta(days=1),
        interval=timeframe,
        progress=False
    )

    if df.empty:
        st.error("No se encontraron datos para esa combinación de activo/timeframe.")
        return
    st.success(f"Datos descargados: {len(df)} filas")

    # Normaliza y limpia el DataFrame
    if isinstance(df.columns[0], tuple):
        df.columns = [col[0].capitalize() for col in df.columns]
    else:
        df.columns = [str(col).capitalize() for col in df.columns]

    df = df.reset_index().dropna(subset=["Close", "High", "Low"])

    # ==============================
    # Señal Darvas
    df['darvas_high']    = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
    df['darvas_low']     = df['Low'].rolling( window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
    df['prev_darvas_high'] = df['darvas_high'].shift(1)
    df['prev_close']     = df['Close'].shift(1)

    df['buy_signal']  = (
        (df['Close'] > df['prev_darvas_high']) &
        (df['prev_close'] <= df['prev_darvas_high'])
    )
    df['sell_signal'] = (
        (df['Close'] < df['darvas_low'].shift(1)) &
        (df['prev_close'] >= df['darvas_low'].shift(1))
    )

    # ==============================
    # Indicador MavilimW + filtro de tendencia
    df['mavilimw']      = calc_mavilimw(df)
    df['trend_filter']  = robust_trend_filter(df)

    # ==============================
    # Indicador WAE + filtro de fuerza
    df = calc_wae(
        df,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    df['wae_filter'] = (
        (df['wae_trendUp'] > df['wae_e1']) &
        (df['wae_trendUp'] > df['wae_deadzone'])
    )

    # ==============================
    # Señal FINAL: se cumplen Darvas + tendencia + fuerza
    df['buy_final'] = df['buy_signal'] & df['trend_filter'] & df['wae_filter']

    # ==============================
    # Tabla de señales finales (buy_final o sell_signal)
    cols_signals = [
        "Close","darvas_high","darvas_low","mavilimw",
        "wae_trendUp","wae_e1","wae_deadzone",
        "buy_signal","trend_filter","wae_filter",
        "buy_final","sell_signal"
    ]
    df_signals = df.loc[df['buy_final'] | df['sell_signal'], cols_signals]
    num_signals = len(df_signals)
    st.success(f"Número de señales finales detectadas: {num_signals}")

    st.dataframe(
        df_signals,
        column_config={
            "Darvas High":   st.column_config.NumberColumn("Darvas High"),
            "Darvas Low":    st.column_config.NumberColumn("Darvas Low"),
            "MavilimW":      st.column_config.NumberColumn("MavilimW"),
            "WAE TrendUp":   st.column_config.NumberColumn("WAE TrendUp"),
            "WAE E1":        st.column_config.NumberColumn("WAE E1"),
            "WAE DeadZone":  st.column_config.NumberColumn("WAE DeadZone"),
            "buy_signal":    st.column_config.CheckboxColumn("Buy Signal"),
            "trend_filter":  st.column_config.CheckboxColumn("Trend Filter"),
            "wae_filter":    st.column_config.CheckboxColumn("WAE Filter"),
            "buy_final":     st.column_config.CheckboxColumn("Buy Final"),
            "sell_signal":   st.column_config.CheckboxColumn("Sell Signal"),
        }
    )

    # ==============================
    # Gráfico con señales
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Date'], df['Close'],            label="Precio Close", color="black", zorder=1)
    ax.plot(df['Date'], df['darvas_high'],      label="Darvas High", color="green", linestyle="--", alpha=0.7, zorder=1)
    ax.plot(df['Date'], df['darvas_low'],       label="Darvas Low",  color="red",   linestyle="--", alpha=0.7, zorder=1)
    ax.plot(df['Date'], df['mavilimw'],         label="MavilimW",    color="white", linewidth=2, zorder=2)
    ax.scatter(df.loc[df['buy_final'], 'Date'], df.loc[df['buy_final'], 'Close'],
               marker="^", color="blue",  s=120, label="Señal Entrada", zorder=3)
    ax.scatter(df.loc[df['sell_signal'], 'Date'], df.loc[df['sell_signal'], 'Close'],
               marker="v", color="orange", s=120, label="Señal Venta",   zorder=3)
    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
