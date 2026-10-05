import os
import json
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List, Optional

class AIEngine:
    """
    Motor de Inteligencia Artificial para LaunchPilot powered by Google Gemini.
    Responsavel por pesquisa de concorrencia, criacao de copy multi-paginas
    e geracao de campanhas validadas para Google Ads.
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
        
        # gemini-3.8-flash e o modelo atual de mais alta performance e velocidade
        self.models_priority = [
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-flash-latest"
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
            try:
                with urllib.request.urlopen(req, timeout=40) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code in (404, 503, 429):
                    continue
                raise
            except Exception as e:
                last_error = e
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

    def analyze_competitors(self, niche: str, client_name: str, region: str = "Brasil") -> Dict[str, Any]:
        """
        Realiza analise de mercado e espionagem competitiva para qualquer nicho.
        """
        prompt = f"""
        Atue como Especialista Senior em Inteligencia de Trafego Pago, Google Ads e Engenharia Reversa de Concorrentes.
        Cliente: "{client_name}"
        Nicho de Atuacao: "{niche}"
        Regiao / Praca Alvo: "{region}"

        Faca uma pesquisa aprofundada de concorrentes que anunciam no Google Ads neste nicho no Brasil.
        Identifique o padrao das ofertas, os diferenciais explorados, as fraquezas e as maiores brechas de mercado.

        Retorne ESTRITAMENTE um objeto JSON valido no seguinte formato exato (sem texto antes ou depois):
        {{
            "niche_summary": "Breve resumo do cenario competitivo e ticket medio do servico",
            "competitors": [
                {{
                    "name": "Nome do concorrente 1 (empresa/escritorio real ou arquetipo lider de leilao)",
                    "domain": "dominio.com.br",
                    "primary_focus": "Foco central da oferta no Google Ads",
                    "approach": "Como abordam o cliente (gatilhos, urgencia, garantias)",
                    "weaknesses": "Ponto fraco identificado (ex: formulario lento, sem preco claro, site poluido)"
                }},
                {{
                    "name": "Concorrente 2",
                    "domain": "dominio2.com.br",
                    "primary_focus": "Foco da oferta",
                    "approach": "Abordagem comercial",
                    "weaknesses": "Ponto fraco"
                }},
                {{
                    "name": "Concorrente 3",
                    "domain": "dominio3.com.br",
                    "primary_focus": "Foco da oferta",
                    "approach": "Abordagem comercial",
                    "weaknesses": "Ponto fraco"
                }},
                {{
                    "name": "Concorrente 4",
                    "domain": "dominio4.com.br",
                    "primary_focus": "Foco da oferta",
                    "approach": "Abordagem comercial",
                    "weaknesses": "Ponto fraco"
                }},
                {{
                    "name": "Concorrente 5",
                    "domain": "dominio5.com.br",
                    "primary_focus": "Foco da oferta",
                    "approach": "Abordagem comercial",
                    "weaknesses": "Ponto fraco"
                }}
            ],
            "market_gaps": [
                {{
                    "title": "1. Brecha / Oportunidade 1",
                    "description": "Explicacao detalhada de como explorar essa brecha no site e nos anuncios."
                }},
                {{
                    "title": "2. Brecha / Oportunidade 2",
                    "description": "Explicacao..."
                }},
                {{
                    "title": "3. Brecha / Oportunidade 3",
                    "description": "Explicacao..."
                }},
                {{
                    "title": "4. Brecha / Oportunidade 4",
                    "description": "Explicacao..."
                }}
            ],
            "verticals": [
                {{
                    "slug": "slug-da-vertical-1",
                    "title": "Nome do Servico / Sub-nicho 1",
                    "pain_point": "Principal dor deste cliente especifico"
                }},
                {{
                    "slug": "slug-da-vertical-2",
                    "title": "Nome do Servico / Sub-nicho 2",
                    "pain_point": "Principal dor deste cliente especifico"
                }},
                {{
                    "slug": "slug-da-vertical-3",
                    "title": "Nome do Servico / Sub-nicho 3",
                    "pain_point": "Principal dor deste cliente especifico"
                }}
            ],
            "negative_keywords": [
                "gratis", "de graca", "curso", "salario", "vagas", "o que e", "pdf",
                "significado", "trabalhe conosco", "concurso", "download", "faculdade",
                "apostila", "login", "reclame aqui", "telefone 0800", "tutorial"
            ],
            "whatsapp_triage_questions": [
                "Pergunta 1 para qualificar o lead imediatamente no WhatsApp",
                "Pergunta 2 sobre a gravidade/valor da demanda",
                "Pergunta 3 sobre prazo/urgencia"
            ]
        }}
        """
        res_text = self.generate(prompt)
        return self._extract_json(res_text)

    def generate_full_client_kit(self, niche: str, business_name: str, whatsapp: str, region: str = "Brasil") -> Dict[str, Any]:
        """
        Gera a estrutura completa de copy para:
        - Pagina Principal (Home)
        - 3 Sub-paginas de Verticais Especializadas
        - Anuncios RSA validados para Google Ads
        - FAQ com transparencia e quebra de objecoes
        """
        prompt = f"""
        Voce e o Diretor de Copywriting e Conversao de maior autoridade no mercado brasileiro.
        Empresa: "{business_name}"
        Nicho: "{niche}"
        WhatsApp: "{whatsapp}"
        Regiao: "{region}"

        Crie o kit completo de lancamento seguindo as melhores praticas de usabilidade, etica/compliance,
        transparencia de preco (FAQ que explica como funciona a cobranca sem assustar) e alto indice de qualidade no Google Ads.

        Regras de estilo:
        - Hero com badge de confianca: 'Atendimento Humano · {region} · Experiencia Comprovada'
        - Banner de Analise Rapida de Viabilidade / Triagem
        - Copy fluida, sem jargoes inuteis, focada em resolver o problema com agilidade
        - 3 Verticais especificas para paginas secundarias
        - Titulos de anuncios RSA com no maximo 30 caracteres
        - Descricoes de anuncios RSA com no maximo 90 caracteres

        Retorne ESTRITAMENTE um objeto JSON valido com o seguinte esquema:
        {{
            "home": {{
                "page_title": "Titulo SEO da Home (max 65 chars)",
                "meta_description": "Meta description persuasiva (max 155 chars)",
                "badge_text": "Atendimento Humano · {region} · Experiencia Comprovada",
                "headline_first": "Pergunta ou afirmacao de impacto inicial",
                "headline_highlight": "Palavras finais em destaque/gradiente",
                "subheadline": "Explicacao clara da solucao, agilidade e autoridade (max 30 palavras)",
                "cta_primary": "Avaliar Meu Caso Agora",
                "viability_banner": {{
                    "title": "Analise Rapida de Viabilidade",
                    "subtitle": "Fale diretamente com nossa equipe e receba um diagnostico preliminar do seu caso em poucos minutos sem compromisso."
                }},
                "trust_cards": [
                    {{"icon": "⚡", "title": "Agilidade Imediata", "description": "Atendimento rapido e acoes urgentes para estancar prejuizos."}},
                    {{"icon": "🛡️", "title": "Sigilo & Seguranca", "description": "Tratamento rigoroso dos dados e protecao integral do cliente."}},
                    {{"icon": "🎯", "title": "Especialistas Dedicados", "description": "Experiencia comprovada em demandas complexas deste segmento."}}
                ],
                "stats": [
                    {{"number": "98%", "label": "Casos avaliados no mesmo dia"}},
                    {{"number": "24/7", "label": "Plantao para emergencias"}},
                    {{"number": "100%", "label": "Atendimento humano personalizado"}}
                ],
                "faq": [
                    {{"question": "Quanto custa a avaliacao inicial?", "answer": "A avaliacao preliminar de viabilidade e 100% gratuita. Analisamos sua situacao antes de propor qualquer medida formal."}},
                    {{"question": "Quanto tempo leva para iniciar o atendimento?", "answer": "Nosso primeiro contato e imediato via WhatsApp, e o plano de acao costuma ser tracado nas primeiras horas."}},
                    {{"question": "O atendimento e presencial ou online?", "answer": "Atendemos com total seguranca de forma digital em todo o territorio nacional, sem necessidade de deslocamento."}},
                    {{"question": "Como funciona a cobranca do servico?", "answer": "Trabalhamos com total transparencia contratual, informando valores e condicoes previamente sem nenhuma surpresa."}}
                ],
                "whatsapp_message": "Ola! Gostaria de uma avaliacao preliminar sobre meu caso."
            }},
            "verticals": [
                {{
                    "slug": "vertical-1",
                    "menu_title": "Servico 1",
                    "page_title": "Titulo SEO Servico 1 (max 65 chars)",
                    "meta_description": "Meta description do Servico 1",
                    "headline": "Headline especifica do Servico 1",
                    "subheadline": "Subheadline com foco na dor do Servico 1",
                    "cards": [
                        {{"title": "Diagnostico Especializado", "description": "Identificacao rapida das raizes do problema."}},
                        {{"title": "Medidas Estrategicas", "description": "Execucao precisa com tecnicas validadas."}},
                        {{"title": "Resolucao Acelerada", "description": "Foco em restaurar a normalidade no menor prazo possivel."}}
                    ],
                    "faq": [
                        {{"question": "Pergunta especifica do Servico 1?", "answer": "Resposta objetiva e clara."}},
                        {{"question": "Qual o prazo para esse servico?", "answer": "Explicacao transparente de prazo."}}
                    ],
                    "whatsapp_message": "Ola! Preciso de ajuda urgente com [Servico 1]. Podem avaliar?"
                }},
                {{
                    "slug": "vertical-2",
                    "menu_title": "Servico 2",
                    "page_title": "Titulo SEO Servico 2",
                    "meta_description": "Meta description do Servico 2",
                    "headline": "Headline especifica do Servico 2",
                    "subheadline": "Subheadline especifica",
                    "cards": [
                        {{"title": "Diferencial A", "description": "Descricao"}},
                        {{"title": "Diferencial B", "description": "Descricao"}},
                        {{"title": "Diferencial C", "description": "Descricao"}}
                    ],
                    "faq": [
                        {{"question": "Pergunta especifica do Servico 2?", "answer": "Resposta"}}
                    ],
                    "whatsapp_message": "Ola! Gostaria de informacoes sobre [Servico 2]."
                }},
                {{
                    "slug": "vertical-3",
                    "menu_title": "Servico 3",
                    "page_title": "Titulo SEO Servico 3",
                    "meta_description": "Meta description do Servico 3",
                    "headline": "Headline especifica do Servico 3",
                    "subheadline": "Subheadline especifica",
                    "cards": [
                        {{"title": "Diferencial X", "description": "Descricao"}},
                        {{"title": "Diferencial Y", "description": "Descricao"}},
                        {{"title": "Diferencial Z", "description": "Descricao"}}
                    ],
                    "faq": [
                        {{"question": "Pergunta especifica do Servico 3?", "answer": "Resposta"}}
                    ],
                    "whatsapp_message": "Ola! Gostaria de atendimento para [Servico 3]."
                }}
            ],
            "google_ads": {{
                "ad_groups": [
                    {{
                        "name": "G1: Principal / Nicho Geral",
                        "headlines": [
                            "15 titulos com max 30 carac cada"
                        ],
                        "descriptions": [
                            "4 descricoes com max 90 carac cada"
                        ],
                        "keywords": [
                            "[termo exato 1]",
                            "\"termo de frase 1\"",
                            "\"termo de frase 2\""
                        ]
                    }},
                    {{
                        "name": "G2: Servico 1",
                        "headlines": ["15 titulos com max 30 carac"],
                        "descriptions": ["4 descricoes com max 90 carac"],
                        "keywords": ["[termo exato]", "\"termo de frase\""]
                    }},
                    {{
                        "name": "G3: Servico 2",
                        "headlines": ["15 titulos com max 30 carac"],
                        "descriptions": ["4 descricoes com max 90 carac"],
                        "keywords": ["[termo exato]", "\"termo de frase\""]
                    }},
                    {{
                        "name": "G4: Servico 3",
                        "headlines": ["15 titulos com max 30 carac"],
                        "descriptions": ["4 descricoes com max 90 carac"],
                        "keywords": ["[termo exato]", "\"termo de frase\""]
                    }}
                ]
            }}
        }}
        """
        res_text = self.generate(prompt)
        return self._extract_json(res_text)

    def generate_copy_json(self, niche: str, business_name: str, audience: str = "") -> Dict[str, Any]:
        """Legado compativel para chamadas simples"""
        kit = self.generate_full_client_kit(niche, business_name, "", "Brasil")
        home = kit.get("home", {})
        return {
            "headline_first": home.get("headline_first", "Atendimento Especializado"),
            "headline_highlight": home.get("headline_highlight", "Para seu Negocio"),
            "subheadline": home.get("subheadline", "Solucoes rapidas com seguranca."),
            "cta_text": home.get("cta_primary", "Falar no WhatsApp"),
            "trust_cards": home.get("trust_cards", []),
            "google_ads": kit.get("google_ads", {})
        }
