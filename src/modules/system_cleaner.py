import os
import shutil
import subprocess
import logging
from pathlib import Path
from tqdm import tqdm
from core.logger import write_audit_event
from core.safety import ConfirmLiveExecution, ensure_live_confirmation, ensure_admin

logger = logging.getLogger("guardianOS")

def matar_processos_travantes():
    """Finaliza processos conhecidos por travar arquivos de cache."""
    print("🎯 Finalizando processos que bloqueiam a limpeza (Chrome, Adobe, etc)...")
    processos = ["chrome", "msedge", "Adobe*", "CCXProcess*", "AGMService*"]
    for p in processos:
        subprocess.run(["powershell", "-Command", f'taskkill /F /IM "{p}" /T'], capture_output=True)

def _deletar_item_calculando(caminho: Path) -> tuple[int, list[str]]:
    """Delete one file/folder and return freed bytes plus explicit errors."""
    bytes_liberados = 0
    errors: list[str] = []

    if caminho.is_file() or caminho.is_symlink():
        try:
            bytes_liberados = caminho.stat().st_size
        except Exception as ex:
            errors.append(f"Could not read size for {caminho}: {ex}")
        try:
            caminho.unlink()
        except Exception as ex:
            errors.append(f"Could not delete file/symlink {caminho}: {ex}")
        return bytes_liberados, errors

    if caminho.is_dir():
        for root, dirs, files in os.walk(caminho, topdown=False):
            for name in files:
                p = os.path.join(root, name)
                try:
                    bytes_liberados += os.path.getsize(p)
                except Exception as ex:
                    errors.append(f"Could not read size for {p}: {ex}")
                try:
                    os.remove(p)
                except Exception as ex:
                    errors.append(f"Could not remove file {p}: {ex}")
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.rmdir(dir_path)
                except Exception as ex:
                    errors.append(f"Could not remove directory {dir_path}: {ex}")
        try:
            os.rmdir(caminho)
        except Exception as ex:
            errors.append(f"Could not remove directory {caminho}: {ex}")

    return bytes_liberados, errors

def limpar_pastas_temporarias(
    dry_run: bool = True,
    confirm: ConfirmLiveExecution | None = None,
):
    """Clean temporary folders with dry-run-first safety gates and audit events."""
    # ROLLBACK: File deletions are irreversible. We log target paths and status events to audit log.
    # If an item is deleted in live mode, recovery depends on backup/restore tools outside GuardianOS.
    ensure_live_confirmation(dry_run, confirm, "limpar_pastas_temporarias")
    if not dry_run:
        ensure_admin("Temp cleanup live execution")

    targets = [Path(os.environ.get("TEMP", "C:/Temp")), Path("C:/Windows/Temp"), Path("C:/Windows/Prefetch")]
    total_bytes = 0
    total_items_scanned = 0
    total_items_failed = 0
    execution_errors: list[str] = []
    
    if not dry_run:
        matar_processos_travantes()

    print("\n🧹 Executando Limpeza...")
    for target in targets:
        if not target.exists():
            continue
        itens = list(target.glob("*"))
        total_items_scanned += len(itens)
        for item in tqdm(itens, desc=f"Limpando {target.name}", leave=False):
            write_audit_event(
                operation="temp_cleanup",
                target=str(item),
                dry_run=dry_run,
                status="pending",
                detail="Item queued for temp cleanup.",
            )
            if dry_run:
                if item.is_file():
                    total_bytes += item.stat().st_size
                write_audit_event(
                    operation="temp_cleanup",
                    target=str(item),
                    dry_run=True,
                    status="success",
                    detail="Dry run only. No file system changes applied.",
                )
            else:
                try:
                    bytes_liberados, item_errors = _deletar_item_calculando(item)
                    total_bytes += bytes_liberados
                    if item_errors:
                        total_items_failed += 1
                        execution_errors.extend(item_errors)
                        write_audit_event(
                            operation="temp_cleanup",
                            target=str(item),
                            dry_run=False,
                            status="failed",
                            detail="Item cleanup completed with partial failures.",
                            extra={"errors": item_errors},
                        )
                        continue
                    write_audit_event(
                        operation="temp_cleanup",
                        target=str(item),
                        dry_run=False,
                        status="success",
                        detail="Item cleanup attempt completed in live mode.",
                    )
                except Exception as ex:
                    total_items_failed += 1
                    execution_errors.append(str(ex))
                    write_audit_event(
                        operation="temp_cleanup",
                        target=str(item),
                        dry_run=False,
                        status="failed",
                        detail="Item cleanup failed in live mode.",
                        extra={"error": str(ex)},
                    )
            
    print(f"✅ Concluído. Liberado: {total_bytes / (1024**2):.2f} MB")
    report = {
        "operation": "temp_cleanup",
        "dry_run": dry_run,
        "status": "success" if total_items_failed == 0 else "failed",
        "items_scanned": total_items_scanned,
        "items_failed": total_items_failed,
        "bytes_freed": total_bytes,
        "errors": execution_errors,
    }
    return report

def desinstalar_bloatware_em_lote(lista_apps: list, dry_run: bool = False):
    print(f"\n🚀 Removendo {len(lista_apps)} alvos de bloatware...")
    for app in lista_apps:
        if dry_run:
            print(f"🔍 [DRY RUN] Seria removido: {app}")
            continue
        cmd = f'Get-AppxPackage *{app}* | Remove-AppxPackage'
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)
        print(f"  ✅ Tentativa concluída: {app}")