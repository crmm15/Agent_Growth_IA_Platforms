import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from utils.data_io import cargar_historial
from utils.options import (
    calcular_payoff_call as payoff_call,
    calcular_payoff_put  as payoff_put,
    calcular_delta_call_put as calc_delta
)

def simulador_opciones():
    st.subheader("📈 Simulador de Opciones con Perfil de Riesgo")
    df = cargar_historial()

    selected_ticker = st.selectbox("Seleccioná un ticker", df["Ticker"].unique())
    nivel_riesgo = st.radio("🎯 Tu perfil de riesgo", ["Conservador","Balanceado","Agresivo"], index=1)
    tipo_opcion  = st.radio("Tipo de opción", ["CALL","PUT"])
    rol          = st.radio("Rol en la opción", ["Comprador","Vendedor"], index=0)

    sugerencia   = {"Conservador":5,"Balanceado":10,"Agresivo":20}
    delta_strike = st.slider("📉 % sobre el precio actual para el strike", -50,50,sugerencia[nivel_riesgo])
    dias_venc    = st.slider("📆 Días hasta vencimiento", 7,90,30)

    datos       = df[df["Ticker"]==selected_ticker].iloc[0]
    precio_act  = datos["Precio Actual"]
    strike_price= round(precio_act*(1+delta_strike/100),2)

    expiraciones = yf.Ticker(selected_ticker).options
    if not expiraciones:
        st.warning("⚠ No se encontró cadena de opciones para este ticker.")
        return

    fecha_venc = min(expiraciones, key=lambda x: abs((pd.to_datetime(x)-pd.Timestamp.today()).days-dias_venc))
    cadena     = yf.Ticker(selected_ticker).option_chain(fecha_venc)
    tabla      = cadena.calls if tipo_opcion=="CALL" else cadena.puts
    tabla      = tabla.dropna(subset=["bid","ask"])
    if tabla.empty:
        st.warning("⚠ No hay opciones válidas para ese strike.")
        return

    fila    = tabla.loc[(tabla["strike"]-strike_price).abs().idxmin()]
    premium = (fila["bid"]+fila["ask"])/2

    # Datos clave
    st.markdown(f"**Precio actual:** ${precio_act:.2f}")
    st.markdown(f"**Strike simulado:** ${strike_price}")
    st.markdown(f"**Prima estimada:** ${premium:.2f}")
    st.markdown(f"**Vencimiento elegido:** {fecha_venc}")

    # Delta → probabilidad
    T     = dias_venc/365
    r     = 0.02
    sigma = fila.get("impliedVolatility",0.25)
    delta = calc_delta(precio_act, strike_price, T, r, sigma, tipo_opcion.lower())
    st.markdown(f"**Probabilidad de ejercicio:** ~{abs(delta)*100:.1f}%")

    # Gráfico de payoff
    S      = np.linspace(precio_act*0.6, precio_act*1.4, 100)
    payoff = payoff_call(S,strike_price,premium) if tipo_opcion=="CALL" else payoff_put(S,strike_price,premium)
    if rol=="Vendedor": payoff = -payoff

    fig, ax = plt.subplots(figsize=(5,3))
    ax.xaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.plot(S,payoff,label=f"Payoff ({rol})")
    ax.axhline(0,linestyle="--",color="gray")
    ax.axvline(strike_price,linestyle="--",color="red",label="Strike")
    be = strike_price + (premium if tipo_opcion=="CALL" else -premium)
    ax.axvline(be,linestyle="--",color="green",label="Break-even")
    ax.legend()
    st.pyplot(fig)
