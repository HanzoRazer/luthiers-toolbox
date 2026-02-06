#!/usr/bin/env python3
"""
Pytest gate: validate viewer_pack_v1 exports for known-good Phase 2 sessions.

Runs the CLI validator against pre-exported packs; fails fast on first failure.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


# Hard-coded "real session" dirs (your two known-good Phase 2 sessions)
REAL_SESSIONS = [
    "runs_phase2/session_20260101T234237Z",
    "runs_phase2/session_20260101T235209Z",
]


def _run_validator(repo_root: Path, pack_dir: Path) -> None:
    """
    Run validate_viewer_pack_v1.py against a viewer_pack_v1 directory.
    Fails fast (raises AssertionError) on non-zero exit.
    """
    validator = repo_root / "scripts" / "phase2" / "validate_viewer_pack_v1.py"
    assert validator.is_file(), f"Validator not found at: {validator}"

    cmd = [
        sys.executable,
        str(validator),
        "--pack",
        str(pack_dir),
        "--quiet",
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env={**os.environ},
    )

    if proc.returncode != 0:
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        raise AssertionError(
            f"viewer_pack_v1 validation failed for pack:\n"
            f"  {pack_dir}\n\n"
            f"Command:\n  {' '.join(cmd)}\n\n"
            f"Output:\n{out}"
        )


@pytest.mark.parametrize("session_rel", REAL_SESSIONS)
def test_validate_viewer_pack_v1_real_sessions(session_rel: str) -> None:
    """
    Validates that the exporter output stays schema-true and hash-true for known real sessions.

    This test expects the pack directory to already exist at:
      out/viewer_packs/<session_name>/viewer_pack_v1

    If you change export destinations, update PACK_ROOT logic below.
    """
    repo_root = Path(__file__).resolve().parents[3]  # scripts/phase2/tests -> repo root
    session_dir = repo_root / session_rel
    assert session_dir.is_dir(), f"Missing session dir: {session_dir}"

    # Expected pack location: out/viewer_packs/<session_name>/viewer_pack_v1
    pack_dir = repo_root / "out" / "viewer_packs" / session_dir.name / "viewer_pack_v1"

    assert pack_dir.is_dir(), (
        f"Missing exported viewer pack directory.\n"
        f"Expected: {pack_dir}\n\n"
        f"Run exporter first, e.g.:\n"
        f"  python scripts/phase2/export_viewer_pack_v1.py "
        f"--session-dir {session_rel} --out out/viewer_packs\n"
    )

    # Fail fast: if first session fails, pytest stops this test instance immediately.
    _run_validator(repo_root, pack_dir)
