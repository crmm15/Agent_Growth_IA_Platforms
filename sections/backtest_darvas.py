# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from yfinance import Ticker

from utils.indicators import calc_mavilimw, calc_wae


def robust_trend_filter(df):
    trend = pd.Series(False, index=df.index)
    mask = df['mavilimw'].notna()
    trend[mask] = df.loc[mask, 'Close'] > df.loc[mask, 'mavilimw']
    first_valid = df['mavilimw'].first_valid_index()
    if first_valid is not None and first_valid >= 1:
        for i in range(first_valid - 1, first_valid + 1):
            if all(
                df.loc[j, 'Close'] > df.loc[first_valid, 'mavilimw']
                for j in range(i, first_valid + 1)
            ):
                trend.iloc[i] = True
    return trend


def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Selección de ticker y periodo
    activo_nombre = st.text_input("Ticker para backtest", "AAPL")
    timeframe = st.selectbox("Periodo histórico", ["1mo", "3mo", "6mo", "1y"], index=2)

    if st.button("Ejecutar backtest"):
        # Carga de datos
        df = Ticker(activo_nombre).history(period=timeframe)
        if df.empty:
            st.error("No se obtuvieron datos para el ticker especificado.")
            return

        # Señales Darvas
        df['prev_close'] = df['Close'].shift(1)
        df['darvas_high'] = df['High'].rolling(20).max()
        df['darvas_low']  = df['Low'].rolling(20).min()
        df['buy_signal']  = (
            (df['Close'] > df['darvas_high'].shift(1)) &
            (df['prev_close'] <= df['darvas_high'].shift(1))
        )
        df['sell_signal'] = (
            (df['Close'] < df['darvas_low'].shift(1)) &
            (df['prev_close'] >= df['darvas_low'].shift(1))
        )

        # Indicadores
        df['mavilimw']     = calc_mavilimw(df)
        df['trend_filter'] = robust_trend_filter(df)
        df = calc_wae(df)
        df['wae_filter']   = (
            (df['wae_trendUp'] > df['wae_e1']) &
            (df['wae_trendUp'] > df['wae_deadzone'])
        )

        # Señal final
        df['buy_final'] = (
            df['buy_signal'] & df['trend_filter'] & df['wae_filter']
        )

        # Tabla de señales
        cols = [
            'Close','darvas_high','darvas_low','mavilimw',
            'wae_trendUp','wae_e1','wae_deadzone',
            'buy_signal','trend_filter','wae_filter','buy_final','sell_signal'
        ]
        df_signals = df.loc[df['buy_signal'] | df['sell_signal'], cols]
        st.success(f"Señales detectadas: {len(df_signals)}")
        st.dataframe(df_signals.head(100))

        # Gráfico
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df.index, df['Close'], label='Precio Close', color='black', zorder=1)
        ax.plot(df.index, df['darvas_high'], label='Darvas High', color='green', linestyle='--', alpha=0.7, zorder=1)
        ax.plot(df.index, df['darvas_low'], label='Darvas Low', color='red', linestyle='--', alpha=0.7, zorder=1)
        ax.plot(df.index, df['mavilimw'], label='MavilimW', color='blue', linewidth=2, zorder=2)
        ax.scatter(df.index[df['buy_final']], df.loc[df['buy_final'], 'Close'], label='Entrada', marker='^', color='blue', s=120, zorder=3)
        ax.scatter(df.index[df['sell_signal']], df.loc[df['sell_signal'], 'Close'], label='Salida', marker='v', color='orange', s=100, zorder=3)
        ax.set_title(f"Backtest Darvas - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
