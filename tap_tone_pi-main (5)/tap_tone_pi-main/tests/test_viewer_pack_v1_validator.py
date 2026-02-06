#!/usr/bin/env python3
"""
Gate test: validate viewer_pack_v1 for real Phase-2 sessions.

Single test, looped over both sessions, fails fast on first error.
"""
import subprocess
import sys
from pathlib import Path


def test_viewer_pack_v1_real_sessions():
    repo_root = Path(__file__).resolve().parents[1]

    validator = repo_root / "scripts" / "validate" / "validate_viewer_pack_v1.py"

    packs = [
        repo_root / "out" / "viewer_packs" / "session_20260101T234237Z" / "viewer_pack_v1",
        repo_root / "out" / "viewer_packs" / "session_20260101T235209Z" / "viewer_pack_v1",
    ]

    for pack in packs:
        if not pack.exists():
            raise AssertionError(
                f"Pack not found: {pack}\n"
                f"Run exporter first:\n"
                f"  python scripts/phase2/export_viewer_pack_v1.py "
                f"--session-dir runs_phase2/{pack.parent.name} --out out/viewer_packs/{pack.parent.name}"
            )

        proc = subprocess.run(
            [sys.executable, str(validator), str(pack)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"Viewer pack validation failed for {pack.name}:\n"
                f"{proc.stdout}\n{proc.stderr}"
            )
