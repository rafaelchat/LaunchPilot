import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from launchpilot.core.auth import GoogleAuthManager

class PermissionsManager:
    """
    Gerencia delegação de permissões e convites para o cliente final.
    Permite rodar a criação na conta central/agência e convidar o e-mail do cliente como Admin.
    """
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth = auth_manager or GoogleAuthManager()

    def invite_gtm_admin(self, account_id: str, container_id: str, user_email: str) -> Dict[str, Any]:
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
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def invite_ga4_admin(self, property_id: str, user_email: str) -> Dict[str, Any]:
        token = self.auth.get_access_token()
        url = f"https://analyticsadmin.googleapis.com/v1beta/properties/{property_id}/accessBindings"
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
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def invite_search_console_owner(self, site_url: str, user_email: str) -> Dict[str, Any]:
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
                return json.loads(content) if content else {}
        except Exception as e:
            return {"error": str(e)}
