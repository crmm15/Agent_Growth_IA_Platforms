import os
import logging
import requests
from streamlit import secrets
import streamlit as st
from requests.auth import HTTPBasicAuth

SCHWAB_BASE_URL = "https://api.schwabapi.com"

logger = logging.getLogger(__name__)

def save_refresh_token(token: str, filename="refresh_token.txt"):
    """Guarda el refresh token en un archivo seguro."""
    with open(filename, "w") as f:
        f.write(token)
    print(f"[INFO] Nuevo refresh_token guardado en {filename}")

def load_refresh_token(filename="refresh_token.txt"):
    try:
        with open(filename, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Busca el refresh_token primero en Streamlit secrets, luego en env, luego en archivo.
REFRESH_TOKEN = (
    secrets.get("REFRESH_TOKEN")
    or os.getenv("REFRESH_TOKEN")
    or load_refresh_token()
)
CLIENT_ID = secrets.get("CLIENT_ID") or os.getenv("CLIENT_ID")
CLIENT_SECRET = secrets.get("CLIENT_SECRET") or os.getenv("CLIENT_SECRET")

class SchwabAPI:
    def __init__(self):
        self.access_token = None
    
    def _verify_credentials(self):
        if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
            raise RuntimeError("Missing Schwab API credentials")
    
    def authenticate(self):
        self._verify_credentials()
        url = f"{SCHWAB_BASE_URL}/v1/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "redirect_uri": "https://agentgrowthia.streamlit.app/"
        }
        try:
            resp = requests.post(
                url,
                data=payload,
                auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data.get("access_token")
            # Si Schwab entrega un nuevo refresh_token, lo guardamos.
            new_refresh = data.get("refresh_token")
            if new_refresh and new_refresh != REFRESH_TOKEN:
                save_refresh_token(new_refresh)
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error authenticating with Schwab: {e}")
            st.error(f"Error de conexión con Schwab: {e}")
            raise

    def _headers(self):
        if not self.access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_accounts(self):
        url = f"{SCHWAB_BASE_URL}/trader/v1/accounts"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
            print("Status code:", resp.status_code)
            print("Response text:", resp.text)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting accounts: {e}")
            st.error(f"Error al obtener cuentas de Schwab: {e}")
            raise

    def get_positions(self, account_id: str):
        url = f"{SCHWAB_BASE_URL}/trader/v1/accounts/{account_id}/positions"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
            print("Status code:", resp.status_code)    # Para debug
            print("Response text:", resp.text)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting positions: {e}")
            st.error(f"Error al obtener posiciones de Schwab: {e}")
            raise
