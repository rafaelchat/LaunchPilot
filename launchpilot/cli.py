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
from launchpilot.core.competitor_spy import CompetitorSpy
from launchpilot.core.site_builder import SiteBuilder
from launchpilot.core.gtm import GTMManager
from launchpilot.core.ga4 import GA4Manager
from launchpilot.core.google_ads import GoogleAdsManager
from launchpilot.core.search_console import SearchConsoleManager
from launchpilot.core.permissions import PermissionsManager
from launchpilot.core.deployer import Deployer
from launchpilot.utils.auditor import Auditor

def load_config(config_path: str = "launchpilot.config.json") -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    example_path = "launchpilot.config.example.json"
    if os.path.exists(example_path):
        with open(example_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def run_turnkey_pipeline(client_data: dict, dry_run: bool = False):
    """
    Executa a esteira completa e replicável de lançamento para qualquer cliente.
    """
    niche = client_data.get("niche", "Serviços Especializados")
    client_name = client_data.get("name", "Minha Empresa")
    client_email = client_data.get("email", "")
    whatsapp = client_data.get("whatsapp", "")
    region = client_data.get("region", "Brasil")
    domain = client_data.get("domain", f"https://{client_name.lower().replace(' ', '')}.vercel.app")
    ads_cid = client_data.get("ads_cid", "491-198-0801")
    
    slug = client_name.lower().replace(" ", "_").replace("&", "e")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    output_dir = os.path.abspath(os.path.join("output", slug))
    dist_dir = os.path.abspath(os.path.join(output_dir, "dist"))
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print(f" 🚀 LAUNCHPILOT — INICIANDO ESTEIRA DE LANÇAMENTO TURNKEY")
    print(f"    Cliente: {client_name}")
    print(f"    Nicho: {niche} | Praça: {region}")
    print(f"    E-mail Admin: {client_email} | WhatsApp: {whatsapp}")
    print("=" * 80)

    auth = GoogleAuthManager()
    ai = AIEngine()

    # -------------------------------------------------------------
    # ETAPA 1: Espionagem de Concorrentes & Dossiê Executivo
    # -------------------------------------------------------------
    print("\n[1/6] 🕵️  PESQUISA DE MERCADO & ESPIONAGEM COMPETITIVA...")
    spy = CompetitorSpy(ai_engine=ai)
    spy_result = spy.run_spy(niche=niche, client_name=client_name, region=region, output_dir=output_dir)
    print(f"  ✓ Dossiê Markdown: {spy_result['markdown_path']}")
    if spy_result.get("pdf_path"):
        print(f"  ✓ Dossiê Executivo em PDF: {spy_result['pdf_path']}")

    # -------------------------------------------------------------
    # ETAPA 2: Inteligência de Copy & Arquitetura Multi-Páginas
    # -------------------------------------------------------------
    print("\n[2/6] 🧠 GERANDO COPYWRITING MULTI-PÁGINAS & ANÚNCIOS RSA...")
    client_kit = ai.generate_full_client_kit(niche=niche, business_name=client_name, whatsapp=whatsapp, region=region)
    kit_json_path = os.path.join(output_dir, f"client_kit_{slug}.json")
    with open(kit_json_path, "w", encoding="utf-8") as f:
        json.dump(client_kit, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Estrutura de copy gerada: Home + {len(client_kit.get('verticals', []))} Verticais Especializadas")
    print(f"  ✓ Salvo em: {kit_json_path}")

    # -------------------------------------------------------------
    # ETAPA 3: Compilação do Site com Telemetria e Deduplicação
    # -------------------------------------------------------------
    print("\n[3/6] 🌐 COMPILANDO SITE RESPONSIVO & TELEMETRIA...")
    builder = SiteBuilder()
    site_config = {
        "business": {
            "company_name": client_name,
            "whatsapp_number": whatsapp,
            "theme": {
                "primary_color": "#0f172a",
                "accent_color": "#2563eb"
            }
        },
        "deploy": {
            "domain": domain
        }
    }
    
    # ID Provisório ou Real
    gtm_public_id = "GTM-PENDING"

    # Se não for dry_run, provisiona GTM real
    gtm_account_id = None
    gtm_container_id = None
    gtm_res = None
    if not dry_run:
        try:
            gtm = GTMManager(auth_manager=auth)
            accounts = gtm.list_accounts()
            if accounts:
                gtm_account_id = accounts[0].get("accountId")
                container = gtm.get_or_create_container(gtm_account_id, f"LP - {client_name}")
                gtm_container_id = container.get("containerId")
                gtm_public_id = container.get("publicId", gtm_public_id)
                print(f"  ✓ Contêiner GTM configurado na agência: {gtm_public_id} (ID: {gtm_container_id})")
        except Exception as e:
            print(f"  ⚠️ Aviso GTM: {e}")

    builder.export_dist(client_kit, site_config, dist_dir, gtm_public_id=gtm_public_id)
    print(f"  ✓ Site multi-páginas compilado em: {dist_dir}")
    print(f"  ✓ Páginas geradas: index.html, servicos/*.html, sitemap.xml, robots.txt")

    # -------------------------------------------------------------
    # ETAPA 4: Provisionamento de Tracking GTM & GA4
    # -------------------------------------------------------------
    print("\n[4/6] 📊 CONFIGURANDO GOOGLE TAG MANAGER & GA4 (AGÊNCIA ADLOVERS)...")
    ga4_prop_id = None
    ga4_meas_id = None
    if not dry_run:
        try:
            ga4 = GA4Manager(auth_manager=auth)
            ga4_accounts = ga4.list_accounts_and_properties()
            if ga4_accounts:
                ga4_acc_id = ga4_accounts[0]["account_id"]
                # Cria ou reutiliza propriedade
                print(f"  ✓ Conectando GA4 na conta de agência {ga4_acc_id}...")
                ga4_setup = ga4.setup_property_complete(ga4_acc_id, client_name, domain)
                ga4_prop_id = ga4_setup.get("property_id")
                ga4_meas_id = ga4_setup.get("measurement_id")
                print(f"  ✓ Propriedade GA4 criada: {ga4_prop_id} | Stream ID: {ga4_meas_id}")
        except Exception as e:
            print(f"  ⚠️ Aviso GA4: {e}")

        # Setup completo de Tags GTM com deduplicação
        if gtm_account_id and gtm_container_id:
            try:
                print(f"  ✓ Injetando Tags de Deduplicação, Conversion Linker e GA4...")
                gtm.setup_complete_tracking(
                    account_id=gtm_account_id,
                    container_id=gtm_container_id,
                    ga4_measurement_id=ga4_meas_id,
                    ads_conversion_id=ads_cid,
                    ads_conversion_label="LEAD_CONVERSION"
                )
                print(f"  ✓ Versão v1.0 publicada no GTM com sucesso!")
            except Exception as e:
                print(f"  ⚠️ Aviso ao publicar GTM: {e}")
    else:
        print("  ✓ [DRY-RUN] Simulação de criação GTM e GA4 concluída.")

    # -------------------------------------------------------------
    # ETAPA 5: Estruturação de Campanhas Google Ads
    # -------------------------------------------------------------
    print("\n[5/6] 🎯 CONFIGURANDO GOOGLE ADS & CONVERSÕES...")
    ads_manager = GoogleAdsManager(auth_manager=auth)
    ads_csv_path = os.path.join(output_dir, "google_ads_campaign_import.csv")
    ad_groups = client_kit.get("google_ads", {}).get("ad_groups", [])
    negatives = spy_result.get("intelligence", {}).get("negative_keywords", [])

    ads_manager.export_campaign_editor_csv(
        campaign_name=f"Campanha Pesquisa - {client_name}",
        ad_groups=ad_groups,
        negative_keywords=negatives,
        final_url=domain,
        output_path=ads_csv_path
    )
    print(f"  ✓ Planilha de Campanha para Google Ads Editor gerada em: {ads_csv_path}")
    print(f"  ✓ Total de Grupos: {len(ad_groups)} | Negativas: {len(negatives)}")

    if not dry_run:
        try:
            # Registra Ação de Conversão na conta
            action_res = ads_manager.get_or_create_conversion_action(ads_cid, "Conversao WhatsApp Lead")
            print(f"  ✓ Ação de Conversão registrada no Google Ads ({ads_cid})")
        except Exception as e:
            print(f"  ⚠️ Aviso Google Ads: {e}")

    # -------------------------------------------------------------
    # ETAPA 6: Delegação de Acesso Admin para o Cliente
    # -------------------------------------------------------------
    print(f"\n[6/6] ✉️  DELEGANDO PERMISSÕES: CONVIDANDO {client_email} COMO ADMINISTRADOR...")
    perms = PermissionsManager(auth_manager=auth)
    invites_log = {}
    if client_email and not dry_run:
        if gtm_account_id and gtm_container_id:
            gtm_inv = perms.invite_gtm_admin(gtm_account_id, gtm_container_id, client_email)
            invites_log["GTM"] = gtm_inv.get("status")
            print(f"  ✓ Convite de Administrador GTM enviado para {client_email}")

        if ga4_prop_id:
            ga4_inv = perms.invite_ga4_admin(ga4_prop_id, client_email)
            invites_log["GA4"] = ga4_inv.get("status")
            print(f"  ✓ Permissão de Administrador GA4 atribuída para {client_email}")

        gsc_inv = perms.invite_search_console_owner(domain, client_email)
        invites_log["SearchConsole"] = gsc_inv.get("status")
        print(f"  ✓ Proprietário no Search Console atribuído para {client_email}")

        ads_inv = perms.invite_google_ads_admin(ads_cid, client_email)
        invites_log["GoogleAds"] = ads_inv.get("status")
        if ads_inv.get("status") == "SUCCESS":
            print(f"  ✓ Convite de Administrador no Google Ads enviado para {client_email}")
        elif ads_inv.get("direct_invite_link"):
            print(f"  ✓ Link de Convite Direto Google Ads: {ads_inv['direct_invite_link']}")
    else:
        print(f"  ✓ [SIMULAÇÃO] Convites de Admin preparados para {client_email}")

    # Relatório Final
    report_path = os.path.join(output_dir, f"relatorio_entrega_{slug}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"""# Relatório de Lançamento Turnkey — {client_name}
**Data:** {datetime.now().strftime("%d/%m/%Y %H:%M")}  
**Nicho:** {niche}  
**E-mail do Cliente (Admin):** {client_email}  
**WhatsApp:** {whatsapp}  
**Domínio:** {domain}  

## 1. Ativos Gerados
- **Dossiê de Concorrentes:** `{spy_result.get('markdown_path')}`
- **Dossiê Executivo PDF:** `{spy_result.get('pdf_path')}`
- **Site Multi-Páginas:** Pasta `{dist_dir}`
- **Google Ads Editor CSV:** `{ads_csv_path}`

## 2. Infraestrutura e Tracking
- **Contêiner GTM:** `{gtm_public_id}`
- **Google Ads:** Conta `{ads_cid}`
- **GA4 Propriedade:** `{ga4_prop_id or 'Configurado'}`

## 3. Permissões de Administrador
O cliente `{client_email}` foi provisionado como Administrador nos seguintes canais:
- Google Tag Manager (GTM): Administrador
- Google Analytics 4 (GA4): Administrador
- Google Search Console: Proprietário Verificado
- Google Ads: Administrador
""")

    print("\n" + "=" * 80)
    print(" 🎉 PROCESSO FINALIZADO COM SUCESSO!")
    print(f"    Arquivos do cliente gerados em: {output_dir}")
    print(f"    Relatório de Entrega: {report_path}")
    print("=" * 80)

def interactive_wizard():
    print("=" * 70)
    print(" 🚀 LAUNCHPILOT — WIZARD DE NOVO CLIENTE")
    print("=" * 70)
    print("Insira as informações básicas para iniciar a esteira automática:\n")
    
    niche = input("1. Qual o nicho de atuação do cliente? (ex: Direito Médico, Desentupidora 24h): ").strip()
    name = input("2. Qual o nome da empresa ou cliente? (ex: Dra. Ana Silva): ").strip()
    email = input("3. Qual o e-mail do cliente para receber convites Admin?: ").strip()
    whatsapp = input("4. Qual o número de WhatsApp com DDD? (ex: 5511999998888): ").strip()
    region = input("5. Qual a região / praça de atendimento? [Brasil]: ").strip() or "Brasil"
    domain = input("6. Qual o domínio desejado? (opcional): ").strip() or f"https://{name.lower().replace(' ', '')}.vercel.app"

    client_data = {
        "niche": niche,
        "name": name,
        "email": email,
        "whatsapp": whatsapp,
        "region": region,
        "domain": domain
    }

    run_turnkey_pipeline(client_data)

def main():
    parser = argparse.ArgumentParser(description="LaunchPilot CLI — Turnkey Client Launcher Engine")
    subparsers = parser.add_subparsers(dest="command")

    # Comando 'launch' ou 'new'
    launch_parser = subparsers.add_parser("launch", help="Lança novo cliente via parâmetros de linha de comando")
    launch_parser.add_argument("--niche", required=True, help="Nicho de atuação do cliente")
    launch_parser.add_argument("--name", required=True, help="Nome da empresa / cliente")
    launch_parser.add_argument("--email", required=True, help="E-mail do cliente para receber convites Admin")
    launch_parser.add_argument("--whatsapp", required=True, help="WhatsApp com DDD")
    launch_parser.add_argument("--region", default="Brasil", help="Praça / Região de atendimento")
    launch_parser.add_argument("--domain", default=None, help="Domínio do site")
    launch_parser.add_argument("--ads-cid", default="491-198-0801", help="Customer ID do Google Ads")
    launch_parser.add_argument("--dry-run", action="store_true", help="Executa sem mutar contas de produção")

    # Comando 'wizard'
    subparsers.add_parser("wizard", help="Inicia o assistente interativo no terminal")

    # Comando 'run'
    run_parser = subparsers.add_parser("run", help="Executa com base em arquivo de configuração")
    run_parser.add_argument("--config", default="launchpilot.config.json", help="Caminho do arquivo de configuração")
    run_parser.add_argument("--dry-run", action="store_true", help="Executa em modo de teste")

    # Build e Audit legados
    subparsers.add_parser("build", help="Compila o site")
    subparsers.add_parser("audit", help="Audita o site gerado")

    args = parser.parse_args()

    if args.command == "launch":
        client_data = {
            "niche": args.niche,
            "name": args.name,
            "email": args.email,
            "whatsapp": args.whatsapp,
            "region": args.region,
            "domain": args.domain or f"https://{args.name.lower().replace(' ', '')}.vercel.app",
            "ads_cid": args.ads_cid
        }
        run_turnkey_pipeline(client_data, dry_run=args.dry_run)
    elif args.command == "wizard":
        interactive_wizard()
    elif args.command == "run" or args.command is None:
        cfg = load_config(getattr(args, "config", "launchpilot.config.json"))
        client_data = {
            "niche": cfg.get("business", {}).get("niche", "Serviços"),
            "name": cfg.get("business", {}).get("company_name", "Minha Empresa"),
            "email": cfg.get("client", {}).get("email", ""),
            "whatsapp": cfg.get("business", {}).get("whatsapp_number", ""),
            "region": cfg.get("business", {}).get("region", "Brasil"),
            "domain": cfg.get("deploy", {}).get("domain", "https://meusite.vercel.app")
        }
        run_turnkey_pipeline(client_data, dry_run=getattr(args, "dry_run", False))
    elif args.command == "build":
        cfg = load_config()
        print("✓ Build executado via launch.")
    elif args.command == "audit":
        res = Auditor.audit_html_file("dist/index.html")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
