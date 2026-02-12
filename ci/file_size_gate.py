#!/usr/bin/env python3
"""CI gate: enforce file size limits with ratchet baseline.

Usage:
    python ci/file_size_gate.py              # Check against baseline
    python ci/file_size_gate.py --update     # Update baseline with current sizes
    python ci/file_size_gate.py --strict     # Fail on ANY file over limit (no baseline)

Exit codes:
    0 - All files within limits (or baseline)
    1 - Files exceed baseline (regression)
    2 - Script error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Limits
PYTHON_LIMIT = 500
VUE_LIMIT = 800

# Baseline file location
BASELINE_FILE = Path(__file__).parent / "file_size_baseline.json"

# Patterns to scan
PATTERNS = [
    ("services/api/app/**/*.py", PYTHON_LIMIT),
    ("packages/client/src/**/*.vue", VUE_LIMIT),
]


def count_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except Exception:
        return 0


def scan_files(root: Path) -> dict[str, tuple[int, int]]:
    """Scan files and return {path: (lines, limit)} for files over limit."""
    violations = {}
    for pattern, limit in PATTERNS:
        for f in root.glob(pattern):
            if f.is_file():
                lines = count_lines(f)
                if lines > limit:
                    rel = str(f.relative_to(root)).replace("\\", "/")
                    violations[rel] = (lines, limit)
    return violations


def load_baseline() -> dict[str, int]:
    """Load baseline from JSON file."""
    if not BASELINE_FILE.exists():
        return {}
    try:
        return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_baseline(data: dict[str, int]) -> None:
    """Save baseline to JSON file."""
    BASELINE_FILE.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="File size gate")
    parser.add_argument("--update", action="store_true", help="Update baseline")
    parser.add_argument("--strict", action="store_true", help="No baseline tolerance")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    violations = scan_files(root)

    if args.update:
        baseline = {path: lines for path, (lines, _) in violations.items()}
        save_baseline(baseline)
        print(f"Baseline updated: {len(baseline)} files")
        for path, lines in sorted(baseline.items(), key=lambda x: -x[1]):
            print(f"  {lines:5d}  {path}")
        return 0

    if args.strict:
        if violations:
            print(f"FAIL: {len(violations)} files exceed limits (strict mode)")
            for path, (lines, limit) in sorted(violations.items(), key=lambda x: -x[1][0]):
                print(f"  {lines:5d} > {limit}  {path}")
            return 1
        print("OK: All files within limits")
        return 0

    # Ratchet mode: fail only if files EXCEED their baseline
    baseline = load_baseline()
    regressions = []
    improvements = []

    for path, (lines, limit) in violations.items():
        baseline_lines = baseline.get(path, limit)
        if lines > baseline_lines:
            regressions.append((path, lines, baseline_lines))
        elif lines < baseline_lines:
            improvements.append((path, lines, baseline_lines))

    # Check for new violations not in baseline
    new_violations = [
        (path, lines, limit)
        for path, (lines, limit) in violations.items()
        if path not in baseline
    ]

    if regressions or new_violations:
        print(f"FAIL: File size regressions detected")
        for path, lines, baseline_lines in regressions:
            print(f"  REGRESSION: {path} ({lines} > baseline {baseline_lines})")
        for path, lines, limit in new_violations:
            print(f"  NEW: {path} ({lines} > limit {limit})")
        print("\nRun with --update to accept current sizes as new baseline")
        return 1

    if improvements:
        print(f"OK: {len(improvements)} files improved (update baseline to lock in gains)")
        for path, lines, baseline_lines in improvements:
            print(f"  IMPROVED: {path} ({lines} < baseline {baseline_lines})")

    print(f"OK: {len(violations)} files at or below baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
