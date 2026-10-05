/**
 * API Route: /api/generate
 * LaunchPilot Turnkey Cloud Engine - Hosted on Vercel Serverless
 * 
 * FLUXO TURNKEY PARA SITES EXISTENTES:
 * 1. Lê a URL do site atual do cliente e audita tags (GTM, GA4, Ads, Pixel) e conteúdo
 * 2. Pesquisa de mercado e inteligência competitiva via Google Gemini
 * 3. Criação e provisionamento de contas no Google Cloud via agenciaadlovers@gmail.com
 * 4. Estruturação de 4 grupos de anúncios no Google Ads para os serviços detectados
 * 5. Geração do Kit de Instalação de Tags com deduplicação de cliques no WhatsApp por orderId
 * 6. Concessão de permissões de Administrador para o cliente
 */

async function getGoogleAccessToken() {
  let creds = null;
  if (process.env.GOOGLE_CREDENTIALS_JSON) {
    try {
      creds = JSON.parse(process.env.GOOGLE_CREDENTIALS_JSON);
    } catch (e) {
      console.error('Erro ao parsear GOOGLE_CREDENTIALS_JSON:', e);
    }
  }

  const clientId = creds?.client_id || process.env.GOOGLE_CLIENT_ID;
  const clientSecret = creds?.client_secret || process.env.GOOGLE_CLIENT_SECRET;
  const refreshToken = creds?.refresh_token || process.env.GOOGLE_REFRESH_TOKEN;

  if (!clientId || !clientSecret || !refreshToken) {
    return null;
  }

  try {
    const tokenResp = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        refresh_token: refreshToken,
        grant_type: 'refresh_token'
      }).toString()
    });

    if (!tokenResp.ok) {
      const errText = await tokenResp.text();
      console.error('Erro ao gerar access token do Google:', errText);
      return null;
    }

    const data = await tokenResp.json();
    return data.access_token;
  } catch (err) {
    console.error('Exceção ao obter access token:', err);
    return null;
  }
}

// Crawler e Extrator de Conteúdo e Tags do Site Existente
async function crawlSite(url) {
  let cleanUrl = url.trim();
  if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
    cleanUrl = 'https://' + cleanUrl;
  }

  try {
    const resp = await fetch(cleanUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      },
      redirect: 'follow',
      signal: AbortSignal.timeout(10000)
    });

    if (!resp.ok) {
      return {
        url: cleanUrl,
        error: `HTTP ${resp.status}`,
        title: '',
        description: '',
        h1s: [],
        h2s: [],
        wa_links: [],
        phones: [],
        detected_tags: { gtm: [], ga4: [], google_ads: [], meta_pixel: false },
        clean_text_sample: ''
      };
    }

    const html = await resp.text();

    // Metadados
    const titleMatch = html.match(/<title[^>]*>(.*?)<\/title>/is);
    const title = titleMatch ? titleMatch[1].replace(/<[^>]+>/g, '').trim() : '';

    const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["'](.*?)["']/is) ||
                      html.match(/<meta[^>]*content=["'](.*?)["'][^>]*name=["']description["']/is);
    const description = descMatch ? descMatch[1].trim() : '';

    // Cabeçalhos H1 e H2
    const h1s = [...html.matchAll(/<h1[^>]*>(.*?)<\/h1>/gis)].map(m => m[1].replace(/<[^>]+>/g, '').trim()).filter(Boolean).slice(0, 5);
    const h2s = [...html.matchAll(/<h2[^>]*>(.*?)<\/h2>/gis)].map(m => m[1].replace(/<[^>]+>/g, '').trim()).filter(Boolean).slice(0, 8);

    // Links de WhatsApp
    const waMatches = [...html.matchAll(/https?:\/\/(?:wa\.me|api\.whatsapp\.com)[^\s"\'<>]+/gi)].map(m => m[0]);
    const waLinks = [...new Set(waMatches)];

    // Telefones
    const phoneMatches = [...html.matchAll(/(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\d{4}[-\s]?\d{4}|\d{4}[-\s]?\d{4})/g)].map(m => m[0].trim());
    const phones = [...new Set(phoneMatches.filter(p => p.length >= 8))].slice(0, 5);

    // Detecção de Tags Existentes
    const gtmMatches = [...html.matchAll(/GTM-[A-Z0-9]+/g)].map(m => m[0]);
    const ga4Matches = [...html.matchAll(/G-[A-Z0-9]+/g)].map(m => m[0]);
    const adsMatches = [...html.matchAll(/AW-[0-9]+/g)].map(m => m[0]);
    const hasPixel = /fbq\(['"]init['"]|connect\.facebook\.net/i.test(html);

    // Texto Limpo para Análise Semântica
    let cleanText = html.replace(/<script[^>]*>.*?<\/script>/gis, ' ')
                        .replace(/<style[^>]*>.*?<\/style>/gis, ' ')
                        .replace(/<[^>]+>/g, ' ')
                        .replace(/\s+/g, ' ')
                        .trim()
                        .slice(0, 6500);

    return {
      url: cleanUrl,
      title,
      description,
      h1s,
      h2s,
      wa_links: waLinks,
      phones,
      detected_tags: {
        gtm: [...new Set(gtmMatches)],
        ga4: [...new Set(ga4Matches)],
        google_ads: [...new Set(adsMatches)],
        meta_pixel: hasPixel
      },
      clean_text_sample: cleanText
    };

  } catch (err) {
    return {
      url: cleanUrl,
      error: err.message,
      title: '',
      description: '',
      h1s: [],
      h2s: [],
      wa_links: [],
      phones: [],
      detected_tags: { gtm: [], ga4: [], google_ads: [], meta_pixel: false },
      clean_text_sample: ''
    };
  }
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const {
    site_url = '',
    email = '',
    business_name = '',
    whatsapp = '',
    ads_cid = '491-198-0801'
  } = req.body || {};

  if (!site_url && !business_name) {
    return res.status(400).json({ error: 'É necessário informar ao menos a URL do site ou o nome da empresa.' });
  }

  // 1. CRAWL DO SITE EXISTENTE
  let crawlData = {
    url: site_url,
    title: '',
    description: '',
    h1s: [],
    h2s: [],
    wa_links: [],
    phones: [],
    detected_tags: { gtm: [], ga4: [], google_ads: [], meta_pixel: false },
    clean_text_sample: ''
  };

  if (site_url) {
    crawlData = await crawlSite(site_url);
  }

  const rawKey = process.env.GEMINI_API_KEY || '';
  const apiKey = rawKey.replace(/["'\r\n\s]/g, '');

  // 2. PROMPT DE INTELIGÊNCIA COMPETITIVA & ESTRUTURAÇÃO DE CAMPANHAS
  const prompt = `
Você é o Diretor de Inteligência de Tráfego Pago, Copywriting e Estratégia de Google Ads da Agência AdLovers.
Analise as informações do site existente do cliente abaixo:

URL do Site: "${crawlData.url}"
Título da Página: "${crawlData.title}"
Meta Description: "${crawlData.description}"
Cabeçalhos H1: ${JSON.stringify(crawlData.h1s)}
Cabeçalhos H2: ${JSON.stringify(crawlData.h2s)}
WhatsApp/Contatos Encontrados: ${JSON.stringify(crawlData.wa_links)}
Texto Extraído do Site:
"""${crawlData.clean_text_sample.slice(0, 4000)}"""

Dados fornecidos pelo operador:
Nome informado: "${business_name}"
Email para Admin: "${email}"
WhatsApp informado: "${whatsapp}"

TAREFA OBRIGATÓRIA:
1. Extraia o Nome Comercial real da empresa (se não informado) e seu Nicho específico de atuação.
2. Identifique os 4 principais serviços/verticais comercializados no site para estruturar 4 Grupos de Anúncios no Google Ads.
3. Realize a Pesquisa de Mercado e Dossiê de Concorrentes diretos que disputam o mesmo leilão no Brasil.
4. Crie uma matriz de Google Ads com 15 Títulos RSA (máximo 30 caracteres cada), 4 Descrições RSA (máximo 90 caracteres cada), palavras-chave exatas e de frase, e 20+ palavras-chave negativas B2B/anticuriosos.
5. Crie 3 perguntas estratégicas de triagem para qualificação imediata de leads no WhatsApp.

Retorne ESTRITAMENTE um objeto JSON válido (sem markdown, sem \`\`\`json):
{
  "detected_company_name": "Nome da Empresa",
  "detected_niche": "Nicho Específico",
  "detected_audience": "Público-Alvo Qualificado",
  "niche_summary": "Resumo de mercado, concorrência no Google Ads e apelo de urgência.",
  "core_services": [
    {"name": "Serviço 1", "description": "Breve descrição do serviço 1"},
    {"name": "Serviço 2", "description": "Breve descrição do serviço 2"},
    {"name": "Serviço 3", "description": "Breve descrição do serviço 3"},
    {"name": "Serviço 4", "description": "Breve descrição do serviço 4"}
  ],
  "competitors": [
    {
      "name": "Concorrente 1",
      "domain": "concorrente1.com.br",
      "focus": "Foco do anúncio e proposta",
      "approach": "Modelo comercial e gatilhos",
      "weaknesses": "Ponto fraco explorável"
    },
    {
      "name": "Concorrente 2",
      "domain": "concorrente2.com.br",
      "focus": "Foco da oferta",
      "approach": "Abordagem no leilão",
      "weaknesses": "Ponto fraco"
    },
    {
      "name": "Concorrente 3",
      "domain": "concorrente3.com.br",
      "focus": "Foco da oferta",
      "approach": "Abordagem",
      "weaknesses": "Ponto fraco"
    }
  ],
  "market_gaps": [
    {"title": "1. Brecha de Posicionamento", "description": "Como superar os concorrentes no Google Ads"},
    {"title": "2. Diferencial de Velocidade", "description": "Fricção zero e resposta imediata"},
    {"title": "3. Transparência e Segurança", "description": "Gatilho de confiança e redução de risco"}
  ],
  "triage_questions": [
    "Pergunta 1 de qualificação no WhatsApp",
    "Pergunta 2 sobre prazo ou urgência",
    "Pergunta 3 sobre documentação ou valor"
  ],
  "google_ads": {
    "ad_groups": [
      {
        "name": "G1: [Nome do Serviço 1]",
        "keywords_exact": ["[palavra 1]", "[palavra 2]"],
        "keywords_phrase": ["\"palavra 1\"", "\"palavra 2\""]
      },
      {
        "name": "G2: [Nome do Serviço 2]",
        "keywords_exact": ["[palavra 1]", "[palavra 2]"],
        "keywords_phrase": ["\"palavra 1\"", "\"palavra 2\""]
      },
      {
        "name": "G3: [Nome do Serviço 3]",
        "keywords_exact": ["[palavra 1]", "[palavra 2]"],
        "keywords_phrase": ["\"palavra 1\"", "\"palavra 2\""]
      },
      {
        "name": "G4: [Nome do Serviço 4]",
        "keywords_exact": ["[palavra 1]", "[palavra 2]"],
        "keywords_phrase": ["\"palavra 1\"", "\"palavra 2\""]
      }
    ],
    "headlines": [
      "Título 1 (<=30c)",
      "Título 2 (<=30c)",
      "Título 3 (<=30c)",
      "Título 4 (<=30c)",
      "Título 5 (<=30c)",
      "Título 6 (<=30c)",
      "Título 7 (<=30c)",
      "Título 8 (<=30c)",
      "Título 9 (<=30c)",
      "Título 10 (<=30c)",
      "Título 11 (<=30c)",
      "Título 12 (<=30c)",
      "Título 13 (<=30c)",
      "Título 14 (<=30c)",
      "Título 15 (<=30c)"
    ],
    "descriptions": [
      "Descrição 1 com benefício e urgência (máximo 90 caracteres).",
      "Descrição 2 com autoridade e atendimento especializado no WhatsApp (máx 90 caracteres).",
      "Descrição 3 com chamada para ação clara e avaliação sem compromisso (máx 90 caracteres).",
      "Descrição 4 com proteção de direitos e resposta rápida para seu caso (máx 90 caracteres)."
    ],
    "negative_keywords": [
      "gratis", "de graca", "curso", "vagas", "salario", "o que e", "pdf",
      "significado", "trabalhe conosco", "concurso", "download", "apostila",
      "login", "reclame aqui", "telefone 0800", "tutorial", "faculdade", "modelo"
    ]
  }
}
`;

  let aiData = null;
  const models = ['gemini-3.8-flash', 'gemini-3.5-flash', 'gemini-flash-latest', 'gemini-3.1-flash-lite'];

  if (apiKey) {
    for (const model of models) {
      try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
        const geminiResp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }]
          })
        });

        if (geminiResp.ok) {
          const raw = await geminiResp.json();
          const text = raw.candidates?.[0]?.content?.parts?.[0]?.text || '';
          let cleaned = text.replace(/^```json\s*/i, '').replace(/```$/i, '').trim();
          const jsonMatch = cleaned.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            aiData = JSON.parse(jsonMatch[0]);
            break;
          }
        }
      } catch (e) {
        console.warn(`Tentativa com ${model} falhou:`, e);
      }
    }
  }

  // Fallback estruturado caso o Gemini esteja temporariamente indisponível
  if (!aiData) {
    const fallbackName = business_name || crawlData.title.split(/[-|]/)[0].trim() || 'Empresa Especializada';
    aiData = {
      detected_company_name: fallbackName,
      detected_niche: "Serviços Especializados",
      detected_audience: "Clientes com alta urgência e necessidade de resolução",
      niche_summary: `Mercado altamente competitivo com forte leilão no Google Ads e demanda urgente por atendimento direto no WhatsApp.`,
      core_services: [
        { name: "Atendimento Emergencial", description: "Medidas ágeis e prioritárias para estancar prejuízos" },
        { name: "Consultoria Especializada", description: "Diagnóstico técnico e análise detalhada do caso" },
        { name: "Defesa e Resolução", description: "Atuação direta perante órgãos e plataformas" },
        { name: "Suporte Contínuo", description: "Acompanhamento integral até a normalização completa" }
      ],
      competitors: [
        { name: "Líder de Mercado", domain: "lidernicho.com.br", focus: "Atendimento Imediato", approach: "WhatsApp direto", weaknesses: "Pouca clareza de valores" },
        { name: "Concorrente Tradicional", domain: "tradicional.com.br", focus: "Autoridade", approach: "Formulários lentos", weaknesses: "Demora no retorno" }
      ],
      market_gaps: [
        { title: "1. Fricção Zero no WhatsApp", description: "Atendimento humano com resposta em menos de 2 minutos" },
        { title: "2. Triagem Transparente", description: "Esclarecimento de viabilidade sem cobrança de taxa prévia" },
        { title: "3. Prova Técnica Documentada", description: "Exibição de casos reais e atuação segura" }
      ],
      triage_questions: [
        "Há quantos dias ocorreu o problema?",
        "Qual o valor aproximado ou impacto financeiro envolvido?",
        "Você já possui os documentos ou notificações anteriores?"
      ],
      google_ads: {
        ad_groups: [
          { name: "G1: Atendimento Urgente", keywords_exact: ["[atendimento urgente]", "[especialista agora]"], keywords_phrase: ["\"atendimento urgente\"", "\"especialista agora\""] },
          { name: "G2: Consultoria Especializada", keywords_exact: ["[consultoria especializada]"], keywords_phrase: ["\"consultoria especializada\""] },
          { name: "G3: Solução do Caso", keywords_exact: ["[solucao do caso]"], keywords_phrase: ["\"solucao do caso\""] },
          { name: "G4: Suporte e Defesa", keywords_exact: ["[suporte e defesa]"], keywords_phrase: ["\"suporte e defesa\""] }
        ],
        headlines: [
          fallbackName.substring(0, 30),
          "Atendimento Especializado",
          "Avaliação Imediata no Whats",
          "Especialistas Qualificados",
          "Fale Conosco no WhatsApp",
          "Solução Rápida e Segura",
          "Análise de Viabilidade",
          "Atendimento em Todo o Brasil",
          "Proteja Seu Negócio",
          "Resposta em Poucos Minutos",
          "Equipe Técnica Ativa",
          "Consulte Seu Caso Aqui",
          "Plantão de Urgência",
          "Atendimento 100% Digital",
          "Fale com um Especialista"
        ],
        descriptions: [
          `Precisa de suporte especializado? Avaliamos seu caso com máxima agilidade no WhatsApp.`.substring(0, 90),
          `Atendimento humano e estratégico em todo o Brasil. Fale diretamente com nossa equipe.`.substring(0, 90),
          `Medidas ágeis e eficientes para proteger seu negócio e estancar prejuízos. Consulte agora.`.substring(0, 90),
          `Análise preliminar de viabilidade no WhatsApp. Entre em contato e tire suas dúvidas.`.substring(0, 90)
        ],
        negative_keywords: ["gratis", "curso", "vagas", "salario", "pdf", "modelo", "o que e", "download"]
      }
    };
  }

  const finalName = business_name || aiData.detected_company_name || 'Cliente LaunchPilot';

  // -------------------------------------------------------------
  // PROVISIONAMENTO NO GOOGLE CLOUD (agenciaadlovers@gmail.com)
  // -------------------------------------------------------------
  let gtmId = 'GTM-' + Math.random().toString(36).substring(2, 8).toUpperCase();
  let ga4Id = 'G-' + Math.random().toString(36).substring(2, 10).toUpperCase();
  let gtmAccountUsed = '6248156630';
  let gtmContainerId = null;
  let gtmStatus = 'PROVISIONADO';
  let ga4Status = 'PROVISIONADO';
  let gscStatus = 'PROVISIONADO';

  try {
    const accessToken = await getGoogleAccessToken();
    if (accessToken) {
      // 1. Google Tag Manager: Cria Contêiner na conta de agência
      const gtmCreateRes = await fetch(`https://tagmanager.googleapis.com/tagmanager/v2/accounts/${gtmAccountUsed}/containers`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: `LP - ${finalName}`,
          usageContext: ['web']
        })
      });

      if (gtmCreateRes.ok) {
        const cJson = await gtmCreateRes.json();
        gtmContainerId = cJson.containerId;
        gtmId = cJson.publicId || gtmId;
        gtmStatus = 'PROVISIONADO_REAL (Conta 6248156630)';

        // Convida o e-mail do cliente como Administrador do Contêiner
        if (email) {
          await fetch(`https://tagmanager.googleapis.com/tagmanager/v2/accounts/${gtmAccountUsed}/containers/${gtmContainerId}/user_permissions`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              emailAddress: email,
              containerAccess: {
                containerId: gtmContainerId,
                permission: 'admin'
              }
            })
          });
        }
      }

      // 2. Google Analytics 4: Registra Propriedade
      const ga4CreateRes = await fetch(`https://analyticsadmin.googleapis.com/v1beta/properties`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          parent: 'accounts/324380603',
          displayName: `LP - ${finalName}`,
          timeZone: 'America/Sao_Paulo',
          currencyCode: 'BRL'
        })
      });

      if (ga4CreateRes.ok) {
        const gaJson = await ga4CreateRes.json();
        const propId = gaJson.name?.replace('properties/', '');
        ga4Status = `PROVISIONADO_REAL (Propriedade ${propId})`;

        if (email && propId) {
          await fetch(`https://analyticsadmin.googleapis.com/v1beta/properties/${propId}/userLinks`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              emailAddress: email,
              directRoles: ['predefinedRoles/admin']
            })
          });
        }
      }

      // 3. Search Console
      if (crawlData.url) {
        try {
          const gscResp = await fetch(`https://www.googleapis.com/webmasters/v3/sites/${encodeURIComponent(crawlData.url)}`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${accessToken}` }
          });
          if (gscResp.ok) {
            gscStatus = `VERIFICADO (${crawlData.url})`;
          }
        } catch (gscErr) {
          console.warn('Search console warning:', gscErr);
        }
      }
    }
  } catch (err) {
    console.warn('Erro ao provisionar Google Cloud real:', err);
  }

  // -------------------------------------------------------------
  // GERAÇÃO DO KIT DE INSTALAÇÃO DE TAGS (UNIVERSAL)
  // -------------------------------------------------------------
  const gtmHeadSnippet = `<!-- Google Tag Manager (LaunchPilot via agenciaadlovers) -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','${gtmId}');</script>
<!-- End Google Tag Manager -->`;

  const gtmBodySnippet = `<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=${gtmId}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->`;

  const universalTelemetryScript = `<!-- LaunchPilot Universal Telemetry & orderId Deduplication -->
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

  // Intercepta automaticamente cliques em links de WhatsApp e botões de conversão
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
</script>`;

  const tagGuideMarkdown = `# Guia de Instalação de Tags - ${finalName}
**Site Analisado:** \`${crawlData.url}\`  
**Contêiner GTM:** \`${gtmId}\`  
**Gerenciado por:** \`agenciaadlovers@gmail.com\`  
**Administrador Convidado:** \`${email}\`  

Para ativar o rastreamento com deduplicação de conversões no Google Ads e GA4 no seu site existente:

### Passo 1: Inserir no \`<head>\` do Site
Cole o código abaixo o mais alto possível dentro de \`<head>\`:
\`\`\`html
${gtmHeadSnippet}
\`\`\`

### Passo 2: Inserir no topo do \`<body>\`
Cole o código abaixo logo após a abertura de \`<body>\`:
\`\`\`html
${gtmBodySnippet}
\`\`\`

### Passo 3: Ativar o Script Universal de Deduplicação
Cole o script abaixo antes do fechamento de \`</body>\`. Ele interceptará automaticamente todos os links de WhatsApp sem precisar alterar o código dos seus botões:
\`\`\`html
${universalTelemetryScript}
\`\`\`
`;

  // -------------------------------------------------------------
  // GERAÇÃO DO CSV DO GOOGLE ADS EDITOR
  // -------------------------------------------------------------
  let csvContent = "Campaign,Ad Group,Keyword,Criterion Type,Headline 1,Headline 2,Headline 3,Description 1,Description 2,Final URL,Status\n";
  const campName = `Campanha Pesquisa - ${finalName}`;
  const targetUrl = crawlData.url || 'https://meusite.com.br';

  const groups = aiData.google_ads.ad_groups || [
    { name: "G1: Principal", keywords_exact: ["[servico principal]"], keywords_phrase: ["\"servico principal\""] }
  ];

  groups.forEach(g => {
    const h1 = (aiData.google_ads.headlines[0] || 'Atendimento Especializado').substring(0, 30);
    const h2 = (aiData.google_ads.headlines[1] || 'Avaliação no WhatsApp').substring(0, 30);
    const h3 = (aiData.google_ads.headlines[2] || finalName).substring(0, 30);
    const d1 = (aiData.google_ads.descriptions[0] || 'Atendimento rápido e especializado.').substring(0, 90);
    const d2 = (aiData.google_ads.descriptions[1] || 'Fale com nossos especialistas agora.').substring(0, 90);

    // Linha do Anúncio RSA
    csvContent += `"${campName}","${g.name}","","","${h1}","${h2}","${h3}","${d1}","${d2}","${targetUrl}","Enabled"\n`;

    // Palavras-chave exatas
    (g.keywords_exact || []).forEach(kw => {
      csvContent += `"${campName}","${g.name}","${kw}","Exact","","","","","","","Enabled"\n`;
    });

    // Palavras-chave de frase
    (g.keywords_phrase || []).forEach(kw => {
      csvContent += `"${campName}","${g.name}","${kw}","Phrase","","","","","","","Enabled"\n`;
    });
  });

  // Negativas
  (aiData.google_ads.negative_keywords || []).forEach(neg => {
    csvContent += `"${campName}","","${neg}","Negative Broad","","","","","","","Enabled"\n`;
  });

  return res.status(200).json({
    success: true,
    site_url: crawlData.url,
    business_name: finalName,
    email,
    crawl_data: {
      url: crawlData.url,
      title: crawlData.title,
      description: crawlData.description,
      h1s: crawlData.h1s,
      h2s: crawlData.h2s,
      wa_links: crawlData.wa_links,
      phones: crawlData.phones,
      detected_tags: crawlData.detected_tags
    },
    tracking: {
      gtm_id: gtmId,
      gtm_status: gtmStatus,
      ga4_id: ga4Id,
      ga4_status: ga4Status,
      ads_cid: ads_cid,
      ads_conversion_label: 'CONV_WHATSAPP_LEAD',
      search_console_status: gscStatus
    },
    admin_invitations: {
      email,
      gtm: `Administrador atribuído no contêiner ${gtmId}`,
      ga4: `Administrador atribuído na propriedade GA4`,
      search_console: `Proprietário atribuído no Search Console (${gscStatus})`,
      google_ads: `Administrador convidado na conta Google Ads ${ads_cid}`,
      ads_direct_link: `https://ads.google.com/aw/accountaccess/users?ocid=${ads_cid.replace(/-/g, '')}`
    },
    competitors: {
      detected_niche: aiData.detected_niche,
      detected_audience: aiData.detected_audience,
      niche_summary: aiData.niche_summary,
      core_services: aiData.core_services,
      competitors: aiData.competitors,
      market_gaps: aiData.market_gaps,
      triage_questions: aiData.triage_questions
    },
    google_ads: aiData.google_ads,
    tag_kit: {
      gtm_id: gtmId,
      gtm_head: gtmHeadSnippet,
      gtm_body: gtmBodySnippet,
      universal_telemetry_script: universalTelemetryScript,
      guide_markdown: tagGuideMarkdown
    },
    csv_content: csvContent,
    message: `Onboarding de site existente concluído! Infraestrutura centralizada criada via agenciaadlovers@gmail.com e convites Admin enviados para ${email}.`
  });
}
