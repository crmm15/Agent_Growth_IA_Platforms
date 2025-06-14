#contiene operaciones de E/S, datos de mercado, cálculos de opciones, registro de portafolio 
#y notificaciones por Telegram, con caché y limpieza de código

import streamlit as st
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_LOG = BASE_DIR / "registro_acciones.csv"

# Secretos
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
