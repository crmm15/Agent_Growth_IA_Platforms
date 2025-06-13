# sections/dashboard.py
import streamlit as st
import pandas as pd
from utils.data_io import cargar_historial
from utils.telegram_helpers import generar_y_enviar_resumen_telegram

def dashboard():
    """
    Muestra métricas y gráficos de rentabilidad
    del historial de decisiones guardado en registro_acciones.csv.
    """
    st.subheader("📊 Dashboard de Desempeño")

    # 1) Cargar historial (devuelve DataFrame vacío si no hay datos)
    df = cargar_historial()

    if df.empty:
        st.info("No hay acciones registradas aún. Ejecutá primero el Gestor de Portafolio.")
        return

    # 2) Asegurar que la columna Fecha sea tipo datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # 3) Filtrado de tickers
    tickers = df['Ticker'].unique().tolist()
    filtro = st.multiselect("📌 Filtrar Tickers", options=tickers, default=tickers)
    df_filtrado = df[df['Ticker'].isin(filtro)]

    # 4) Métricas clave
    col1, col2, col3 = st.columns(3)
    col1.metric("Total decisiones", len(df_filtrado))
    col2.metric("% PUTs", f"{(df_filtrado['Acción Tomada']=='Comprar PUT').mean()*100:.1f}%")
    col3.metric("% Mantener", f"{(df_filtrado['Acción Tomada']=='Mantener').mean()*100:.1f}%")

    st.markdown("---")

    # 5) Gráficos de desempeño
    st.bar_chart(
        df_filtrado.groupby('Acción Tomada')['Rentabilidad %'].mean()
    )
    st.line_chart(
        df_filtrado.set_index('Fecha')['Rentabilidad %']
    )

    # 6) Botón para enviar resumen por Telegram
    if st.button("📤 Enviar resumen a Telegram", key="dash_resumen"):
        generar_y_enviar_resumen_telegram()
        st.success("📤 Resumen enviado por Telegram!")
