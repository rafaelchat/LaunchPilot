# 🚀 LaunchPilot

**LaunchPilot** é uma plataforma e motor de automação que transforma o lançamento de sites, tracking avançado e campanhas de tráfego em um processo instantâneo de **1 comando ou 1 clique** ("Pagou, Rodou").

---

## ⚡ O Que Ele Faz Automaticamente

1. **Construção de Site:** Compila uma Landing Page moderna, responsiva, com design escuro/slate premium, foco em conversão e botão flutuante com animação de pulso.
2. **Consent Mode V2 Nativo:** Configura previamente as diretrizes de consentimento do Google Analytics e Google Ads.
3. **Google Tag Manager (GTM API v2):** Cria o contêiner, variáveis da camada de dados (`click_origin`), acionadores de clique e publica o contêiner programaticamente.
4. **Google Analytics 4 (GA4 Admin API):** Cria a propriedade, conecta o Web Stream e registra dimensões customizadas.
5. **Google Ads (API v25):** Cria Ações de Conversão, Tag Vinculadora e aplica restrições de público B2B In-Market para evitar desperdício de verba.
6. **Search Console (Webmasters API):** Registra o site e submete o `sitemap.xml` para indexação imediata.
7. **Delegação e Convite Admin:** Cria os ativos e convida o e-mail do cliente final como Administrador no GTM, GA4 e Search Console.
8. **Deploy Automatizado:** Publica o site na Vercel com SSL ativo e URLs limpas.

---

## 📁 Estrutura do Projeto

```text
LaunchPilot/
├── launchpilot.config.example.json   # Arquivo de configuração zero-touch
├── vercel.json                        # Regras de roteamento e segurança de deploy
├── main.py                            # Entrypoint principal
├── requirements.txt                   # Dependências do projeto
│
├── launchpilot/
│   ├── cli.py                         # Interface de Linha de Comando (CLI)
│   ├── core/                          # Motores de Automação
│   │   ├── auth.py                    # Gerenciador OAuth 2.0 unificado
│   │   ├── gtm.py                     # Motor da API v2 do GTM
│   │   ├── ga4.py                     # Motor do Google Analytics 4
│   │   ├── google_ads.py              # Motor do Google Ads API v25
│   │   ├── search_console.py          # Motor do Search Console
│   │   ├── permissions.py             # Motor de Convite Admin para o cliente
│   │   ├── site_builder.py            # Motor de compilação da Landing Page
│   │   └── deployer.py                # Motor de Deploy (Vercel)
│   │
│   ├── templates/                     # Templates de Landing Page
│   │   └── default_lp/
│   │       └── index.html             # Template com dataLayer e Consent Mode v2
│   │
│   └── utils/
│       └── auditor.py                 # Auditor de integridade de tags e botões
```

---

## 🛠️ Como Usar

### 1. Instalação
```bash
git clone https://github.com/seu-usuario/LaunchPilot.git
cd LaunchPilot
pip install -r requirements.txt
```

### 2. Configuração Rápida
Copie o arquivo de exemplo e preencha com os dados do cliente/empresa:
```bash
cp launchpilot.config.example.json launchpilot.config.json
```

### 3. Execução Master ("Pagou, Rodou")
Para rodar a esteira completa:
```bash
python main.py run
```

---

## 💡 Modelo de Negócio SaaS (Planos A e B)

* **Plano A (Turnkey / "Pagou, Rodou"):** O cliente preenche o formulário no checkout, a esteira roda em segundo plano e entrega o site no ar com todo o tracking validado em 2 minutos.
* **Plano B (Studio Copilot):** Tudo do Plano A + Dashboard interativo com preview do site e um Chat com IA para o cliente solicitar edições no texto, cores e seções com deploy automático.

---

Desenvolvido para máxima velocidade, robustez e independência técnica.
