import pandas as pd
import datetime
from utils.data_io import cargar_historial, guardar_historial
from utils.telegram_helpers import send_telegram_message


def registrar_accion(ticker: str, accion: str, rentab: float):
    """Registra acción en CSV y notifica vía Telegram."""
    df = cargar_historial()
    nueva = {
        "Fecha": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
        "Ticker": ticker,
        "Acción Tomada": accion,
        "Rentabilidad %": rentab
    }
    df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
    guardar_historial(df)
    send_telegram_message(f"📢 Acción: *{accion}* para `{ticker}` con rentab *{rentab*100:.2f}%*")
