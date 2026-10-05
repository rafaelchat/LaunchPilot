import os
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

class SiteBuilder:
    """
    Compila o template HTML com dados do negócio, estilização e injeção automática de GTM e GA4.
    """
    def __init__(self, template_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.template_path = template_path or os.path.join(base_dir, "templates", "default_lp", "index.html")

    def build(self, config: Dict[str, Any], gtm_public_id: Optional[str] = None) -> str:
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()

        biz = config.get("business", {})
        theme = biz.get("theme", {})

        # Formata link de WhatsApp
        phone = biz.get("whatsapp_number", "").replace("+", "").replace("-", "").replace(" ", "")
        message = urllib.parse.quote(biz.get("whatsapp_default_message", "Olá! Gostaria de mais informações."))
        wa_link = f"https://wa.me/{phone}?text={message}"

        # Divide a headline para ter destaque em gradiente
        headline = biz.get("headline", "Recupere o Acesso ao seu Negócio Online")
        parts = headline.split("?")
        headline_first = parts[0] + "?" if len(parts) > 1 else headline
        headline_highlight = parts[1] if len(parts) > 1 else ""

        # GTM Snippets
        gtm_head = ""
        gtm_body = ""
        if gtm_public_id:
            gtm_head = f"""<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{gtm_public_id}');</script>"""
            
            gtm_body = f"""<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gtm_public_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>"""

        # Substituições no template
        replacements = {
            "{{TITLE}}": f"{biz.get('company_name')} | Atendimento Especializado",
            "{{DESCRIPTION}}": biz.get("subheadline", ""),
            "{{COMPANY_NAME}}": biz.get("company_name", "Empresa"),
            "{{PRIMARY_COLOR}}": theme.get("primary_color", "#0f172a"),
            "{{ACCENT_COLOR}}": theme.get("accent_color", "#2563eb"),
            "{{ACCENT_HOVER}}": theme.get("accent_hover", "#1d4ed8"),
            "{{WHATSAPP_LINK}}": wa_link,
            "{{HEADLINE_FIRST}}": headline_first,
            "{{HEADLINE_HIGHLIGHT}}": headline_highlight,
            "{{SUBHEADLINE}}": biz.get("subheadline", ""),
            "{{CTA_TEXT}}": biz.get("cta_text", "Falar no WhatsApp"),
            "{{YEAR}}": str(datetime.now().year),
            "{{GTM_HEAD_SNIPPET}}": gtm_head,
            "{{GTM_BODY_SNIPPET}}": gtm_body
        }

        output = template
        for key, val in replacements.items():
            output = output.replace(key, str(val))

        return output

    def export_dist(self, config: Dict[str, Any], dist_dir: str, gtm_public_id: Optional[str] = None):
        os.makedirs(dist_dir, exist_ok=True)
        html = self.build(config, gtm_public_id)
        
        # 1. index.html
        with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
            
        # 2. robots.txt
        with open(os.path.join(dist_dir, "robots.txt"), "w", encoding="utf-8") as f:
            f.write("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n")
            
        # 3. sitemap.xml
        domain = config.get("deploy", {}).get("domain", "https://seusite.com.br")
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{domain}/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
        with open(os.path.join(dist_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(sitemap)
