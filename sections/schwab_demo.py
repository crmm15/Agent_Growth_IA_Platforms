import streamlit as st
from utils.schwab_api import SchwabAPI  # Ajusta la ruta según tu proyecto

def schwab_demo():
    st.title("🔗 Conexión con Schwab API")

    api = SchwabAPI()

    # Botón para obtener cuentas
    if st.button("Obtener cuentas"):
        try:
            cuentas = api.get_accounts()
            st.success("Cuentas cargadas")
            st.json(cuentas)
            # Extrae el accountId (ajusta según tu respuesta real)
            if cuentas and isinstance(cuentas, list):
                account_id = cuentas[0]["securitiesAccount"]["accountId"]
                st.session_state["account_id"] = account_id
        except Exception as e:
            st.error(f"Error al consultar: {e}")

    # Botón para ver posiciones (si ya se obtuvo account_id)
    if "account_id" in st.session_state:
        if st.button("Ver posiciones"):
            try:
                positions = api.get_positions(st.session_state["account_id"])
                st.json(positions)
            except Exception as e:
                st.error(f"Error al consultar: {e}")
