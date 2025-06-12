import streamlit as st
from utils.data_io import cargar_historial
from utils.telegram_helpers import generar_y_enviar_resumen_telegram
from utils.portfolio import registrar_accion

def gestor_portfolio():
    st.subheader("🗂️ Gestor de Portafolio")
    df = cargar_historial()
    st.dataframe(df)
    # formulario para registrar acciones...
    if st.button("📤 Enviar resumen diario a Telegram"):
        generar_y_enviar_resumen_telegram()