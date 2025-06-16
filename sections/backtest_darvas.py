# sections/backtest_darvas.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # 1) UI
    activos = {"BTC/USD":"BTC-USD","ETH/USD":"ETH-USD","AAPL":"AAPL","TSLA":"TSLA","AMZN":"AMZN","SPY":"SPY"}
    activo_nombre = st.selectbox("Activo", list(activos.keys()))
    simbolo = activos[activo_nombre]
    timeframe = st.selectbox("Temporalidad", ["1d","1h","15m"])
    start = st.date_input("Desde", pd.to_datetime("2023-01-01"))
    end   = st.date_input("Hasta", pd.to_datetime("today"))
    boxp  = st.slider("Largo Darvas Box", 1, 50, 5)

    if not st.button("Ejecutar"):
        return

    # 2) Parámetros indicadores
    SENS, F_EMA, S_EMA, CH_LEN, BB_M = 150, 20, 40, 20, 2.0

    # 3) Descarga
    st.info("Descargando datos…")
    df = cargar_precio_historico(simbolo, timeframe, start, end)
    if df is None or df.empty:
        st.error("No hay datos.")
        return
    st.success(f"Descargadas {len(df)} filas.")

    # 4) Formateo y muestra de históricos
    df_hist = df.reset_index().rename(columns={'index':'Date'})
    df_hist['Date'] = pd.to_datetime(df_hist['Date']).dt.tz_localize(None)
    for c in ['Open','High','Low','Close']:
        df_hist[c] = df_hist[c].map(lambda x: f"{x:,.2f}")
    df_hist['Volume'] = df_hist['Volume'].map(lambda x: f"{int(x):,}")
    st.dataframe(df_hist, use_container_width=True)

    # 5) Cálculos
    df = df.reset_index(drop=False).dropna(subset=["Close","High","Low"])
    df['darvas_high'] = df['High'].rolling(boxp).max()
    df['darvas_low']  = df['Low'].rolling(boxp).min()
    df['prev_dh']     = df['darvas_high'].shift(1)
    df['prev_dl']     = df['darvas_low'].shift(1)
    df['prev_c']      = df['Close'].shift(1)

    df['buy_sig']  = (df['Close']>df['prev_dh']) & (df['prev_c']<=df['prev_dh'])
    df['sell_sig'] = (df['Close']<df['prev_dl']) & (df['prev_c']>=df['prev_dl'])

    df['mav']        = calc_mavilimw(df)
    df['trend_up']   = df['Close']>df['mav'].shift(2)
    df['trend_down'] = df['Close']<df['mav'].shift(2)

    df = calc_wae(df, SENS, F_EMA, S_EMA, CH_LEN, BB_M)
    fast = df['Close'].ewm(F_EMA).mean()
    slow = df['Close'].ewm(S_EMA).mean()
    macd = fast-slow
    t1   = (macd - macd.shift(1))*SENS
    df['wae_down'] = np.where(t1<0,-t1,0)

    df['w_buy']  = (df['wae_trendUp']>df['wae_e1']) & (df['wae_trendUp']>df['wae_deadzone'])
    df['w_sell'] = (df['wae_down']>df['wae_e1'])     & (df['wae_down']>df['wae_deadzone'])

    df['buy_f']  = df['buy_sig']  & df['trend_up']   & df['w_buy']
    df['sell_f'] = df['sell_sig'] & df['trend_down'] & df['w_sell']

    # 6) Señales formateadas
    df_sig = df.loc[df['buy_f']|df['sell_f']].reset_index(drop=False).rename(columns={'index':'Date'})
    df_sig['Date'] = pd.to_datetime(df_sig['Date']).dt.tz_localize(None).dt.strftime("%d/%m/%Y")

    for c in ['Close','darvas_high','darvas_low','mav',
              'wae_trendUp','wae_e1','wae_deadzone','wae_down']:
        df_sig[c] = df_sig[c].map(lambda x: f"{x:,.2f}")

    df_sig['buy_sig']  = df_sig['buy_sig'].astype(str)
    df_sig['sell_sig'] = df_sig['sell_sig'].astype(str)

    st.success(f"Señales: {len(df_sig)}")
    st.dataframe(df_sig, use_container_width=True)

    # 7) Gráfico
    fig,ax = plt.subplots(1,1,figsize=(12,4))
    ax.plot(df.index, df['Close'], label="Close", c='k')
    ax.plot(df.index, df['darvas_high'], '--', label="High")
    ax.plot(df.index, df['darvas_low'],  '--', label="Low")
    ax.plot(df.index, df['mav'],        '-',  label="Mav", linewidth=2)
    ax.scatter(df.index[df['buy_f']],  df['Close'][df['buy_f']], marker='^', c='g', s=80)
    ax.scatter(df.index[df['sell_f']], df['Close'][df['sell_f']], marker='v', c='r', s=80)
    ax.legend()
    st.pyplot(fig)
