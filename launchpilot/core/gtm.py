import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any, List, Optional
from launchpilot.core.auth import GoogleAuthManager

class GTMManager:
    """
    Controlador programático da API v2 do Google Tag Manager.
    Automatiza criação de Contêineres, Variáveis, Acionadores (Triggers), Tags e Publicação de Versões
    com suporte completo a deduplicação de conversões via orderId e Consent Mode V2.
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

    def list_accounts(self) -> List[Dict[str, Any]]:
        res = self.request("accounts")
        return res.get("account", [])

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

    def get_or_create_container(self, account_id: str, name: str) -> Dict[str, Any]:
        existing = self.list_containers(account_id)
        for c in existing:
            if c.get("name") == name:
                return c
        return self.create_container(account_id, name)

    def get_default_workspace(self, account_id: str, container_id: str) -> str:
        res = self.request(f"accounts/{account_id}/containers/{container_id}/workspaces")
        workspaces = res.get("workspace", [])
        if not workspaces:
            # Cria workspace padrao se necessario
            create_res = self.request(f"accounts/{account_id}/containers/{container_id}/workspaces", payload={"name": "Padrao"})
            return create_res.get("workspaceId", "1")
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
            pub_res = self.request(
                f"accounts/{account_id}/containers/{container_id}/versions/{version_id}/publish",
                method="POST"
            )
            return {
                "status": "PUBLISHED",
                "versionId": version_id,
                "versionName": version_name,
                "result": pub_res
            }
        return ver_res

    def setup_complete_tracking(self, account_id: str, container_id: str, ga4_measurement_id: Optional[str] = None, ads_conversion_id: Optional[str] = None, ads_conversion_label: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera em lote no GTM:
        - Variáveis da Camada de Dados (dlv - orderId, dlv - btn_name, dlv - btn_placement, dlv - page_path)
        - Trigger Custom Event: whatsapp_conversion
        - Tag Vinculador de Conversões (Conversion Linker)
        - Google Tag Oficial do Google Ads (AW-...)
        - Tag de Conversão Master do Ads com deduplicação por orderId
        - Tag GA4 Evento generate_lead
        - Publica uma versão ativa imediatamente
        """
        ws_id = self.get_default_workspace(account_id, container_id)
        
        # 1. Variáveis Data Layer
        dl_vars = [
            ("dlv - orderId", "orderId"),
            ("dlv - btn_name", "btn_name"),
            ("dlv - btn_placement", "btn_placement"),
            ("dlv - page_path", "page_path")
        ]
        for var_name, var_key in dl_vars:
            self.create_variable(account_id, container_id, ws_id, var_name, "v", [
                {"type": "integer", "key": "dataLayerVersion", "value": "2"},
                {"type": "template", "key": "name", "value": var_key}
            ])
        
        # 2. Trigger Custom Event: whatsapp_conversion
        trigger_res = self.create_trigger(account_id, container_id, ws_id, {
            "name": "CE - whatsapp_conversion",
            "type": "customEvent",
            "customEventFilter": [
                {
                    "type": "equals",
                    "parameter": [
                        {"type": "template", "key": "arg0", "value": "{{_event}}"},
                        {"type": "template", "key": "arg1", "value": "whatsapp_conversion"}
                    ]
                }
            ]
        })
        trigger_id = trigger_res.get("triggerId", "2147479553")

        # 3. Conversion Linker (Dispara em All Pages)
        self.create_tag(account_id, container_id, ws_id, {
            "name": "Google Ads - Conversion Linker",
            "type": "gclidw",
            "firingTriggerId": ["2147479553"] # ID padrao All Pages no GTM
        })

        # 4. Google Tag (Ads) se configurado
        if ads_conversion_id:
            raw_id = ads_conversion_id.replace("AW-", "").strip()
            self.create_tag(account_id, container_id, ws_id, {
                "name": f"Google Tag - AW-{raw_id}",
                "type": "googtag",
                "parameter": [{"type": "template", "key": "tagId", "value": f"AW-{raw_id}"}],
                "firingTriggerId": ["2147479553"]
            })

            # Tag de Conversão do Google Ads com Deduplicação por orderId
            if ads_conversion_label:
                self.create_tag(account_id, container_id, ws_id, {
                    "name": "Google Ads - Conversao WhatsApp Lead (Deduplicada)",
                    "type": "awct",
                    "parameter": [
                        {"type": "template", "key": "conversionId", "value": raw_id},
                        {"type": "template", "key": "conversionLabel", "value": ads_conversion_label},
                        {"type": "template", "key": "conversionValue", "value": "1.0"},
                        {"type": "template", "key": "currencyCode", "value": "BRL"},
                        {"type": "template", "key": "orderId", "value": "{{dlv - orderId}}"}
                    ],
                    "firingTriggerId": [trigger_id]
                })

        # 5. GA4 Tag (se measurement id fornecido)
        if ga4_measurement_id:
            raw_g = ga4_measurement_id.strip()
            self.create_tag(account_id, container_id, ws_id, {
                "name": f"Google Tag - GA4 {raw_g}",
                "type": "googtag",
                "parameter": [{"type": "template", "key": "tagId", "value": raw_g}],
                "firingTriggerId": ["2147479553"]
            })

            self.create_tag(account_id, container_id, ws_id, {
                "name": "GA4 - Evento Lead WhatsApp",
                "type": "gaawc",
                "parameter": [
                    {"type": "template", "key": "eventName", "value": "generate_lead"},
                    {"type": "template", "key": "measurementId", "value": raw_g},
                    {
                        "type": "list",
                        "key": "eventParameters",
                        "list": [
                            {"type": "map", "map": [{"type": "template", "key": "name", "value": "order_id"}, {"type": "template", "key": "value", "value": "{{dlv - orderId}}"}]},
                            {"type": "map", "map": [{"type": "template", "key": "name", "value": "btn_name"}, {"type": "template", "key": "value", "value": "{{dlv - btn_name}}"}]},
                            {"type": "map", "map": [{"type": "template", "key": "name", "value": "btn_placement"}, {"type": "template", "key": "value", "value": "{{dlv - btn_placement}}"}]}
                        ]
                    }
                ],
                "firingTriggerId": [trigger_id]
            })

        # 6. Publicar versão
        return self.publish_workspace(account_id, container_id, ws_id, "LaunchPilot v1.0 - Auto Tracking & Deduplication")
