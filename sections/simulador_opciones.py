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

    selected_ticker = st.selectbox("Seleccioná un ticker", df["Ticker"].unique())
    
    nivel_riesgo = st.radio(
        "🎯 Tu perfil de riesgo",
        ["Conservador", "Balanceado", "Agresivo"],
        index=1,
        help="Define cuánto riesgo estás dispuesto a asumir. Conservador prioriza protección, Agresivo busca mayor upside."
    )
    
    tipo_opcion = st.radio(
        "Tipo de opción",
        ["CALL", "PUT"],
        help="CALL te beneficia si sube el precio. PUT protege si baja el precio."
    )
    
    rol = st.radio(
        "Rol en la opción",
        ["Comprador", "Vendedor"],
        index=0,
        help="Elegí si querés simular comprar o vender la opción."
    )
    
    sugerencia = {"Conservador": 5, "Balanceado": 10, "Agresivo": 20}
    delta_strike = st.slider(
        "📉 % sobre el precio actual para el strike",
        -50, 50, sugerencia[nivel_riesgo],
        help="Determina qué tan alejado estará el strike del precio actual. Positivo para CALL, negativo para PUT."
    )
    
    dias_a_vencimiento = st.slider(
        "📆 Días hasta vencimiento",
        7, 90, 30,
        help="Número estimado de días hasta la fecha de vencimiento de la opción."
    )
    
    datos = df[df["Ticker"] == selected_ticker].iloc[0]
    precio_actual = datos["Precio Actual"]
    strike_price = round(precio_actual * (1 + delta_strike / 100), 2)
    
    ticker_yf = yf.Ticker(selected_ticker)
    expiraciones = ticker_yf.options
    
    if expiraciones:
        fecha_venc = min(
            expiraciones,
            key=lambda x: abs((pd.to_datetime(x) - pd.Timestamp.today()).days - dias_a_vencimiento)
        )
    
        cadena = ticker_yf.option_chain(fecha_venc)
        tabla_opciones = cadena.calls if tipo_opcion == "CALL" else cadena.puts
        tabla_opciones = tabla_opciones.dropna(subset=["bid", "ask"])
    
        if tabla_opciones.empty:
            st.warning("⚠ No hay opciones válidas para ese strike.")
        else:
            fila = tabla_opciones.loc[np.abs(tabla_opciones["strike"] - strike_price).idxmin()]
            premium = (fila["bid"] + fila["ask"]) / 2
    
        st.markdown(f"**Precio actual:** ${precio_actual:.2f}")
        st.markdown(f"**Strike simulado:** ${strike_price}")
        st.markdown(f"**Prima estimada:** ${premium:.2f}")
        st.markdown(f"**Vencimiento elegido:** {fecha_venc}")
    
        try:
            if "delta" in fila and not pd.isna(fila["delta"]):
                delta = fila["delta"]
            else:
                T = dias_a_vencimiento / 365
                r = 0.02
                sigma = fila.get("impliedVolatility", 0.25)
                delta = calcular_delta_call_put(precio_actual, strike_price, T, r, sigma, tipo_opcion)
    
            if delta is not None:
                prob = abs(delta) * 100
                st.markdown(f"**Probabilidad estimada de que se ejecute la opción (Delta): ~{prob:.1f}%**")
            else:
                st.warning("⚠ No se pudo calcular el delta estimado.")
        except Exception:
            st.warning("⚠ Error al calcular el delta.")
    
        S = np.linspace(precio_actual * 0.6, precio_actual * 1.4, 100)
        payoff = calcular_payoff_call(S, strike_price, premium) if tipo_opcion == "CALL" else calcular_payoff_put(S, strike_price, premium)
        if rol == "Vendedor":
            payoff = -payoff
    
        max_payoff = np.max(payoff)
        if premium > 0 and rol == "Comprador":
            rentabilidad_pct = (max_payoff / premium) * 100
            st.markdown(f"**Rentabilidad máxima estimada sobre la prima invertida: ~{rentabilidad_pct:.1f}%**")
    
        break_even = strike_price + premium if tipo_opcion == "CALL" else strike_price - premium
        if rol == "Vendedor":
            break_even = strike_price - premium if tipo_opcion == "CALL" else strike_price + premium

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.xaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.set_xlabel("Precio del activo al vencimiento (USD)")
    ax.set_ylabel("Resultado neto (USD)")
    ax.plot(S, payoff, label=f"Payoff ({rol})")
    ax.axhline(0, color="gray", linestyle="--")
    ax.axvline(strike_price, color="red", linestyle="--", label="Strike")
    ax.axvline(break_even, color="green", linestyle="--", label="Break-even")
    ax.set_title(f"{tipo_opcion} - {selected_ticker} ({nivel_riesgo})")
    ax.legend()
    st.pyplot(fig)

   with st.expander("ℹ️ Interpretación del gráfico"):
        if rol == "Comprador" and tipo_opcion == "CALL":
            st.markdown(f"🎯 Comprás el derecho a comprar la acción a {strike_price:.2f} pagando una prima de {premium:.2f}")
            st.markdown("📉 Si el precio final está por debajo del strike, no ejercés y pierdes solo la prima")
            st.markdown(f"📈 Si el precio sube por encima de {break_even:.2f}, tienes ganancias netas")
            st.markdown("⚖️ El gráfico muestra tu rentabilidad según el precio al vencimiento")

        elif rol == "Comprador" and tipo_opcion == "PUT":
            st.markdown(f"🎯 Comprás el derecho a vender la acción a {strike_price:.2f} pagando una prima de {premium:.2f}")
            st.markdown(f"📈 Ganás si la acción baja por debajo de {break_even:.2f}")
            st.markdown("📉 Si se mantiene por encima del strike, la pérdida se limita a la prima")
            st.markdown("⚖️ El gráfico refleja tu cobertura o especulación a la baja.")

        elif rol == "Vendedor" and tipo_opcion == "CALL":
            st.markdown(f"💰 Vendés la opción y recibes {premium:.2f} de prima, pero asumes la obligación de vender a {strike_price:.2f}")
            st.markdown("✅ Si la acción cierra por debajo del strike, ganás toda la prima")
            st.markdown(f"⚠️ Si sube por encima de {break_even:.2f}, comenzás a perder dinero")
            st.markdown("📉 Riesgo ilimitado si el precio sube mucho (al menos que tengas las acciones)")

        elif rol == "Vendedor" and tipo_opcion == "PUT":
            st.markdown(f"💰 Vendés la opción y te pagan {premium:.2f} por asumir la obligación de comprar a {strike_price:.2f}")
            st.markdown("✅ Ganás la prima si el precio se mantiene por encima del strike")
            st.markdown(f"⚠️ Si cae por debajo de {break_even:.2f}, comenzás a perder dinero")
            st.markdown("📉 Riesgo limitado: como máximo hasta que la acción llegue a $0")

    with st.expander("📘 Perfil del rol seleccionado"):
        if rol == "Comprador":
            st.markdown(f"💸 Pagás una prima {premium:.2f} por el derecho a ejercer")
            st.markdown("📈 Ganancia potencial ilimitada (CALL) o limitada (PUT)")
            st.markdown("🔻 Pérdida máxima: la prima")
        else:
            if tipo_opcion == "CALL":
                st.markdown(f"💵 Recibes una prima {premium:.2f} por asumir la obligación de vender a {strike_price:.2f}")
                st.markdown("✅ Ganancia máxima: la prima si la acción no supera el strike")
                st.markdown(f"⚠️ Si el precio sube por encima de {break_even:.2f}, comenzás a tener pérdidas. Estas son potencialmente ilimitadas")
                st.markdown("🔒 Estrategia útil para generar ingresos si creés que la acción no superará el strike")
            else:
                st.markdown(f"💵 Recibes una prima {premium:.2f} por asumir la obligación de comprar a {strike_price:.2f}")
                st.markdown("✅ Ganancia máxima: la prima si la acción se mantiene por encima del strike.")
                st.markdown(f"⚠️ Si la acción cae por debajo de {break_even:.2f}, empiezás a tener pérdidas. El riesgo es alto, pero finito (hasta que la acción llegue a $0)")
                st.markdown("🛡 Estrategia usada si estás dispuesto a comprar la acción más barata que hoy")

    # 13) Envío a Telegram
    if st.button("📤 Enviar simulación a Telegram", key="simu_telegram"):
        from utils.telegram_helpers import enviar_grafico_simulacion_telegram
        enviar_grafico_simulacion_telegram(fig, selected_ticker)
        st.success("📤 Simulación enviada por Telegram!")
