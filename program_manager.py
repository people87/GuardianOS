import subprocess
import questionary

def listar_programas_instalados():
    """Chama o winget para listar programas e processa o output."""
    print("\n🔍 Mapeando programas instalados... (Isso pode levar alguns segundos)")
    
    try:
        # Executa o winget list
        resultado = subprocess.run(
            ["winget", "list", "--accept-source-agreements"], 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        
        linhas = resultado.stdout.split('\n')
        programas = []

        # O Winget retorna uma tabela. Vamos pular o cabeçalho (2 primeiras linhas)
        for linha in linhas[2:]:
            if len(linha.strip()) > 0:
                # Tentativa simples de capturar Nome e ID (as duas primeiras colunas)
                partes = [p.strip() for p in linha.split('  ') if p.strip()]
                if len(partes) >= 2:
                    nome = partes[0]
                    app_id = partes[1]
                    programas.append({"nome": nome, "id": app_id})
        
        return programas
    except Exception as e:
        print(f"❌ Erro ao listar programas: {e}")
        return []

def desinstalar_programa(app_id):
    """Executa a desinstalação via Winget."""
    print(f"⚙️ Desinstalando {app_id}...")
    try:
        # --silent tenta rodar sem abrir janelas extras
        processo = subprocess.run(
            ["winget", "uninstall", "--id", app_id, "--silent"],
            capture_output=True,
            text=True
        )
        if processo.returncode == 0:
            print(f"✅ Sucesso ao remover {app_id}!")
        else:
            print(f"⚠️ Falha ou cancelado pelo sistema: {app_id}")
    except Exception as e:
        print(f"❌ Erro na execução: {e}")