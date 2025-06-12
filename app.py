# app.py (estructura resumida)
```python
import streamlit as st
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

st.set_page_config(page_title="Agent GrowthIA M&M", layout="wide")

# Aquí irían funciones por sección: gestor_portfolio(), simulador_opciones(), dashboard(), backtest_darvas()
# Cada función separa lógica de UI y usa utilitarios importados.

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
