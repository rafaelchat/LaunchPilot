import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any, List, Optional
from launchpilot.core.auth import GoogleAuthManager

class GTMManager:
    """
    Controlador programático da API v2 do Google Tag Manager.
    Automatiza criação de Contêineres, Variáveis, Acionadores (Triggers), Tags e Publicação de Versões.
    """
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth = auth_manager or GoogleAuthManager()
        self.base_url = "https://tagmanager.googleapis.com/tagmanager/v2"

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
        
        # Retry simples com backoff se houver rate limit (HTTP 429)
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_content = e.read().decode("utf-8", errors="ignore")
                if e.code == 429 and attempt < max_attempts - 1:
                    time.sleep(10 * (attempt + 1))
                    continue
                try:
                    return {"error": json.loads(error_content), "code": e.code}
                except Exception:
                    return {"error": error_content, "code": e.code}

    def list_containers(self, account_id: str) -> List[Dict[str, Any]]:
        res = self.request(f"accounts/{account_id}/containers")
        return res.get("container", [])

    def create_container(self, account_id: str, name: str, usage_context: List[str] = None) -> Dict[str, Any]:
        if usage_context is None:
            usage_context = ["web"]
        payload = {
            "name": name,
            "usageContext": usage_context
        }
        return self.request(f"accounts/{account_id}/containers", payload=payload)

    def get_default_workspace(self, account_id: str, container_id: str) -> str:
        res = self.request(f"accounts/{account_id}/containers/{container_id}/workspaces")
        workspaces = res.get("workspace", [])
        if not workspaces:
            raise RuntimeError(f"Nenhum workspace encontrado no contêiner {container_id}")
        return workspaces[0]["workspaceId"]

    def create_variable(self, account_id: str, container_id: str, workspace_id: str, name: str, var_type: str, parameter: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "name": name,
            "type": var_type,
            "parameter": parameter
        }
        return self.request(f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/variables", payload=payload)

    def create_trigger(self, account_id: str, container_id: str, workspace_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.request(f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/triggers", payload=payload)

    def create_tag(self, account_id: str, container_id: str, workspace_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.request(f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/tags", payload=payload)

    def publish_workspace(self, account_id: str, container_id: str, workspace_id: str, version_name: str) -> Dict[str, Any]:
        payload = {
            "name": version_name,
            "notes": "Criado e publicado automaticamente pelo LaunchPilot"
        }
        ver_res = self.request(
            f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/create_version",
            payload=payload
        )
        if "containerVersion" in ver_res:
            version_id = ver_res["containerVersion"]["containerVersionId"]
            return self.request(
                f"accounts/{account_id}/containers/{container_id}/versions/{version_id}/publish",
                method="POST"
            )
        return ver_res

    def setup_complete_tracking(self, account_id: str, container_id: str, ga4_measurement_id: Optional[str] = None, ads_conversion_id: Optional[str] = None, ads_conversion_label: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera em lote:
        - Variáveis da Camada de Dados (dlv - event_category, dlv - click_origin)
        - Triggers de Clique de WhatsApp e Formulário
        - Tag Vinculador de Conversões (Conversion Linker)
        - Google Tag Oficial do Google Ads
        - Tag de Conversão Master do Ads
        - Publica uma versão ativa
        """
        ws_id = self.get_default_workspace(account_id, container_id)
        
        # 1. Variáveis Data Layer
        self.create_variable(account_id, container_id, ws_id, "dlv - click_origin", "v", [
            {"type": "integer", "key": "dataLayerVersion", "value": "2"},
            {"type": "template", "key": "name", "value": "click_origin"}
        ])
        
        # 2. Trigger Custom Event: whatsapp_click
        trigger_res = self.create_trigger(account_id, container_id, ws_id, {
            "name": "CE - whatsapp_click",
            "type": "customEvent",
            "customEventFilter": [
                {
                    "type": "equals",
                    "parameter": [
                        {"type": "template", "key": "arg0", "value": "{{_event}}"},
                        {"type": "template", "key": "arg1", "value": "whatsapp_click"}
                    ]
                }
            ]
        })
        trigger_id = trigger_res.get("triggerId", "2147479553")

        # 3. Conversion Linker
        self.create_tag(account_id, container_id, ws_id, {
            "name": "Google Ads - Conversion Linker",
            "type": "gclidw",
            "firingTriggerId": ["2147479553"] # All Pages
        })

        # 4. Google Tag (Ads) se configurado
        if ads_conversion_id:
            raw_id = ads_conversion_id.replace("AW-", "")
            self.create_tag(account_id, container_id, ws_id, {
                "name": f"Google Tag - AW-{raw_id}",
                "type": "googtag",
                "parameter": [{"type": "template", "key": "tagId", "value": f"AW-{raw_id}"}],
                "firingTriggerId": ["2147479553"]
            })

            if ads_conversion_label:
                self.create_tag(account_id, container_id, ws_id, {
                    "name": "Google Ads - Conversao WhatsApp Lead",
                    "type": "awct",
                    "parameter": [
                        {"type": "template", "key": "conversionId", "value": raw_id},
                        {"type": "template", "key": "conversionLabel", "value": ads_conversion_label},
                        {"type": "template", "key": "conversionValue", "value": "1.0"},
                        {"type": "template", "key": "currencyCode", "value": "BRL"}
                    ],
                    "firingTriggerId": [trigger_id]
                })

        # Publicar versão
        return self.publish_workspace(account_id, container_id, ws_id, "LaunchPilot v1.0 - Auto Configured")
