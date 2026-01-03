from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_legacy_endpoint_usage_gate_smoke(tmp_path: Path):
    """
    Smoke test that the script runs and respects budget envs.
    Does not depend on repo truth file; uses a tiny test truth JSON.
    """
    truth = Path("scripts/governance/testdata_min_truth.json").resolve()
    assert truth.exists()

    env = dict(os.environ)
    env["ENDPOINT_TRUTH_FILE"] = str(truth)
    env["LEGACY_USAGE_BUDGET"] = "9999"
    env["LEGACY_SCAN_PATHS"] = "scripts/governance"  # only scan small folder

    p = subprocess.run(
        [sys.executable, "scripts/governance/check_legacy_endpoint_usage.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert p.returncode == 0, p.stdout
    assert "Legacy Endpoint Usage Gate" in p.stdout
