import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import datetime

from utils.indicators import calc_mavilimw, calc_wae

# -------------------------
# Backtesting Darvas Module
# -------------------------
def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros de selección
    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    timeframe = st.selectbox("Temporalidad", ["1d", "1h", "15m", "5m"])
    fecha_inicio = st.date_input("Desde", value=datetime.date(2023, 1, 1), key="darvas_ini")
    fecha_fin = st.date_input("Hasta", value=datetime.date.today(), key="darvas_fin")

    if st.button("Ejecutar Backtest Darvas", key="btn_backtest_darvas"):
        st.info("Descargando datos históricos...")
        simbolo = activos_predef[activo_nombre]
        # Descargar datos
        df = yf.download(
            simbolo,
            start=fecha_inicio,
            end=fecha_fin + datetime.timedelta(days=1),
            interval=timeframe,
            progress=False
        )
        if df.empty:
            st.error("No se encontraron datos para esa combinación. Intenta otro rango o activo.")
            return
        st.success(f"Datos descargados: {len(df)} filas")
        st.dataframe(df)

        # Normalizar nombres de columnas
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].capitalize() for col in df.columns]
        else:
            df.columns = [str(col).capitalize() for col in df.columns]

        # Requerimos Close, High, Low
        for col in ["Close", "High", "Low"]:
            if col not in df.columns:
                st.error(f"Falta la columna '{col}'. No se puede continuar.")
                return

        # Preparar DataFrame
        df = df.reset_index(drop=False).dropna(subset=["Close", "High", "Low"])

        # Parámetros Darvas
        DARVAS_WINDOW = 20
        df['darvas_high'] = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
        df['darvas_low'] = df['Low'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
        df['prev_darvas_high'] = df['darvas_high'].shift(1)
        df['prev_close'] = df['Close'].shift(1)

        # Señales simples
        df['buy_signal'] = (
            (df['Close'] > df['prev_darvas_high']) &
            (df['prev_close'] <= df['prev_darvas_high'])
        )
        df['sell_signal'] = (
            (df['Close'] < df['darvas_low'].shift(1)) &
            (df['prev_close'] >= df['darvas_low'].shift(1))
        )

        # MavilimW (tendencia)
        df['mavilimw'] = calc_mavilimw(df)
        # Robusto: para primeras velas después de que mavilimw arranca
        def robust_trend_filter(f):
            trend = pd.Series(False, index=f.index)
            mask = f['mavilimw'].notna()
            trend[mask] = f.loc[mask, 'Close'] > f.loc[mask, 'mavilimw']
            first = f['mavilimw'].first_valid_index()
            if first is not None and first >= 1:
                for i in range(first - 1, first + 1):
                    if i >= 0 and all(f.loc[j, 'Close'] > f.loc[first, 'mavilimw'] for j in range(i, first + 1)):
                        trend.iloc[i] = True
            return trend
        df['trend_filter'] = robust_trend_filter(df)

        # WAE (fuerza)
        df = calc_wae(
            df,
            sensitivity=150,
            fastLength=20,
            slowLength=40,
            channelLength=20,
            mult=2.0
        )
        df['wae_filter'] = (
            (df['wae_trendUp'] > df['wae_e1']) &
            (df['wae_trendUp'] > df['wae_deadzone'])
        )

        # Señales finales
        df['buy_final'] = df['buy_signal'] & df['trend_filter'] & df['wae_filter']
        # Señal de venta: simple, considera ruptura y tendencia bajista
        df['trend_filter_sell'] = df['mavilimw'].notna() & (df['Close'] < df['mavilimw'])
        df['sell_final'] = df['sell_signal'] & df['trend_filter_sell']

        # Mostrar tabla de señales
        cols = [
            'Close', 'darvas_high', 'darvas_low', 'mavilimw',
            'wae_trendUp', 'wae_e1', 'wae_deadzone',
            'buy_signal', 'trend_filter', 'wae_filter', 'buy_final',
            'sell_signal', 'trend_filter_sell', 'sell_final'
        ]
        df_signals = df.loc[df['buy_final'] | df['sell_final'], cols].copy()
        st.success(f"Número de señales detectadas: {len(df_signals)}")
        st.dataframe(df_signals)

        # Gráfico
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df.index, df['Close'], label='Precio Close', zorder=1)
        ax.plot(df.index, df['darvas_high'], label='Darvas High', linestyle='--', zorder=1)
        ax.plot(df.index, df['darvas_low'], label='Darvas Low', linestyle='--', zorder=1)
        ax.plot(df.index, df['mavilimw'], label='MavilimW', linewidth=2, zorder=2)
        ax.scatter(df.index[df['buy_final']], df.loc[df['buy_final'], 'Close'],
                   marker='^', s=100, color='green', label='Señal Compra', zorder=3)
        ax.scatter(df.index[df['sell_final']], df.loc[df['sell_final'], 'Close'],
                   marker='v', s=100, color='red', label='Señal Venta', zorder=3)
        ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
