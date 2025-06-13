# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import datetime

from utils.indicators import calc_mavilimw


def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros fijos de los indicadores
    SENSITIVITY = 150
    FAST_EMA = 20
    SLOW_EMA = 40
    CHANNEL_LEN = 20
    BB_MULT = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # ====== UI: Selección de activo, timeframe y fechas ======
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

    timeframes = ["1d", "1h", "15m", "5m"]
    timeframe = st.selectbox("Temporalidad", timeframes)

    fecha_inicio = st.date_input("Desde", value=datetime.date(2023, 1, 1), key="darvas_ini")
    fecha_fin = st.date_input("Hasta", value=datetime.date.today(), key="darvas_fin")

    if st.button("Ejecutar Backtest Darvas", key="run_darvas"):
        st.info("Descargando datos históricos...")
        # Descargar con yfinance
        df = yf.download(
            activo,
            start=fecha_inicio,
            end=fecha_fin + datetime.timedelta(days=1),
            interval=timeframe,
            progress=False
        )
        if df.empty:
            st.error("No se encontraron datos para ese activo o período.")
            return

        st.success(f"Datos descargados: {len(df)} filas")

        # Normalizar columnas
        if isinstance(df.columns[0], tuple):
            df.columns = [col[0].capitalize() for col in df.columns]
        else:
            df.columns = [str(col).capitalize() for col in df.columns]

        # Filtrar columnas requeridas
        req = ["Close", "High", "Low"]
        df = df.dropna(subset=req)

        # Reset index y filtrar intervalo exacto
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df.index = df.index.tz_localize(None)
        df = df.loc[fecha_inicio:fecha_fin]

        # ===================== Señales Darvas =====================
        df['darvas_high'] = df['High'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
        df['darvas_low'] = df['Low'].rolling(window=DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
        df['prev_darvas_high'] = df['darvas_high'].shift(1)
        df['prev_darvas_low'] = df['darvas_low'].shift(1)
        df['prev_close'] = df['Close'].shift(1)

        df['buy_signal'] = (
            (df['Close'] > df['prev_darvas_high']) &
            (df['prev_close'] <= df['prev_darvas_high'])
        )
        df['sell_signal'] = (
            (df['Close'] < df['prev_darvas_low']) &
            (df['prev_close'] >= df['prev_darvas_low'])
        )

        # ================ Indicador MavilimW (tendencia) ================
        df['mavilimw'] = calc_mavilimw(df)

        # Filtros de tendencia robusta
        def robust_trend_buy(df):
            trend = pd.Series(False, index=df.index)
            mask = df['mavilimw'].notna()
            trend.loc[mask] = df.loc[mask, 'Close'] > df.loc[mask, 'mavilimw']
            first_valid = df['mavilimw'].first_valid_index()
            if first_valid is not None and first_valid >= 1:
                for i in range(first_valid-1, first_valid+1):
                    if i >= 0 and all(
                        df.iloc[j]['Close'] > df.iloc[first_valid]['mavilimw']
                        for j in range(i, first_valid+1)
                    ):
                        trend.iloc[i] = True
            return trend

        def robust_trend_sell(df):
            trend = pd.Series(False, index=df.index)
            mask = df['mavilimw'].notna()
            trend.loc[mask] = df.loc[mask, 'Close'] < df.loc[mask, 'mavilimw']
            first_valid = df['mavilimw'].first_valid_index()
            if first_valid is not None and first_valid >= 1:
                for i in range(first_valid-1, first_valid+1):
                    if i >= 0 and all(
                        df.iloc[j]['Close'] < df.iloc[first_valid]['mavilimw']
                        for j in range(i, first_valid+1)
                    ):
                        trend.iloc[i] = True
            return trend

        df['trend_filter_buy'] = robust_trend_buy(df)
        df['trend_filter_sell'] = robust_trend_sell(df)

        # ================ Indicador WAE (fuerza/momentum) ================
        # MACD y barra de momentum
        fastMA = df['Close'].ewm(span=FAST_EMA, adjust=False).mean()
        slowMA = df['Close'].ewm(span=SLOW_EMA, adjust=False).mean()
        macd = fastMA - slowMA
        macd_diff = macd - macd.shift(1)
        df['wae_trendUp'] = np.where(macd_diff >= 0, macd_diff * SENSITIVITY, 0)
        df['wae_trendDown'] = np.where(macd_diff <  0, -macd_diff * SENSITIVITY, 0)

        # Bollinger bands para e1
        basis = df['Close'].rolling(window=CHANNEL_LEN).mean()
        dev   = df['Close'].rolling(window=CHANNEL_LEN).std(ddof=0) * BB_MULT
        df['wae_e1']        = basis + dev - (basis - dev)  # e1 = upper - lower

        # Dead zone (TR)
        tr = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low']  - df['Close'].shift(1))
            )
        )
        df['wae_deadzone'] = pd.Series(tr).rolling(window=100).mean().fillna(0) * 3.7

        df['wae_filter_buy']  = (df['wae_trendUp']   > df['wae_e1']) & (df['wae_trendUp']   > df['wae_deadzone'])
        df['wae_filter_sell'] = (df['wae_trendDown'] > df['wae_e1']) & (df['wae_trendDown'] > df['wae_deadzone'])

        # ================ Señales finales ================
        df['buy_final']  = df['buy_signal']  & df['trend_filter_buy']  & df['wae_filter_buy']
        df['sell_final'] = df['sell_signal'] & df['trend_filter_sell'] & df['wae_filter_sell']

        # Tabla de señales detectadas
        df_signals = df.loc[df['buy_final'] | df['sell_final'], [
            'Close', 'darvas_high', 'darvas_low', 'mavilimw',
            'wae_trendUp', 'wae_trendDown', 'wae_e1', 'wae_deadzone',
            'buy_signal', 'trend_filter_buy', 'wae_filter_buy', 'buy_final',
            'sell_signal', 'trend_filter_sell', 'wae_filter_sell', 'sell_final'
        ]].copy()
        num_signals = len(df_signals)
        st.success(f"Número de señales detectadas: {num_signals}")
        st.dataframe(df_signals)

        # Plot principal
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df.index, df['Close'], label="Precio Close", color="black", zorder=1)
        ax.plot(df.index, df['darvas_high'], label="Darvas High", color="green", linestyle="--", zorder=1)
        ax.plot(df.index, df['darvas_low'],  label="Darvas Low",  color="red",   linestyle="--", zorder=1)
        ax.plot(df.index, df['mavilimw'],   label="MavilimW (Tendencia)", color="white", linewidth=2, zorder=2)

        # Flechas de compra/venta
        ax.scatter(df.index[df['buy_final']],  df.loc[df['buy_final'],  'Close'], label="Señal Compra",  marker="^", color="green", s=100, zorder=3)
        ax.scatter(df.index[df['sell_final']], df.loc[df['sell_final'], 'Close'], label="Señal Venta", marker="v", color="red",   s=100, zorder=3)

        ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
        ax.legend()
        st.pyplot(fig)
