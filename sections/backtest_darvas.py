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
        # Puedes agregar más activos aquí
    }

    # Selección de activo, temporalidad y rango de fechas
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    timeframe     = st.selectbox("Temporalidad", ["1d", "1h"], index=0)
    start         = st.date_input("Desde", value=pd.to_datetime("2023-01-01"))
    end           = st.date_input("Hasta", value=pd.to_datetime("today"))

    # Ejecutar backtest
    if st.button("Ejecutar Backtest Darvas"):
        st.info("Descargando datos históricos...")
        # Carga datos históricos (retorna DataFrame con DatetimeIndex tz-aware)
        df = cargar_precio_historico(activos_predef[activo_nombre], timeframe)
        st.success(f"Datos descargados: {len(df)} filas")

        # Filtrar por rango de fechas usando date, evitando problemas tz
        df = df[(df.index.date >= start) & (df.index.date <= end)]

        # Cálculo de señales Darvas
        df['prev_close']  = df['Close'].shift(1)
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

        # Indicadores tendencia y fuerza
        df['mavilimw']     = calc_mavilimw(df)
        df['trend_filter'] = robust_trend_filter(df)
        df = calc_wae(df)
        df['wae_filter']   = (
            (df['wae_trendUp'] > df['wae_e1']) &
            (df['wae_trendUp'] > df['wae_deadzone'])
        )

        # Señal final compuesta
        df['buy_final'] = df['buy_signal'] & df['trend_filter'] & df['wae_filter']

        # Mostrar tabla de señales
        cols = [
            'Close','darvas_high','darvas_low','mavilimw',
            'wae_trendUp','wae_e1','wae_deadzone',
            'buy_signal','trend_filter','wae_filter','buy_final','sell_signal'
        ]
        df_signals = df.loc[df['buy_signal'] | df['sell_signal'], cols]
        st.success(f"Número de primeras señales detectadas: {len(df_signals)}")
        st.dataframe(df_signals.head(100))

        # Gráfico con señales de entrada y salida
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df.index, df['Close'],            label='Precio Close',   zorder=1)
        ax.plot(df.index, df['darvas_high'],       label='Darvas High',    linestyle='--', zorder=1)
        ax.plot(df.index, df['darvas_low'],        label='Darvas Low',     linestyle='--', zorder=1)
        ax.plot(df.index, df['mavilimw'],          label='MavilimW',       linewidth=2, zorder=2)
        ax.scatter(
            df.index[df['buy_final']], 
            df.loc[df['buy_final'], 'Close'],
            marker='^', color='blue', s=120, zorder=3, label='Señal Entrada'
        )
        ax.scatter(
            df.index[df['sell_signal']], 
            df.loc[df['sell_signal'], 'Close'],
            marker='v', color='orange', s=100, zorder=3, label='Señal Venta'
        )
        ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
