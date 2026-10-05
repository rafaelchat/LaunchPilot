import os
from typing import Dict, Any

class TagInstaller:
    """
    Gerador do Kit de Instalação de Tags e Telemetria para Sites Existentes.
    Fornece os códigos exatos de GTM e o script universal de deduplicação por orderId
    para colar no site atual do cliente (WordPress, Webflow, Wix, HTML, etc.).
    """
    def __init__(self):
        pass

    def generate_gtm_head(self, gtm_id: str) -> str:
        return f"""<!-- Google Tag Manager (LaunchPilot via agenciaadlovers) -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{gtm_id}');</script>
<!-- End Google Tag Manager -->"""

    def generate_gtm_body(self, gtm_id: str) -> str:
        return f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gtm_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""

    def generate_universal_tracking_script(self) -> str:
        return """<!-- LaunchPilot Universal Telemetry & orderId Deduplication -->
<script>
(function() {
  // Gerador de Lead ID exclusivo para deduplicação no Google Ads e GA4
  function getOrCreateOrderId() {
    var id = sessionStorage.getItem('lead_order_id');
    if (!id) {
      id = 'LEAD_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8).toUpperCase();
      sessionStorage.setItem('lead_order_id', id);
    }
    return id;
  }

  // Intercepta automaticamente cliques em links de WhatsApp, formulários e botões de conversão
  document.addEventListener('click', function(e) {
    var target = e.target.closest('a[href*="wa.me"], a[href*="api.whatsapp.com"], a[href*="whatsapp"], .track-btn, button[type="submit"], input[type="submit"]');
    if (target) {
      var orderId = getOrCreateOrderId();
      var btnText = (target.innerText || target.value || target.getAttribute('aria-label') || 'whatsapp_lead').trim().substring(0, 50);
      var clickUrl = target.href || '';

      if (window.dataLayer) {
        window.dataLayer.push({
          'event': 'whatsapp_conversion',
          'event_category': 'lead',
          'orderId': orderId,
          'btn_name': btnText,
          'click_url': clickUrl,
          'page_path': window.location.pathname,
          'timestamp': new Date().toISOString()
        });
      }
    }
  }, true);
})();
</script>"""

    def generate_guide_markdown(self, gtm_id: str, client_name: str, site_url: str) -> str:
        head_snippet = self.generate_gtm_head(gtm_id)
        body_snippet = self.generate_gtm_body(gtm_id)
        universal_script = self.generate_universal_tracking_script()

        return f"""# Guia de Instalação de Tags — {client_name}
**Site:** `{site_url}`  
**Contêiner GTM Criado:** `{gtm_id}`  
**Gerenciado por:** `agenciaadlovers@gmail.com`  

Para ativar o rastreamento oficial de conversões do Google Ads e GA4 no seu site existente, siga os 3 passos simples abaixo:

---

### Passo 1: Inserir no `<head>` do Site
Cole o código abaixo o mais alto possível dentro da tag `<head>` de todas as páginas:

```html
{head_snippet}
```

---

### Passo 2: Inserir logo após o `<body>`
Cole o código abaixo imediatamente após a abertura da tag `<body>`:

```html
{body_snippet}
```

---

### Passo 3: Ativar a Deduplicação de Conversões no WhatsApp
Cole este script logo antes do fechamento do `</body>`. Ele rastreará automaticamente todos os cliques nos seus botões de WhatsApp e impedirá conversões duplicadas no Google Ads:

```html
{universal_script}
```
"""
