# sections/backtest_darvas.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # Parámetros fijos de los indicadores
    SENSITIVITY   = 150
    FAST_EMA      = 20
    SLOW_EMA      = 40
    CHANNEL_LEN   = 20
    BB_MULT       = 2.0
    DARVAS_WINDOW = 20  # igual que en la config de TradingView

    # ==============================
    # Auxiliares: indicadores Darvas, MavilimW, WAE
    # ==============================
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

        basis   = df['Close'].rolling(window=channelLength).mean()
        dev     = df['Close'].rolling(window=channelLength).std(ddof=0) * mult
        bb_up   = basis + dev
        bb_low  = basis - dev
        e1      = bb_up - bb_low

        tr1 = df['High'] - df['Low']
        tr2 = np.abs(df['High'] - df['Close'].shift(1))
        tr3 = np.abs(df['Low']  - df['Close'].shift(1))
        true_range = pd.concat([tr1,tr2,tr3], axis=1).max(axis=1)
        deadzone = true_range.rolling(window=100, min_periods=100).mean() * 3.7

        df['wae_trendUp']   = np.where(t1 >= 0, t1, 0)
        df['wae_e1']        = e1
        df['wae_deadzone']  = deadzone
        return df

    def robust_trend_filter(df):
        trend = pd.Series(False, index=df.index)
        mask = df['mavilimw'].notna()
        trend.loc[mask] = df.loc[mask, 'Close'] > df.loc[mask, 'mavilimw']
        first = df['mavilimw'].first_valid_index()
        if first is not None and first >= 1:
            for i in range(first-1, first+1):
                if all(df.loc[j, 'Close'] > df.loc[first, 'mavilimw'] for j in range(i, first+1)):
                    trend.iloc[i] = True
        return trend

    # ==============================
    # Selección UI
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

    timeframe = st.selectbox("Temporalidad", ["1d","1h","15m","5m"])
    fecha_inicio = st.date_input("Desde", pd.to_datetime("2023-01-01"), key="darvas_ini")
    fecha_fin    = st.date_input("Hasta", pd.Timestamp.today(), key="darvas_fin")

    if not st.button("Ejecutar Backtest Darvas", key="boton_backtest"):
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
        st.error("No hay datos para esa combinación.")
        return
    st.success(f"Datos descargados: {len(df)} filas")

    # Normalizar columnas
    if isinstance(df.columns[0], tuple):
        df.columns = [c[0].capitalize() for c in df.columns]
    else:
        df.columns = [str(c).capitalize() for c in df.columns]

    df = df.reset_index().dropna(subset=["Close","High","Low"])

    # ==============================
    # Señales Darvas
    df['darvas_high']     = df['High'].rolling(DARVAS_WINDOW, min_periods=DARVAS_WINDOW).max()
    df['darvas_low']      = df['Low'].rolling( DARVAS_WINDOW, min_periods=DARVAS_WINDOW).min()
    df['prev_darvas_high']= df['darvas_high'].shift(1)
    df['prev_close']      = df['Close'].shift(1)

    df['buy_signal']  = (df['Close'] > df['prev_darvas_high']) & (df['prev_close'] <= df['prev_darvas_high'])
    df['sell_signal'] = (df['Close'] < df['darvas_low'].shift(1)) & (df['prev_close'] >= df['darvas_low'].shift(1))

    # ==============================
    # MavilimW + filtro tendencia
    df['mavilimw']     = calc_mavilimw(df)
    df['trend_filter'] = robust_trend_filter(df)

    # ==============================
    # WAE + filtro fuerza
    df = calc_wae(df, sensitivity=SENSITIVITY,
                     fastLength=FAST_EMA,
                     slowLength=SLOW_EMA,
                     channelLength=CHANNEL_LEN,
                     mult=BB_MULT)
    df['wae_filter'] = (df['wae_trendUp'] > df['wae_e1']) & (df['wae_trendUp'] > df['wae_deadzone'])

    # ==============================
    # Señales finales de compra y venta
    df['buy_final']  = df['buy_signal']  & df['trend_filter'] & df['wae_filter']
    df['sell_final'] = df['sell_signal'] & (~df['trend_filter']) & (~df['wae_filter'])

    # ==============================
    # Tabla de señales finales
    cols = [
        "Date","Close","darvas_high","darvas_low","mavilimw",
        "wae_trendUp","wae_e1","wae_deadzone",
        "buy_final","sell_final"
    ]
    df_signals = df.loc[df['buy_final'] | df['sell_final'], cols]
    n = len(df_signals)
    st.success(f"Señales finales detectadas: {n}")

    st.dataframe(
        df_signals,
        column_config={
            "Close":        st.column_config.NumberColumn("Close"),
            "darvas_high":  st.column_config.NumberColumn("Darvas High"),
            "darvas_low":   st.column_config.NumberColumn("Darvas Low"),
            "mavilimw":     st.column_config.NumberColumn("MavilimW"),
            "wae_trendUp":  st.column_config.NumberColumn("WAE TrendUp"),
            "wae_e1":       st.column_config.NumberColumn("WAE E1"),
            "wae_deadzone": st.column_config.NumberColumn("WAE DeadZone"),
            "buy_final":    st.column_config.CheckboxColumn("Buy Final"),
            "sell_final":   st.column_config.CheckboxColumn("Sell Final"),
        }
    )

    # ==============================
    # Gráfico con ambas señales
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(df['Date'], df['Close'], label="Precio Close", color="black", zorder=1)
    ax.plot(df['Date'], df['darvas_high'], label="Darvas High", color="green", linestyle="--", zorder=1)
    ax.plot(df['Date'], df['darvas_low'], label="Darvas Low",  color="red",   linestyle="--", zorder=1)
    ax.plot(df['Date'], df['mavilimw'], label="MavilimW",    color="white", linewidth=2, zorder=2)

    ax.scatter(
        df.loc[df['buy_final'],'Date'],
        df.loc[df['buy_final'],'Close'],
        marker="^", color="blue", s=120, label="Compra (Buy Final)", zorder=3
    )
    ax.scatter(
        df.loc[df['sell_final'],'Date'],
        df.loc[df['sell_final'],'Close'],
        marker="v", color="orange", s=120, label="Venta (Sell Final)", zorder=3
    )

    ax.set_title(f"Darvas Box Backtest - {activo_nombre} [{timeframe}]")
    ax.legend()
    st.pyplot(fig)
