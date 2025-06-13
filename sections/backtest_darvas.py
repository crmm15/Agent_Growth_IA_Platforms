# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

def backtest_darvas():
    from utils.indicators import calc_mavilimw, calc_wae
    from utils.backtest_helpers import robust_trend_filter
    from utils.market_data import cargar_precio_historico

    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros fijos de los indicadores
    SENSITIVITY = 150
    FAST_EMA = 20
    SLOW_EMA = 40
    CHANNEL_LEN = 20
    BB_MULT = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # Activos predefinidos
    activos_predef = {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "S&P500 ETF (SPY)": "SPY"
    }
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    activo = activos_predef[activo_nombre]

    # Temporalidades
    timeframes = ["1d", "1h", "15m", "5m"]
    timeframe = st.selectbox("Temporalidad", timeframes)

    # Fechas de inicio y fin
    fecha_inicio = st.date_input("Desde", value=datetime.date(2023, 1, 1), key="darvas_ini")
    fecha_fin = st.date_input("Hasta", value=datetime.date.today(), key="darvas_fin")

    if st.button("Ejecutar Backtest Darvas", key="ejecutar_backtest_darvas"):
        # Para intradía, Yahoo limita a 60 días: ajustamos rango si es mayor
        if timeframe != '1d':
            max_days = 60
            diff = (fecha_fin - fecha_inicio).days
            if diff > max_days:
                nueva_ini = fecha_fin - datetime.timedelta(days=max_days)
                st.warning(
                    f"El intervalo intradía '{timeframe}' solo soporta hasta {max_days} días de datos.\n"
                    f"Ajustando fecha de inicio a {nueva_ini.strftime('%Y-%m-%d')}"
                )
                fecha_inicio = nueva_ini

        st.info("Descargando datos históricos...")
        # Descarga de datos usando nuestra función en utils/market_data
        df = cargar_precio_historico(
            activo,
            timeframe,
            fecha_inicio,
            fecha_fin + datetime.timedelta(days=1)
        )
        # Si no hubo datos, mostramos error
        if df is None or df.empty:
            st.error("No se encontraron datos para esa configuración.")
            return

        st.success(f"Datos descargados: {len(df)} filas")
        st.dataframe(df)

        # Normaliza columnas
        if isinstance(df.columns[0], tuple):
            df.columns = [col[0].capitalize() for col in df.columns]
        else:
            df.columns = [str(col).capitalize() for col in df.columns]
        required_cols = ["Close", "High", "Low"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"El DataFrame descargado NO tiene todas las columnas requeridas: {required_cols}.")
            st.dataframe(df)
            return

        # Preparamos el DataFrame
        df = df.reset_index(drop=False)
        df = df.dropna(subset=required_cols)

        # Indicador Darvas
        df['darvas_high'] = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
        df['darvas_low'] = df['Low'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
        df['prev_darvas_high'] = df['darvas_high'].shift(1)
        df['prev_close'] = df['Close'].shift(1)
        df['buy_signal'] = (
            (df['Close'] > df['prev_darvas_high']) &
            (df['prev_close'] <= df['prev_darvas_high'])
        )
        df['sell_signal'] = (
            (df['Close'] < df['darvas_low'].shift(1)) &
            (df['prev_close'] >= df['darvas_low'].shift(1))
        )

        # Indicador MavilimW
        df['mavilimw'] = calc_mavilimw(df)
        df['trend_filter'] = robust_trend_filter(df)

        # Indicador WAE
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

        # Señales finales
        df['buy_final'] = df['buy_signal'] & df['trend_filter'] & df['wae_filter']
        df['sell_final'] = df['sell_signal'] & (~df['trend_filter']) & (df['wae_trendUp'] < df['wae_e1'])

        # Tabla de señales
        cols_signals = [
            "Close", "darvas_high", "darvas_low", "mavilimw",
            "wae_trendUp", "wae_e1", "wae_deadzone",
            "buy_signal", "trend_filter", "wae_filter", "buy_final",
            "sell_signal", "sell_final"
        ]
        df_signals = df.loc[df['buy_final'] | df['sell_final'], cols_signals].copy()
        num_signals = len(df_signals)
        st.success(f"Número de señales detectadas: {num_signals}")
        st.dataframe(df_signals.head(100))

        # Gráfico
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df.index, df['Close'], label="Precio Close", color="black", zorder=1)
        ax.plot(df.index, df['darvas_high'], label="Darvas High", linestyle="--", alpha=0.7, zorder=1)
        ax.plot(df.index, df['darvas_low'], label="Darvas Low", linestyle="--", alpha=0.7, zorder=1)
        ax.plot(df.index, df['mavilimw'], label="MavilimW (Tendencia)", linewidth=2, zorder=2)
        ax.scatter(df.index[df['buy_final']], df.loc[df['buy_final'], 'Close'],
                   label="Señal Compra", marker="^", color="green", s=100, zorder=3)
        ax.scatter(df.index[df['sell_final']], df.loc[df['sell_final'], 'Close'],
                   label="Señal Venta", marker="v", color="red", s=100, zorder=3)
        ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
