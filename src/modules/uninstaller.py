from __future__ import annotations

import subprocess
import shutil
import os
from pathlib import Path
from typing import Any
from core.logger import write_audit_event
from core.safety import ConfirmLiveExecution, ensure_live_confirmation, ensure_admin

try:
    import winreg
except ImportError:  # pragma: no cover - only relevant outside Windows
    winreg = None  # type: ignore[assignment]


def _scan_leftover_folders(app_nome: str) -> list[str]:
    """Scan common locations and return matching leftover folder paths."""
    leftovers: list[str] = []
    search_roots = [
        Path(os.environ.get("APPDATA", "")),
        Path(os.environ.get("LOCALAPPDATA", "")),
        Path("C:/ProgramData"),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
    ]
    for root in search_roots:
        if not root.exists():
            continue
        for candidate in root.glob(f"*{app_nome}*"):
            if candidate.is_dir():
                leftovers.append(str(candidate))
    return sorted(set(leftovers))


def _build_leftover_report(app_nome: str) -> dict:
    """Build a categorized leftover report before any removal actions."""
    folder_paths = _scan_leftover_folders(app_nome)
    registry_keys = _scan_registry_leftovers(app_nome)
    return {
        "folders": folder_paths,
        "registry_keys": registry_keys,
        "scheduled_tasks": [],
        "startup_entries": [],
    }


def _scan_registry_leftovers(app_nome: str) -> list[dict[str, str]]:
    """Scan uninstall registry hives and return entries matching app name."""
    if winreg is None:
        return []

    normalized_name = app_nome.lower().strip()
    if not normalized_name:
        return []

    matches: list[dict[str, str]] = []
    uninstall_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for hive, base_path in uninstall_paths:
        try:
            with winreg.OpenKey(hive, base_path) as base_key:
                subkey_count, _, _ = winreg.QueryInfoKey(base_key)
                for i in range(subkey_count):
                    try:
                        subkey_name = winreg.EnumKey(base_key, i)
                        subkey_path = f"{base_path}\\{subkey_name}"
                        with winreg.OpenKey(hive, subkey_path) as app_key:
                            display_name = _safe_query_reg_value(app_key, "DisplayName")
                            publisher = _safe_query_reg_value(app_key, "Publisher")
                            uninstall_string = _safe_query_reg_value(app_key, "UninstallString")
                            searchable = f"{display_name} {publisher}".lower()
                            if normalized_name in searchable:
                                matches.append(
                                    {
                                        "hive": _hive_to_str(hive),
                                        "key_path": subkey_path,
                                        "display_name": display_name,
                                        "publisher": publisher,
                                        "uninstall_string": uninstall_string,
                                    }
                                )
                    except OSError:
                        continue
        except OSError:
            continue

    return matches


def _safe_query_reg_value(key: Any, value_name: str) -> str:
    """Read one registry value and return empty string when unavailable."""
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        return str(value)
    except OSError:
        return ""


def _hive_to_str(hive: Any) -> str:
    """Return a readable label for known registry hives."""
    if winreg is None:
        return "UNKNOWN"
    if hive == winreg.HKEY_LOCAL_MACHINE:
        return "HKLM"
    if hive == winreg.HKEY_CURRENT_USER:
        return "HKCU"
    return "UNKNOWN"


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
        "leftover_report": {},
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

    # 2. Leftover report (always generated before any cleanup action).
    print("🔍 Building leftover report...")
    leftover_report = _build_leftover_report(app_nome)
    report["leftover_report"] = leftover_report
    report["leftovers_found"] = len(leftover_report["folders"])

    print("📄 Leftover report:")
    print(f"   - folders: {len(leftover_report['folders'])}")
    print(f"   - registry_keys: {len(leftover_report['registry_keys'])}")
    print(f"   - scheduled_tasks: {len(leftover_report['scheduled_tasks'])} (v1 pending)")
    print(f"   - startup_entries: {len(leftover_report['startup_entries'])} (v1 pending)")

    for folder in leftover_report["folders"]:
        write_audit_event(
            operation="leftover_folder_cleanup",
            target=folder,
            dry_run=dry_run,
            status="pending",
            detail="Residual folder identified during deep uninstall scan.",
        )
        if dry_run:
            print(f"🔍 [DRY RUN] Residual folder detected: {folder}")
            write_audit_event(
                operation="leftover_folder_cleanup",
                target=folder,
                dry_run=True,
                status="success",
                detail="Dry run only. Residual folder was not removed.",
            )
            continue

        confirmar = input(f"   ❓ Residual folder found: {folder}. Delete it? (y/n): ")
        if confirmar.lower() == "y":
            try:
                shutil.rmtree(folder)
                report["leftovers_removed"] += 1
                print(f"   ✅ Removed: {Path(folder).name}")
                write_audit_event(
                    operation="leftover_folder_cleanup",
                    target=folder,
                    dry_run=False,
                    status="success",
                    detail="Residual folder removed successfully.",
                )
            except Exception as ex:
                report["leftovers_failed"] += 1
                report["errors"].append(f"Failed to remove {folder}: {str(ex)}")
                print(f"   ❌ Could not remove {Path(folder).name} (likely in use).")
                write_audit_event(
                    operation="leftover_folder_cleanup",
                    target=folder,
                    dry_run=False,
                    status="failed",
                    detail="Residual folder removal failed.",
                    extra={"error": str(ex)},
                )
    report["status"] = "success" if not report["errors"] else "failed"
    return report