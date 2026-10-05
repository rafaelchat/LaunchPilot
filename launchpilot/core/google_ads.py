import json
import csv
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from launchpilot.core.auth import GoogleAuthManager

class GoogleAdsManager:
    """
    Controlador da API v25 do Google Ads.
    Permite criação de Ações de Conversão, Gestão de Campanhas, Grupos,
    Palavras-chave, Anúncios Responsivos (RSA), Filtros B2B e Exportação de Planilha Editor.
    """
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth = auth_manager or GoogleAuthManager()
        self.api_version = "v25"
        self.base_url = f"https://googleads.googleapis.com/{self.api_version}/customers"

    def request(self, customer_id: str, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        creds = self.auth.load_credentials()
        access_token = self.auth.get_access_token()
        cid = customer_id.replace("-", "").strip()
        login_cid = creds.get("login_customer_id", "").replace("-", "").strip() or cid

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
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_content = e.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(error_content)
            except Exception:
                return {"error": error_content, "code": e.code}

    def list_accessible_customers(self) -> List[str]:
        creds = self.auth.load_credentials()
        access_token = self.auth.get_access_token()
        url = f"https://googleads.googleapis.com/{self.api_version}/customers:listAccessibleCustomers"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "developer-token": creds.get("developer_token", "")
            }
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("resourceNames", [])
        except Exception as e:
            return []

    def get_or_create_conversion_action(self, customer_id: str, name: str = "Conversao WhatsApp Lead") -> Dict[str, Any]:
        cid = customer_id.replace("-", "").strip()
        
        # 1. Verifica se já existe
        search_res = self.request(cid, "googleAds:search", {
            "query": f"SELECT conversion_action.id, conversion_action.name, conversion_action.status FROM conversion_action WHERE conversion_action.name = '{name}'"
        })
        if "results" in search_res and search_res["results"]:
            action = search_res["results"][0].get("conversionAction", {})
            return {
                "id": action.get("id"),
                "name": action.get("name"),
                "status": action.get("status"),
                "exists": True
            }

        # 2. Cria nova
        payload = {
            "operations": [
                {
                    "create": {
                        "name": name,
                        "category": "CONTACT",
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
        res = self.request(cid, "conversionActions:mutate", payload)
        return res

    def export_campaign_editor_csv(self, campaign_name: str, ad_groups: List[Dict[str, Any]], negative_keywords: List[str], final_url: str, output_path: str):
        """
        Gera planilha compatível com Google Ads Editor contendo:
        - Campanha e Orçamento
        - 4 Grupos de Anúncios (G1 Geral + 3 Verticais)
        - Palavras-chave em Frase e Exata
        - Anúncios Responsivos de Pesquisa (RSAs) com 15 títulos e 4 descrições
        - Lista de Palavras-chave Negativas
        """
        rows = []
        # Header do Google Ads Editor
        fieldnames = [
            "Campaign", "Ad Group", "Keyword", "Criterion Type",
            "Headline 1", "Headline 2", "Headline 3", "Headline 4", "Headline 5",
            "Headline 6", "Headline 7", "Headline 8", "Headline 9", "Headline 10",
            "Headline 11", "Headline 12", "Headline 13", "Headline 14", "Headline 15",
            "Description 1", "Description 2", "Description 3", "Description 4",
            "Final URL", "Status"
        ]

        # 1. Linha da Campanha
        rows.append({
            "Campaign": campaign_name,
            "Ad Group": "",
            "Status": "Paused"
        })

        # 2. Grupos, Anúncios e Palavras
        for ag in ad_groups:
            ag_name = ag.get("name", "Geral")
            headlines = ag.get("headlines", [])
            descriptions = ag.get("descriptions", [])
            keywords = ag.get("keywords", [])

            # Linha do Grupo
            rows.append({
                "Campaign": campaign_name,
                "Ad Group": ag_name,
                "Status": "Enabled"
            })

            # Linha do Anúncio RSA
            rsa_row = {
                "Campaign": campaign_name,
                "Ad Group": ag_name,
                "Final URL": final_url,
                "Status": "Enabled"
            }
            for i in range(15):
                h_val = headlines[i] if i < len(headlines) else ""
                rsa_row[f"Headline {i+1}"] = h_val[:30]
            for j in range(4):
                d_val = descriptions[j] if j < len(descriptions) else ""
                rsa_row[f"Description {j+1}"] = d_val[:90]
            rows.append(rsa_row)

            # Linhas de Palavras-Chave
            for kw in keywords:
                clean_kw = kw.strip()
                match_type = "Broad"
                if clean_kw.startswith("[") and clean_kw.endswith("]"):
                    match_type = "Exact"
                    clean_kw = clean_kw[1:-1]
                elif clean_kw.startswith('"') and clean_kw.endswith('"'):
                    match_type = "Phrase"
                    clean_kw = clean_kw[1:-1]

                rows.append({
                    "Campaign": campaign_name,
                    "Ad Group": ag_name,
                    "Keyword": clean_kw,
                    "Criterion Type": match_type,
                    "Status": "Enabled"
                })

        # 3. Palavras Negativas da Campanha
        for neg in negative_keywords:
            rows.append({
                "Campaign": campaign_name,
                "Ad Group": "",
                "Keyword": neg.strip(),
                "Criterion Type": "Negative Broad",
                "Status": "Enabled"
            })

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

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
        
        res = self.request(cid, "campaignCriteria:mutate", {"operations": ops})
        
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
