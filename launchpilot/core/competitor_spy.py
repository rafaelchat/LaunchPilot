import os
import sys
import json
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
from launchpilot.core.ai import AIEngine

try:
    from xhtml2pdf import pisa
    HAS_PISA = True
except ImportError:
    HAS_PISA = False

class CompetitorSpy:
    """
    Modulo de Inteligencia de Concorrencia e Mercado.
    Analisa os principais players no Google Ads para qualquer nicho,
    identifica brechas de mercado e gera dossie executivo em Markdown e PDF.
    """
    def __init__(self, ai_engine: Optional[AIEngine] = None):
        self.ai = ai_engine or AIEngine()

    def build_transparency_url(self, domain: str) -> str:
        clean_domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()
        encoded = urllib.parse.quote(clean_domain)
        return f"https://adstransparency.google.com/?region=BR&domain={encoded}"

    def run_spy(self, niche: str, client_name: str, region: str = "Brasil", output_dir: str = "output") -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)
        slug = client_name.lower().replace(" ", "_").replace("&", "e")
        slug = "".join(c for c in slug if c.isalnum() or c == "_")

        # 1. Pesquisa e Engenharia Reversa via Gemini
        print(f"[*] Analisando concorrentes no Google Ads para o nicho '{niche}' ({region})...")
        intel = self.ai.analyze_competitors(niche=niche, client_name=client_name, region=region)

        # Enriquecer concorrentes com links do Ads Transparency
        competitors = intel.get("competitors", [])
        for c in competitors:
            c["transparency_url"] = self.build_transparency_url(c.get("domain", ""))

        # 2. Gerar Dossie em Markdown
        md_path = os.path.join(output_dir, f"dossie_concorrentes_{slug}.md")
        self._generate_markdown(intel, client_name, niche, region, md_path)
        print(f"✓ Dossiê Markdown gerado em: {md_path}")

        # 3. Gerar Dossie em PDF Executivo
        pdf_path = os.path.join(output_dir, f"dossie_concorrentes_{slug}.pdf")
        if HAS_PISA:
            try:
                self._generate_pdf(intel, client_name, niche, region, pdf_path)
                print(f"✓ Dossiê Executivo em PDF gerado em: {pdf_path}")
            except Exception as e:
                print(f"⚠️ Erro ao compilar PDF: {e}")
                pdf_path = None
        else:
            print("⚠️ xhtml2pdf não instalado, PDF não gerado.")
            pdf_path = None

        return {
            "intelligence": intel,
            "markdown_path": md_path,
            "pdf_path": pdf_path
        }

    def _generate_markdown(self, data: Dict[str, Any], client_name: str, niche: str, region: str, file_path: str):
        date_str = datetime.now().strftime("%d/%m/%Y")
        lines = [
            f"# Dossiê de Inteligência & Espionagem Competitiva",
            f"**Cliente:** {client_name}  ",
            f"**Nicho:** {niche}  ",
            f"**Praça:** {region}  ",
            f"**Data da Auditoria:** {date_str}  \n",
            f"## 1. Visão Geral do Cenário Competitivo",
            f"{data.get('niche_summary', '')}\n",
            f"## 2. Matriz dos Principais Concorrentes Ativos no Google Ads\n",
            f"| # | Empresa / Concorrente | Domínio | Foco da Oferta | Abordagem Comercial | Ads Transparency |",
            f"|---|---|---|---|---|---|"
        ]

        for i, c in enumerate(data.get("competitors", []), 1):
            name = c.get("name", "")
            domain = c.get("domain", "")
            focus = c.get("primary_focus", "")
            approach = c.get("approach", "")
            t_url = c.get("transparency_url", "")
            lines.append(f"| {i} | **{name}** | `{domain}` | {focus} | {approach} | [Ver Anúncios]({t_url}) |")

        lines.extend([
            f"\n## 3. As Maiores Brechas e Oportunidades de Mercado Identificadas\n"
        ])
        for gap in data.get("market_gaps", []):
            lines.append(f"### {gap.get('title', '')}")
            lines.append(f"{gap.get('description', '')}\n")

        lines.extend([
            f"## 4. Estrutura Tática de Verticais Recomendadas para o Site\n"
        ])
        for v in data.get("verticals", []):
            lines.append(f"- **{v.get('title', '')}** (Rota: `/servicos/{v.get('slug', '')}.html`)")
            lines.append(f"  * Dor do Lead: {v.get('pain_point', '')}")

        lines.extend([
            f"\n## 5. Script Rápido de Triagem e Qualificação no WhatsApp\n"
        ])
        for q in data.get("whatsapp_triage_questions", []):
            lines.append(f"1. *\"{q}\"*")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _generate_pdf(self, data: Dict[str, Any], client_name: str, niche: str, region: str, file_path: str):
        date_str = datetime.now().strftime("%d/%m/%Y")
        
        # HTML do relatório formatado para xhtml2pdf sem aninhamentos inválidos de CSS
        competitors_rows = ""
        for i, c in enumerate(data.get("competitors", []), 1):
            bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
            competitors_rows += f"""
            <tr style="background-color: {bg};">
                <td style="text-align: center; font-weight: bold; width: 5%;">{i}</td>
                <td style="font-weight: bold; width: 25%;">{c.get('name', '')}</td>
                <td style="width: 20%; color: #2563eb;">{c.get('domain', '')}</td>
                <td style="width: 25%;">{c.get('primary_focus', '')}</td>
                <td style="width: 25%;">{c.get('approach', '')}</td>
            </tr>
            """

        gaps_html = ""
        for gap in data.get("market_gaps", []):
            gaps_html += f"""
            <div class="card">
                <h3>{gap.get('title', '')}</h3>
                <p>{gap.get('description', '')}</p>
            </div>
            """

        triage_html = ""
        for q in data.get("whatsapp_triage_questions", []):
            triage_html += f"<li><i>\"{q}\"</i></li>"

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: a4 portrait;
        margin: 1.2cm 1.2cm 1.5cm 1.2cm;
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        color: #1e293b;
        line-height: 1.45;
        font-size: 10pt;
    }}
    .header {{
        border-bottom: 2px solid #2563eb;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }}
    h1 {{
        color: #0f172a;
        font-size: 20pt;
        margin: 0 0 4px 0;
        font-weight: bold;
    }}
    .meta-box {{
        background-color: #f1f5f9;
        border-left: 4px solid #2563eb;
        padding: 10px 14px;
        margin-bottom: 20px;
        font-size: 9.5pt;
    }}
    h2 {{
        color: #1e3a8a;
        font-size: 13pt;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 4px;
        margin-top: 18px;
        margin-bottom: 12px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 16px;
    }}
    th {{
        background-color: #0f172a;
        color: #ffffff;
        text-align: left;
        padding: 7px 8px;
        font-size: 8.5pt;
        font-weight: bold;
    }}
    td {{
        padding: 7px 8px;
        border-bottom: 1px solid #e2e8f0;
        font-size: 8.5pt;
    }}
    .card {{
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        padding: 10px 12px;
        margin-bottom: 10px;
    }}
    .card h3 {{
        margin: 0 0 4px 0;
        color: #1e40af;
        font-size: 10pt;
    }}
    .card p {{
        margin: 0;
        color: #334155;
        font-size: 9pt;
    }}
    .page-break {{
        page-break-before: always;
    }}
    .triage-box {{
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #16a34a;
        padding: 12px;
        margin-top: 15px;
    }}
    .triage-box h4 {{
        margin: 0 0 6px 0;
        color: #15803d;
        font-size: 10.5pt;
    }}
    .triage-box ul {{
        margin: 0;
        padding-left: 18px;
        font-size: 9pt;
        color: #166534;
    }}
</style>
</head>
<body>
    <div class="header">
        <h1>Dossiê de Espionagem & Inteligência Competitiva</h1>
        <div style="font-size: 11pt; color: #475569;">Estratégia Tática de Conversão e Tráfego Pago</div>
    </div>

    <div class="meta-box">
        <b>Cliente / Empresa:</b> {client_name} &nbsp;|&nbsp; 
        <b>Nicho:</b> {niche} &nbsp;|&nbsp; 
        <b>Praça:</b> {region} &nbsp;|&nbsp; 
        <b>Data:</b> {date_str}
    </div>

    <h2>1. Resumo do Cenário Competitivo</h2>
    <p style="font-size: 9.5pt; color: #334155;">{data.get('niche_summary', '')}</p>

    <h2>2. Matriz de Concorrentes Líderes no Google Ads</h2>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Concorrente</th>
                <th>Domínio</th>
                <th>Foco da Oferta</th>
                <th>Abordagem Comercial</th>
            </tr>
        </thead>
        <tbody>
            {competitors_rows}
        </tbody>
    </table>

    <div class="page-break"></div>

    <h2>3. Maiores Brechas e Oportunidades de Mercado</h2>
    {gaps_html}

    <h2>4. Script Rápido de Triagem Comercial no WhatsApp</h2>
    <div class="triage-box">
        <h4>Perguntas de Qualificação Imediata:</h4>
        <ul>
            {triage_html}
        </ul>
    </div>
</body>
</html>
"""
        with open(file_path, "wb") as pdf_file:
            pisa.CreatePDF(html_content, dest=pdf_file)
