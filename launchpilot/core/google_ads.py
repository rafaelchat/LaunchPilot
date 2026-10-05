import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from launchpilot.core.auth import GoogleAuthManager

class GoogleAdsManager:
    """
    Controlador da API v25 do Google Ads.
    Permite criação de Ações de Conversão, Gestão de Anúncios e Filtros de Audiência B2B.
    """
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth = auth_manager or GoogleAuthManager()
        self.api_version = "v25"
        self.base_url = f"https://googleads.googleapis.com/{self.api_version}/customers"

    def request(self, customer_id: str, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        creds = self.auth.load_credentials()
        access_token = self.auth.get_access_token()
        cid = customer_id.replace("-", "")
        login_cid = creds.get("login_customer_id", "").replace("-", "") or cid

        url = f"{self.base_url}/{cid}/{endpoint.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8") if payload else None

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "developer-token": creds.get("developer_token", ""),
                "login-customer-id": login_cid,
                "Content-Type": "application/json"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_content = e.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(error_content)
            except Exception:
                return {"error": error_content, "code": e.code}

    def create_conversion_action(self, customer_id: str, name: str, category: str = "CONTACT") -> Dict[str, Any]:
        cid = customer_id.replace("-", "")
        payload = {
            "operations": [
                {
                    "create": {
                        "name": name,
                        "category": category,
                        "type": "WEBPAGE",
                        "status": "ENABLED",
                        "valueSettings": {
                            "defaultValue": 1.0,
                            "defaultCurrencyCode": "BRL",
                            "alwaysUseDefaultValue": True
                        },
                        "countingType": "ONE_PER_CLICK"
                    }
                }
            ]
        }
        return self.request(cid, "conversionActions:mutate", payload)

    def apply_b2b_in_market_filter(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """
        Aplica 12 categorias In-Market B2B com restrição obrigatória (bidOnly=False),
        focando estritamente em tomadores de decisão empresariais.
        """
        cid = customer_id.replace("-", "")
        b2b_categories = [
            "80523", "80463", "80517", "80518", "80520", "80530",
            "80279", "80281", "80883", "80138", "80137", "80528"
        ]
        ops = []
        for cat_id in b2b_categories:
            ops.append({
                "create": {
                    "campaign": f"customers/{cid}/campaigns/{campaign_id}",
                    "userInterest": {
                        "userInterestCategory": f"customers/{cid}/userInterests/{cat_id}"
                    }
                }
            })
        
        # 1. Adiciona os critérios
        res = self.request(cid, "campaignCriteria:mutate", {"operations": ops})
        
        # 2. Configura targetingSetting como TARGETING (restrição estrita)
        target_payload = {
            "operations": [
                {
                    "update": {
                        "resourceName": f"customers/{cid}/campaigns/{campaign_id}",
                        "targetingSetting": {
                            "targetRestrictions": [
                                {
                                    "targetingDimension": "AUDIENCE",
                                    "bidOnly": False
                                }
                            ]
                        }
                    },
                    "updateMask": "targetingSetting.targetRestrictions"
                }
            ]
        }
        self.request(cid, "campaigns:mutate", target_payload)
        return res
