import os
import sys
import questionary
import json
from pathlib import Path
from core.safety import ConfirmLiveExecution

# Imports dos módulos
from modules import scanner, system_cleaner, program_manager, startup_manager, diagnostics, uninstaller

def _header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "═" * 60)
    print("       GUARDIAN OS — OMNI AUDIT (DIAGNÓSTICO ATIVO)")
    print("═" * 60)

def salvar_relatorio(dados):
    log_path = Path("logs/performance_history.json")
    historico = []
    if log_path.exists():
        with open(log_path, "r") as f: historico = json.load(f)
    historico.append(dados)
    with open(log_path, "w") as f: json.dump(historico, f, indent=4)


def ask_execution_mode(operation_label: str) -> tuple[bool, ConfirmLiveExecution | None]:
    """Ask user for dry-run vs live mode and return safety parameters."""
    choice = questionary.select(
        f"{operation_label}: choose execution mode",
        choices=[
            "Dry run (recommended, no system changes)",
            "Live execution (applies real changes)",
        ],
    ).ask()

    if choice is None or "Dry run" in choice:
        return True, None

    confirmed = questionary.confirm(
        "You selected LIVE execution. This may perform irreversible changes. Continue?",
        default=False,
    ).ask()
    if not confirmed:
        print("Operation cancelled. No changes were applied.")
        return True, None

    return False, ConfirmLiveExecution.CONFIRMED


def print_operation_report(report: dict | None) -> None:
    """Print a compact operation summary to improve CLI observability."""
    if not report:
        return
    print("\nOperation summary:")
    for key, value in report.items():
        print(f"  - {key}: {value}")

def menu_principal():
    while True:
        _header()
        escolha = questionary.select(
            "Selecione o protocolo:",
            choices=[
                "1. 🩺 Diagnóstico de Performance (NOVO)",
                "2. 🔎 Scan Inteligente de Arquivos",
                "3. 🧹 Limpeza de Cache e Temp",
                "4. 🚀 Gerenciar Startup (Boot)",
                "5. 📦 Desinstalação Profunda",
                "❌ Sair"
            ]
        ).ask()

        if escolha == "❌ Sair" or escolha is None: break
        
        if "1" in escolha:
            relatorio = diagnostics.realizar_diagnostico()
            salvar_relatorio(relatorio)
        elif "2" in escolha:
            scanner.localizar_arquivos_grandes(os.path.expanduser("~"))
        elif "3" in escolha:
            dry_run, confirm = ask_execution_mode("Temp cleanup")
            report = system_cleaner.limpar_pastas_temporarias(dry_run=dry_run, confirm=confirm)
            print_operation_report(report)
        elif "4" in escolha:
            entradas = startup_manager.listar_entradas_startup()
            if entradas:
                opcoes = [questionary.Choice(f"{e.nome}", value=e) for e in entradas]
                selecionados = questionary.checkbox("Desabilitar no Boot:", choices=opcoes).ask()
                if selecionados: startup_manager.desabilitar_entradas(selecionados)
        elif "5" in escolha:
            progs = program_manager.listar_programas_instalados()
            if progs:
                p = questionary.select("Escolha o programa para remoção PROFUNDA:", 
                                       choices=[questionary.Choice(x['nome'], value=x) for x in progs[:30]]).ask()
                if p:
                    dry_run, confirm = ask_execution_mode("Deep uninstall")
                    report = uninstaller.desinstalacao_profunda(
                        p['id'],
                        p['nome'],
                        dry_run=dry_run,
                        confirm=confirm,
                    )
                    print_operation_report(report)
        
        input("\nENTER para voltar...")

if __name__ == "__main__":
    menu_principal()