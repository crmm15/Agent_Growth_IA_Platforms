# app.py
import streamlit as st
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Y tus utilitarios de opciones/ delta y payoff:
from utils.options import payoff_call, payoff_put, calc_delta

import pandas as pd
import numpy as np
import datetime
import yfinance as yf

from config import ARCHIVO_LOG
from utils.data_io import cargar_historial, guardar_historial
from utils.portfolio import registrar_accion
from utils.telegram import send_telegram_chart
from utils.market_data import cargar_precio_historico
from utils.options import payoff_call, payoff_put, calc_delta
from strategies.darvas import calc_mavilimw, calc_wae, robust_trend_filter

# 1) Configuración de la página
st.set_page_config(page_title="Agent GrowthIA M&M", layout="wide")

# 2) Menú lateral
seccion = st.sidebar.radio(
    "📂 Elegí una sección",
    [
        "Inicio",
        "Gestor de Portafolio",
        "Simulador de Opciones",
        "Dashboard de Desempeño",
        "Backtesting Darvas"
    ]
)
def simulador_opciones():
    st.subheader("📈 Simulador de Opciones con Perfil de Riesgo")

    # Asegúrate de tener un DataFrame 'df' con columnas "Ticker" y "Precio Actual".
    # Si antes cargabas tu histórico o tu portafolio, reutiliza esa variable.
    df = cargar_historial()  # o la variable que usabas

    selected_ticker = st.selectbox("Seleccioná un ticker", df["Ticker"].unique())

    nivel_riesgo = st.radio(
        "🎯 Tu perfil de riesgo",
        ["Conservador", "Balanceado", "Agresivo"],
        index=1,
        help="Define cuánto riesgo estás dispuesto a asumir..."
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
        help="Determina qué tan alejado estará el strike del precio actual."
    )

    dias_a_vencimiento = st.slider(
        "📆 Días hasta vencimiento",
        7, 90, 30,
        help="Número estimado de días hasta vencimiento."
    )

    datos = df[df["Ticker"] == selected_ticker].iloc[0]
    precio_actual = datos["Precio Actual"]
    strike_price = round(precio_actual * (1 + delta_strike / 100), 2)

    ticker_yf = yf.Ticker(selected_ticker)
    expiraciones = ticker_yf.options

    if expiraciones:
        # Encuentra la fecha más cercana al slider
        fecha_venc = min(
            expiraciones,
            key=lambda x: abs((pd.to_datetime(x) - pd.Timestamp.today()).days - dias_a_vencimiento)
        )

        cadena = ticker_yf.option_chain(fecha_venc)
        tabla_opciones = cadena.calls if tipo_opcion == "CALL" else cadena.puts
        tabla_opciones = tabla_opciones.dropna(subset=["bid", "ask"])

        if tabla_opciones.empty:
            st.warning("⚠ No hay opciones válidas para ese strike.")
            return

        fila = tabla_opciones.loc[np.abs(tabla_opciones["strike"] - strike_price).idxmin()]
        premium = (fila["bid"] + fila["ask"]) / 2

        # Mostrar datos clave
        st.markdown(f"**Precio actual:** ${precio_actual:.2f}")
        st.markdown(f"**Strike simulado:** ${strike_price}")
        st.markdown(f"**Prima estimada:** ${premium:.2f}")
        st.markdown(f"**Vencimiento elegido:** {fecha_venc}")

        # Calcula delta/probabilidad
        T = dias_a_vencimiento / 365
        r = 0.02
        sigma = fila.get("impliedVolatility", 0.25)
        delta = calc_delta(precio_actual, strike_price, T, r, sigma, tipo_opcion.lower())
        prob = abs(delta) * 100
        st.markdown(f"**Probabilidad de ejercicio (Delta):** ~{prob:.1f}%")

        # Gráfico de payoff
        S = np.linspace(precio_actual * 0.6, precio_actual * 1.4, 100)
        payoff = payoff_call(S, strike_price, premium) if tipo_opcion == "CALL" else payoff_put(S, strike_price, premium)
        if rol == "Vendedor":
            payoff = -payoff

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.xaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
        ax.set_xlabel("Precio al vencimiento (USD)")
        ax.set_ylabel("Resultado neto (USD)")
        ax.plot(S, payoff, label=f"Payoff ({rol})")
        ax.axhline(0, linestyle="--", linewidth=1, color="gray")
        ax.axvline(strike_price, linestyle="--", linewidth=1, color="red", label="Strike")
        ax.axvline(strike_price + (premium if tipo_opcion=="CALL" else -premium),
                   linestyle="--", linewidth=1, color="green", label="Break-even")
        ax.legend()
        st.pyplot(fig)

        # Aquí puedes reinsertar tus expanders de interpretación y perfil...
    else:
        st.warning("⚠ No se encontró cadena de opciones para este ticker.")

# 3) Renderizado de secciones
if seccion == "Inicio":
    st.title("🚀 Bienvenido a GrowthIA M&M")
    md_path = Path(__file__).parent / "prompts" / "prompt_inicial.md"
    if md_path.exists():
        contenido = md_path.read_text(encoding="utf-8")
        st.markdown(contenido)
    else:
        st.info("No se encontró el archivo prompt_inicial.md")
    st.markdown("---")

elif seccion == "Gestor de Portafolio":
    gestor_portfolio()      # tu función importada

elif seccion == "Simulador de Opciones":
    simulador_opciones()   # tu función importada

elif seccion == "Dashboard de Desempeño":
    dashboard()             # tu función importada

elif seccion == "Backtesting Darvas":
    backtest_darvas()       # tu función importada
