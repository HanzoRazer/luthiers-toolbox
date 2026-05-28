#!/usr/bin/env python3
"""
CAM Assist Non-Execution Invariant Verifier

Verifies that the non-execution invariant holds at every pipeline stage.
This is a CI-required check — failure blocks merge.

The invariant:
  - execution_authority_claim = false (strategy + manifest)
  - non_execution_declaration = true (strategy + manifest)
  - requires_human_review = true (manifest)
  - human_review_required = true (strategy safety_boundary)

Usage:
    python scripts/verify_non_execution_invariant.py <package_dir>
    python scripts/verify_non_execution_invariant.py examples/packages/*/

Exit codes:
    0 — Invariant holds at all stages
    1 — Invariant violated
    2 — File/read error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class InvariantViolation(Exception):
    """Raised when the non-execution invariant is violated."""
    pass


def get_nested(data: dict, path: str) -> Any:
    """Get nested value by dot path."""
    keys = path.split(".")
    value = data
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def verify_strategy_invariant(strategy: dict, source: str) -> list[str]:
    """Verify non-execution invariant in strategy JSON."""
    violations = []

    exec_claim = get_nested(strategy, "safety_boundary.execution_authority_claim")
    if exec_claim is not False:
        violations.append(
            f"{source}: safety_boundary.execution_authority_claim must be false, "
            f"got {exec_claim!r}"
        )

    non_exec = get_nested(strategy, "operation_intent.non_execution_declaration")
    if non_exec is not True:
        violations.append(
            f"{source}: operation_intent.non_execution_declaration must be true, "
            f"got {non_exec!r}"
        )

    human_review = get_nested(strategy, "safety_boundary.human_review_required")
    if human_review is not True:
        violations.append(
            f"{source}: safety_boundary.human_review_required must be true, "
            f"got {human_review!r}"
        )

    return violations


def verify_manifest_invariant(manifest: dict, source: str) -> list[str]:
    """Verify non-execution invariant in manifest JSON."""
    violations = []

    authority = manifest.get("authority", {})
    exec_claim = manifest.get("execution_authority_claim", authority.get("execution_authority_claim"))
    if exec_claim is not False:
        violations.append(
            f"{source}: execution_authority_claim must be false, got {exec_claim!r}"
        )

    non_exec = manifest.get("non_execution_declaration", authority.get("non_execution_declaration"))
    if non_exec is not True:
        violations.append(
            f"{source}: non_execution_declaration must be true, got {non_exec!r}"
        )

    human_review = manifest.get("requires_human_review", authority.get("requires_human_review"))
    if human_review is not True:
        violations.append(
            f"{source}: requires_human_review must be true, got {human_review!r}"
        )

    return violations


def verify_review_decision_invariant(decision: dict, source: str) -> list[str]:
    """Verify non-execution invariant in review decision record."""
    violations = []

    no_auth = decision.get("does_not_authorize_machine_execution")
    if no_auth is not True:
        violations.append(
            f"{source}: does_not_authorize_machine_execution must be true, "
            f"got {no_auth!r}"
        )

    return violations


def verify_package(package_dir: Path) -> list[str]:
    """Verify non-execution invariant for all artifacts in a package."""
    violations = []

    strategy_path = package_dir / "strategy.json"
    if strategy_path.exists():
        with open(strategy_path, "r", encoding="utf-8") as f:
            strategy = json.load(f)
        violations.extend(verify_strategy_invariant(strategy, str(strategy_path)))

    manifest_path = package_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        violations.extend(verify_manifest_invariant(manifest, str(manifest_path)))

    decision_path = package_dir / "review_decision.json"
    if decision_path.exists():
        with open(decision_path, "r", encoding="utf-8") as f:
            decision = json.load(f)
        violations.extend(
            verify_review_decision_invariant(decision, str(decision_path))
        )

    staged_dir = package_dir / "staged"
    if staged_dir.is_dir():
        for staged_manifest in staged_dir.glob("manifest.json"):
            with open(staged_manifest, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            violations.extend(
                verify_manifest_invariant(manifest, str(staged_manifest))
            )

    archive_dir = package_dir / "archive"
    if archive_dir.is_dir():
        for archive_manifest in archive_dir.glob("**/manifest.json"):
            with open(archive_manifest, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            violations.extend(
                verify_manifest_invariant(manifest, str(archive_manifest))
            )

    return violations


def verify_all_packages(paths: list[Path]) -> tuple[int, int, list[str]]:
    """Verify multiple packages. Returns (checked, failed, violations)."""
    checked = 0
    failed = 0
    all_violations = []

    for path in paths:
        if path.is_dir():
            violations = verify_package(path)
            checked += 1
            if violations:
                failed += 1
                all_violations.extend(violations)

    return checked, failed, all_violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify non-execution invariant across pipeline stages"
    )
    parser.add_argument(
        "packages",
        type=Path,
        nargs="+",
        help="Package directories to verify",
    )
    parser.add_argument("--quiet", "-q", action="store_true")

    args = parser.parse_args()

    try:
        checked, failed, violations = verify_all_packages(args.packages)

        if not args.quiet:
            if violations:
                print("Non-execution invariant VIOLATED:")
                for v in violations:
                    print(f"  - {v}")
            else:
                print(f"[OK] Non-execution invariant verified: {checked} packages")

        return 1 if violations else 0

    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
