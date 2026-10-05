import os
import json
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List, Optional

class AIEngine:
    """
    Motor de Inteligencia Artificial para LaunchPilot powered by Google Gemini.
    Responsavel por analise de concorrencia, criacao de copy de Landing Page
    e geracao automatica de anuncios para Google Ads.
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
            "gemini-flash-latest",
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite"
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
                with urllib.request.urlopen(req) as resp:
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

    def generate_copy_json(self, niche: str, business_name: str, audience: str = "") -> Dict[str, Any]:
        prompt = f"""
        Voce e um Diretor de Copywriting e Conversao de padrao internacional.
        Crie a estrutura completa de copy para a Landing Page da empresa: "{business_name}".
        Nicho: "{niche}".
        Publico-alvo: "{audience or 'Empresarios e clientes qualificados'}".

        Retorne ESTRITAMENTE um objeto JSON valido (sem tags markdown de bloco de codigo) com a seguinte estrutura:
        {{
            "headline_first": "Pergunta ou gancho inicial impactante",
            "headline_highlight": "Palavras-chave em destaque para conversao",
            "subheadline": "Proposta unica de valor clara e sem jargoes (max 25 palavras)",
            "cta_text": "Chamada para acao irresistivel no botao",
            "trust_cards": [
                {{"title": "Diferencial 1", "description": "Descricao rapida"}},
                {{"title": "Diferencial 2", "description": "Descricao rapida"}},
                {{"title": "Diferencial 3", "description": "Descricao rapida"}}
            ],
            "google_ads": {{
                "headlines": ["15 titulos com max 30 caracteres cada"],
                "descriptions": ["4 descricoes com max 90 caracteres cada"]
            }}
        }}
        """
        response_text = self.generate(prompt)
        cleaned = re.sub(r"^```json\s*", "", response_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Resposta do Gemini nao pode ser convertida para JSON: {response_text}")
