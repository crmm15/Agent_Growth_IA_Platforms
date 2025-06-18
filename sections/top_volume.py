import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def top_volume():
    st.header("📊  Tickers S&P 500 con Volumen 7d > Percentil (previos)")

    # 1. Leer tickers S&P 500 desde un CSV público
    try:
        url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
        df_sp = pd.read_csv(url)
        tickers = df_sp['Symbol'].tolist()
    except Exception as e:
        st.error(f"No se pudo obtener la lista del S&P500: {e}")
        return

    st.caption(f"Analizando {len(tickers)} tickers S&P500: volumen promedio últimos 7 días hábiles vs. percentil de días previos")

    # 2. Fechas para analizar (descargar suficiente historia)
    end = datetime.today()
    start = end - timedelta(days=60)   # Bajamos 2 meses por seguridad

    seleccionables = []
    resultados = []

    for tk in tickers:
        try:
            df = yf.download(
                tk,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
            )
            if df.empty:
                continue

            # Si el DataFrame tiene MultiIndex en columnas, aplanamos
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]
            # Normaliza nombres de columnas
            cols_norm = [str(col).strip().lower() for col in df.columns]
            if "volume" not in cols_norm:
                continue
            vol_col_name = df.columns[cols_norm.index("volume")]
            df["Volume"] = pd.to_numeric(df[vol_col_name], errors="coerce")
            df = df.dropna(subset=["Volume"])

            # Cortes flexibles
            if len(df) < 14:  # Necesitamos al menos 14 días para tener 7+7
                continue

            # Últimos 7 días hábiles (los más recientes)
            vol_7d = df["Volume"].iloc[-7:]
            # Todos los días previos a esos 7 (para percentil)
            vol_p_
