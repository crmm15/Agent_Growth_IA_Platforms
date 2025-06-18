#contiene operaciones de E/S, datos de mercado, cálculos de opciones, registro de portafolio 
#y notificaciones por Telegram, con caché y limpieza de código

import streamlit as st
from pathlib import Path
import logging

# Rutas base
BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_LOG = BASE_DIR / "registro_acciones.csv"

# Secretos
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID")

if TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
    logging.getLogger(__name__).warning(
        "Telegram secrets missing; related features will be disabled"
    )
