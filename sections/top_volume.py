import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False)
def _cargar_tickers_sp500() -> list[str]:
    """Devuelve la lista de símbolos del S&P 500 desde un CSV público."""
    url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
    df_sp = pd.read_csv(url)
    return df_sp["Symbol"].tolist()


def top_volume():
    st.header("📊  Tickers S&P 500 con Volumen 7d > Percentil (previos)")

    # 1. Parámetros de usuario
    percentil_sel = st.slider(
        "Percentil histórico de comparación",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.05,
    )
    dias_hist = st.slider(
        "Días de historial a descargar",
        min_value=30,
        max_value=180,
        value=60,
        step=10,
    )

    # 2. Leer tickers S&P 500 (con caché)
    try:
         tickers = _cargar_tickers_sp500()
    except Exception as e:
        st.error(f"No se pudo obtener la lista del S&P500: {e}")
        return

     st.caption(
        f"Analizando {len(tickers)} tickers S&P500: volumen promedio últimos 7 días hábiles vs. percentil de días previos"
    )

     # 3. Fechas para analizar (descargar suficiente historia)
    end = datetime.today()
    start = end - timedelta(days=dias_hist)

    seleccionables = []
    resultados = []

    progreso = st.progress(0.0)
    for idx, tk in enumerate(tickers):
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
            vol_prev = df["Volume"].iloc[:-7]

            if len(vol_prev) < 7 or vol_7d.empty:
                continue

            percentil = vol_prev.quantile(percentil_sel)
            media_7d = vol_7d.mean()

            if pd.notna(media_7d) and pd.notna(percentil) and percentil > 0:
                seleccionables.append(tk)
                resultados.append({
                    "Ticker": tk,
                    "Vol_7d": int(media_7d),
                    "Percentil_prev": int(percentil),
                    "Ratio": round(media_7d / percentil, 2) if percentil > 0 else None
                })
        except Exception:
            continue

    progreso.progress((idx + 1) / len(tickers))

    if not seleccionables:
        st.warning("No se encontraron tickers con ese criterio.")
        return

    df_result = pd.DataFrame(resultados)
    st.dataframe(df_result.sort_values("Ratio", ascending=False).reset_index(drop=True))

    elegido = st.selectbox(
        "Seleccioná un ticker destacado por volumen alto (vs percentil previos)",
        seleccionables,
    )
    st.success(f"Ticker elegido: {elegido}")

if __name__ == "__main__":
    top_volume()
