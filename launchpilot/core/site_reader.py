import re
import urllib.request
from typing import Dict, Any, List, Optional

class SiteReader:
    """
    Leitor e Analisador de Sites Existentes para o LaunchPilot.
    Rastreia a URL do cliente, extrai o posicionamento, serviços, botões de conversão,
    tags existentes e utiliza IA para mapear a estrutura completa de tráfego e concorrentes.
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_site(self, url: str) -> Dict[str, Any]:
        """
        Faz o scraping seguro do HTML e extrai informações estruturais do site.
        """
        clean_url = url.strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url

        req = urllib.request.Request(clean_url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return {"error": f"Não foi possível acessar a URL {clean_url}: {str(e)}", "url": clean_url}

        # Extração de Título e Meta Description
        title_m = re.search(r'<title>(.*?)</title>', html, re.I | re.S)
        desc_m = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.I | re.S)
        
        title = title_m.group(1).strip() if title_m else ""
        description = desc_m.group(1).strip() if desc_m else ""

        # Extração de Títulos H1 e H2
        h1s = [re.sub(r'<[^>]+>', '', h).strip() for h in re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.I | re.S)]
        h2s = [re.sub(r'<[^>]+>', '', h).strip() for h in re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.I | re.S)]

        # Extração de Links de WhatsApp
        wa_links = re.findall(r'https://(?:wa\.me|api\.whatsapp\.com)[^\s"\'<>]+', html)

        # Extração de Telefones e E-mails
        phones = re.findall(r'(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\d{4}[-\s]?\d{4}|\d{4}[-\s]?\d{4})', html)
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', html)

        # Detecção de Tags Existentes
        detected_gtm = list(set(re.findall(r'GTM-[A-Z0-9]+', html)))
        detected_ga4 = list(set(re.findall(r'G-[A-Z0-9]+', html)))
        detected_ads = list(set(re.findall(r'AW-[0-9]+', html)))
        has_meta_pixel = bool(re.search(r'fbq\([\'"]init[\'"]', html))

        # Limpeza de texto para envio à IA (remove scripts, styles e tags html)
        cleaned_html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.I | re.S)
        cleaned_html = re.sub(r'<style[^>]*>.*?</style>', ' ', cleaned_html, flags=re.I | re.S)
        text_content = re.sub(r'<[^>]+>', ' ', cleaned_html)
        text_content = re.sub(r'\s+', ' ', text_content).strip()[:7000]

        return {
            "url": clean_url,
            "title": title,
            "description": description,
            "h1s": h1s[:5],
            "h2s": h2s[:10],
            "wa_links": list(set(wa_links)),
            "detected_phones": list(set(phones))[:5],
            "detected_emails": list(set(emails))[:5],
            "detected_tags": {
                "gtm": detected_gtm,
                "ga4": detected_ga4,
                "google_ads": detected_ads,
                "meta_pixel": has_meta_pixel
            },
            "clean_text_sample": text_content
        }
