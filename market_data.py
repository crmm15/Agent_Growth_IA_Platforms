import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=600, show_spinner=False)
def cargar_precio_historico(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Descarga historial con caché de 10 minutos."""
    df = yf.Ticker(ticker).history(period=period)
    df.index = pd.to_datetime(df.index)
    return df