#!/usr/bin/env python3
"""PR-3: submit_correction must not be called from production services/ code."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICES = REPO_ROOT / "services"

CALL_PATTERN = re.compile(r"\bsubmit_correction\s*\(")


def main() -> int:
    violations: list[str] = []
    for py in SERVICES.rglob("*.py"):
        rel = py.relative_to(REPO_ROOT).as_posix()
        try:
            lines = py.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if "def submit_correction" in line:
                continue
            if CALL_PATTERN.search(line):
                violations.append(f"{rel}:{line_no}: {line.strip()}")

    if violations:
        print("check_feedback_correction_calls: FAIL", file=sys.stderr)
        for v in violations[:20]:
            print(f"  {v}", file=sys.stderr)
        return 1
    print("check_feedback_correction_calls: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
