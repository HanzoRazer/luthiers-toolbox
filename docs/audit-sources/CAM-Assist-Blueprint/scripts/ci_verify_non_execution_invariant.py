#!/usr/bin/env python3
"""
CI Non-Execution Invariant Check

Runs verify_non_execution_invariant.py against all example packages.
This is a required CI check — failure blocks merge.

Usage:
    python scripts/ci_verify_non_execution_invariant.py

Exit codes:
    0 — All packages pass
    1 — Invariant violation detected
    2 — No packages found (configuration error)
"""

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
PACKAGES_DIR = REPO_ROOT / "examples" / "packages"
VERIFIER = REPO_ROOT / "scripts" / "verify_non_execution_invariant.py"


def main() -> int:
    packages = list(PACKAGES_DIR.glob("*/"))

    if not packages:
        print(f"ERROR: No packages found in {PACKAGES_DIR}", file=sys.stderr)
        return 2

    print(f"CI: Verifying non-execution invariant for {len(packages)} packages...")

    result = subprocess.run(
        [sys.executable, str(VERIFIER)] + [str(p) for p in packages],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode == 0:
        print("CI: Non-execution invariant check PASSED")
    else:
        print("CI: Non-execution invariant check FAILED", file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
