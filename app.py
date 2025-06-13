import streamlit as st
from sections.inicio          import show_inicio
from sections.gestor_portfolio import gestor_portfolio
from sections.simulador_opciones import simulador_opciones
from sections.dashboard       import dashboard
from sections.backtest_darvas import backtest_darvas

st.set_page_config(page_title="Agent GrowthIA M&M", layout="wide")
seccion = st.sidebar.radio(
    "📂 Elegí una sección",
    ["Inicio","Gestor de Portafolio","Simulador de Opciones","Dashboard de Desempeño","Backtesting Darvas"]
)

if seccion == "Inicio":
    show_inicio()
elif seccion == "Gestor de Portafolio":
    gestor_portfolio()
elif seccion == "Simulador de Opciones":
    simulador_opciones()
elif seccion == "Dashboard de Desempeño":
    dashboard()
elif seccion == "Backtesting Darvas":
    backtest_darvas()
