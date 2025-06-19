import streamlit as st
from utils.schwab_api import SchwabAPI  # Ajusta la ruta según tu proyecto

def schwab_demo():
    st.title("🔗 Conexión con Schwab API")

    api = SchwabAPI()

    if st.button("Obtener cuentas y posiciones"):
        try:
            cuentas = api.get_accounts()
            st.success("Cuentas cargadas")
            st.json(cuentas)

            # Extrae el primer accountNumber (por si lo necesitas después)
            if cuentas and isinstance(cuentas, list):
                acc = cuentas[0]
                sa = acc.get("securitiesAccount", {})
                account_id = sa.get("accountNumber")
                st.session_state["account_id"] = account_id
                positions = sa.get("positions")
                if positions:
                    st.subheader("Tus posiciones")
                    st.json(positions)
                else:
                    st.info("No se encontraron posiciones en la cuenta.")
        except Exception as e:
            st.error(f"Error al consultar: {e}")
