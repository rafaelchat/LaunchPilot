import os
import re
from typing import Dict, Any, List

class Auditor:
    """
    Audita integridade dos botões, links de WhatsApp e presença de tags no HTML gerado.
    """
    @staticmethod
    def audit_html_file(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"Arquivo {file_path} nao encontrado"}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        issues = []
        checks = []

        # 1. Verifica GTM
        has_gtm_head = "googletagmanager.com/gtm.js" in content
        has_gtm_body = "googletagmanager.com/ns.html" in content
        if has_gtm_head and has_gtm_body:
            checks.append("✓ Google Tag Manager instalado corretamente (Head & Body)")
        else:
            issues.append("⚠ GTM ausente ou incompleto")

        # 2. Verifica Consent Mode
        if "gtag('consent', 'default'" in content or 'gtag("consent", "default"' in content:
            checks.append("✓ Consent Mode V2 ativo")
        else:
            issues.append("⚠ Consent Mode V2 ausente")

        # 3. Verifica Links de WhatsApp
        wa_links = re.findall(r"https://wa\.me/[a-zA-Z0-9_?=&%-]+", content)
        if wa_links:
            checks.append(f"✓ {len(wa_links)} botões de WhatsApp ativos e formatados")
        else:
            issues.append("⚠ Nenhum link de WhatsApp encontrado")

        # 4. Verifica dataLayer click_origin
        if "whatsapp_click" in content and "click_origin" in content:
            checks.append("✓ Telemetria de cliques no dataLayer ativa")
        else:
            issues.append("⚠ Eventos de clique no dataLayer não encontrados")

        return {
            "status": "pass" if not issues else "warning",
            "passed_checks": checks,
            "issues": issues
        }
