"""Tests for uninstaller leftover report and safety gates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from core.safety import ConfirmLiveExecution
from modules import uninstaller


def test_build_leftover_report_has_expected_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Leftover report must expose all categories even when empty."""
    monkeypatch.setattr(uninstaller, "_scan_leftover_folders", lambda _: ["C:/Program Files/DemoApp"])
    monkeypatch.setattr(uninstaller, "_scan_registry_leftovers", lambda _: [{"hive": "HKLM"}])

    report = uninstaller._build_leftover_report("DemoApp")

    assert set(report.keys()) == {"folders", "registry_keys", "scheduled_tasks", "startup_entries"}
    assert report["folders"] == ["C:/Program Files/DemoApp"]
    assert report["registry_keys"] == [{"hive": "HKLM"}]
    assert report["scheduled_tasks"] == []
    assert report["startup_entries"] == []


def test_deep_uninstall_requires_explicit_live_confirmation() -> None:
    """Live mode must fail unless confirmation sentinel is provided."""
    with pytest.raises(ValueError):
        uninstaller.desinstalacao_profunda(
            "demo.app",
            "DemoApp",
            dry_run=False,
            confirm=None,
        )


def test_deep_uninstall_dry_run_reports_leftovers_without_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dry run should report leftovers without attempting folder deletion."""
    # Stub subprocess uninstall execution path and audit logger side effects.
    monkeypatch.setattr(uninstaller, "write_audit_event", lambda **_: {})
    monkeypatch.setattr(uninstaller, "_build_leftover_report", lambda _: {
        "folders": ["C:/Program Files/DemoApp"],
        "registry_keys": [{"hive": "HKLM", "key_path": "SOFTWARE\\DemoApp"}],
        "scheduled_tasks": [],
        "startup_entries": [],
    })

    def _fail_if_delete_called(_: str) -> None:
        raise AssertionError("shutil.rmtree should not be called in dry run mode")

    monkeypatch.setattr(uninstaller.shutil, "rmtree", _fail_if_delete_called)

    report = uninstaller.desinstalacao_profunda(
        "demo.app",
        "DemoApp",
        dry_run=True,
        confirm=None,
    )

    assert report["dry_run"] is True
    assert report["winget_status"] == "dry_run"
    assert report["leftovers_found"] == 1
    assert report["leftovers_removed"] == 0
    assert report["leftovers_failed"] == 0
    assert report["leftover_report"]["registry_keys"][0]["hive"] == "HKLM"


def test_live_mode_accepts_confirmation_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live mode should execute when explicit confirmation sentinel is passed."""
    monkeypatch.setattr(uninstaller, "ensure_admin", lambda *_: None)
    monkeypatch.setattr(uninstaller, "write_audit_event", lambda **_: {})
    monkeypatch.setattr(uninstaller, "_build_leftover_report", lambda _: {
        "folders": [],
        "registry_keys": [],
        "scheduled_tasks": [],
        "startup_entries": [],
    })

    class _Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr(uninstaller.subprocess, "run", lambda *_, **__: _Result())

    report = uninstaller.desinstalacao_profunda(
        "demo.app",
        "DemoApp",
        dry_run=False,
        confirm=ConfirmLiveExecution.CONFIRMED,
    )

    assert report["dry_run"] is False
    assert report["winget_status"] == "success"

