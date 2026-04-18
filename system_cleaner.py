"""
system_cleaner.py — GuardianOS System Cleaner (Testable Version)
"""
import os
import shutil
import subprocess
import logging
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger("guardianOS")

def _get_temp_targets() -> list[Path]:
    """Default system paths."""
    return [
        Path(os.environ.get("TEMP", "C:/Temp")),
        Path("C:/Windows/Temp"),
        Path("C:/Windows/Prefetch")
    ]

def _deletar_item_calculando(caminho: Path) -> int:
    bytes_liberados = 0
    try:
        if caminho.is_file() or caminho.is_symlink():
            bytes_liberados = caminho.stat().st_size
            caminho.unlink()
        elif caminho.is_dir():
            for root, dirs, files in os.walk(caminho, topdown=False):
                for name in files:
                    p = os.path.join(root, name)
                    try:
                        bytes_liberados += os.path.getsize(p)
                        os.remove(p)
                    except: pass
                for name in dirs:
                    try: os.rmdir(os.path.join(root, name))
                    except: pass
            os.rmdir(caminho)
    except Exception:
        pass
    return bytes_liberados

def limpar_pastas_temporarias(dry_run: bool = False, targets: list[Path] = None):
    """
    targets: Permite injetar pastas de teste (Dependency Injection).
    """
    # Se targets for None, usa os padrões do sistema. Caso contrário, usa os fornecidos.
    pastas_alvo = targets if targets is not None else _get_temp_targets()
    total_bytes = 0
    
    if dry_run:
        print(f"\n🔍 [DRY RUN] Simulando limpeza em {len(pastas_alvo)} locais...")
        for t in pastas_alvo:
            if t.exists():
                # Rápido cálculo de tamanho para simulação
                size = sum(f.stat().st_size for f in t.glob('**/*') if f.is_file())
                total_bytes += size
        print(f"Espaço recuperável: {total_bytes / (1024**2):.2f} MB")
        return total_bytes

    print(f"\n🧹 Executando Limpeza em {len(pastas_alvo)} locais...")
    for target in pastas_alvo:
        if not target.exists(): continue
        itens = list(target.glob("*"))
        for item in tqdm(itens, desc=f"Limpando {target.name[:20]}", leave=False):
            total_bytes += _deletar_item_calculando(item)
            
    print(f"✅ Sucesso. Liberado: {total_bytes / (1024**2):.2f} MB")
    return total_bytes

def desinstalar_bloatware(app_nome: str, dry_run: bool = False):
    sanitizado = "".join(c for c in app_nome if c.isalnum() or c in "*-")
    cmd = f"Get-AppxPackage *{sanitizado}* | Remove-AppxPackage"
    if dry_run: cmd = f"Get-AppxPackage *{sanitizado}* | Select-Object Name"
    
    try:
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=45)
    except Exception as e:
        print(f"❌ Erro PowerShell: {e}")