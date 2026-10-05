import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

class GoogleAuthManager:
    """
    Gerenciador de autenticação unificado para as APIs do Google (GTM, GA4, Ads, Search Console).
    Suporta renovação automática de access token via Refresh Token e credenciais OAuth2.
    """
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
        self._access_token = None
        self._creds = None

    def load_credentials(self) -> Dict[str, Any]:
        if self._creds:
            return self._creds
            
        if os.path.exists(self.credentials_path):
            with open(self.credentials_path, "r", encoding="utf-8") as f:
                self._creds = json.load(f)
                return self._creds
                
        self._creds = {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN", ""),
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
            "customer_id": os.getenv("GOOGLE_ADS_CUSTOMER_ID", ""),
            "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
        }
        return self._creds

    def get_access_token(self, force_refresh: bool = False) -> str:
        if self._access_token and not force_refresh:
            return self._access_token

        creds = self.load_credentials()
        client_id = creds.get("client_id")
        client_secret = creds.get("client_secret")
        refresh_token = creds.get("refresh_token")

        if not all([client_id, client_secret, refresh_token]):
            raise ValueError(
                "Credenciais OAuth2 incompletas (necessário client_id, client_secret e refresh_token). "
                f"Verifique o arquivo {self.credentials_path} ou as variáveis de ambiente."
            )

        token_data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }).encode("utf-8")

        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._access_token = data["access_token"]
                return self._access_token
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erro ao renovar token OAuth do Google: {error_body} (Código HTTP {e.code})")
