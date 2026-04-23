"""Structured audit logging for safety-critical GuardianOS operations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any


DEFAULT_AUDIT_LOG = Path("logs/audit.log.jsonl")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_audit_event(
    *,
    operation: str,
    target: str,
    dry_run: bool,
    status: str,
    detail: str,
    audit_log_path: Path = DEFAULT_AUDIT_LOG,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one structured event to the audit log file."""
    payload: dict[str, Any] = {
        "timestamp": _iso_now(),
        "operation": operation,
        "target": target,
        "dry_run": dry_run,
        "status": status,
        "detail": detail,
    }
    if extra:
        payload.update(extra)

    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")

    return payload

