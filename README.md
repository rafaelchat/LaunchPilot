# 🚀 LaunchPilot - Turnkey Client Onboarding & Google Ads Engine

O **LaunchPilot** é uma esteira de automação industrial de marketing e tráfego pago da agência **Adlovers** (`agenciaadlovers@gmail.com`). 

Ele permite ler o site existente do cliente, realizar pesquisa competitiva de mercado, criar a infraestrutura analítica oficial no Google Cloud (GTM e GA4) sob a conta da agência, estruturar as campanhas do Google Ads com 4 grupos segmentados e gerar o kit universal de instalação de tags com deduplicação de conversões por `orderId`.

Interface Web em Produção: **[https://launchpilot-seven.vercel.app/](https://launchpilot-seven.vercel.app/)**

---

## ⚡ Fluxo Principal: Onboarding de Sites Existentes

Ao informar a **URL de um site existente** e o **e-mail do cliente**, o LaunchPilot executa:

1. **🌐 Leitura e Auditoria Estrutural do Site (`site_reader.py`):**
   - Rastreia o HTML da URL informada.
   - Extrai metadados (`<title>`, `<meta name="description">`), cabeçalhos `<h1>` e `<h2>`, telefones e links de WhatsApp.
   - Audita tags existentes instaladas no código: **Google Tag Manager**, **Google Analytics 4**, **Google Ads Tag** e **Meta Pixel**.
   - Sintetiza semanticamente o posicionamento e identifica os 4 principais serviços prestados pelo cliente.

2. **🕵️ Pesquisa de Concorrentes & Dossiê Executivo (`competitor_spy.py`):**
   - Mapeia os principais concorrentes que disputam leilão de Google Ads no Brasil para aquele nicho.
   - Identifica ofertas, modelos de fechamento, pontos fracos e as maiores brechas de mercado.
   - Gera um **Dossiê em Markdown** e compila automaticamente um **Dossiê Executivo em PDF** via `xhtml2pdf` com links diretos para o Google Ads Transparency Center.
   - Fornece roteiro de triagem e qualificação imediata de leads no WhatsApp.

3. **🏷️ Provisionamento Google Cloud sob `agenciaadlovers@gmail.com` (`gtm.py` & `ga4.py`):**
   - Cria o Contêiner Web no **Google Tag Manager** (Conta `6248156630`).
   - Configura as tags oficiais: *Conversion Linker*, *Google Tag*, *Google Ads Conversão (deduplicada por orderId)* e *GA4 Evento whatsapp_conversion*.
   - Publica automaticamente o contêiner live no ar.
   - Cria a propriedade e Web Data Stream no **Google Analytics 4** (Conta `324380603`) e registra dimensões personalizadas (`order_id`, `btn_name`, `btn_placement`).
   - Registra o site no **Google Search Console** para acompanhamento orgânico.

4. **🎯 Estruturação de Campanhas Google Ads (`google_ads.py`):**
   - Mapeia 4 Grupos de Anúncios correspondentes aos 4 serviços detectados no site.
   - Gera 15 Títulos RSA (≤ 30 caracteres) e 4 Descrições RSA (≤ 90 caracteres).
   - Define palavras-chave em correspondência Exata `[termo]` e de Frase `"termo"`.
   - Gera lista com 20+ palavras-chave negativas B2B/anticuriosos para blindagem de verba.
   - Exporta a planilha pronta para importação no **Google Ads Editor** (`google_ads_campaign_import.csv`).

5. **📦 Kit Universal de Instalação de Tags (`tag_installer.py`):**
   - Fornece os códigos exatos de `<head>` e `<body>` do GTM criado.
   - Fornece o **Script Universal de Telemetria e Deduplicação**: código JS de interceptação automática de cliques em `wa.me` e botões de conversão que gera `orderId` exclusivo (`LEAD_{TIMESTAMP}_{HASH}`).
   - **Funciona em qualquer CMS existente** (WordPress, Wix, Webflow, Shopify ou HTML estático) sem necessidade de reconstruir o site do cliente!

6. **✉️ Delegação de Permissões de Administrador (`permissions.py`):**
   - Delega perfil de **Administrador / Proprietário** para o e-mail do cliente:
     - **GTM:** Administrador do Contêiner (`permission: 'admin'`).
     - **GA4:** Administrador da Propriedade (`roles: ['predefinedRoles/admin']`).
     - **Google Search Console:** Proprietário Verificado (`siteOwner`).
     - **Google Ads:** Link direto de 1 clique para concessão de acesso Admin na conta da agência.

---

## 💻 Como Executar

### 1. Interface Web (Online na Nuvem)
Acesse **[https://launchpilot-seven.vercel.app/](https://launchpilot-seven.vercel.app/)**:
- Digite a URL do site do cliente (ex: `https://desbloqueiodecontas.online` ou qualquer outro cliente).
- Digite o e-mail do cliente que receberá os acessos.
- Clique em **"🚀 Ler Site, Pesquisar Concorrentes & Criar Contas"**.
- Acompanhe o log em tempo real no console e visualize todos os resultados nas abas de Diagnóstico, Dossiê, Campanhas, Kit de Tags e Acessos.

### 2. Linha de Comando (CLI Local)
Para executar o onboarding de um site existente via terminal:

```bash
python main.py scan \
  --url "https://desbloqueiodecontas.online" \
  --email "contato@desbloqueiodecontas.online"
```

Opções adicionais:
- `--name "Nome da Empresa"` (opcional se quiser forçar um nome)
- `--ads-cid "491-198-0801"` (conta MCC da agência)
- `--dry-run` (executa a leitura, inteligência e geração dos arquivos sem alterar as contas reais no Google Cloud)

---

## 📁 Estrutura do Projeto

```
LaunchPilot/
├── api/
│   └── generate.js                # API Serverless no Vercel (OAuth2, Gemini, GTM, GA4, GSC)
├── launchpilot/
│   ├── core/
│   │   ├── site_reader.py         # Crawler e extrator de tags e conteúdo de sites existentes
│   │   ├── ai.py                  # Integração com Google Gemini (modelos flash com retry)
│   │   ├── competitor_spy.py      # Espionagem competitiva e dossiê executivo em Markdown e PDF
│   │   ├── tag_installer.py       # Kit universal de tags e script de deduplicação por orderId
│   │   ├── gtm.py                 # Provisionamento de contêineres e publicação no GTM v2
│   │   ├── ga4.py                 # Criação de propriedades e dimensões customizadas no GA4
│   │   ├── google_ads.py          # Estruturação de campanhas e CSV para o Google Ads Editor
│   │   ├── permissions.py         # Delegação de permissões de Administrador para o cliente
│   │   └── auth.py                # Gerenciador OAuth2 central sob agenciaadlovers@gmail.com
│   └── cli.py                     # Interface de linha de comando com comando 'scan'
├── index.html                     # Interface Web responsiva de alta fidelidade
├── main.py                        # Ponto de entrada CLI
├── requirements.txt               # Dependências Python
└── vercel.json                    # Configurações do Vercel com timeout estendido de 60s
```
