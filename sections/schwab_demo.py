import streamlit as st
from utils.schwab_api import SchwabAPI

def schwab_demo():
    st.title("🔗 Conexión con Schwab API")

    if 'schwab_api' not in st.session_state:
        st.session_state['schwab_api'] = SchwabAPI()

    api = st.session_state['schwab_api']

    if st.button("Obtener cuentas"):
        with st.spinner("Consultando Schwab..."):
            try:
                cuentas = api.get_accounts()
                st.session_state['schwab_cuentas'] = cuentas
                st.success("Cuentas cargadas")
            except Exception as e:
                st.error(f"Error al consultar: {e}")

    cuentas = st.session_state.get('schwab_cuentas')
    if cuentas:
        st.subheader("Respuesta")
        st.json(cuentas)
