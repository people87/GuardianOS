import os
import pathlib
from tqdm import tqdm

def localizar_arquivos_grandes(diretorio, tamanho_minimo_mb=50):
    print(f"\n--- [ GuardianOS: Scanner Ativado ] ---")
    caminho_base = pathlib.Path(diretorio)
    
    # Lista para guardar o que encontrarmos
    encontrados = []
    
    # Coleta rápida de arquivos (ignora pastas do sistema inacessíveis)
    print("Mapeando arquivos na sua pasta de usuário...")
    arquivos_lista = []
    
    # Usamos o os.walk porque ele é mais estável para evitar travamentos de permissão
    for raiz, pastas, arquivos in os.walk(diretorio):
        for nome in arquivos:
            arquivos_lista.append(os.path.join(raiz, nome))

    total = len(arquivos_lista)
    
    # Barra de Progresso
    with tqdm(total=total, desc="Progresso", unit="arq", colour='blue') as pbar:
        for caminho_completo in arquivos_lista:
            try:
                arquivo = pathlib.Path(caminho_completo)
                if arquivo.is_file():
                    tamanho = arquivo.stat().st_size / (1024 * 1024)
                    if tamanho > tamanho_minimo_mb:
                        encontrados.append({
                            'caminho': arquivo,
                            'tamanho': tamanho,
                            'extensao': arquivo.suffix.lower()
                        })
            except:
                pass # Ignora silenciosamente arquivos que o Windows bloqueou
            pbar.update(1)

    # Ordenação
    encontrados.sort(key=lambda x: x['tamanho'], reverse=True)
    
    print(f"\n{'ARQUIVO':<50} | {'TAMANHO':<10} | {'VEREDITO'}")
    print("-" * 85)
    
    for item in encontrados[:15]:
        ext = item['extensao']
        veredito = "⚠️ ANALISAR"
        if ext == '.ost': veredito = "🗑️ CACHE OUTLOOK (ANTIGO)"
        elif ext == '.psd': veredito = "📸 PHOTOSHOP (OPCIONAL)"
        elif ext in ['.exe', '.msi']: veredito = "💿 INSTALADOR (LIMPAR)"
        
        nome = item['caminho'].name[:47]
        print(f"{nome:<50} | {item['tamanho']:>7.2f} MB | {veredito}")
        
    return encontrados

if __name__ == "__main__":
    # Focando apenas na sua pasta de usuário para evitar erros de sistema
    pasta_alvo = os.path.expanduser("~")
    localizar_arquivos_grandes(pasta_alvo)