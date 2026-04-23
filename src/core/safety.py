"""Safety primitives for destructive operations in GuardianOS."""

from __future__ import annotations

from enum import Enum
import ctypes


class ConfirmLiveExecution(Enum):
    """Sentinel token required to allow live destructive execution."""

    CONFIRMED = "confirmed"


def ensure_live_confirmation(
    dry_run: bool,
    confirm: ConfirmLiveExecution | None,
    operation_name: str,
) -> None:
    """Validate explicit confirmation token before live execution."""
    if not dry_run and confirm is not ConfirmLiveExecution.CONFIRMED:
        raise ValueError(
            f"{operation_name} requires confirm=ConfirmLiveExecution.CONFIRMED when dry_run=False."
        )


def is_running_as_admin() -> bool:
    """Return True if the current process has administrative privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_admin(required_for: str) -> None:
    """Fail fast when an admin-only operation is requested without elevation."""
    if not is_running_as_admin():
        raise PermissionError(
            f"{required_for} requires administrator privileges. "
            "Run GuardianOS from an elevated terminal."
        )

