import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def top_volume():
    st.header("🛠️ DEBUG: Chequeo de Descarga y Cálculo de Volumen S&P500")

    # Para debug: fuerza una fila para chequear visualización
    resultados = [{
        "Ticker": "TEST",
        "Vol_7d": 1,
        "Percentil_prev": 1,
        "Ratio": 1
    }]

    # Solo para pruebas, tickers grandes:
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]

    end = datetime.today()
    start = end - timedelta(days=60)

    for tk in tickers:
        try:
            df = yf.download(
                tk,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
            )
            st.write(f"{tk} - Cantidad de días descargados: {len(df)}")
            if df.empty:
                st.write(f"{tk}: DataFrame vacío")
                continue

            # Si el DataFrame tiene MultiIndex en columnas, aplanamos
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]

            cols_norm = [str(col).strip().lower() for col in df.columns]
            if "volume" not in cols_norm:
                st.write(f"{tk}: No se encontró columna 'Volume'. Columnas: {df.columns.tolist()}")
                continue

            vol_col_name = df.columns[cols_norm.index("volume")]
            df["Volume"] = pd.to_numeric(df[vol_col_name], errors="coerce")
            df = df.dropna(subset=["Volume"])
            st.write(f"{tk} - Volúmenes recientes: {df['Volume'].tail(10).tolist()}")

            if len(df) < 14:
                st.write(f"{tk}: Menos de 14 días hábiles con datos")
                continue

            vol_7d = df["Volume"].iloc[-7:]
            vol_prev = df["Volume"].iloc[:-7]

            if len(vol_prev) < 7 or vol_7d.empty:
                st.write(f"{tk}: Insuficientes días previos para percentil")
                continue

            percentil = vol_prev.quantile(0.0)  # Debe ser el mínimo histórico
            media_7d = vol_7d.mean()

            st.write(f"{tk}: Vol_7d={media_7d:.0f}, Percentil={percentil:.0f}, VolPrevLen={len(vol_prev)}")
            resultados.append({
                "Ticker": tk,
                "Vol_7d": int(media_7d),
                "Percentil_prev": int(percentil),
                "Ratio": round(media_7d / percentil, 2) if percentil > 0 else None
            })
        except Exception as ex:
            st.write(f"Error en {tk}: {ex}")
            continue

    # Muestra la tabla aunque solo tenga la fila TEST
    df_result = pd.DataFrame(resultados)
    st.dataframe(df_result)

    # También muestra la lista de tickers procesados
    st.write("Tickers procesados:", [r["Ticker"] for r in resultados])

if __name__ == "__main__":
    top_volume()
