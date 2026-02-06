"""Smoke test for gold-run --dry-run mode."""
import sys
import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_out(tmp_path: Path) -> Path:
    return tmp_path / "exports"


def test_gold_run_dry_run_exits_zero(tmp_out):
    """gold-run --dry-run should exit 0 without capturing."""
    from tap_tone.cli.gold_run import main as gold_run_main

    rc = gold_run_main([
        "--specimen-id", "test_plate",
        "--device", "0",
        "--out-dir", str(tmp_out),
        "--dry-run",
    ])

    assert rc == 0


def test_gold_run_dry_run_json_output(tmp_out, capsys):
    """gold-run --dry-run --json should emit valid JSON."""
    from tap_tone.cli.gold_run import main as gold_run_main

    rc = gold_run_main([
        "--specimen-id", "test_plate",
        "--device", "0",
        "--out-dir", str(tmp_out),
        "--dry-run",
        "--json",
    ])

    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["schema_id"] == "tap_tone_gold_run_out_v1"
    assert data["specimen_id"] == "test_plate"
    assert data["points"] == ["A1", "A2", "A3"]


def test_gold_run_custom_points(tmp_out, capsys):
    """gold-run --points 5 should generate 5 point labels."""
    from tap_tone.cli.gold_run import main as gold_run_main

    rc = gold_run_main([
        "--specimen-id", "5pt_test",
        "--device", "0",
        "--out-dir", str(tmp_out),
        "--points", "5",
        "--dry-run",
        "--json",
    ])

    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["points"] == ["A1", "A2", "A3", "A4", "A5"]
