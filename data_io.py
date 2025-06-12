import pandas as pd
import streamlit as st
from config import ARCHIVO_LOG

@st.cache_data(show_spinner=False)
def cargar_historial() -> pd.DataFrame:
    """Carga el CSV de historial o crea DataFrame vacío si no existe."""
    if ARCHIVO_LOG.exists():
        return pd.read_csv(ARCHIVO_LOG)
    return pd.DataFrame(columns=["Fecha", "Ticker", "Acción Tomada", "Rentabilidad %"])


def guardar_historial(df: pd.DataFrame):
    """Guarda el historial y refresca la caché."""
    df.to_csv(ARCHIVO_LOG, index=False)
    st.cache_data.clear()