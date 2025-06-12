import pandas as pd
import streamlit as st
from config import ARCHIVO_LOG

@st.cache_data(show_spinner=False)
def cargar_historial() -> pd.DataFrame:
    """
    Carga el CSV de historial o crea DataFrame vacío con columnas si no existe
    o si está vacío.
    """
    if ARCHIVO_LOG.exists():
        try:
            return pd.read_csv(ARCHIVO_LOG)
        except pd.errors.EmptyDataError:
            # El archivo existe pero no tiene datos
            return pd.DataFrame(
                columns=["Fecha", "Ticker", "Acción Tomada", "Rentabilidad %"]
            )
    # No existe el archivo
    return pd.DataFrame(
        columns=["Fecha", "Ticker", "Acción Tomada", "Rentabilidad %"]
    )
