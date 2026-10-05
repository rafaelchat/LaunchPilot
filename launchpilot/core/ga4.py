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

    def list_accounts_and_properties(self) -> List[Dict[str, Any]]:
        """
        Retorna lista consolidada de todas as contas e propriedades no GA4 via accountSummaries.
        """
        res = self.request("accountSummaries")
        accounts = []
        for acc in res.get("accountSummaries", []):
            acc_id = acc.get("account", "").replace("accounts/", "")
            acc_name = acc.get("displayName", "")
            props = []
            for p in acc.get("propertySummaries", []):
                p_id = p.get("property", "").replace("properties/", "")
                props.append({
                    "property_id": p_id,
                    "display_name": p.get("displayName", "")
                })
            accounts.append({
                "account_id": acc_id,
                "display_name": acc_name,
                "properties": props
            })
        return accounts

    def list_properties(self) -> List[Dict[str, Any]]:
        """Retorna lista plana de todas as propriedades"""
        accounts = self.list_accounts_and_properties()
        all_props = []
        for acc in accounts:
            for p in acc["properties"]:
                p["account_id"] = acc["account_id"]
                all_props.append(p)
        return all_props

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

    def list_data_streams(self, property_id: str) -> List[Dict[str, Any]]:
        res = self.request(f"properties/{property_id}/dataStreams")
        return res.get("dataStreams", [])

    def create_custom_dimension(self, property_id: str, parameter_name: str, display_name: str, description: str = "") -> Dict[str, Any]:
        payload = {
            "parameterName": parameter_name,
            "displayName": display_name,
            "description": description,
            "scope": "EVENT"
        }
        return self.request(f"properties/{property_id}/customDimensions", payload=payload)

    def setup_property_complete(self, account_id: str, display_name: str, site_url: str) -> Dict[str, Any]:
        """
        Gera propriedade, web stream e dimensões customizadas essenciais (order_id, btn_name, btn_placement).
        """
        prop_res = self.create_property(account_id, display_name)
        if "name" not in prop_res:
            return prop_res
        
        prop_id = prop_res["name"].replace("properties/", "")
        
        # Cria Web Stream
        stream_res = self.create_data_stream(prop_id, f"Web - {display_name}", site_url)
        measurement_id = None
        if "webStreamData" in stream_res:
            measurement_id = stream_res["webStreamData"].get("measurementId")

        # Cria Dimensões Customizadas para Telemetria
        self.create_custom_dimension(prop_id, "order_id", "Lead Order ID (Deduplicacao)")
        self.create_custom_dimension(prop_id, "btn_name", "Nome do Botao Clicado")
        self.create_custom_dimension(prop_id, "btn_placement", "Posicao do Botao na Pagina")

        return {
            "property_id": prop_id,
            "measurement_id": measurement_id,
            "property": prop_res,
            "stream": stream_res
        }
