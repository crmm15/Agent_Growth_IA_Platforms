# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

from utils.indicators import calc_mavilimw, calc_wae
from utils.backtest_helpers import run_darvas_backtest, robust_trend_filter

def backtest_darvas():
    seccion == "Backtesting Darvas"  # placeholder
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros fijos de los indicadores
    SENSITIVITY = 150
    FAST_EMA = 20
    SLOW_EMA = 40
    CHANNEL_LEN = 20
    BB_MULT = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # Indicador MavilimW (tendencia)
    df['mavilimw'] = calc_mavilimw(df)

    # Filtro tendencia robusto para primeras velas
    def robust_trend_filter(df):
        trend = pd.Series(False, index=df.index)
        trend[df['mavilimw'].notna()] = (
            df.loc[df['mavilimw'].notna(), 'Close'] >
            df.loc[df['mavilimw'].notna(), 'mavilimw']
        )
        first_valid = df['mavilimw'].first_valid_index()
        if first_valid is not None and first_valid >= 1:
            for i in range(first_valid - 1, first_valid + 1):
                if i >= 0 and all(
                    df.loc[j, 'Close'] > df.loc[first_valid, 'mavilimw']
                    for j in range(i, first_valid + 1)
                ):
                    trend.iloc[i] = True
        return trend

    df['trend_filter'] = robust_trend_filter(df)

    # Indicador WAE (fuerza/momentum)
    df = calc_wae(
        df,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    # Filtro fuerza: solo si el histograma (trendUp) está sobre ExplosionLine y DeadZone
    df['wae_filter'] = (
        (df['wae_trendUp'] > df['wae_e1']) &
        (df['wae_trendUp'] > df['wae_deadzone'])
    )

    # Señal final: SOLO cuando las tres condiciones se cumplen
    df['buy_final'] = df['buy_signal'] & df['trend_filter'] & df['wae_filter']

    # Tabla de señales (solo filas con buy o sell)
    cols_signals = [
        "Close", "darvas_high", "darvas_low", "mavilimw", "wae_trendUp", "wae_e1", "wae_deadzone",
        "buy_signal", "trend_filter", "wae_filter", "buy_final", "sell_signal"
    ]
    df_signals = df.loc[
        df['buy_signal'] | df['sell_signal'], cols_signals
    ].copy()
    num_signals = len(df_signals)
    st.success(f"Número de primeras señales detectadas: {num_signals}")

    st.dataframe(
        df_signals.head(100),
        column_config={
            "Close": st.column_config.NumberColumn(
                "Close", help="Precio de cierre del periodo."),
            "darvas_high": st.column_config.NumberColumn(
                "darvas_high", help="Máximo de los últimos 20 periodos (techo Darvas)."),
            "darvas_low": st.column_config.NumberColumn(
                "darvas_low", help="Mínimo de los últimos 20 periodos (base Darvas)."),
            "mavilimw": st.column_config.NumberColumn(
                "mavilimw", help="Línea MavilimW: tendencia de fondo suavizada (cálculo anidado de medias)."),
            "wae_trendUp": st.column_config.NumberColumn(
                "wae_trendUp", help="Histograma WAE positivo: fuerza alcista."),
            "wae_e1": st.column_config.NumberColumn(
                "wae_e1", help="Explosion Line: volatilidad/fuerza según banda de Bollinger."),
            "wae_deadzone": st.column_config.NumberColumn(
                "wae_deadzone", help="DeadZone: umbral mínimo para considerar fuerza relevante."),
            "buy_signal": st.column_config.CheckboxColumn(
                "buy_signal", help="True si el cierre rompe el máximo Darvas anterior (solo la primera vez)."),
            "trend_filter": st.column_config.CheckboxColumn(
                "trend_filter", help="True si la tendencia es alcista (Close > MavilimW)."),
            "wae_filter": st.column_config.CheckboxColumn(
                "wae_filter", help="True si el histograma supera ambos umbrales de fuerza."),
            "buy_final": st.column_config.CheckboxColumn(
                "buy_final", help="True si TODAS las condiciones de entrada están OK (ruptura + tendencia + fuerza)."),
            "sell_signal": st.column_config.CheckboxColumn(
                "sell_signal", help="True si el cierre rompe el mínimo Darvas anterior (solo la primera vez)."),
        }
    )

    # Plot gráfico visual
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(
        df.index, df['Close'], label="Precio Close",
        color="black", zorder=1
    )
    ax.plot(
        df.index, df['darvas_high'], label="Darvas High",
        color="green", linestyle="--", alpha=0.7, zorder=1
    )
    ax.plot(
        df.index, df['darvas_low'], label="Darvas Low",
        color="red", linestyle="--", alpha=0.7, zorder=1
    )
    ax.plot(
        df.index, df['mavilimw'], label="MavilimW (Tendencia)",
        color="white", linewidth=2, zorder=2
    )
    ax.scatter(
        df.index[df['buy_final']], df.loc[df['buy_final'], 'Close'],
        label="Señal Entrada", marker="^",
        color="blue", s=120, zorder=3
    )
    ax.scatter(
        df.index[df['sell_signal']], df.loc[df['sell_signal'], 'Close'],
        label="Señal Venta", marker="v",
        color="orange", s=100, zorder=3
    )
    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
