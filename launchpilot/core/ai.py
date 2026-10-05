import os
import json
import time
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List, Optional

class AIEngine:
    """
    Motor de Inteligencia Artificial para LaunchPilot powered by Google Gemini.
    Responsavel por analise profunda de sites existentes, espionagem de concorrentes,
    auditoria de conversao e geracao de campanhas validadas para Google Ads.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            self.api_key = line.strip().split("=", 1)[1]
                            break
        
        self.models_priority = [
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-3.1-flash-lite",
            "gemini-2.5-pro"
        ]

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY nao encontrada. Configure no arquivo .env ou passe como parametro.")

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        last_error = None
        for model in self.models_priority:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            for attempt in range(2):
                try:
                    with urllib.request.urlopen(req, timeout=40) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return text
                except urllib.error.HTTPError as e:
                    last_error = e
                    if e.code in (503, 429):
                        time.sleep(2 * (attempt + 1))
                        continue
                    if e.code == 404:
                        break
                    raise
                except Exception as e:
                    last_error = e
                    time.sleep(1)
                    continue

        raise RuntimeError(f"Falha ao gerar conteudo com Gemini nos modelos disponiveis: {last_error}")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        cleaned = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Resposta do Gemini nao pode ser convertida para JSON: {text[:200]}...")

    def analyze_existing_site(self, site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lê e audita os dados reais de um site existente e extrai:
        - Nome do negócio, nicho e público-alvo
        - As 3 a 4 verticais específicas de serviços oferecidos
        - Diagnóstico de pontos fortes e gargalos de conversão
        - Estrutura completa de Google Ads (4 grupos segmentados, RSAs, palavras e negativas)
        """
        sample_text = site_data.get('clean_text_sample', '')[:3500]
        prompt = f"""
        Você é o Diretor Técnico de CRO e Google Ads da agência Adlovers.
        Foi fornecido o conteúdo raspado do site de um cliente:

        URL: {site_data.get('url')}
        Título: {site_data.get('title')}
        Meta Description: {site_data.get('description')}
        Títulos H1: {site_data.get('h1s')}
        Títulos H2: {site_data.get('h2s')}
        Texto do Site: \"{sample_text}\"

        Faça a auditoria e engenharia reversa completa deste site.
        Retorne ESTRITAMENTE um objeto JSON válido (sem tags markdown):
        {{
            "company_name": "Nome da empresa identificado no site",
            "niche": "Nicho exato de atuação",
            "region": "Região atendida (ex: Brasil Todo)",
            "core_offer": "Oferta principal identificada",
            "target_audience": "Perfil do cliente ideal",
            "detected_services": [
                {{
                    "title": "Serviço / Vertical 1",
                    "description": "Explicação do serviço detectado no site",
                    "target_pain": "Dor que este serviço resolve"
                }},
                {{
                    "title": "Serviço / Vertical 2",
                    "description": "Explicação",
                    "target_pain": "Dor"
                }},
                {{
                    "title": "Serviço / Vertical 3",
                    "description": "Explicação",
                    "target_pain": "Dor"
                }},
                {{
                    "title": "Serviço / Vertical 4",
                    "description": "Explicação",
                    "target_pain": "Dor"
                }}
            ],
            "conversion_audit": {{
                "strengths": [
                    "Ponto forte 1 identificado na página",
                    "Ponto forte 2"
                ],
                "bottlenecks": [
                    "Gargalo 1",
                    "Gargalo 2"
                ],
                "recommendations": [
                    "Recomendação 1 para aumentar conversão",
                    "Recomendação 2"
                ]
            }},
            "google_ads": {{
                "ad_groups": [
                    {{
                        "name": "G1: Principal / Oferta Central",
                        "headlines": ["15 títulos com max 30 caracteres cada"],
                        "descriptions": ["4 descrições com max 90 caracteres cada"],
                        "keywords": ["[termo exato 1]", "\"termo de frase 1\"", "\"termo de frase 2\""]
                    }},
                    {{
                        "name": "G2: Serviço 1",
                        "headlines": ["15 títulos com max 30 carac"],
                        "descriptions": ["4 descrições com max 90 carac"],
                        "keywords": ["[termo exato]", "\"termo de frase\""]
                    }},
                    {{
                        "name": "G3: Serviço 2",
                        "headlines": ["15 títulos com max 30 carac"],
                        "descriptions": ["4 descrições com max 90 carac"],
                        "keywords": ["[termo exato]", "\"termo de frase\""]
                    }},
                    {{
                        "name": "G4: Serviço 3",
                        "headlines": ["15 títulos com max 30 carac"],
                        "descriptions": ["4 descrições com max 90 carac"],
                        "keywords": ["[termo exato]", "\"termo de frase\""]
                    }}
                ],
                "negative_keywords": [
                    "gratis", "de graca", "curso", "salario", "vagas", "o que e", "pdf",
                    "significado", "trabalhe conosco", "concurso", "download", "faculdade",
                    "apostila", "login", "reclame aqui", "telefone 0800", "tutorial"
                ]
            }}
        }}
        """
        res_text = self.generate(prompt)
        return self._extract_json(res_text)

    def analyze_competitors(self, niche: str, client_name: str, region: str = "Brasil") -> Dict[str, Any]:
        prompt = f"""
        Atue como Especialista Senior em Inteligencia de Trafego Pago e Google Ads.
        Cliente: "{client_name}"
        Nicho de Atuacao: "{niche}"
        Regiao: "{region}"

        Pesquise concorrentes reais e atuantes no Google Ads no Brasil para este nicho.
        Retorne ESTRITAMENTE um objeto JSON valido:
        {{
            "niche_summary": "Resumo competitivo, CPC estimado e maturidade do mercado",
            "competitors": [
                {{
                    "name": "Concorrente 1",
                    "domain": "concorrente1.com.br",
                    "primary_focus": "Foco da oferta no Ads",
                    "approach": "Modelo comercial e promessas",
                    "weaknesses": "Ponto fraco exploravel"
                }},
                {{
                    "name": "Concorrente 2",
                    "domain": "concorrente2.com.br",
                    "primary_focus": "...",
                    "approach": "...",
                    "weaknesses": "..."
                }},
                {{
                    "name": "Concorrente 3",
                    "domain": "concorrente3.com.br",
                    "primary_focus": "...",
                    "approach": "...",
                    "weaknesses": "..."
                }}
            ],
            "market_gaps": [
                {{"title": "1. Brecha de Mercado 1", "description": "Explicacao de como explorar"}},
                {{"title": "2. Brecha de Mercado 2", "description": "Explicacao"}},
                {{"title": "3. Brecha de Mercado 3", "description": "Explicacao"}}
            ],
            "whatsapp_triage_questions": [
                "Pergunta de triagem 1 para WhatsApp",
                "Pergunta de triagem 2",
                "Pergunta de triagem 3"
            ]
        }}
        """
        res_text = self.generate(prompt)
        return self._extract_json(res_text)
