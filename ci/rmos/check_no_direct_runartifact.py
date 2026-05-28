#!/usr/bin/env python3
"""
RunArtifact authority gate — Makefile step [5/7] / FENCE_REGISTRY artifact_authority.

Scans services/api for direct RunArtifact construction/imports outside authorized
modules. Uses brownfield baseline from app/ci/fence_baseline.json (fail only on NEW).

Usage (repo root):
  python ci/rmos/check_no_direct_runartifact.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "services" / "api"
BASELINE_PATH = API_ROOT / "app" / "ci" / "fence_baseline.json"


def main() -> int:
    os.chdir(API_ROOT)
    sys.path.insert(0, str(API_ROOT))

    from app.ci.boundary_imports.baseline import load_baseline, symbol_key
    from app.ci.boundary_imports.fences import check_artifact_authority
    from app.ci.boundary_imports.parser import iter_python_files, parse_imports_and_symbols, repo_root_from_cwd

    root = repo_root_from_cwd()
    app_dir = root / "app"

    violations = []
    for py_file in iter_python_files(app_dir):
        _, symbols, _ = parse_imports_and_symbols(py_file)
        violations.extend(check_artifact_authority(py_file, symbols, root))

    artifact_keys = {symbol_key(v) for v in violations}

    if not BASELINE_PATH.exists():
        print(f"Baseline not found: {BASELINE_PATH}", file=sys.stderr)
        return 3

    baseline = load_baseline(BASELINE_PATH)
    baseline_artifact = {
        key for key in baseline.get("symbols", []) if key.startswith("artifact_authority|")
    }
    new_violations = sorted(artifact_keys - baseline_artifact)

    print(
        f"RunArtifact authority: {len(artifact_keys)} current, "
        f"{len(baseline_artifact)} baselined"
    )

    if new_violations:
        print(f"FAIL: {len(new_violations)} NEW violation(s):")
        for key in new_violations[:10]:
            print(f"  {key}")
        if len(new_violations) > 10:
            print(f"  ... and {len(new_violations) - 10} more")
        return 2

    print("PASS: No new RunArtifact authority violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
