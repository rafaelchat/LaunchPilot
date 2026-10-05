import os
import re
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional

class SiteBuilder:
    """
    Motor de Geracao de Sites Multi-Paginas de Alta Conversao para LaunchPilot.
    Compila:
    - Pagina Inicial (Home)
    - 3 Paginas Dedicadas de Verticais / Servicos Especificos
    - Arquivo sitemap.xml e robots.txt
    - JSON-LD Schemas (ProfessionalService + FAQPage + Breadcrumbs)
    - Telemetria de 19+ botoes com data-attributes granulares
    - Script de deduplicacao de conversoes por orderId para Google Ads e GA4
    """
    def __init__(self):
        pass

    def build_multi_page(self, kit: Dict[str, Any], config: Dict[str, Any], gtm_public_id: Optional[str] = None) -> Dict[str, str]:
        biz = config.get("business", {})
        client = config.get("client", {})
        domain = config.get("deploy", {}).get("domain", "https://meusite.com.br").rstrip("/")
        
        home_data = kit.get("home", {})
        verticals_data = kit.get("verticals", [])
        
        phone = biz.get("whatsapp_number", "").replace("+", "").replace("-", "").replace(" ", "")
        
        # 1. Compila Home
        home_html = self._render_home(home_data, verticals_data, biz, phone, domain, gtm_public_id)
        
        # 2. Compila Verticais
        vertical_pages = {}
        for v in verticals_data:
            v_slug = v.get("slug", "servico")
            v_html = self._render_vertical(v, home_data, biz, phone, domain, gtm_public_id)
            vertical_pages[v_slug] = v_html

        # 3. Compila Sitemap e Robots
        sitemap_xml = self._render_sitemap(domain, verticals_data)
        robots_txt = f"User-agent: *\nAllow: /\n\nSitemap: {domain}/sitemap.xml\n"
        vercel_json = '{\n  "cleanUrls": true,\n  "trailingSlash": false\n}\n'

        return {
            "index.html": home_html,
            "verticals": vertical_pages,
            "sitemap.xml": sitemap_xml,
            "robots.txt": robots_txt,
            "vercel.json": vercel_json
        }

    def export_dist(self, kit: Dict[str, Any], config: Dict[str, Any], dist_dir: str, gtm_public_id: Optional[str] = None):
        os.makedirs(dist_dir, exist_ok=True)
        servicos_dir = os.path.join(dist_dir, "servicos")
        os.makedirs(servicos_dir, exist_ok=True)

        pages = self.build_multi_page(kit, config, gtm_public_id)

        # Salvar Home
        with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(pages["index.html"])

        # Salvar Verticais
        for slug, html in pages["verticals"].items():
            with open(os.path.join(servicos_dir, f"{slug}.html"), "w", encoding="utf-8") as f:
                f.write(html)

        # Salvar Sitemap e Robots
        with open(os.path.join(dist_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(pages["sitemap.xml"])

        with open(os.path.join(dist_dir, "robots.txt"), "w", encoding="utf-8") as f:
            f.write(pages["robots.txt"])

        with open(os.path.join(dist_dir, "vercel.json"), "w", encoding="utf-8") as f:
            f.write(pages["vercel.json"])

    def _render_gtm_snippets(self, gtm_public_id: Optional[str]):
        if not gtm_public_id:
            return "", ""
        head = f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{gtm_public_id}');</script>
<!-- End Google Tag Manager -->"""

        body = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gtm_public_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""
        return head, body

    def _render_shared_css(self, primary_color: str = "#0f172a", accent_color: str = "#2563eb"):
        return f"""
    :root {{
      --primary: {primary_color};
      --accent: {accent_color};
      --accent-hover: #1d4ed8;
      --bg: #090d16;
      --card-bg: rgba(255, 255, 255, 0.03);
      --card-border: rgba(255, 255, 255, 0.08);
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; }}
    body {{ background-color: var(--bg); color: var(--text); line-height: 1.6; overflow-x: hidden; }}
    .container {{ max-width: 1180px; margin: 0 auto; padding: 0 24px; }}
    
    /* Top Bar */
    .top-bar {{ background: linear-gradient(90deg, #1e1b4b, #312e81); padding: 8px 16px; text-align: center; font-size: 13px; font-weight: 600; color: #c7d2fe; }}
    
    /* Header */
    header {{ padding: 18px 0; border-bottom: 1px solid var(--card-border); backdrop-filter: blur(16px); position: sticky; top: 0; z-index: 50; background: rgba(9, 13, 22, 0.85); }}
    .nav-wrap {{ display: flex; justify-content: space-between; align-items: center; }}
    .logo {{ font-size: 20px; font-weight: 800; color: #fff; text-decoration: none; display: flex; align-items: center; gap: 8px; }}
    .logo-badge {{ background: var(--accent); color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 99px; text-transform: uppercase; font-weight: 700; }}
    .nav-links {{ display: flex; gap: 20px; align-items: center; }}
    .nav-links a {{ color: var(--text-muted); text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; }}
    .nav-links a:hover {{ color: #fff; }}

    /* Buttons */
    .btn {{ display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 14px 28px; border-radius: 12px; font-weight: 700; text-decoration: none; transition: all 0.25s ease; cursor: pointer; border: none; font-size: 15px; }}
    .btn-primary {{ background: var(--accent); color: #fff; box-shadow: 0 8px 24px -4px rgba(37, 99, 235, 0.4); }}
    .btn-primary:hover {{ background: var(--accent-hover); transform: translateY(-2px); box-shadow: 0 12px 28px -4px rgba(37, 99, 235, 0.6); }}
    .btn-pulse {{ animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.6); }} 70% {{ box-shadow: 0 0 0 14px rgba(37, 99, 235, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }} }}

    /* Trust Badge */
    .trust-badge-wrap {{ display: inline-flex; align-items: center; gap: 10px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: #86efac; padding: 6px 18px; border-radius: 99px; font-size: 13px; font-weight: 600; margin-bottom: 24px; }}
    .pulse-dot {{ width: 8px; height: 8px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 8px #22c55e; animation: pulse-green 1.5s infinite; }}
    @keyframes pulse-green {{ 0% {{ transform: scale(0.95); opacity: 0.8; }} 50% {{ transform: scale(1.2); opacity: 1; }} 100% {{ transform: scale(0.95); opacity: 0.8; }} }}

    /* Hero Section */
    .hero {{ padding: 70px 0 50px; text-align: center; position: relative; }}
    .hero h1 {{ font-size: 46px; font-weight: 800; line-height: 1.15; max-width: 860px; margin: 0 auto 20px; letter-spacing: -1.2px; }}
    .hero h1 span {{ background: linear-gradient(135deg, #60a5fa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .hero p {{ font-size: 18px; color: var(--text-muted); max-width: 660px; margin: 0 auto 34px; }}

    /* Viability Banner */
    .viability-banner {{ background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(15, 23, 42, 0.6)); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 20px; padding: 32px; margin: 40px auto; max-width: 900px; text-align: center; }}
    .viability-banner h3 {{ font-size: 22px; color: #fff; margin-bottom: 8px; font-weight: 800; }}
    .viability-banner p {{ font-size: 15px; color: #cbd5e1; max-width: 600px; margin: 0 auto 20px; }}

    /* Cards Grid */
    .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin: 40px 0; }}
    .card {{ background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 18px; padding: 28px; text-align: left; transition: all 0.25s ease; position: relative; overflow: hidden; }}
    .card:hover {{ border-color: rgba(59, 130, 246, 0.4); transform: translateY(-4px); }}
    .card h3 {{ font-size: 19px; color: #fff; margin-bottom: 10px; font-weight: 700; }}
    .card p {{ font-size: 14px; color: var(--text-muted); margin-bottom: 18px; }}

    /* Stats Section */
    .stats-wrap {{ display: flex; justify-content: space-around; flex-wrap: wrap; gap: 24px; margin: 60px 0; padding: 30px; background: rgba(255,255,255,0.02); border-radius: 18px; border: 1px solid var(--card-border); }}
    .stat-item {{ text-align: center; }}
    .stat-number {{ font-size: 38px; font-weight: 800; color: #38bdf8; }}
    .stat-label {{ font-size: 13px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }}

    /* FAQ */
    .faq-section {{ max-width: 800px; margin: 60px auto; text-align: left; }}
    .faq-section h2 {{ font-size: 30px; text-align: center; margin-bottom: 30px; color: #fff; font-weight: 800; }}
    details {{ background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; margin-bottom: 14px; padding: 18px 22px; cursor: pointer; transition: all 0.2s; }}
    details summary {{ font-weight: 700; font-size: 16px; color: #fff; list-style: none; display: flex; justify-content: space-between; align-items: center; }}
    details summary::-webkit-details-marker {{ display: none; }}
    details summary::after {{ content: '+'; font-size: 20px; color: var(--accent); }}
    details[open] summary::after {{ content: '−'; }}
    details p {{ margin-top: 14px; font-size: 14.5px; color: var(--text-muted); line-height: 1.6; }}

    /* Floating WhatsApp */
    .float-wa {{ position: fixed; bottom: 24px; right: 24px; width: 62px; height: 62px; background: #22c55e; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 25px rgba(34, 197, 94, 0.4); z-index: 100; text-decoration: none; animation: pulse-green 2s infinite; }}
    
    /* Footer */
    footer {{ padding: 50px 0; border-top: 1px solid var(--card-border); margin-top: 80px; text-align: center; color: var(--text-muted); font-size: 14px; }}

    @media (max-width: 768px) {{
      .hero h1 {{ font-size: 32px; }}
      .hero p {{ font-size: 16px; }}
      .nav-links {{ display: none; }}
    }}
        """

    def _render_tracking_script(self):
        return """
  <script>
    // Gerador de Lead Order ID exclusivo para deduplicação no Google Ads e GA4
    function getOrCreateOrderId() {
      var id = sessionStorage.getItem('lead_order_id');
      if (!id) {
        id = 'LEAD_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8).toUpperCase();
        sessionStorage.setItem('lead_order_id', id);
      }
      return id;
    }

    // Escuta cliques em todos os botões rastreáveis
    document.querySelectorAll('[data-btn-event="whatsapp_conversion"]').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        var orderId = getOrCreateOrderId();
        var btnName = btn.getAttribute('data-btn-name') || 'whatsapp_lead_click';
        var placement = btn.getAttribute('data-placement') || 'unknown';
        var page = btn.getAttribute('data-page') || window.location.pathname;

        if (window.dataLayer) {
          window.dataLayer.push({
            'event': 'whatsapp_conversion',
            'event_category': 'lead',
            'orderId': orderId,
            'btn_name': btnName,
            'btn_placement': placement,
            'page_path': page,
            'timestamp': new Date().toISOString()
          });
        }
      });
    });
  </script>
        """

    def _render_home(self, home_data: Dict[str, Any], verticals: List[Dict[str, Any]], biz: Dict[str, Any], phone: str, domain: str, gtm_id: Optional[str]) -> str:
        gtm_head, gtm_body = self._render_gtm_snippets(gtm_id)
        css = self._render_shared_css(biz.get("theme", {}).get("primary_color", "#0f172a"), biz.get("theme", {}).get("accent_color", "#2563eb"))
        tracking_script = self._render_tracking_script()

        c_name = biz.get("company_name", "Empresa")
        default_msg = urllib.parse.quote(home_data.get("whatsapp_message", "Olá! Gostaria de uma avaliação inicial."))
        default_wa_url = f"https://wa.me/{phone}?text={default_msg}"

        # Verticals HTML
        vertical_cards_html = ""
        for i, v in enumerate(verticals, 1):
            v_slug = v.get("slug", f"servico-{i}")
            v_url = f"/servicos/{v_slug}.html"
            v_msg = urllib.parse.quote(v.get("whatsapp_message", f"Olá! Preciso de atendimento sobre {v.get('title')}."))
            wa_v_url = f"https://wa.me/{phone}?text={v_msg}"
            
            vertical_cards_html += f"""
            <div class="card">
              <h3>{v.get('title', 'Serviço Especializado')}</h3>
              <p>{v.get('pain_point', 'Atendimento com estratégia e segurança.')}</p>
              <div style="display: flex; gap: 12px; align-items: center; margin-top: 16px;">
                <a href="{wa_v_url}" class="btn btn-primary" data-btn-name="card_vertical_{i}_wa" data-btn-event="whatsapp_conversion" data-page="home" data-placement="verticals" style="padding: 10px 18px; font-size: 13px;">
                  Avaliar Este Caso
                </a>
                <a href="{v_url}" style="color: #60a5fa; font-size: 13px; text-decoration: none; font-weight: 600;">
                  Saiba mais →
                </a>
              </div>
            </div>
            """

        # Trust Cards HTML
        trust_cards_html = ""
        for i, tc in enumerate(home_data.get("trust_cards", []), 1):
            trust_cards_html += f"""
            <div class="card">
              <div style="font-size: 28px; margin-bottom: 12px;">{tc.get('icon', '⚡')}</div>
              <h3>{tc.get('title', '')}</h3>
              <p>{tc.get('description', '')}</p>
            </div>
            """

        # Stats HTML
        stats_html = ""
        for s in home_data.get("stats", []):
            stats_html += f"""
            <div class="stat-item">
              <div class="stat-number">{s.get('number', '')}</div>
              <div class="stat-label">{s.get('label', '')}</div>
            </div>
            """

        # FAQ HTML
        faq_html = ""
        faq_schema_items = []
        for f in home_data.get("faq", []):
            faq_html += f"""
            <details>
              <summary>{f.get('question', '')}</summary>
              <p>{f.get('answer', '')}</p>
            </details>
            """
            faq_schema_items.append({
                "@type": "Question",
                "name": f.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f.get("answer", "")
                }
            })

        faq_schema_json = re.sub(r'[\r\n]+', ' ', str(faq_schema_items).replace("'", '"'))

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{home_data.get('page_title', f"{c_name} | Atendimento Especializado")}</title>
  <meta name="description" content="{home_data.get('meta_description', '')}">
  <link rel="canonical" href="{domain}/">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

  {gtm_head}

  <style>
  {css}
  </style>

  <!-- Schemas JSON-LD -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    "name": "{c_name}",
    "url": "{domain}",
    "telephone": "{biz.get('whatsapp_number', '')}",
    "priceRange": "$$",
    "areaServed": "BR"
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": {faq_schema_json}
  }}
  </script>
</head>
<body>
  {gtm_body}

  <div class="top-bar">
    ⚡ Atendimento Especializado com Medidas Ágeis em Todo o Brasil
  </div>

  <header>
    <div class="container nav-wrap">
      <a href="/" class="logo">
        {c_name}
        <span class="logo-badge">Oficial</span>
      </a>
      <div class="nav-links">
        <a href="#servicos">Especialidades</a>
        <a href="#como-funciona">Como Funciona</a>
        <a href="#faq">Perguntas Frequentes</a>
      </div>
      <a href="{default_wa_url}" class="btn btn-primary" data-btn-name="header_nav_cta" data-btn-event="whatsapp_conversion" data-page="home" data-placement="header">
        Falar com Especialista
      </a>
    </div>
  </header>

  <main>
    <section class="hero container">
      <div class="trust-badge-wrap">
        <span class="pulse-dot"></span>
        {home_data.get('badge_text', 'Atendimento Humano · Brasil Todo · Experiência Comprovada')}
      </div>
      
      <h1>{home_data.get('headline_first', 'Atendimento Especializado')} <span>{home_data.get('headline_highlight', '')}</span></h1>
      <p>{home_data.get('subheadline', '')}</p>
      
      <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
        <a href="{default_wa_url}" class="btn btn-primary btn-pulse" data-btn-name="hero_primary_cta" data-btn-event="whatsapp_conversion" data-page="home" data-placement="hero" style="font-size: 17px; padding: 18px 36px;">
          {home_data.get('cta_primary', 'Avaliar Meu Caso Agora')}
        </a>
      </div>

      <!-- Banner de Análise Rápida de Viabilidade -->
      <div class="viability-banner">
        <h3>🔍 {home_data.get('viability_banner', {}).get('title', 'Análise Rápida de Viabilidade')}</h3>
        <p>{home_data.get('viability_banner', {}).get('subtitle', 'Receba um diagnóstico preliminar do seu caso em poucos minutos diretamente no WhatsApp.')}</p>
        <a href="{default_wa_url}" class="btn btn-primary" data-btn-name="viability_banner_cta" data-btn-event="whatsapp_conversion" data-page="home" data-placement="viability_banner">
          Iniciar Análise sem Compromisso
        </a>
      </div>

      <!-- Grid de Verticais de Serviços -->
      <div id="servicos" style="margin-top: 60px; text-align: left;">
        <h2 style="font-size: 30px; color: #fff; font-weight: 800; margin-bottom: 12px; text-align: center;">Áreas de Atuação Especializada</h2>
        <p style="text-align: center; color: var(--text-muted); margin-bottom: 30px;">Selecione o seu caso para atendimento direcionado</p>
        <div class="grid-3">
          {vertical_cards_html}
        </div>
      </div>

      <!-- Números e Prova Técnica -->
      <div class="stats-wrap">
        {stats_html}
      </div>

      <!-- Diferenciais -->
      <div style="margin-top: 60px;">
        <h2 style="font-size: 30px; color: #fff; font-weight: 800; margin-bottom: 24px;">Por Que Escolher Nossa Equipe</h2>
        <div class="grid-3">
          {trust_cards_html}
        </div>
      </div>

      <!-- FAQ Transparente -->
      <div id="faq" class="faq-section">
        <h2>Perguntas Frequentes & Transparência</h2>
        {faq_html}
        <div style="text-align: center; margin-top: 32px;">
          <a href="{default_wa_url}" class="btn btn-primary" data-btn-name="faq_bottom_cta" data-btn-event="whatsapp_conversion" data-page="home" data-placement="faq">
            Ainda com dúvidas? Falar no WhatsApp
          </a>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <p>© {datetime.now().year} {c_name} — Todos os direitos reservados.</p>
      <p style="font-size: 12px; margin-top: 6px;">Plataforma desenvolvida com alta performance LaunchPilot.</p>
    </div>
  </footer>

  <!-- Botão Flutuante de WhatsApp -->
  <a href="{default_wa_url}" class="float-wa" data-btn-name="floating_whatsapp" data-btn-event="whatsapp_conversion" data-page="home" data-placement="floating" title="Conversar no WhatsApp">
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
    </svg>
  </a>

  {tracking_script}
</body>
</html>"""

    def _render_vertical(self, vertical: Dict[str, Any], home_data: Dict[str, Any], biz: Dict[str, Any], phone: str, domain: str, gtm_id: Optional[str]) -> str:
        gtm_head, gtm_body = self._render_gtm_snippets(gtm_id)
        css = self._render_shared_css(biz.get("theme", {}).get("primary_color", "#0f172a"), biz.get("theme", {}).get("accent_color", "#2563eb"))
        tracking_script = self._render_tracking_script()

        c_name = biz.get("company_name", "Empresa")
        v_slug = vertical.get("slug", "servico")
        page_url = f"{domain}/servicos/{v_slug}.html"
        
        msg = urllib.parse.quote(vertical.get("whatsapp_message", f"Olá! Preciso de avaliação para {vertical.get('title')}."))
        wa_url = f"https://wa.me/{phone}?text={msg}"

        cards_html = ""
        for c in vertical.get("cards", []):
            cards_html += f"""
            <div class="card">
              <h3>{c.get('title', '')}</h3>
              <p>{c.get('description', '')}</p>
            </div>
            """

        faq_html = ""
        faq_schema_items = []
        for f in vertical.get("faq", []):
            faq_html += f"""
            <details>
              <summary>{f.get('question', '')}</summary>
              <p>{f.get('answer', '')}</p>
            </details>
            """
            faq_schema_items.append({
                "@type": "Question",
                "name": f.get("question", ""),
                "acceptedAnswer": {"@type": "Answer", "text": f.get("answer", "")}
            })

        faq_schema_json = re.sub(r'[\r\n]+', ' ', str(faq_schema_items).replace("'", '"'))

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{vertical.get('page_title', f"{vertical.get('title')} | {c_name}")}</title>
  <meta name="description" content="{vertical.get('meta_description', '')}">
  <link rel="canonical" href="{page_url}">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

  {gtm_head}

  <style>
  {css}
  </style>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Início", "item": "{domain}/" }},
      {{ "@type": "ListItem", "position": 2, "name": "{vertical.get('title')}", "item": "{page_url}" }}
    ]
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": {faq_schema_json}
  }}
  </script>
</head>
<body>
  {gtm_body}

  <div class="top-bar">
    ⚡ Atendimento Direcionado: {vertical.get('title')}
  </div>

  <header>
    <div class="container nav-wrap">
      <a href="/" class="logo">
        {c_name}
        <span class="logo-badge">Especializado</span>
      </a>
      <div class="nav-links">
        <a href="/">← Voltar ao Início</a>
        <a href="#etapas">Etapas</a>
        <a href="#faq">Dúvidas</a>
      </div>
      <a href="{wa_url}" class="btn btn-primary" data-btn-name="vertical_nav_cta" data-btn-event="whatsapp_conversion" data-page="{v_slug}" data-placement="header">
        Falar com Especialista
      </a>
    </div>
  </header>

  <main>
    <section class="hero container">
      <div class="trust-badge-wrap">
        <span class="pulse-dot"></span>
        {home_data.get('badge_text', 'Atendimento Especializado em Todo o Brasil')}
      </div>
      
      <h1>{vertical.get('headline', vertical.get('title'))}</h1>
      <p>{vertical.get('subheadline', '')}</p>
      
      <div style="display: flex; justify-content: center; gap: 16px;">
        <a href="{wa_url}" class="btn btn-primary btn-pulse" data-btn-name="vertical_hero_primary_cta" data-btn-event="whatsapp_conversion" data-page="{v_slug}" data-placement="hero" style="font-size: 17px; padding: 18px 36px;">
          Avaliar Meu Caso Agora
        </a>
      </div>

      <div id="etapas" style="margin-top: 60px;">
        <h2 style="font-size: 28px; color: #fff; font-weight: 800; margin-bottom: 24px;">Como Atuamos Nesta Situação</h2>
        <div class="grid-3">
          {cards_html}
        </div>
      </div>

      <div id="faq" class="faq-section">
        <h2>Perguntas Específicas</h2>
        {faq_html}
        <div style="text-align: center; margin-top: 32px;">
          <a href="{wa_url}" class="btn btn-primary" data-btn-name="vertical_faq_cta" data-btn-event="whatsapp_conversion" data-page="{v_slug}" data-placement="faq">
            Falar Diretamente no WhatsApp
          </a>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <p>© {datetime.now().year} {c_name} — Todos os direitos reservados.</p>
    </div>
  </footer>

  <a href="{wa_url}" class="float-wa" data-btn-name="vertical_floating_whatsapp" data-btn-event="whatsapp_conversion" data-page="{v_slug}" data-placement="floating" title="Conversar no WhatsApp">
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
    </svg>
  </a>

  {tracking_script}
</body>
</html>"""

    def _render_sitemap(self, domain: str, verticals: List[Dict[str, Any]]) -> str:
        date_today = datetime.now().strftime("%Y-%m-%d")
        urls = [
            f"""  <url>
    <loc>{domain}/</loc>
    <lastmod>{date_today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""
        ]

        for v in verticals:
            slug = v.get("slug", "servico")
            urls.append(f"""  <url>
    <loc>{domain}/servicos/{slug}.html</loc>
    <lastmod>{date_today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

        body = "\n".join(urls)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>"""
