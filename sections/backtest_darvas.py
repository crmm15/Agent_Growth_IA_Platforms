# sections/backtest_darvas.py  
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.market_data import cargar_precio_historico
from utils.indicators   import calc_mavilimw, calc_wae

def backtest_darvas():
    st.header("📦 Backtesting Estrategia Darvas Box")

    # 1) Parámetros UI
    activos_predef = {
        "BTC/USD":        "BTC-USD",
        "ETH/USD":        "ETH-USD",
        "Apple (AAPL)":   "AAPL",
        "Tesla (TSLA)":   "TSLA",
        "Amazon (AMZN)":  "AMZN",
        "S&P500 ETF (SPY)":"SPY"
    }
    activo_nombre = st.selectbox("Elige activo para backtesting", list(activos_predef.keys()))
    activo        = activos_predef[activo_nombre]

    timeframe = st.selectbox("Temporalidad", ["1d", "1h", "15m", "5m"])
    start     = st.date_input("Desde", pd.to_datetime("2020/01/01"), key="darvas_start")
    end       = st.date_input("Hasta", pd.to_datetime("today"),     key="darvas_end")

    DARVAS_WINDOW = st.slider(
        "Largo del Darvas Box (boxp)",
        min_value=1, max_value=50, value=5, step=1, key="darvas_window"
    )

    if not st.button("Ejecutar Backtest Darvas", key="run_darvas"):
        return

    # 2) Parámetros fijos
    SENSITIVITY = 150
    FAST_EMA    = 20
    SLOW_EMA    = 40
    CHANNEL_LEN = 20
    BB_MULT     = 2.0

    # 3) Descarga de históricos
    st.info("Descargando datos históricos...")
    df = cargar_precio_historico(activo, timeframe, start, end)
    if df is None or df.empty:
        st.error("No se encontraron datos para esa configuración.")
        return
    st.success(f"Datos descargados: {len(df)} filas")

    # 4) Preparo tabla histórica
    df_hist = df.reset_index().rename(columns={'index':'Date'})
    df_hist['Date'] = pd.to_datetime(df_hist['Date']).dt.tz_localize(None)

    # FORZAMOS columnas numéricas (¡esto es lo importante!)
    numeric_cols_hist = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in numeric_cols_hist:
        if col in df_hist.columns:
            df_hist[col] = pd.to_numeric(df_hist[col], errors='coerce')

    st.dataframe(
        df_hist,
        use_container_width=True,
        column_config={
            'Date':   st.column_config.DateColumn('Fecha',format='DD/MM/YYYY'),
            'Open':   st.column_config.NumberColumn('Apertura'),
            'High':   st.column_config.NumberColumn('Máximo'),
            'Low':    st.column_config.NumberColumn('Mínimo'),
            'Close':  st.column_config.NumberColumn('Cierre'),
            'Volume': st.column_config.NumberColumn('Volumen')
        }
    )

    # 5) Cálculos Darvas & filtros
    df_calc = df.copy().reset_index(drop=False).rename(columns={'index':'Date'})
    df_calc['Date'] = pd.to_datetime(df_calc['Date']).dt.tz_localize(None)
    df_calc = df_calc.dropna(subset=['Close','High','Low'])

    # Darvas Box
    df_calc['darvas_high'] = df_calc['High'].rolling(DARVAS_WINDOW).max()
    df_calc['darvas_low']  = df_calc['Low'].rolling(DARVAS_WINDOW).min()
    df_calc['prev_dh']     = df_calc['darvas_high'].shift(1)
    df_calc['prev_dl']     = df_calc['darvas_low'].shift(1)
    df_calc['prev_c']      = df_calc['Close'].shift(1)

    # Señales Darvas
    df_calc['buy_signal']  = (df_calc['Close'] > df_calc['prev_dh']) & (df_calc['prev_c'] <= df_calc['prev_dh'])
    df_calc['sell_signal'] = (df_calc['Close'] < df_calc['prev_dl']) & (df_calc['prev_c'] >= df_calc['prev_dl'])

    # Tendencia MavilimW
    df_calc['mavilimw']   = calc_mavilimw(df_calc)
    df_calc['trend_up']   = df_calc['Close'] > df_calc['mavilimw'].shift(2)
    df_calc['trend_down'] = df_calc['Close'] < df_calc['mavilimw'].shift(2)

    # Fuerza WAE
    df_calc = calc_wae(
        df_calc,
        sensitivity=SENSITIVITY,
        fastLength=FAST_EMA,
        slowLength=SLOW_EMA,
        channelLength=CHANNEL_LEN,
        mult=BB_MULT
    )
    fast = df_calc['Close'].ewm(span=FAST_EMA, adjust=False).mean()
    slow = df_calc['Close'].ewm(span=SLOW_EMA, adjust=False).mean()
    macd = fast - slow
    t1   = (macd - macd.shift(1)) * SENSITIVITY
    df_calc['wae_trendDown'] = np.where(t1 < 0, -t1, 0)

    df_calc['wae_filter_buy']  = (df_calc['wae_trendUp']   > df_calc['wae_e1']) & (df_calc['wae_trendUp']   > df_calc['wae_deadzone'])
    df_calc['wae_filter_sell'] = (df_calc['wae_trendDown'] > df_calc['wae_e1']) & (df_calc['wae_trendDown'] > df_calc['wae_deadzone'])

   # Estado de tendencia: 1 alcista, -1 bajista, 0 lateral
    df_calc['trend_state'] = np.select(
        [df_calc['trend_up'], df_calc['trend_down']],
        [1, -1],
        default=0
    )

    # Señales finales: solo la primera tras lateral o cambio de tendencia
    df_calc['buy_final'] = False
    df_calc['sell_final'] = False
    buy_ready = False
    sell_ready = False
    prev_state = 0
    for i, row in df_calc.iterrows():
        curr_state = row['trend_state']
        if curr_state == 1 and prev_state <= 0:
            buy_ready = True
        if curr_state == -1 and prev_state >= 0:
            sell_ready = True
        if buy_ready and row['buy_signal'] and row['wae_filter_buy']:
            df_calc.at[i, 'buy_final'] = True
            buy_ready = False
        if sell_ready and row['sell_signal'] and row['wae_filter_sell']:
            df_calc.at[i, 'sell_final'] = True
            sell_ready = False
        prev_state = curr_state

    # 6) Preparo tabla de señales
    cols = [
        'Date','Close','darvas_high','darvas_low','mavilimw',
        'wae_trendUp','wae_e1','wae_deadzone','wae_trendDown',
        'buy_signal','trend_up','wae_filter_buy','buy_final',
        'sell_signal','trend_down','wae_filter_sell','sell_final'
    ]
    df_signals = df_calc.loc[df_calc['buy_final'] | df_calc['sell_final'], cols]

    # FORZAMOS columnas numéricas para las señales
    numeric_cols_signals = ['Close', 'darvas_high', 'darvas_low', 'mavilimw',
                            'wae_trendUp', 'wae_e1', 'wae_deadzone', 'wae_trendDown']
    for col in numeric_cols_signals:
        if col in df_signals.columns:
            df_signals[col] = pd.to_numeric(df_signals[col], errors='coerce')

    st.success(f"Número de señales detectadas: {len(df_signals)}")
    st.dataframe(
        df_signals,
        use_container_width=True,
        column_config={
            'Date':             st.column_config.DateColumn('Fecha',format='DD/MM/YYYY'),
            'Close':            st.column_config.NumberColumn('Cierre'),
            'darvas_high':      st.column_config.NumberColumn('Darvas High'),
            'darvas_low':       st.column_config.NumberColumn('Darvas Low'),
            'mavilimw':         st.column_config.NumberColumn('MavilimW'),
            'wae_trendUp':      st.column_config.NumberColumn('WAE↑'),
            'wae_e1':           st.column_config.NumberColumn('Explosión'),
            'wae_deadzone':     st.column_config.NumberColumn('DeadZone'),
            'wae_trendDown':    st.column_config.NumberColumn('WAE↓')
            # NO BooleanColumn aquí, ya que las lógicas no necesitan formato
        }
    )

    # 7) Gráfico
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df_calc['Date'], df_calc['Close'],      color='black', label='Cierre', zorder=1)
    ax.plot(df_calc['Date'], df_calc['darvas_high'], linestyle='--', label='Darvas High', zorder=1)
    ax.plot(df_calc['Date'], df_calc['darvas_low'],  linestyle='--', label='Darvas Low',  zorder=1)
    ax.plot(df_calc['Date'], df_calc['mavilimw'],    linewidth=2, label='MavilimW',    zorder=2)
    ax.scatter(
        df_calc.loc[df_calc['buy_final'],'Date'],
        df_calc.loc[df_calc['buy_final'],'Close'],
        marker='^', color='green', s=100, label='Señal Compra', zorder=3
    )
    ax.scatter(
        df_calc.loc[df_calc['sell_final'],'Date'],
        df_calc.loc[df_calc['sell_final'],'Close'],
        marker='v', color='red',   s=100, label='Señal Venta',  zorder=3
    )
    ax.set_title(f"Darvas Box Backtest – {activo_nombre} [{timeframe}]")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Precio")
    ax.legend()
    plt.xticks(rotation=20)
    st.pyplot(fig)

    # 8) Explicación de señales
    with st.expander("ℹ️ Interpretación de las señales"):
        st.markdown("""  
        - 🔼 **Señal de compra**: se genera cuando el precio cierra por encima de la Darvas High del día anterior, la tendencia (MavilimW) es alcista y la fuerza (WAE) supera el umbral.  
        - 🔽 **Señal de venta**: se genera cuando el precio cierra por debajo de la Darvas Low del día anterior, la tendencia es bajista y la fuerza WAE también confirma impulso a la baja.  
        - 📅 **Fecha**: corresponde al día en que se rompe el canal Darvas y se cumplen ambos filtros.  
        - 📊 **Cantidad de señales**: compras y ventas detectadas en el periodo seleccionado.
        """)

    # 9) Perfil del backtest
    with st.expander("📈 Perfil del Backtest"):
        # calculamos algunos KPIs básicos
        total_ops = len(df_signals)
        compras    = df_signals['buy_final'].sum()
        ventas     = df_signals['sell_final'].sum()
        st.markdown(f"""
        - 🔄 **Operaciones totales**: {total_ops}  
        - 🟢 **Compras**: {compras}  
        - 🔴 **Ventas**: {ventas}  
        - ⏳ **Periodo analizado**: {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}  
        - ⚙️ **Parámetros**: Darvas Window = {DARVAS_WINDOW}, EMA rápida = {FAST_EMA}, EMA lenta = {SLOW_EMA}
        """)

    # métricas de rentabilidad y riesgo
    if len(df_calc) > 1:
        df_calc["ret"] = df_calc["Close"].pct_change().fillna(0)
        df_calc["signal"] = np.where(df_calc["buy_final"], 1,
                                     np.where(df_calc["sell_final"], 0, np.nan))
        df_calc["position"] = df_calc["signal"].ffill().fillna(0)
        df_calc["strategy_ret"] = df_calc["position"].shift(1) * df_calc["ret"]
        df_calc["equity"] = (1 + df_calc["strategy_ret"]).cumprod()
        total_ret = df_calc["equity"].iloc[-1] - 1
        max_dd = (df_calc["equity"] / df_calc["equity"].cummax() - 1).min()
        factor = {"1d": 252, "1h": 24*252, "15m": 96*252, "5m": 288*252}.get(timeframe, 252)
        sharpe = 0.0
        if df_calc["strategy_ret"].std() != 0:
            sharpe = (df_calc["strategy_ret"].mean() / df_calc["strategy_ret"].std()) * np.sqrt(factor)

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "💰 Rentabilidad acumulada",
            f"{total_ret:.2%}",
            help="Ganancia total obtenida siguiendo todas las señales"
        )
        col2.metric(
            "📉 Máx Drawdown",
            f"{max_dd:.2%}",
            help="Caída porcentual más pronunciada desde un máximo"
        )
        col3.metric(
            "⚖️ Sharpe ratio",
            f"{sharpe:.2f}",
            help="Rentabilidad ajustada por volatilidad"
        )
