import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional
from launchpilot.core.auth import GoogleAuthManager

class SearchConsoleManager:
    """
    Controlador da API do Google Search Console (Webmasters API v3).
    Automatiza cadastro de sites e envio de sitemaps.
    """
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        self.auth = auth_manager or GoogleAuthManager()
        self.base_url = "https://www.googleapis.com/webmasters/v3"

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
                content = resp.read().decode("utf-8")
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            error_content = e.read().decode("utf-8", errors="ignore")
            try:
                return {"error": json.loads(error_content), "code": e.code}
            except Exception:
                return {"error": error_content, "code": e.code}

    def add_site(self, site_url: str) -> Dict[str, Any]:
        encoded_site = urllib.parse.quote(site_url, safe="")
        return self.request(f"sites/{encoded_site}", method="PUT")

    def submit_sitemap(self, site_url: str, sitemap_url: str) -> Dict[str, Any]:
        encoded_site = urllib.parse.quote(site_url, safe="")
        encoded_sitemap = urllib.parse.quote(sitemap_url, safe="")
        return self.request(f"sites/{encoded_site}/sitemaps/{encoded_sitemap}", method="PUT")
