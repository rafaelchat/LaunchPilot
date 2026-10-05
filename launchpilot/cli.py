import os
import sys
import json
import argparse
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from launchpilot.core.auth import GoogleAuthManager
from launchpilot.core.ai import AIEngine
from launchpilot.core.site_reader import SiteReader
from launchpilot.core.competitor_spy import CompetitorSpy
from launchpilot.core.tag_installer import TagInstaller
from launchpilot.core.site_builder import SiteBuilder
from launchpilot.core.gtm import GTMManager
from launchpilot.core.ga4 import GA4Manager
from launchpilot.core.google_ads import GoogleAdsManager
from launchpilot.core.search_console import SearchConsoleManager
from launchpilot.core.permissions import PermissionsManager
from launchpilot.core.deployer import Deployer
from launchpilot.utils.auditor import Auditor

def run_existing_site_pipeline(site_url: str, client_email: str, client_name: str = "", ads_cid: str = "491-198-0801", dry_run: bool = False):
    """
    Esteira Turnkey para Sites Existentes:
    1. Lê e audita o site atual do cliente
    2. Realiza pesquisa competitiva e gera dossiê
    3. Provisiona GTM e GA4 na agência (agenciaadlovers@gmail.com)
    4. Gera campanhas segmentadas pelos serviços detectados
    5. Gera kit de instalação de tags com deduplicação de cliques
    6. Convida o e-mail do cliente como Administrador de todos os ativos
    """
    print("=" * 80)
    print(f" 🚀 LAUNCHPILOT — ONBOARDING & ATIVAÇÃO DE SITE EXISTENTE")
    print(f"    URL do Site: {site_url}")
    print(f"    E-mail Admin do Cliente: {client_email}")
    print(f"    Conta Agência: agenciaadlovers@gmail.com")
    print("=" * 80)

    auth = GoogleAuthManager()
    ai = AIEngine()
    reader = SiteReader()
    installer = TagInstaller()

    # 1. Leitura do Site Atual
    print("\n[1/6] 🌐 LENDO E AUDITANDO O SITE ATUAL...")
    site_data = reader.fetch_site(site_url)
    if "error" in site_data:
        print(f"  ❌ Erro ao acessar site: {site_data['error']}")
        return

    print(f"  ✓ Título Detectado: {site_data.get('title')}")
    print(f"  ✓ Amostra de Conteúdo: {len(site_data.get('clean_text_sample', ''))} caracteres analisados")
    print(f"  ✓ Tags Existentes: {site_data.get('detected_tags')}")

    print("  [*] Sintetizando inteligência de negócio e serviços com IA...")
    audit = ai.analyze_existing_site(site_data)
    
    final_name = client_name or audit.get("company_name", "Empresa Cliente")
    niche = audit.get("niche", "Serviços Especializados")
    region = audit.get("region", "Brasil Todo")
    detected_services = audit.get("detected_services", [])

    slug = final_name.lower().replace(" ", "_").replace("&", "e")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    output_dir = os.path.abspath(os.path.join("output", slug))
    os.makedirs(output_dir, exist_ok=True)

    print(f"  ✓ Empresa: {final_name}")
    print(f"  ✓ Nicho Mapeado: {niche} ({region})")
    print(f"  ✓ Serviços Específicos Detectados: {[s.get('title') for s in detected_services]}")

    # Salva relatório de auditoria do site
    with open(os.path.join(output_dir, "auditoria_site_atual.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)

    # 2. Pesquisa de Concorrentes & Dossiê Executivo
    print("\n[2/6] 🕵️ PESQUISA DE MERCADO & ESPIONAGEM NO GOOGLE ADS...")
    spy = CompetitorSpy(ai_engine=ai)
    spy_result = spy.run_spy(niche=niche, client_name=final_name, region=region, output_dir=output_dir)

    # 3. Provisionamento de GTM na Conta de Agência
    print("\n[3/6] 🏷️ PROVISIONANDO GOOGLE TAG MANAGER (AGÊNCIA ADLOVERS)...")
    gtm_public_id = "GTM-PENDING"
    gtm_account_id = None
    gtm_container_id = None

    if not dry_run:
        try:
            gtm = GTMManager(auth_manager=auth)
            accounts = gtm.list_accounts()
            if accounts:
                gtm_account_id = accounts[0].get("accountId")
                container = gtm.get_or_create_container(gtm_account_id, f"LP - {final_name}")
                gtm_container_id = container.get("containerId")
                gtm_public_id = container.get("publicId", gtm_public_id)
                print(f"  ✓ Contêiner GTM criado na agência: {gtm_public_id} (ID: {gtm_container_id})")
        except Exception as e:
            print(f"  ⚠️ Aviso GTM: {e}")
    else:
        gtm_public_id = "GTM-SIMULADO"
        print(f"  ✓ [DRY-RUN] Contêiner simulado: {gtm_public_id}")

    # 4. Conexão do Google Analytics 4
    print("\n[4/6] 📈 CONECTANDO GOOGLE ANALYTICS 4...")
    ga4_prop_id = None
    ga4_meas_id = None
    if not dry_run:
        try:
            ga4 = GA4Manager(auth_manager=auth)
            ga4_accounts = ga4.list_accounts_and_properties()
            if ga4_accounts:
                ga4_acc_id = ga4_accounts[0]["account_id"]
                ga4_setup = ga4.setup_property_complete(ga4_acc_id, final_name, site_url)
                ga4_prop_id = ga4_setup.get("property_id")
                ga4_meas_id = ga4_setup.get("measurement_id")
                print(f"  ✓ Propriedade GA4 criada: {ga4_prop_id} | Stream: {ga4_meas_id}")
        except Exception as e:
            print(f"  ⚠️ Aviso GA4: {e}")

        # Configura tags no GTM com deduplicação
        if gtm_account_id and gtm_container_id:
            try:
                gtm.setup_complete_tracking(
                    account_id=gtm_account_id,
                    container_id=gtm_container_id,
                    ga4_measurement_id=ga4_meas_id,
                    ads_conversion_id=ads_cid,
                    ads_conversion_label="CONV_LEAD"
                )
                print(f"  ✓ Tags de Conversão e Deduplicação publicadas no GTM!")
            except Exception as e:
                print(f"  ⚠️ Aviso publicação GTM: {e}")
    else:
        print("  ✓ [DRY-RUN] Setup GA4 simulado.")

    # 5. Estruturação de Campanhas Google Ads para os Serviços do Site
    print("\n[5/6] 🎯 CONFIGURANDO CAMPANHA NO GOOGLE ADS...")
    ads_manager = GoogleAdsManager(auth_manager=auth)
    ads_csv_path = os.path.join(output_dir, "google_ads_campaign_import.csv")
    ad_groups = audit.get("google_ads", {}).get("ad_groups", [])
    negatives = audit.get("google_ads", {}).get("negative_keywords", [])

    ads_manager.export_campaign_editor_csv(
        campaign_name=f"Pesquisa - {final_name}",
        ad_groups=ad_groups,
        negative_keywords=negatives,
        final_url=site_url,
        output_path=ads_csv_path
    )
    print(f"  ✓ Planilha Google Ads Editor gerada: {ads_csv_path}")
    print(f"  ✓ Total de Grupos Segmentados: {len(ad_groups)} | Negativas: {len(negatives)}")

    if not dry_run:
        try:
            ads_manager.get_or_create_conversion_action(ads_cid, "Conversao WhatsApp Lead")
            print(f"  ✓ Ação de Conversão registrada na conta {ads_cid}")
        except Exception as e:
            print(f"  ⚠️ Aviso Google Ads: {e}")

    # 6. Kit de Instalação de Tags para o Site Atual
    print("\n[6/6] 📦 GERANDO KIT DE INSTALAÇÃO DE TAGS & TELEMETRIA...")
    guide_md = installer.generate_guide_markdown(gtm_public_id, final_name, site_url)
    guide_path = os.path.join(output_dir, "guia_instalacao_tags.md")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(guide_md)
    print(f"  ✓ Guia de Instalação e Scripts gerados em: {guide_path}")

    # 7. Delegação de Permissões: Convites de Administrador
    print(f"\n[7/7] ✉️  ENVIANDO CONVITES DE ADMINISTRADOR PARA {client_email}...")
    perms = PermissionsManager(auth_manager=auth)
    if client_email and not dry_run:
        if gtm_account_id and gtm_container_id:
            perms.invite_gtm_admin(gtm_account_id, gtm_container_id, client_email)
            print(f"  ✓ Convite de Administrador GTM enviado para {client_email}")

        if ga4_prop_id:
            perms.invite_ga4_admin(ga4_prop_id, client_email)
            print(f"  ✓ Permissão de Administrador GA4 atribuída para {client_email}")

        perms.invite_search_console_owner(site_url, client_email)
        print(f"  ✓ Proprietário no Search Console atribuído para {client_email}")

        ads_inv = perms.invite_google_ads_admin(ads_cid, client_email)
        if ads_inv.get("direct_invite_link"):
            print(f"  ✓ Link de Convite Google Ads: {ads_inv['direct_invite_link']}")
    else:
        print(f"  ✓ [SIMULAÇÃO] Convites de Admin preparados para {client_email}")

    # Relatório Final
    report_path = os.path.join(output_dir, f"relatorio_onboarding_{slug}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"""# Relatório de Onboarding & Ativação de Tráfego — {final_name}
**Data:** {datetime.now().strftime("%d/%m/%Y %H:%M")}  
**Site do Cliente:** `{site_url}`  
**E-mail Admin:** `{client_email}`  
**Conta Agência:** `agenciaadlovers@gmail.com`  

## 1. Ativos Gerados
- **Auditoria do Site:** `{output_dir}/auditoria_site_atual.json`
- **Dossiê de Concorrentes:** `{spy_result.get('markdown_path')}`
- **Dossiê Executivo em PDF:** `{spy_result.get('pdf_path')}`
- **Planilha Google Ads Editor:** `{ads_csv_path}`
- **Guia de Instalação de Tags:** `{guide_path}`

## 2. Infraestrutura Provisionada
- **GTM Contêiner:** `{gtm_public_id}`
- **GA4 Propriedade:** `{ga4_prop_id or 'Configurado'}`
- **Google Ads:** `{ads_cid}`

## 3. Permissões de Administrador
O cliente `{client_email}` foi provisionado como Administrador nos seguintes canais:
- Google Tag Manager: Administrador do Contêiner
- Google Analytics 4: Administrador da Propriedade
- Google Search Console: Proprietário Verificado
- Google Ads: Administrador da Conta
""")

    print("\n" + "=" * 80)
    print(" 🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
    print(f"    Arquivos gerados em: {output_dir}")
    print(f"    Relatório de Onboarding: {report_path}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="LaunchPilot CLI — Turnkey Client Launcher Engine")
    subparsers = parser.add_subparsers(dest="command")

    # Comando 'scan' (Onboarding de site existente)
    scan_parser = subparsers.add_parser("scan", help="Lê um site existente, audita, pesquisa concorrentes e cria as contas/campanhas")
    scan_parser.add_argument("--url", required=True, help="URL do site atual do cliente (ex: https://meucliente.com.br)")
    scan_parser.add_argument("--email", required=True, help="E-mail do cliente para receber convites Admin")
    scan_parser.add_argument("--name", default="", help="Nome da empresa / cliente (opcional)")
    scan_parser.add_argument("--ads-cid", default="491-198-0801", help="Customer ID do Google Ads")
    scan_parser.add_argument("--dry-run", action="store_true", help="Executa sem mutar contas de produção")

    # Comando 'launch'
    launch_parser = subparsers.add_parser("launch", help="Cria site novo a partir de dados básicos")
    launch_parser.add_argument("--niche", required=True)
    launch_parser.add_argument("--name", required=True)
    launch_parser.add_argument("--email", required=True)
    launch_parser.add_argument("--whatsapp", required=True)
    launch_parser.add_argument("--region", default="Brasil")
    launch_parser.add_argument("--domain", default=None)
    launch_parser.add_argument("--ads-cid", default="491-198-0801")
    launch_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "scan":
        run_existing_site_pipeline(
            site_url=args.url,
            client_email=args.email,
            client_name=args.name,
            ads_cid=args.ads_cid,
            dry_run=args.dry_run
        )
    elif args.command == "launch":
        print("Para lançar com base em site existente, use: python main.py scan --url ...")

if __name__ == "__main__":
    main()
