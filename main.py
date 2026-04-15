import os
import scanner
import system_cleaner
import program_manager
import questionary

def iniciar_guardian_os():
    print("="*60)
    print("           GUARDIAN OS - CENTRAL DE CONTROLE           ")
    print("="*60)

    acao = questionary.select(
        "Selecione o protocolo de otimização:",
        choices=[
            "1. Scan de Arquivos Grandes",
            "2. Limpeza de Cache de Sistema",
            "3. Gerenciar/Desinstalar Programas (Winget)",
            "4. Remover Bloatware Específico",
            "Sair"
        ]
    ).ask()

    if acao == "1. Scan de Arquivos Grandes":
        pasta_alvo = os.path.expanduser("~")
        arquivos = scanner.localizar_arquivos_grandes(pasta_alvo)
        # ... (lógica de deleção que já criamos antes)

    elif acao == "2. Limpeza de Cache de Sistema":
        system_cleaner.limpar_pastas_temporarias()

    elif acao == "3. Gerenciar/Desinstalar Programas (Winget)":
        programas = program_manager.listar_programas_instalados()
        if programas:
            # Criamos as opções para o checkbox
            opcoes = [questionary.Choice(title=p['nome'], value=p['id']) for p in programas[:50]]
            
            selecionados = questionary.checkbox(
                "Marque os programas que deseja desinstalar (CUIDADO):",
                choices=opcoes
            ).ask()

            if selecionados:
                for app_id in selecionados:
                    program_manager.desinstalar_programa(app_id)
        else:
            print("❌ Nenhum programa mapeado.")

    elif acao == "4. Remover Bloatware Específico":
        app = questionary.text("ID do App (ex: cortana, maps):").ask()
        if app: system_cleaner.desinstalar_bloatware(app)

if __name__ == "__main__":
    iniciar_guardian_os()