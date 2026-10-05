# 🚀 LaunchPilot — Turnkey Client Launcher Engine

O **LaunchPilot** é uma esteira de automação industrial de marketing e tráfego pago da agência **Adlovers** (`agenciaadlovers@gmail.com`). 

Ele transforma o processo completo de pesquisa, criação de site multi-páginas, telemetria analítica com deduplicação, estruturação de Google Ads e delegação de permissões de administrador em uma esteira 100% automatizada e replicável para **qualquer cliente ou nicho**.

---

## ⚡ As 6 Etapas Automatizadas da Esteira

Quando você insere dados básicos de um cliente (`nicho`, `nome`, `e-mail`, `whatsapp`, `região`), o LaunchPilot executa:

1. **🕵️ Pesquisa de Concorrentes & Dossiê Executivo (`competitor_spy.py`):**
   - Mapeia os 5 a 10 principais players que anunciam no Google Ads para aquele nicho no Brasil/região.
   - Analisa ofertas, gatilhos, pontos fracos e identifica as 4 maiores brechas de mercado.
   - Gera um **Dossiê em Markdown** e compila automaticamente um **Dossiê Executivo em PDF** de alta qualidade visual via `xhtml2pdf` com links diretos para o Google Ads Transparency Center.
   - Fornece script de triagem rápida para qualificação imediata de leads no WhatsApp.

2. **🧠 Inteligência de Copywriting & Arquitetura Multi-Páginas (`ai.py` - Google Gemini):**
   - Cria a copy persuasiva para a Página Principal (Home).
   - Identifica e desenvolve 3 sub-páginas de **Verticais Especializadas** (ex: no Direito Médico: *Defesa em Processos Éticos CRM*, *Ações de Erro Médico*, *Consultoria Preventiva Hospitalar*).
   - Inclui selo de confiança comprovado (*"Atendimento Humano · Região · Experiência Comprovada"*), banner de Análise Rápida de Viabilidade e FAQ com quebra de objeções sobre custos e prazos.
   - Redige anúncios responsivos de pesquisa (RSAs) com 15 títulos (≤ 30 carac.) e 4 descrições (≤ 90 carac.) para cada vertical.

3. **🌐 Compilação do Site Multi-Páginas com Telemetria (`site_builder.py`):**
   - Gera layout moderno e fluido (sem caixas rígidas), tipografia *Plus Jakarta Sans*, gradientes sutis e modo escuro/slate premium.
   - Rastreabilidade cirúrgica com **19+ botões táticos** equipados com data-attributes granulares (`data-btn-name`, `data-btn-event="whatsapp_conversion"`, `data-page`, `data-placement`, `data-source`).
   - Injeta o script de **Deduplicação por `orderId`** (`LEAD_{TIMESTAMP}_{HASH}`), que impede que múltiplos cliques do mesmo visitante inflem as métricas de conversão no Google Ads e no GA4.
   - Gera dados estruturados **JSON-LD** (`ProfessionalService` / `LocalBusiness`, `FAQPage` e `BreadcrumbList`), além de `sitemap.xml` e `robots.txt`.

4. **📊 Infraestrutura Central de Tracking Google Cloud (`gtm.py` & `ga4.py`):**
   - Cria o Contêiner Web no **Google Tag Manager (GTM API v2)** sob a conta da agência.
   - Cria as Variáveis da Camada de Dados (`dlv - orderId`, `dlv - btn_name`, etc.), o acionador `whatsapp_conversion` e as tags oficiais: *Conversion Linker*, *Google Tag*, *Google Ads Conversão (deduplicada por orderId)* e *GA4 Evento generate_lead*.
   - Cria a versão e **publica automaticamente** o contêiner no ar.
   - Conecta a propriedade e o stream de dados no **Google Analytics 4 (GA4 Admin API v1beta)** e registra as dimensões customizadas.

5. **🎯 Estruturação de Campanhas Google Ads (`google_ads.py`):**
   - Registra ou valida a Ação de Conversão no Google Ads (`CONTACT` / `SUBMIT_LEAD_FORM`).
   - Exporta a planilha completa pronta para importação no **Google Ads Editor** (`google_ads_campaign_import.csv`), contendo a campanha, os 4 grupos segmentados, palavras-chave em Frase e Exata, 15 títulos e 4 descrições RSA por anúncio, e 20+ palavras-chave negativas para blindagem de verba.

6. **✉️ Delegação de Permissões: Convites de Administrador (`permissions.py`):**
   - Envia convites com perfil de **Administrador / Proprietário** para o e-mail do cliente em todos os canais:
     - **GTM:** Administrador do Contêiner (`containerAccess: admin`).
     - **GA4:** Administrador da Propriedade (`roles/analytics.admin`).
     - **Google Search Console:** Proprietário Verificado (`siteOwner`).
     - **Google Ads:** Administrador da conta via API ou link direto de 1 clique (`https://ads.google.com/aw/accountaccess/users?ocid={cid}`).

---

## 🛠️ Como Usar

### 1. Modo Linha de Comando (Direto)

Para lançar um novo cliente com apenas 1 comando no terminal:

```bash
python main.py launch \
  --niche "Direito Médico e Defesa de Médicos" \
  --name "Dra. Beatriz Mendes" \
  --email "cliente@email.com" \
  --whatsapp "5511987654321" \
  --region "São Paulo - SP"
```

*Adicione a flag `--dry-run` para executar em modo de teste e gerar todos os artefatos locais sem modificar as contas em produção.*

### 2. Modo Assistente Interativo (Wizard)

Basta digitar:

```bash
python main.py wizard
```

O assistente solicitará passo a passo:
1. Nicho do cliente
2. Nome da empresa / profissional
3. E-mail do cliente para convites de Administrador
4. WhatsApp de atendimento com DDD
5. Praça ou região de atendimento

---

## 📂 Estrutura de Saída (`output/<slug>/`)

Cada execução gera um pacote executivo completo e pronto para entrega:

```text
output/dra_beatriz_mendes/
├── client_kit_dra_beatriz_mendes.json      # JSON completo com todas as copies e anúncios
├── dossie_concorrentes_dra_beatriz_mendes.md # Dossiê de pesquisa de mercado em Markdown
├── dossie_concorrentes_dra_beatriz_mendes.pdf # Dossiê Executivo formatado em PDF para o cliente
├── google_ads_campaign_import.csv           # Planilha de importação direta para Google Ads Editor
├── relatorio_entrega_dra_beatriz_mendes.md  # Resumo executivo de entrega com links e acessos
└── dist/                                    # Site completo estático pronto para deploy
    ├── index.html                           # Home Page com 10+ CTAs e schemas
    ├── sitemap.xml                          # Sitemap com todas as páginas
    ├── robots.txt                           # Diretivas de indexação
    ├── vercel.json                          # Configuração de URLs limpas
    └── servicos/                            # Verticais específicas
        ├── processos-eticos.html
        ├── erro-medico.html
        └── consultoria-contratual.html
```

---

## 🔑 Credenciais Utilizadas

- **Google Cloud Platform:** Autenticado via `google_credentials.json` na conta central `agenciaadlovers@gmail.com`.
- **Google Ads MCC:** `491-198-0801`.
- **Gemini AI:** Configurado via `.env` (`GEMINI_API_KEY`).
