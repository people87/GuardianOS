import os
import pathlib
from typing import List, Generator
from tqdm import tqdm

# Base de conhecimento para categorização inteligente
KNOWLEDGE_BASE = {
    "SISTEMA/DEV": {
        "ext": [".lib", ".dll", ".sys", ".exe", ".msi", ".pdb", ".pyc"],
        "risco": "🔴 ALTO",
        "desc": "Biblioteca ou executável. Essencial para o funcionamento de softwares."
    },
    "DADOS USUÁRIO": {
        "ext": [".psd", ".ai", ".pdf", ".csv", ".xlsx", ".jpg", ".png", ".mp4", ".zip", ".rar"],
        "risco": "🟡 MÉDIO",
        "desc": "Documento, mídia ou arquivo de projeto pessoal."
    },
    "CACHE/TEMP": {
        "ext": [".tmp", ".log", ".cache", ".body", ".bak", ".old", ".ost", ".tlog"],
        "risco": "🟢 BAIXO",
        "desc": "Dados temporários. Geralmente seguros para remover e recuperar espaço."
    }
}

def _get_contexto(caminho: pathlib.Path) -> dict:
    """Analisa o caminho e extensão para determinar a origem e o risco."""
    path_str = str(caminho).lower()
    ext = caminho.suffix.lower()
    nome = caminho.name.lower()
    
    # Regras de Heurística (Adivinhação Inteligente)
    if "google\\chrome" in path_str or "data_" in nome:
        return {"categoria": "CACHE", "risco": "🟢 BAIXO", "desc": "Cache do Chrome (Imagens/Sites).", "dono": "Google Chrome"}
    
    if "anaconda" in path_str or "pkgs\\cache" in path_str:
        return {"categoria": "CACHE", "risco": "🟢 BAIXO", "desc": "Cache de pacotes do Anaconda/Python.", "dono": "Anaconda"}

    if "adobe" in path_str or "photoshop" in path_str:
        return {"categoria": "SISTEMA", "risco": "🟡 MÉDIO", "desc": "Arquivos da Suite Adobe.", "dono": "Adobe Creative Cloud"}

    # Fallback para a base de conhecimento geral
    for cat, info in KNOWLEDGE_BASE.items():
        if ext in info["ext"]:
            return {"categoria": cat, "risco": info["risco"], "desc": info["desc"], "dono": "Desconhecido"}
            
    return {"categoria": "INCERTO", "risco": "⚪ INCERTO", "desc": "Natureza não identificada.", "dono": "Desconhecido"}

def _walk_scandir(root: str) -> Generator[os.DirEntry, None, None]:
    try:
        with os.scandir(root) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        yield from _walk_scandir(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        yield entry
                except PermissionError: continue
    except (PermissionError, OSError): pass

def localizar_arquivos_grandes(diretorio: str, tamanho_minimo_mb: float = 50.0) -> List[dict]:
    limiar_bytes = tamanho_minimo_mb * 1024 * 1024
    encontrados = []
    print(f"\n🔍 Analisando arquivos acima de {tamanho_minimo_mb}MB...")
    
    with tqdm(desc="Mapeando Contexto", unit=" arq", dynamic_ncols=True) as pbar:
        for entry in _walk_scandir(diretorio):
            pbar.update(1)
            try:
                f_size = entry.stat().st_size
                if f_size >= limiar_bytes:
                    path_obj = pathlib.Path(entry.path)
                    encontrados.append({
                        "caminho": path_obj,
                        "tamanho_mb": f_size / (1024**2),
                        "contexto": _get_contexto(path_obj)
                    })
            except: continue

    encontrados.sort(key=lambda x: x["tamanho_mb"], reverse=True)
    return encontrados