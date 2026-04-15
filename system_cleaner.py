import os
import shutil
import subprocess
from pathlib import Path

def limpar_pastas_temporarias():
    """Limpa as pastas de cache e arquivos temporários do usuário e do sistema."""
    pastas_alvo = [
        Path(os.environ.get('TEMP', '')),           # %TEMP% do usuário
        Path("C:/Windows/Temp"),                    # Temp do Sistema
        Path("C:/Windows/Prefetch")                 # Cache de inicialização de apps
    ]
    
    print("\n🧹 Iniciando limpeza de arquivos temporários...")
    total_removido = 0
    
    for pasta in pastas_alvo:
        if not pasta.exists():
            continue
            
        print(f"Verificando: {pasta}")
        for item in pasta.glob('*'):
            try:
                tamanho = 0
                if item.is_file() or item.is_symlink():
                    tamanho = item.stat().st_size
                    item.unlink() # Deleta arquivo
                elif item.is_dir():
                    # Calcula tamanho da pasta antes de apagar
                    tamanho = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                    shutil.rmtree(item) # Deleta pasta
                
                total_removido += tamanho
            except Exception:
                # O Windows bloqueia arquivos que estão sendo usados no momento
                continue
                
    print(f"✅ Limpeza concluída! Espaço recuperado: {total_removido / (1024*1024):.2f} MB")

def desinstalar_bloatware(app_nome):
    """Remove aplicativos nativos do Windows via PowerShell."""
    print(f"🚀 Tentando remover: {app_nome}...")
    # Comando PowerShell para remover pacotes Appx
    comando = f'Get-AppxPackage *{app_nome}* | Remove-AppxPackage'
    
    try:
        resultado = subprocess.run(["powershell", "-Command", comando], capture_output=True, text=True)
        if resultado.returncode == 0:
            print(f"✅ {app_nome} removido com sucesso!")
        else:
            print(f"⚠️ Não foi possível remover {app_nome} (Pode já ter sido removido).")
    except Exception as e:
        print(f"❌ Erro ao executar comando: {e}")