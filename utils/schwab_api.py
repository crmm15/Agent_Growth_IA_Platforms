import os
import requests
from streamlit import secrets

SCHWAB_BASE_URL = "https://api.schwabapi.com"
CLIENT_ID = secrets.get("CLIENT_ID") or os.getenv("CLIENT_ID")
CLIENT_SECRET = secrets.get("CLIENT_SECRET") or os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = secrets.get("REFRESH_TOKEN") or os.getenv("REFRESH_TOKEN")

class SchwabAPI:
    """Pequeño cliente para la API de Schwab."""
    def __init__(self):
        self.access_token = None
    
    def _verify_credentials(self):
        """Ensure required credentials are present."""
        if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
            raise RuntimeError("Missing Schwab API credentials")
    
    def authenticate(self):
        self._verify_credentials()
        url = f"{SCHWAB_BASE_URL}/v1/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        resp = requests.post(url, data=payload)
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
