"""
main.py — GuardianOS Entry Point
Foco: Roteamento, Auditoria de privilégios e Gestão de Logs.
"""
import os
import sys
import logging
import ctypes
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import questionary

import scanner
import system_cleaner
import program_manager
import startup_manager

# ─── Configuração de Log Otimizada ───────────────────────────────────────────
LOG_DIR = Path.home() / "GuardianOS_Logs"
LOG_DIR.mkdir(exist_ok=True)
_log_file = LOG_DIR / "guardian_session.log"

# Rotação de logs: Mantém apenas os últimos 5MB de histórico
log_handler = RotatingFileHandler(_log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[log_handler]
)
logger = logging.getLogger("guardianOS")

def is_admin():
    """Verifica se o script está rodando com privilégios de Administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def _header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "═" * 60)
    print("       ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ")
    print("      ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗")
    print("      ██║  ███╗██║   ██║███████║██████╔╝██║  ██║")
    print("      ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║")
    print("      ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝")
    print("                    O  M  N  I")
    print("═" * 60)
    if not is_admin():
        print("  ⚠️  AVISO: RODANDO SEM PRIVILÉGIOS DE ADMINISTRADOR")
        print("  Algumas funções de limpeza profunda estarão limitadas.")
        print("═" * 60)

def _perguntar_dry_run() -> bool:
    return questionary.select(
        "  Modo de execução:",
        choices=[
            questionary.Choice("🔍 Simulação (Dry Run) — Seguro", value=True),
            questionary.Choice("⚡ Execução Real — Aplicar Mudanças", value=False),
        ]
    ).ask()

def menu_principal():
    _header()
    while True:
        escolha = questionary.select(
            "Selecione o protocolo de otimização:",
            choices=[
                "1. 🔎 Scan de Arquivos Grandes",
                "2. 🧹 Limpeza de Cache e Temporários",
                "3. 📦 Gerenciar Programas (Winget)",
                "4. 🗑️  Remover Bloatware (AppX)",
                "5. 🚀 Gerenciador de Inicialização",
                questionary.Separator(),
                "❌ Sair"
            ]
        ).ask()

        if escolha == "❌ Sair" or escolha is None:
            print("\nEncerrando GuardianOS...")
            break

        dry_run = _perguntar_dry_run()

        try:
            if "1" in escolha:
                arquivos = scanner.localizar_arquivos_grandes(os.path.expanduser("~"))
                if arquivos:
                    opcoes = [questionary.Choice(f"{a['caminho'].name} ({a['tamanho_mb']:.0f} MB)", value=a) for a in arquivos[:30]]
                    selecionados = questionary.checkbox("Arquivos para DELETAR:", choices=opcoes).ask()
                    if selecionados and not dry_run:
                        if questionary.confirm("Confirmar deleção irreversível?").ask():
                            for s in selecionados:
                                s['caminho'].unlink()
                                logger.info(f"ARQUIVO_DELETADO | {s['caminho']}")

            elif "2" in escolha:
                system_cleaner.limpar_pastas_temporarias(dry_run)
            
            elif "3" in escolha:
                programas = program_manager.listar_programas_instalados()
                if programas:
                    opcoes = [questionary.Choice(f"{p['nome']} (v{p['versao']})", value=p['id']) for p in programas[:50]]
                    selecionados = questionary.checkbox("Programas para DESINSTALAR:", choices=opcoes).ask()
                    if selecionados:
                        program_manager.desinstalar_em_lote(selecionados, dry_run)

            elif "4" in escolha:
                app = questionary.text("Digite o nome parcial do App (ex: xbox, maps):").ask()
                if app: system_cleaner.desinstalar_bloatware(app, dry_run)

            elif "5" in escolha:
                entradas = startup_manager.listar_entradas_startup()
                opcoes = [questionary.Choice(f"{e.impacto} | {e.nome}", value=e) for e in entradas]
                selecionados = questionary.checkbox("Entradas para DESABILITAR:", choices=opcoes).ask()
                if selecionados: startup_manager.desabilitar_entradas(selecionados, dry_run)

        except Exception as e:
            logger.exception("Erro durante operação")
            print(f"❌ Ocorreu um erro: {e}")
        
        input("\nPressione ENTER para voltar ao menu...")
        _header()

if __name__ == "__main__":
    menu_principal()