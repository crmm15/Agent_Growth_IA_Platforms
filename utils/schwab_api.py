import os
import requests
from streamlit import secrets
from requests.auth import HTTPBasicAuth  # <-- Nuevo import

SCHWAB_BASE_URL = "https://api.schwabapi.com"
CLIENT_ID = secrets.get("CLIENT_ID") or os.getenv("CLIENT_ID")
CLIENT_SECRET = secrets.get("CLIENT_SECRET") or os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = secrets.get("REFRESH_TOKEN") or os.getenv("REFRESH_TOKEN")

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
            "redirect_uri": "https://agentgrowthia.streamlit.app/"  # Debe coincidir con el de tu app Schwab
        }
        # Auth por header, NO en el body
        resp = requests.post(
            url,
            data=payload,
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)  # <-- Importante
        )
        resp.raise_for_status()
        self.access_token = resp.json().get("access_token")
        return self.access_token

    def _headers(self):
        if not self.access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_accounts(self):
        url = f"{SCHWAB_BASE_URL}/v1/accounts"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def get_positions(self, account_id: str):
        url = f"{SCHWAB_BASE_URL}/v1/accounts/{account_id}/positions"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()
