#!/usr/bin/env python3
"""
Unified Fence Runner — Runs All Boundary Checks
------------------------------------------------

Runs both import-based and pattern-based fence checks in a single command.
Uses baseline mode by default for brownfield enforcement.

Usage:
  cd services/api
  python -m app.ci.check_all_fences                    # Run all with baselines
  python -m app.ci.check_all_fences --strict           # Strict mode (no baselines)
  python -m app.ci.check_all_fences --write-baselines  # Regenerate all baselines

Exit codes:
  0 = all checks passed
  2 = violations found
  3 = configuration / runtime error

This is the recommended CI entry point for fence enforcement.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


# Baseline file locations (relative to services/api)
IMPORT_BASELINE = "app/ci/fence_baseline.json"
PATTERN_BASELINE = "app/ci/fence_patterns_baseline.json"


def _run_checker(module: str, args: list[str], label: str) -> int:
    """Run a checker module and return exit code."""
    cmd = [sys.executable, "-m", module] + args
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, cwd=Path.cwd())
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.ci.check_all_fences",
        description="Run all boundary fence checks (imports + patterns)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on ANY violation (ignores baselines)",
    )
    parser.add_argument(
        "--write-baselines",
        action="store_true",
        help="Regenerate all baseline files and exit 0",
    )
    parser.add_argument(
        "--imports-only",
        action="store_true",
        help="Run only import-based checks",
    )
    parser.add_argument(
        "--patterns-only",
        action="store_true",
        help="Run only pattern-based checks",
    )
    args = parser.parse_args()

    results: dict[str, int] = {}

    # Determine which checks to run
    run_imports = not args.patterns_only
    run_patterns = not args.imports_only

    # Write baselines mode
    if args.write_baselines:
        print("\n" + "="*60)
        print("  REGENERATING BASELINES")
        print("="*60)

        if run_imports:
            rc = _run_checker(
                "app.ci.check_boundary_imports",
                ["--write-baseline", IMPORT_BASELINE],
                "Import Baseline"
            )
            results["imports_baseline"] = rc

        if run_patterns:
            rc = _run_checker(
                "app.ci.check_boundary_patterns",
                ["--write-baseline", PATTERN_BASELINE],
                "Pattern Baseline"
            )
            results["patterns_baseline"] = rc

        print("\n" + "="*60)
        print("  BASELINES REGENERATED")
        print("="*60)
        print(f"\nFiles updated:")
        if run_imports:
            print(f"  - {IMPORT_BASELINE}")
        if run_patterns:
            print(f"  - {PATTERN_BASELINE}")
        print("\nCommit these files to lock in current debt.")
        return 0

    # Run checks
    if run_imports:
        import_args = [] if args.strict else ["--baseline", IMPORT_BASELINE]
        rc = _run_checker(
            "app.ci.check_boundary_imports",
            import_args,
            "Boundary Import Check" + (" (strict)" if args.strict else " (baseline)")
        )
        results["imports"] = rc

    if run_patterns:
        pattern_args = [] if args.strict else ["--baseline", PATTERN_BASELINE]
        rc = _run_checker(
            "app.ci.check_boundary_patterns",
            pattern_args,
            "Boundary Pattern Check" + (" (strict)" if args.strict else " (baseline)")
        )
        results["patterns"] = rc

    # Summary
    print("\n" + "="*60)
    print("  FENCE CHECK SUMMARY")
    print("="*60)

    all_passed = True
    for name, rc in results.items():
        status = "PASS" if rc == 0 else "FAIL"
        icon = "[OK]" if rc == 0 else "[FAIL]"
        print(f"  {icon} {name}: {status}")
        if rc != 0:
            all_passed = False

    print()
    if all_passed:
        print("All fence checks passed.")
        return 0
    else:
        print("Some fence checks failed. See above for details.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
