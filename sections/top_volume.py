import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def top_volume():
    st.header("📊 Tickers S&P 500 con Volumen 7d por Encima del Percentil 75 (30d previos)")

    # 1. Leer tickers S&P 500 desde un CSV público
    try:
        url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
        df_sp = pd.read_csv(url)
        tickers = df_sp['Symbol'].tolist()
    except Exception as e:
        st.error(f"No se pudo obtener la lista del S&P500: {e}")
        return

    st.caption(f"Analizando {len(tickers)} tickers S&P500: volumen promedio últimos 7 días vs. percentil 75 de los 30 días previos")

    # 2. Fechas para analizar
    end = datetime.today()
    start_37 = end - timedelta(days=37)
    start_7 = end - timedelta(days=7)
    start_30 = end - timedelta(days=37)

    seleccionables = []
    resultados = []

    for tk in tickers:
        df = yf.download(
            tk,
            start=start_37.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
        )
        if df.empty or "Volume" not in df.columns:
            continue
        # Desenrolla MultiIndex si hace falta
        if isinstance(df.columns, pd.MultiIndex):
            if "Volume" in df.columns.get_level_values(0):
                df.columns = df.columns.get_level_values(-1)
            else:
                continue

        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

        # Volúmenes a comparar
        vol_7d = df[df.index >= start_7]["Volume"]
        vol_30d = df[(df.index < start_7) & (df.index >= start_30)]["Volume"]

        if vol_30d.empty or vol_7d.empty:
            continue

        percentil_75 = vol_30d.quantile(0.75)
        media_7d = vol_7d.mean()

        if pd.notna(media_7d) and pd.notna(percentil_75) and media_7d > percentil_75:
            seleccionables.append(tk)
            resultados.append({
                "Ticker": tk,
                "Vol_7d": int(media_7d),
                "P75_vol_30d": int(percentil_75),
                "Ratio": round(media_7d / percentil_75, 2) if percentil_75 > 0 else None
            })

    if not seleccionables:
        st.warning("No se encontraron tickers con ese criterio.")
        return

    df_result = pd.DataFrame(resultados)
    st.dataframe(df_result.sort_values("Ratio", ascending=False).reset_index(drop=True))

    elegido = st.selectbox(
        "Seleccioná un ticker destacado por volumen alto (vs percentil 75)",
        seleccionables,
    )
    st.success(f"Ticker elegido: {elegido}")
