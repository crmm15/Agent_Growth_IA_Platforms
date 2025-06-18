import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def top_volume():
    st.header("📊 Tickers con mayor volumen 7d")

    # Leer tickers S&P 500 desde un CSV público (¡no requiere lxml!)
    try:
        url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
        df_sp = pd.read_csv(url)
        tickers = df_sp['Symbol'].tolist()
    except Exception as e:
        st.error(f"No se pudo obtener la lista del S&P500: {e}")
        return

    st.caption(f"Analizando {len(tickers)} tickers S&P500 con aumento de volumen ≥ 50% vs 7 días previos")

    end = datetime.today()
    start_prev = end - timedelta(days=14)
    start_curr = end - timedelta(days=7)

    seleccionables = []
    for tk in tickers:
        df = yf.download(
            tk,
            start=start_prev.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
        )
        if df.empty:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if "Volume" not in df.columns:
            continue
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
        vol_prev = df.loc[df.index < start_curr, "Volume"].mean()
        vol_curr = df.loc[df.index >= start_curr, "Volume"].mean()
        if (
            pd.notna(vol_prev)
            and pd.notna(vol_curr)
            and vol_prev > 0
            and vol_curr >= 1.5 * vol_prev
        ):
            seleccionables.append(tk)

    if not seleccionables:
        st.warning("No se encontraron tickers con ese criterio.")
        return

    elegido = st.selectbox(
        "Seleccioná un ticker destacado por volumen",
        seleccionables,
    )
    st.success(f"Ticker elegido: {elegido}")
