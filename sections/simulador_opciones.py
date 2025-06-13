# sections/simulador_opciones.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import yfinance as yf

from utils.market_data import cargar_precio_historico
from utils.options import (
    calcular_payoff_call as payoff_call,
    calcular_payoff_put  as payoff_put,
    calcular_delta_call_put as calc_delta
)

def simulador_opciones():
    st.subheader("📈 Simulador de Opciones con Perfil de Riesgo")

    # 1) Subir Excel con la hoja "Inversiones"
    archivo = st.sidebar.file_uploader(
        "📁 Subí tu archivo Excel (.xlsx)",
        type=["xlsx"],
        key="simulador"
    )
    if archivo is None:
        st.info("Subí el archivo Excel para empezar.")
        return

    # 2) Leer hoja y limpiar nombres de columnas
    df = pd.read_excel(archivo, sheet_name="Inversiones")
    df.columns = df.columns.str.strip()
    st.write("Columnas disponibles:", df.columns.tolist())

    # 3) Validar que exista la columna Ticker
    if "Ticker" not in df.columns:
        st.error("El archivo debe contener la columna 'Ticker'.")
        return

    # 4) Selección de ticker y extracción de fila
    tickers = df["Ticker"].dropna().unique()
    selected_ticker = st.selectbox("Seleccioná un ticker", tickers)
    datos = df[df["Ticker"] == selected_ticker].iloc[0]

    # 5) Precio actual (columna o fallback a yfinance)
    if "Precio Actual" in df.columns:
        precio_actual = datos["Precio Actual"]
    else:
        hist = cargar_precio_historico(selected_ticker, period="1d")
        precio_actual = hist["Close"].iloc[-1]
    st.markdown(f"**Precio actual usado:** ${precio_actual:.2f}")

    # 6) Parámetros de simulación
    nivel_riesgo = st.radio(
        "🎯 Tu perfil de riesgo",
        ["Conservador", "Balanceado", "Agresivo"],
        index=1
    )
    tipo_opcion = st.radio("Tipo de opción", ["CALL", "PUT"])
    rol         = st.radio("Rol en la opción", ["Comprador", "Vendedor"], index=0)

    sugerencia = {"Conservador": 5, "Balanceado": 10, "Agresivo": 20}
    delta_strike = st.slider(
        "📉 % sobre el precio actual para el strike",
        -50, 50, sugerencia[nivel_riesgo]
    )
    dias_venc = st.slider(
        "📆 Días hasta vencimiento",
        7, 90, 30
    )

    # 7) Calcula strike y busca cadena de opciones
    strike_price = round(precio_actual * (1 + delta_strike/100), 2)
    ticker_yf    = yf.Ticker(selected_ticker)
    expiraciones = ticker_yf.options
    if not expiraciones:
        st.warning("⚠ No se encontró cadena de opciones para este ticker.")
        return

    # Fecha de vencimiento más cercana al slider
    fecha_venc = min(
        expiraciones,
        key=lambda x: abs((pd.to_datetime(x) - pd.Timestamp.today()).days - dias_venc)
    )
    cadena       = ticker_yf.option_chain(fecha_venc)
    tabla        = cadena.calls if tipo_opcion == "CALL" else cadena.puts
    tabla        = tabla.dropna(subset=["bid","ask"])
    if tabla.empty:
        st.warning("⚠ No hay opciones válidas para ese strike.")
        return

    # 8) Encuentra fila más cercana al strike
    fila    = tabla.loc[(tabla["strike"] - strike_price).abs().idxmin()]
    premium = (fila["bid"] + fila["ask"]) / 2

    # 9) Muestra resultados básicos
    st.markdown(f"**Strike simulado:** ${strike_price}")
    st.markdown(f"**Prima estimada:** ${premium:.2f}")
    st.markdown(f"**Vencimiento elegido:** {fecha_venc}")

    # 10) Calcula Delta → probabilidad
    T     = dias_venc / 365
    r     = 0.02
    sigma = fila.get("impliedVolatility", 0.25)
    delta = calc_delta(precio_actual, strike_price, T, r, sigma, tipo_opcion)
    st.markdown(f"**Probabilidad (Delta):** ~{abs(delta)*100:.1f}%")

    # 11) Grafico de Payoff
    S      = np.linspace(precio_actual*0.6, precio_actual*1.4, 100)
    payoff = payoff_call(S, strike_price, premium) if tipo_opcion=="CALL" else payoff_put(S, strike_price, premium)
    if rol == "Vendedor":
        payoff = -payoff

    fig, ax = plt.subplots(figsize=(5,3))
    ax.xaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.plot(S, payoff, label=f"Payoff ({rol})")
    ax.axhline(0, linestyle="--", color="gray")
    ax.axvline(strike_price, linestyle="--", color="red", label="Strike")
    break_even = strike_price + (premium if tipo_opcion=="CALL" else -premium)
    ax.axvline(break_even, linestyle="--", color="green", label="Break-even")
    ax.legend()
    st.pyplot(fig)

    # 12) Expansores explicativos (opcional)
    with st.expander("ℹ️ Interpretación"):
        if rol == "Comprador" and tipo_opcion == "CALL":
            st.markdown(
                f"- Pagás ${premium:.2f} por comprar a ${strike_price:.2f}.\n"
                f"- Pierdes solo la prima si no ejerce.\n"
                f"- Ganás a partir de ${break_even:.2f}."
            )
        # … añade los demás casos según prefieras …

    # 13) Envío a Telegram
    if st.button("📤 Enviar simulación a Telegram", key="simu_telegram"):
        from utils.telegram_helpers import enviar_grafico_simulacion_telegram
        enviar_grafico_simulacion_telegram(fig, selected_ticker)
        st.success("📤 Simulación enviada por Telegram!")
