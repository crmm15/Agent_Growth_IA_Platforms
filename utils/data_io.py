import pandas as pd
import streamlit as st
from pathlib import Path
from config import ARCHIVO_LOG

@st.cache_data(show_spinner=False)
def cargar_historial() -> pd.DataFrame:
    if ARCHIVO_LOG.exists():
        try:
            return pd.read_csv(ARCHIVO_LOG)
        except pd.errors.EmptyDataError:
            # Si el CSV está vacío
            return pd.DataFrame(
                columns=["Fecha", "Ticker", "Acción Tomada", "Rentabilidad %"]
            )
    # Si no existe aún el archivo
    return pd.DataFrame(
        columns=["Fecha", "Ticker", "Acción Tomada", "Rentabilidad %"]
    )

def guardar_historial(df: pd.DataFrame):
    """
    Guarda el DataFrame en CSV y limpia la caché para que
    cargar_historial recargue los datos actualizados.
    """
    df.to_csv(ARCHIVO_LOG, index=False)
    st.cache_data.clear()
