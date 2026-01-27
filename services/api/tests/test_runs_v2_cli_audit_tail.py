"""
Tests for RMOS runs_v2 CLI audit tail command.

H3.6.3: Incident response utility.

Run:
  cd services/api
  pytest tests/test_runs_v2_cli_audit_tail.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _get_subprocess_env(runs_dir: Path) -> dict:
    """Get environment dict for subprocess with RMOS_RUNS_DIR set."""
    env = os.environ.copy()
    env["RMOS_RUNS_DIR"] = str(runs_dir)
    return env


@pytest.fixture
def audit_setup(tmp_path, monkeypatch):
    """Set up a temporary RMOS runs directory with audit log."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    # Create audit directory and log
    audit_dir = runs_dir / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    audit_log = audit_dir / "deletes.jsonl"

    # Write some sample audit lines
    events = [
        {
            "ts_utc": "2025-12-23T10:00:00Z",
            "run_id": "run_test_001",
            "mode": "soft",
            "reason": "Test delete 1",
            "actor": "user1",
            "index_updated": True,
            "artifact_deleted": False,
            "attachments_deleted": 0,
            "errors": None,
        },
        {
            "ts_utc": "2025-12-23T10:01:00Z",
            "run_id": "run_test_002",
            "mode": "hard",
            "reason": "Test delete 2",
            "actor": "user2",
            "index_updated": True,
            "artifact_deleted": True,
            "attachments_deleted": 2,
            "errors": None,
        },
        {
            "ts_utc": "2025-12-23T10:02:00Z",
            "run_id": "run_test_003",
            "mode": "hard",
            "reason": "Cleanup old runs",
            "actor": "admin",
            "index_updated": True,
            "artifact_deleted": True,
            "attachments_deleted": 0,
            "errors": None,
        },
    ]

    with open(audit_log, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))

    return {
        "runs_dir": runs_dir,
        "audit_log": audit_log,
        "events": events,
    }


def test_cli_audit_tail_exits_zero(audit_setup):
    """CLI audit tail command exits with code 0."""
    # Call main() directly to avoid subprocess startup overhead,
    # which can timeout under full-suite load.
    from app.rmos.runs_v2.cli_audit import main

    rc = main(["tail", "--lines", "5"])
    assert rc == 0


def test_cli_audit_tail_shows_lines(audit_setup):
    """CLI audit tail shows the expected number of lines."""
    runs_dir = audit_setup["runs_dir"]

    result = subprocess.run(
        [
            sys.executable,
            "-m", "app.rmos.runs_v2.cli_audit",
            "tail",
            "--lines", "2",
        ],
        cwd=str(Path(__file__).parent.parent),
        env=_get_subprocess_env(runs_dir),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0

    lines = result.stdout.strip().split("\n")
    assert len(lines) == 2

    # Should show last 2 events
    last_event = json.loads(lines[-1])
    assert last_event["run_id"] == "run_test_003"


def test_cli_audit_tail_empty_log(tmp_path):
    """CLI audit tail handles empty/missing log gracefully."""
    runs_dir = tmp_path / "rmos_runs_empty"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m", "app.rmos.runs_v2.cli_audit",
            "tail",
            "--lines", "10",
        ],
        cwd=str(Path(__file__).parent.parent),
        env=_get_subprocess_env(runs_dir),
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Should exit 0 even with no log file
    assert result.returncode == 0
    # Output should be empty
    assert result.stdout.strip() == ""


def test_cli_module_resolves(audit_setup):
    """Module can be imported without errors."""
    runs_dir = audit_setup["runs_dir"]

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.rmos.runs_v2.cli_audit import main; print('OK')",
        ],
        cwd=str(Path(__file__).parent.parent),
        env=_get_subprocess_env(runs_dir),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "OK" in result.stdout


def test_cli_audit_help(tmp_path):
    """CLI audit --help works."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m", "app.rmos.runs_v2.cli_audit",
            "tail",
            "--help",
        ],
        cwd=str(Path(__file__).parent.parent),
        env=_get_subprocess_env(runs_dir),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "--lines" in result.stdout
    assert "--follow" in result.stdout
