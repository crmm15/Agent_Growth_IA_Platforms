# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae


def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # ==============================
    # Selección de parámetros
    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY",
    }
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    timeframe = st.selectbox("Temporalidad", ["1d", "1h", "15m", "5m"])
    fecha_inicio = st.date_input("Desde", value=pd.Timestamp(2023, 1, 1))
    fecha_fin = st.date_input("Hasta", value=pd.Timestamp.today())

    if st.button("Ejecutar Backtest Darvas", key="ejecutar_backtest_darvas"):
        st.info("Descargando datos históricos...")
        df = cargar_precio_historico(activos_predef[activo_nombre], timeframe, fecha_inicio, fecha_fin)
        if df.empty:
            st.error("No se encontraron datos para esa configuración.")
            return
        # Quitar zona horaria si existe
        if hasattr(df.index, 'tz'):
            df.index = df.index.tz_localize(None)

        # Normalizar columnas si fuera necesario
        df = df.rename(columns={c: c.capitalize() for c in df.columns})

        # ==============================
        # Indicador Darvas
        DARVAS_WINDOW = 20
        df['darvas_high'] = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
        df['darvas_low']  = df['Low'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
        df['prev_darvas_high'] = df['darvas_high'].shift(1)
        df['prev_close']       = df['Close'].shift(1)
        df['buy_signal']  = (df['Close'] > df['prev_darvas_high']) & (df['prev_close'] <= df['prev_darvas_high'])
        df['sell_signal'] = (df['Close'] < df['darvas_low'].shift(1)) & (df['prev_close'] >= df['darvas_low'].shift(1))

        # ==============================
        # Indicador MavilimW (tendencia)
        df['mavilimw'] = calc_mavilimw(df)
        df['trend_filter'] = df['Close'] > df['mavilimw']
        df['trend_filter_sell'] = df['Close'] < df['mavilimw']

        # ==============================
        # Indicador WAE (fuerza/momentum)
        df = calc_wae(df)
        df['wae_filter'] = (df['wae_trendUp'] > df['wae_e1']) & (df['wae_trendUp'] > df['wae_deadzone'])
        # Para venta usamos sólo la tendencia (no pedimos WAE negativo de momento)

        # ==============================
        # Señales finales
        df['buy_final']  = df['buy_signal']  & df['trend_filter']  & df['wae_filter']
        df['sell_final'] = df['sell_signal'] & df['trend_filter_sell']

        # Sólo primera señal válida de compra y de venta
        for col in ['buy_final', 'sell_final']:
            idxs = df.index[df[col]].tolist()
            if idxs:
                first = idxs[0]
                df[col] = False
                df.at[first, col] = True

        # ==============================
        # Mostrar tabla de señales
        cols = [
            'Close','darvas_high','darvas_low','mavilimw',
            'wae_trendUp','wae_e1','wae_deadzone',
            'buy_signal','trend_filter','wae_filter','buy_final',
            'sell_signal','trend_filter_sell','sell_final'
        ]
        df_signals = df.loc[df['buy_final'] | df['sell_final'], cols].copy()
        st.success(f"Señales detectadas (compra y venta): {len(df_signals)}")
        st.dataframe(df_signals)

        # ==============================
        # Gráfico de backtest
        fig, ax = plt.subplots(figsize=(12,5))
        ax.plot(df.index, df['Close'], label="Precio Close", color='black')
        ax.plot(df.index, df['darvas_high'], label="Darvas High", linestyle='--', alpha=0.7)
        ax.plot(df.index, df['darvas_low'],  label="Darvas Low",  linestyle='--', alpha=0.7)
        ax.plot(df.index, df['mavilimw'],   label="MavilimW", linewidth=2)
        ax.scatter(df.index[df['buy_final']],  df.loc[df['buy_final'],'Close'],  marker='^', color='green', s=100, label='Señal Compra')
        ax.scatter(df.index[df['sell_final']], df.loc[df['sell_final'],'Close'], marker='v', color='red',   s=100, label='Señal Venta')
        ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
