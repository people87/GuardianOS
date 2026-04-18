"""
scanner.py — GuardianOS File Scanner
Otimizado para reduzir chamadas stat() e evitar criação excessiva de objetos Path.
"""
import os
import pathlib
from typing import List, Generator
from tqdm import tqdm

EXTENSION_VERDICTS: dict[str, str] = {
    ".ost": "🗑️ CACHE OUTLOOK",
    ".tmp": "🗑️ TEMPORÁRIO",
    ".exe": "💿 INSTALADOR",
    ".iso": "💿 IMAGEM DISCO",
    ".log": "📋 LOG",
}

def _walk_scandir(root: str) -> Generator[os.DirEntry, None, None]:
    """Usa scandir para obter metadados sem perambular pela árvore duas vezes."""
    try:
        with os.scandir(root) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    yield from _walk_scandir(entry.path)
                else:
                    yield entry
    except (PermissionError, OSError):
        pass

def localizar_arquivos_grandes(diretorio: str, tamanho_minimo_mb: float = 50.0) -> List[dict]:
    limiar_bytes = tamanho_minimo_mb * 1024 * 1024
    encontrados = []
    
    print(f"\n🔍 Iniciando Varredura Profunda em: {diretorio}")
    
    with tqdm(desc="Mapeando Arquivos", unit=" arq", dynamic_ncols=True) as pbar:
        for entry in _walk_scandir(diretorio):
            pbar.update(1)
            try:
                # Otimização: Acessa stat() diretamente do DirEntry
                f_size = entry.stat().st_size
                if f_size >= limiar_bytes:
                    ext = os.path.splitext(entry.name)[1].lower()
                    encontrados.append({
                        "caminho": pathlib.Path(entry.path),
                        "tamanho_mb": f_size / (1024**2),
                        "veredito": EXTENSION_VERDICTS.get(ext, "📄 ANALISAR")
                    })
            except (PermissionError, FileNotFoundError):
                continue

    encontrados.sort(key=lambda x: x["tamanho_mb"], reverse=True)
    return encontrados