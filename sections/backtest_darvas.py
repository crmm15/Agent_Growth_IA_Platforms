# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import datetime

from utils.indicators import calc_mavilimw, calc_wae
from utils.backtest_helpers import robust_trend_filter


def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros de los indicadores
    SENSITIVITY = 150
    FAST_EMA = 20
    SLOW_EMA = 40
    CHANNEL_LEN = 20
    BB_MULT = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # ==============================
    # UI: selección de activo, timeframe y fechas
    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    timeframe     = st.selectbox("Temporalidad", ["1d", "1h", "15m", "5m"], index=0)
    fecha_inicio  = st.date_input("Desde", value=datetime.date(2023, 1, 1), key="darvas_ini")
    fecha_fin     = st.date_input("Hasta", value=datetime.date.today(),    key="darvas_fin")

    if st.button("Ejecutar Backtest Darvas", key="ejecutar_backtest_darvas"):
        st.info("Descargando datos históricos...")

        # 1) Descargar datos
        df = yf.download(
            activos_predef[activo_nombre],
            start=fecha_inicio,
            end=fecha_fin + datetime.timedelta(days=1),
            interval=timeframe,
            progress=False
        )

        if df.empty:
            st.error("No se encontraron datos para ese activo y timeframe. Prueba otra combinación.")
            return

        st.success(f"Datos descargados: {len(df)} filas")
        st.dataframe(df)

        # Normaliza columnas en caso de MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].capitalize() for col in df.columns]
        else:
            df.columns = [str(col).capitalize() for col in df.columns]

        # Verifica columnas requeridas
        required_cols = ["Close", "High", "Low"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"El DataFrame descargado NO tiene todas las columnas requeridas: {required_cols}.")
            st.dataframe(df)
            return

        df = df.reset_index(drop=False)
        df = df.dropna(subset=required_cols)

        # ==============================
        # 2) Señales Darvas
        df['darvas_high']   = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
        df['darvas_low']    = df['Low'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
        df['prev_darvas_high'] = df['darvas_high'].shift(1)
        df['prev_close']    = df['Close'].shift(1)

        df['buy_signal']  = (
            (df['Close'] > df['prev_darvas_high']) &
            (df['prev_close'] <= df['prev_darvas_high'])
        )
        df['sell_signal'] = (
            (df['Close'] < df['darvas_low'].shift(1)) &
            (df['prev_close'] >= df['darvas_low'].shift(1))
        )

        # ==============================
        # 3) Indicador de tendencia y fuerza
        df['mavilimw']     = calc_mavilimw(df)
        df['trend_filter'] = robust_trend_filter(df)
        df = calc_wae(df, sensitivity=SENSITIVITY, fastLength=FAST_EMA, slowLength=SLOW_EMA, channelLength=CHANNEL_LEN, mult=BB_MULT)
        df['wae_filter']   = (
            (df['wae_trendUp'] > df['wae_e1']) &
            (df['wae_trendUp'] > df['wae_deadzone'])
        )

        # ==============================
        # 4) Señal final compuesta
        df['buy_final'] = df['buy_signal'] & df['trend_filter'] & df['wae_filter']

        # ==============================
        # 5) Mostrar tabla de señales
        cols_signals = [
            "Close", "darvas_high", "darvas_low", "mavilimw", "wae_trendUp", "wae_e1", "wae_deadzone",
            "buy_signal", "trend_filter", "wae_filter", "buy_final", "sell_signal"
        ]
        df_signals = df.loc[df['buy_signal'] | df['sell_signal'], cols_signals].copy()
        st.success(f"Número de primeras señales detectadas: {len(df_signals)}")
        st.dataframe(
            df_signals.head(100),
            column_config={
                "Close": st.column_config.NumberColumn("Close"),
                "darvas_high": st.column_config.NumberColumn("Darvas High"),
                "darvas_low": st.column_config.NumberColumn("Darvas Low"),
                "mavilimw": st.column_config.NumberColumn("MavilimW"),
                "wae_trendUp": st.column_config.NumberColumn("WAE TrendUp"),
                "wae_e1": st.column_config.NumberColumn("WAE E1"),
                "wae_deadzone": st.column_config.NumberColumn("WAE DeadZone"),
                "buy_signal": st.column_config.CheckboxColumn("Buy Signal"),
                "trend_filter": st.column_config.CheckboxColumn("Trend Filter"),
                "wae_filter": st.column_config.CheckboxColumn("WAE Filter"),
                "buy_final": st.column_config.CheckboxColumn("Buy Final"),
                "sell_signal": st.column_config.CheckboxColumn("Sell Signal")
            }
        )

        # ==============================
        # 6) Gráfico de precio y señales
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df.index, df['Close'], label="Precio Close", color="black", zorder=1)
        ax.plot(df.index, df['darvas_high'], label="Darvas High", color="green", linestyle="--", alpha=0.7, zorder=1)
        ax.plot(df.index, df['darvas_low'], label="Darvas Low", color="red", linestyle="--", alpha=0.7, zorder=1)
        ax.plot(df.index, df['mavilimw'], label="MavilimW (Tendencia)", color="white", linewidth=2, zorder=2)
        ax.scatter(df.index[df['buy_final']], df.loc[df['buy_final'], 'Close'], marker="^", color="blue", s=120, zorder=3, label="Señal Entrada")
        ax.scatter(df.index[df['sell_signal']], df.loc[df['sell_signal'], 'Close'], marker="v", color="orange", s=100, zorder=3, label="Señal Venta")
        ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
