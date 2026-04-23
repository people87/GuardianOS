import subprocess
import shutil
import os
from pathlib import Path
from core.logger import write_audit_event
from core.safety import ConfirmLiveExecution, ensure_live_confirmation, ensure_admin

def desinstalacao_profunda(
    app_id: str,
    app_nome: str,
    dry_run: bool = True,
    confirm: ConfirmLiveExecution | None = None,
):
    """Run deep uninstall flow with dry-run-first safety and audit logging."""
    # ROLLBACK: Uninstall and folder deletion may be partially reversible depending on vendor installer.
    # We record pending/success/failed events for each step. Full restoration may require reinstall/backup.
    ensure_live_confirmation(dry_run, confirm, "desinstalacao_profunda")
    if not dry_run:
        ensure_admin("Deep uninstall live execution")

    report = {
        "operation": "deep_uninstall",
        "dry_run": dry_run,
        "app_id": app_id,
        "app_name": app_nome,
        "winget_status": "not_started",
        "leftovers_found": 0,
        "leftovers_removed": 0,
        "leftovers_failed": 0,
        "errors": [],
    }

    print(f"\n🚀 Iniciando desinstalação profunda de: {app_nome}")
    
    # 1. Desinstalação via Winget
    print("📦 Executando desinstalador oficial...")
    write_audit_event(
        operation="winget_uninstall",
        target=app_id,
        dry_run=dry_run,
        status="pending",
        detail=f"Deep uninstall requested for {app_nome}.",
    )
    if dry_run:
        print(f"🔍 [DRY RUN] Would execute: winget uninstall --id {app_id} --silent")
        report["winget_status"] = "dry_run"
        write_audit_event(
            operation="winget_uninstall",
            target=app_id,
            dry_run=True,
            status="success",
            detail="Dry run only. Winget uninstall not executed.",
        )
    else:
        result = subprocess.run(
            ["winget", "uninstall", "--id", app_id, "--silent"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            report["winget_status"] = "success"
            write_audit_event(
                operation="winget_uninstall",
                target=app_id,
                dry_run=False,
                status="success",
                detail="Winget uninstall completed successfully.",
                extra={"stdout": result.stdout.strip()},
            )
        else:
            report["winget_status"] = "failed"
            report["errors"].append(
                f"Winget uninstall failed with code {result.returncode}: {result.stderr.strip()}"
            )
            write_audit_event(
                operation="winget_uninstall",
                target=app_id,
                dry_run=False,
                status="failed",
                detail="Winget uninstall returned non-zero exit code.",
                extra={"stderr": result.stderr.strip(), "returncode": result.returncode},
            )
            print("❌ Official uninstaller failed. Check logs/audit.log.jsonl for details.")

    # 2. Caça a resíduos (AppData e ProgramFiles)
    print("🔍 Procurando por arquivos residuais...")
    locais_busca = [
        Path(os.environ.get("APPDATA", "")),
        Path(os.environ.get("LOCALAPPDATA", "")),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)")
    ]
    
    for local in locais_busca:
        if not local.exists():
            continue
        # Tenta achar pastas com o nome do app
        for pasta in local.glob(f"*{app_nome}*"):
            if pasta.is_dir():
                report["leftovers_found"] += 1
                write_audit_event(
                    operation="leftover_folder_cleanup",
                    target=str(pasta),
                    dry_run=dry_run,
                    status="pending",
                    detail="Residual folder identified during deep uninstall scan.",
                )
                if dry_run:
                    print(f"🔍 [DRY RUN] Residual folder detected: {pasta}")
                    write_audit_event(
                        operation="leftover_folder_cleanup",
                        target=str(pasta),
                        dry_run=True,
                        status="success",
                        detail="Dry run only. Residual folder was not removed.",
                    )
                    continue

                confirmar = input(f"   ❓ Residual folder found: {pasta}. Delete it? (y/n): ")
                if confirmar.lower() == 'y':
                    try:
                        shutil.rmtree(pasta)
                        report["leftovers_removed"] += 1
                        print(f"   ✅ Removed: {pasta.name}")
                        write_audit_event(
                            operation="leftover_folder_cleanup",
                            target=str(pasta),
                            dry_run=False,
                            status="success",
                            detail="Residual folder removed successfully.",
                        )
                    except Exception as ex:
                        report["leftovers_failed"] += 1
                        report["errors"].append(f"Failed to remove {pasta}: {str(ex)}")
                        print(f"   ❌ Could not remove {pasta.name} (likely in use).")
                        write_audit_event(
                            operation="leftover_folder_cleanup",
                            target=str(pasta),
                            dry_run=False,
                            status="failed",
                            detail="Residual folder removal failed.",
                            extra={"error": str(ex)},
                        )
    report["status"] = "success" if not report["errors"] else "failed"
    return report