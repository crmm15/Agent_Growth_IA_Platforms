# sections/gestor_portfolio.py
import streamlit as st
import pandas as pd
import numpy as np

from utils.portfolio        import registrar_accion
from utils.telegram_helpers import generar_y_enviar_resumen_telegram

def gestor_portfolio():
    st.subheader("📊 Análisis de Posiciones")

    # Subida de Excel
    archivo = st.session_state.get("global_excel")
    if archivo is None:
        st.info("Subí el archivo Excel para empezar.")
        return

    # Lectura y limpieza
    df = pd.read_excel(archivo, sheet_name="Inversiones")
    df.columns = df.columns.str.strip()
    if 'Ticker' not in df.columns or 'Cantidad' not in df.columns:
        st.error("El Excel debe tener columnas 'Ticker' y 'Cantidad'.")
        return
    df = df[df['Ticker'].notnull() & df['Cantidad'].notnull()]

    # Show summary table
    st.dataframe(df)

    # Lógica de recomendaciones
    for _, row in df.iterrows():
        ticker = row["Ticker"]
        rentab = row.get("Rentabilidad", np.nan)
        dca     = row.get("DCA", np.nan)

        st.markdown(f"### ▶ {ticker}: " +
                    (f"{rentab*100:.2f}%" if pd.notna(rentab) else "—"))

        if pd.isna(rentab):
            st.write("🔍 Revisión: Datos incompletos o mal formateados.")
        elif rentab >= 0.2:
            st.write("🔒 Recomendación: Comprar PUT para proteger ganancias.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Ejecutar PUT {ticker}", key=f"put_{ticker}"):
                    registrar_accion(ticker, "Comprar PUT", rentab)
                    st.success(f"✔ Acción registrada para {ticker}")
            with col2:
                if st.button(f"❌ Ignorar {ticker}", key=f"ign_{ticker}"):
                    registrar_accion(ticker, "Ignorado", rentab)
                    st.info(f"🔕 Ignorado para {ticker}")

        elif rentab > 0.08:
            st.write("🔄 Recomendación: Mantener posición.")
            if st.button(f"✅ Mantener {ticker}", key=f"mant_{ticker}"):
                registrar_accion(ticker, "Mantener", rentab)
                st.success(f"✔ Acción registrada para {ticker}")

        else:
            st.write("📉 Recomendación: Revisar, baja rentabilidad.")
            if st.button(f"📋 Revisar {ticker}", key=f"rev_{ticker}"):
                registrar_accion(ticker, "Revisión Manual", rentab)
                st.info(f"🔍 Acción registrada para {ticker}")

    st.markdown("---")
    if st.button("📤 Enviar resumen a Telegram", key="resumen_portafolio"):
        generar_y_enviar_resumen_telegram()
        st.success("📈 Resumen enviado por Telegram.")
