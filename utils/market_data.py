# utils/market_data.py 
import pandas as pd
import yfinance as yf
from datetime import timedelta

def cargar_precio_historico(
    ticker: str,
    intervalo: str,
    start: pd.Timestamp = None,
    end: pd.Timestamp = None
) -> pd.DataFrame:
    """
    Descarga OHLCV para `ticker` en `intervalo`.
    Si `start` y `end` están, usa yf.download con fechas;
    si no, descarga TODO el histórico (period='max').
    """
    if start is not None and end is not None:
        # yfinance trata end como exclusivo, así que sumamos un día
        end_dt = pd.to_datetime(end)
        df = yf.download(
            ticker,
            start=pd.to_datetime(start).strftime("%Y-%m-%d"),
            end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval=intervalo,
            progress=False,
        )
    else:
        df = yf.download(
            ticker,
            period="max",
            interval=intervalo,
            progress=False,
        )

    # 1) Aseguramos índice datetime sin zona horaria
    df.index = pd.to_datetime(df.index).tz_localize(None)

    # 2) Si vinieran columnas MultiIndex (por ejemplo, nivel0=‘Close’, nivel1=‘BTC-USD’),
    #    las aplanamos y nos quedamos con el primer nivel:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 3) Devolvemos sólo las columnas que nos interesan
    return df[["Open", "High", "Low", "Close", "Volume"]]
