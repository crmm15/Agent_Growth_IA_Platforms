import streamlit as st
import pandas as pd
from utils.telegram_helpers import generar_y_enviar_resumen_telegram

def dashboard():
    st.subheader("📊 Dashboard de Desempeño")
    df = pd.read_csv('registro_acciones.csv', parse_dates=['Fecha'])
    col1,col2,col3 = st.columns(3)
    col1.metric("Decisiones", len(df))
    col2.metric("% PUT", f"{(df['Acción Tomada']=='Comprar PUT').mean()*100:.1f}%")
    col3.metric("% Mantener", f"{(df['Acción Tomada']=='Mantener').mean()*100:.1f}%")
    st.bar_chart(df.groupby('Acción Tomada')['Rentabilidad %'].mean())