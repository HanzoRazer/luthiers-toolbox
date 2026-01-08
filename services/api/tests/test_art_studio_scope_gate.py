"""
Art Studio Scope Gate - Pytest Wrapper

Ensures Art Studio code respects architectural boundaries.
Fails if ornament-only code attempts to define host geometry,
create manufacturing authority, or bypass RMOS governance.
"""

import subprocess
import sys
from pathlib import Path


def test_art_studio_scope_gate_v1():
    """
    Run Art Studio scope gate as blocking test.
    
    This enforces:
    - No host geometry (headstock, bridge, neck, body)
    - No CAM/machine output authority
    - No RMOS governance bypass
    """
    repo_root = Path(__file__).resolve().parents[3]  # services/api/tests/ -> repo
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "ci" / "check_art_studio_scope.py"),
        "--repo-root",
        str(repo_root),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        raise AssertionError(f"Art Studio scope gate failed:\n{out}")
