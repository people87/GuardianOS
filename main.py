import os
import scanner
import system_cleaner
import questionary 

def iniciar_guardian_os():
    print("="*60)
    print("           GUARDIAN OS - MÓDULO INTERATIVO           ")
    print("="*60)

    # Nova pergunta inicial
    acao = questionary.select(
        "O que deseja fazer hoje?",
        choices=[
            "1. Scan de Arquivos Grandes (Limpeza Manual)",
            "2. Limpeza de Sistema (Temp/Prefetch)",
            "3. Remover Bloatware do Windows",
            "Sair"
        ]
    ).ask()

    if acao == "1. Scan de Arquivos Grandes (Limpeza Manual)":
        pasta_alvo = os.path.expanduser("~")
        
        # 1. Roda o scanner
        arquivos_encontrados = scanner.localizar_arquivos_grandes(pasta_alvo, tamanho_minimo_mb=50)
        
        if not arquivos_encontrados:
            print("\n✅ Nada de pesado encontrado. Sistema otimizado!")
            return

        # 2. Prepara o menu interativo
        opcoes_menu = []
        for item in arquivos_encontrados[:15]: 
            texto_exibicao = f"{item['caminho'].name} ({item['tamanho']:.2f} MB)"
            opcoes_menu.append(questionary.Choice(title=texto_exibicao, value=item['caminho']))

        print("\n" + "="*60)
        
        # 3. Desenha a Interface na Tela
        arquivos_selecionados = questionary.checkbox(
            "Selecione os arquivos para APAGAR (Espaço = Marcar | Setas = Navegar | Enter = Confirmar):",
            choices=opcoes_menu,
            style=questionary.Style([
                ('qmark', 'fg:#ff9d00 bold'),       
                ('question', 'bold'),               
                ('selected', 'fg:#00ff00 bold'),    
                ('pointer', 'fg:#00ff00 bold'),     
            ])
        ).ask()

        # 4. A Execução
        if arquivos_selecionados:
            print("\n⚙️ Iniciando protocolo de limpeza...")
            espaco_liberado = 0
            
            for caminho in arquivos_selecionados:
                try:
                    tamanho = caminho.stat().st_size / (1024 * 1024)
                    os.remove(caminho) 
                    espaco_liberado += tamanho
                    print(f"🗑️ Deletado: {caminho.name}")
                except Exception as e:
                    print(f"❌ O Windows bloqueou a exclusão de {caminho.name}: {e}")
                    
            print(f"\n🎉 SUCESSO! Você recuperou {espaco_liberado:.2f} MB de espaço livre.")
        else:
            print("\n⏭️ Nenhum arquivo selecionado. Operação cancelada.")
        
    elif acao == "2. Limpeza de Sistema (Temp/Prefetch)":
        system_cleaner.limpar_pastas_temporarias()

    elif acao == "3. Remover Bloatware do Windows":
        app = questionary.text("Qual app deseja remover? (ex: cortana, maps, weather):").ask()
        if app:
            system_cleaner.desinstalar_bloatware(app)

if __name__ == "__main__":
    iniciar_guardian_os()