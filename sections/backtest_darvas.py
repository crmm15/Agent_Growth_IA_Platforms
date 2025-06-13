# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae
from utils.backtest_helpers import robust_trend_filter

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros fijos de Darvas
    DARVAS_WINDOW = 20

    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        # Agrega más activos si lo deseas
    }

    # 1) Selección de activo, temporalidad y rango de fechas
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    timeframe     = st.selectbox("Temporalidad", ["1d", "1h"], index=0)
    start         = st.date_input("Desde", value=pd.to_datetime("2023-01-01"))
    end           = st.date_input("Hasta", value=pd.to_datetime("today"))

    # 2) Ejecutar backtest
    if st.button("Ejecutar Backtest Darvas"):
        st.info("Descargando datos históricos...")
        # Carga datos usando ticker e intervalo
        df = cargar_precio_historico(activos_predef[activo_nombre], timeframe)

        # Remover zona horaria para evitar discrepancia tz-aware vs tz-naive
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # Filtrado por rango de fechas (índice datetime)
        df = df.loc[start:end]
        st.success(f"Datos descargados: {len(df)} filas")

        # 3) Cálculo de señales Darvas
        df['prev_close'] = df['Close'].shift(1)
        df['darvas_high'] = df['High'].rolling(DARVAS_WINDOW).max()
        df['darvas_low']  = df['Low'].rolling(DARVAS_WINDOW).min()
        df['buy_signal']  = (
            (df['Close'] > df['darvas_high'].shift(1)) &
            (df['prev_close'] <= df['darvas_high'].shift(1))
        )
        df['sell_signal'] = (
            (df['Close'] < df['darvas_low'].shift(1)) &
            (df['prev_close'] >= df['darvas_low'].shift(1))
        )

        # 4) Indicadores de tendencia y fuerza
        df['mavilimw']     = calc_mavilimw(df)
        df['trend_filter'] = robust_trend_filter(df)
        df = calc_wae(df)
        df['wae_filter']   = (
            (df['wae_trendUp'] > df['wae_e1']) &
            (df['wae_trendUp'] > df['wae_deadzone'])
        )

        # 5) Señal final compuesta
        df['buy_final'] = df['buy_signal'] & df['trend_filter'] & df['wae_filter']

        # 6) Mostrar tabla de señales
        cols = [
            'Close','darvas_high','darvas_low','mavilimw',
            'wae_trendUp','wae_e1','wae_deadzone',
            'buy_signal','trend_filter','wae_filter','buy_final','sell_signal'
        ]
        df_signals = df.loc[df['buy_signal'] | df['sell_signal'], cols]
        st.success(f"Número de primeras señales detectadas: {len(df_signals)}")
        st.dataframe(df_signals.head(100))

        # 7) Gráfico con entradas y salidas
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df.index, df['Close'],   label="Precio Close",   zorder=1)
        ax.plot(df.index, df['darvas_high'], label="Darvas High", linestyle="--", zorder=1)
        ax.plot(df.index, df['darvas_low'],  label="Darvas Low",  linestyle="--", zorder=1)
        ax.plot(df.index, df['mavilimw'],    label="MavilimW",      linewidth=2, zorder=2)
        ax.scatter(df.index[df['buy_final']], df.loc[df['buy_final'], 'Close'],
                   marker="^", label="Señal Entrada", zorder=3)
        ax.scatter(df.index[df['sell_signal']], df.loc[df['sell_signal'], 'Close'],
                   marker="v", label="Señal Venta",  zorder=3)
        ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
