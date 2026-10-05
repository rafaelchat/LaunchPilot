import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from launchpilot.core.auth import GoogleAuthManager

class PermissionsManager:
    """
    Gerencia delegação de permissões e convites para o cliente final.
    Permite rodar a criação na conta central/agência e convidar o e-mail do cliente como Administrador
    no Google Tag Manager, Google Analytics 4, Google Search Console e Google Ads.
    """
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth = auth_manager or GoogleAuthManager()

    def invite_gtm_admin(self, account_id: str, container_id: str, user_email: str) -> Dict[str, Any]:
        """
        Convida o cliente como Administrador do Contêiner GTM (acesso de publicação e administração).
        """
        token = self.auth.get_access_token()
        url = f"https://tagmanager.googleapis.com/tagmanager/v2/accounts/{account_id}/containers/{container_id}/user_permissions"
        payload = {
            "emailAddress": user_email,
            "containerAccess": {
                "containerId": container_id,
                "permission": "admin"
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return {"status": "SUCCESS", "service": "GTM", "email": user_email, "data": json.loads(resp.read().decode("utf-8"))}
        except Exception as e:
            return {"status": "ERROR", "service": "GTM", "email": user_email, "error": str(e)}

    def invite_ga4_admin(self, property_id: str, user_email: str) -> Dict[str, Any]:
        """
        Atribui permissão de Administrador da Propriedade no GA4 (roles/analytics.admin).
        """
        token = self.auth.get_access_token()
        clean_prop = property_id.replace("properties/", "")
        url = f"https://analyticsadmin.googleapis.com/v1beta/properties/{clean_prop}/accessBindings"
        payload = {
            "user": user_email,
            "roles": ["roles/analytics.admin"]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return {"status": "SUCCESS", "service": "GA4", "email": user_email, "data": json.loads(resp.read().decode("utf-8"))}
        except Exception as e:
            return {"status": "ERROR", "service": "GA4", "email": user_email, "error": str(e)}

    def invite_search_console_owner(self, site_url: str, user_email: str) -> Dict[str, Any]:
        """
        Adiciona o cliente como Proprietário Verificado (siteOwner) no Google Search Console.
        """
        token = self.auth.get_access_token()
        encoded_site = urllib.parse.quote(site_url, safe="")
        url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/users"
        payload = {
            "email": user_email,
            "permissionLevel": "siteOwner"
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                content = resp.read().decode("utf-8")
                data = json.loads(content) if content else {}
                return {"status": "SUCCESS", "service": "SearchConsole", "email": user_email, "data": data}
        except Exception as e:
            return {"status": "ERROR", "service": "SearchConsole", "email": user_email, "error": str(e)}

    def invite_google_ads_admin(self, customer_id: str, user_email: str) -> Dict[str, Any]:
        """
        Envia convite de Administrador da conta no Google Ads via CustomerUserAccessInvitation.
        Se o Developer Token estiver em nível Explorer/Teste, gera link de acesso direto para liberação imediata.
        """
        creds = self.auth.load_credentials()
        access_token = self.auth.get_access_token()
        cid = customer_id.replace("-", "").strip()
        login_cid = creds.get("login_customer_id", "").replace("-", "").strip() or cid

        url = f"https://googleads.googleapis.com/v25/customers/{cid}/customerUserAccessInvitations:mutate"
        payload = {
            "operation": {
                "create": {
                    "emailAddress": user_email,
                    "accessRole": "ADMIN"
                }
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
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
                return {"status": "SUCCESS", "service": "GoogleAds", "email": user_email, "data": json.loads(resp.read().decode("utf-8"))}
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="ignore")
            # Link direto caso o token esteja em modo explorer
            direct_link = f"https://ads.google.com/aw/accountaccess/users?ocid={cid}"
            return {
                "status": "FALLBACK_LINK",
                "service": "GoogleAds",
                "email": user_email,
                "direct_invite_link": direct_link,
                "message": "Developer Token restrito para mutation de usuários em produção. Utilize o link direto para aprovar em 1 clique.",
                "details": err
            }
        except Exception as e:
            return {"status": "ERROR", "service": "GoogleAds", "email": user_email, "error": str(e)}

    def delegate_all_admin_permissions(self, client_email: str, gtm_account_id: Optional[str] = None, gtm_container_id: Optional[str] = None, ga4_property_id: Optional[str] = None, site_url: Optional[str] = None, ads_customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa delegação completa de Administrador em todos os serviços provisionados.
        """
        results = {}
        if gtm_account_id and gtm_container_id:
            results["gtm"] = self.invite_gtm_admin(gtm_account_id, gtm_container_id, client_email)
            
        if ga4_property_id:
            results["ga4"] = self.invite_ga4_admin(ga4_property_id, client_email)
            
        if site_url:
            results["search_console"] = self.invite_search_console_owner(site_url, client_email)
            
        if ads_customer_id:
            results["google_ads"] = self.invite_google_ads_admin(ads_customer_id, client_email)

        return results
