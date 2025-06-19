import streamlit as st
from sections.inicio            import show_inicio
from sections.gestor_portfolio  import gestor_portfolio
from sections.simulador_opciones import simulador_opciones
from sections.dashboard        import dashboard
from sections.backtest_darvas  import backtest_darvas
from sections.top_volume       import top_volume
from sections.schwab_demo      import schwab_demo

st.set_page_config(page_title="Agent GrowthIA M&M", layout="wide")

# ——— Subida de Excel global ————————————————————————————————
uploaded_file = st.sidebar.file_uploader(
    "📁 Subí tu archivo Excel (.xlsx) para Portafolio, Simulador y Dashboard",
    type=["xlsx"],
    key="global_excel"
)

# ——— Menú lateral ———————————————————————————————————————————
seccion = st.sidebar.radio(
    "📂 Elegí una sección",
    [
        "Inicio",
        "Gestor de Portafolio",
        "Simulador de Opciones",
        "Dashboard de Desempeño",
        "Backtesting Darvas",
        "Top Volumen",
        "Schwab API Test"
    ]
)
# ——— Rutina principal ———————————————————————————————————————
if seccion == "Inicio":
    show_inicio()

elif seccion == "Gestor de Portafolio":
    # dentro de gestor_portfolio() debes usar st.session_state["global_excel"]
    gestor_portfolio()

elif seccion == "Simulador de Opciones":
    simulador_opciones()

elif seccion == "Dashboard de Desempeño":
    dashboard()

elif seccion == "Backtesting Darvas":
    backtest_darvas()
    
elif seccion == "Top Volumen":
    top_volume()

else:  # Schwab API Test
    schwab_demo()

