import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from launchpilot.core.auth import GoogleAuthManager

class GA4Manager:
    """
    Controlador da API do Google Analytics 4 (Admin API v1beta).
    Automatiza criação de Propriedades, Streams de Dados Web e Dimensões Customizadas.
    """
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth = auth_manager or GoogleAuthManager()
        self.base_url = "https://analyticsadmin.googleapis.com/v1beta"

    def request(self, endpoint: str, payload: Optional[Dict[str, Any]] = None, method: Optional[str] = None) -> Dict[str, Any]:
        token = self.auth.get_access_token()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        
        if method is None:
            method = "POST" if payload is not None else "GET"

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            method=method
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_content = e.read().decode("utf-8", errors="ignore")
            try:
                return {"error": json.loads(error_content), "code": e.code}
            except Exception:
                return {"error": error_content, "code": e.code}

    def list_properties(self) -> List[Dict[str, Any]]:
        res = self.request("properties?filter=ancestor:accounts/0")
        return res.get("properties", [])

    def create_property(self, account_id: str, display_name: str, time_zone: str = "America/Sao_Paulo", currency_code: str = "BRL") -> Dict[str, Any]:
        payload = {
            "parent": f"accounts/{account_id}",
            "displayName": display_name,
            "timeZone": time_zone,
            "currencyCode": currency_code
        }
        return self.request("properties", payload=payload)

    def create_data_stream(self, property_id: str, stream_name: str, default_uri: str) -> Dict[str, Any]:
        payload = {
            "displayName": stream_name,
            "type": "WEB_DATA_STREAM",
            "webStreamData": {
                "defaultUri": default_uri
            }
        }
        return self.request(f"properties/{property_id}/dataStreams", payload=payload)

    def create_custom_dimension(self, property_id: str, parameter_name: str, display_name: str, description: str = "") -> Dict[str, Any]:
        payload = {
            "parameterName": parameter_name,
            "displayName": display_name,
            "description": description,
            "scope": "EVENT"
        }
        return self.request(f"properties/{property_id}/customDimensions", payload=payload)
