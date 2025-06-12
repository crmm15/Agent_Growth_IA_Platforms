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

from sections.simulador_opciones import simulador_opciones

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
