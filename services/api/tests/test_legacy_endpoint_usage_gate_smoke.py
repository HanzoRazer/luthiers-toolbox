from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_legacy_endpoint_usage_gate_smoke(tmp_path: Path):
    """
    Smoke test that the script runs and respects budget envs.
    Runs from repo root; skips if script/truth not found (e.g. tests run from services/api).
    """
    # Resolve from repo root (parent of services/)
    repo_root = Path(__file__).resolve().parent.parent.parent
    truth = repo_root / "scripts" / "governance" / "testdata_min_truth.json"
    script = repo_root / "scripts" / "governance" / "check_legacy_endpoint_usage.py"
    if not truth.exists() or not script.exists():
        pytest.skip(
            "scripts/governance or testdata_min_truth.json not found (run from repo root)"
        )

    env = dict(os.environ)
    env["ENDPOINT_TRUTH_FILE"] = str(truth)
    env["LEGACY_USAGE_BUDGET"] = "9999"
    env["LEGACY_SCAN_PATHS"] = str(repo_root / "scripts" / "governance")

    p = subprocess.run(
        [sys.executable, str(script)],
        env=env,
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert p.returncode == 0, p.stdout
    assert "Legacy Endpoint Usage Gate" in p.stdout
