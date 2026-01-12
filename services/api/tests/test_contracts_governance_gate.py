"""
Pytest wrapper for contracts governance gate.

Runs the check_contracts_governance.py script and fails if any violations are found.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.unit
def test_contracts_governance_gate():
    """
    Contracts governance gate (Scenario B).

    Enforces:
      1) sha256 file format = single 64-hex line
      2) contract schema/hash changes require CHANGELOG.md update
      3) v1 contracts are immutable after public release
    """
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "ci" / "check_contracts_governance.py"

    if not script.exists():
        pytest.skip(f"Governance script not found: {script}")

    cmd = [
        sys.executable,
        str(script),
        "--repo-root",
        str(repo_root),
        "--base-ref",
        "origin/main",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode == 2:
        # Execution error (e.g., git not available) - skip in CI edge cases
        pytest.skip(f"Governance script execution error:\n{proc.stderr}")

    if proc.returncode != 0:
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        raise AssertionError(f"Contracts governance gate failed:\n{out}")
