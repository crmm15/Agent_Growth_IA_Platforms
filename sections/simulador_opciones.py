import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from utils.market_data import cargar_precio_historico
from utils.options import (
    calcular_payoff_call as payoff_call,
    calcular_payoff_put  as payoff_put,
    calcular_delta_call_put as calc_delta
)

def simulador_opciones():
    st.subheader("📈 Simulador de Opciones con Perfil de Riesgo")
    archivo = st.sidebar.file_uploader("📁 Subí tu Excel", type=["xlsx"], key="simu")
    if archivo is None:
        st.info("Subí el archivo Excel para empezar.")
        return

    df = pd.read_excel(archivo, sheet_name="Inversiones")
    df.columns = df.columns.str.strip()
    st.write("Columnas disponibles:", df.columns.tolist())

    tickers = df["Ticker"].dropna().unique().tolist()
    if not tickers:
        st.error("No encontré tickers en el Excel.")
        return

    selected_ticker = st.selectbox("Seleccioná un ticker", tickers)
    datos = df[df["Ticker"] == selected_ticker].iloc[0]

    # Fallback precio
    if "Precio Actual" in df.columns:
        precio_actual = datos["Precio Actual"]
    else:
        hist = cargar_precio_historico(selected_ticker, period="1d")
        precio_actual = hist["Close"].iloc[-1]

    st.markdown(f"**Precio actual usado:** ${precio_actual:.2f}")

    # … el resto de tu lógica de strike, expiración, payoff, gráficos, etc.
