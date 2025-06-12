# app.py (estructura resumida)
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
from pathlib import Path

from config import ARCHIVO_LOG
from utils.data_io import cargar_historial, guardar_historial
from utils.portfolio import registrar_accion
from utils.telegram import send_telegram_chart
from utils.market_data import cargar_precio_historico
from utils.options import payoff_call, payoff_put, calc_delta
from strategies.darvas import calc_mavilimw, calc_wae, robust_trend_filter

st.set_page_config(page_title="Agent GrowthIA M&M", layout="wide")

# Aquí irían funciones por sección: gestor_portfolio(), simulador_opciones(), dashboard(), backtest_darvas()
# Cada función separa lógica de UI y usa utilitarios importados.

if seccion == "Inicio":
    st.title("🚀 Bienvenido a GrowthIA M&M")
    # Ruta al .md
    md_path = Path(__file__).parent / "prompts" / "prompt_inicial.md"
    if md_path.exists():
        contenido = md_path.read_text(encoding="utf-8")
        st.markdown(contenido)
    else:
        st.info("No se encontró el archivo prompt_inicial.md")
    st.markdown("---")


if __name__ == "__main__":
    seccion = st.sidebar.radio(...)
    if seccion == "Gestor de Portafolio":
        gestor_portfolio()
    elif seccion == "Simulador de Opciones":
        simulador_opciones()
    elif seccion == "Dashboard de Desempeño":
        dashboard()
    elif seccion == "Backtesting Darvas":
        backtest_darvas()
