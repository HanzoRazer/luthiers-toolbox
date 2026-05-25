#!/usr/bin/env python3
"""
CAM Assist Non-Execution Invariant Verifier

Walks a strategy package through all pipeline stages and verifies the
non-execution declaration is present and correct at each stage.

This is a CI guard. It ensures the non-execution invariant survives the
entire pipeline: assemble → validate → stage → review → archive.

Usage:
    python scripts/verify_non_execution_invariant.py <strategy.json>
    python scripts/verify_non_execution_invariant.py <package_dir>/
    python scripts/verify_non_execution_invariant.py <package.zip>
    python scripts/verify_non_execution_invariant.py <strategy.json> --quiet

Exit codes:
    0 — All invariants verified
    1 — Invariant violation detected
    2 — File/read error
"""

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import NamedTuple


class InvariantCheck(NamedTuple):
    stage: str
    field: str
    expected: bool | str
    actual: any
    passed: bool


class VerificationResult(NamedTuple):
    passed: bool
    checks: list[InvariantCheck]
    errors: list[str]


# Fields that MUST have specific values for the non-execution invariant
STRATEGY_INVARIANTS = [
    ("operation_intent.non_execution_declaration", True),
    ("safety_boundary.non_execution_declaration", True),
    ("safety_boundary.human_review_required", True),
    ("safety_boundary.execution_authority_claim", False),
]

MANIFEST_INVARIANTS = [
    ("authority.non_execution_declaration", True),
    ("authority.execution_authority_claim", False),
    ("authority.requires_human_review", True),
]

REVIEW_DECISION_INVARIANTS = [
    ("authority.does_not_authorize_machine_execution", True),
    ("authority.requires_downstream_cam_verification", True),
    ("authority.human_review_recorded", True),
]


def get_nested(data: dict, path: str) -> any:
    """Get a nested value by dot-separated path."""
    keys = path.split(".")
    value = data
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def check_invariants(
    data: dict,
    invariants: list[tuple[str, any]],
    stage: str,
) -> list[InvariantCheck]:
    """Check a set of invariants against data."""
    checks = []
    for field_path, expected in invariants:
        actual = get_nested(data, field_path)
        passed = actual == expected
        checks.append(InvariantCheck(
            stage=stage,
            field=field_path,
            expected=expected,
            actual=actual,
            passed=passed,
        ))
    return checks


def verify_strategy_json(strategy_path: Path) -> list[InvariantCheck]:
    """Verify invariants in a strategy.json file."""
    if not strategy_path.exists():
        return [InvariantCheck("strategy", "file", "exists", "missing", False)]

    try:
        data = json.loads(strategy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [InvariantCheck("strategy", "json", "valid", str(e), False)]

    return check_invariants(data, STRATEGY_INVARIANTS, "strategy")


def verify_manifest_json(manifest_path: Path) -> list[InvariantCheck]:
    """Verify invariants in a manifest.json file."""
    if not manifest_path.exists():
        return [InvariantCheck("manifest", "file", "exists", "missing", False)]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [InvariantCheck("manifest", "json", "valid", str(e), False)]

    return check_invariants(data, MANIFEST_INVARIANTS, "manifest")


def verify_review_decision(decision_path: Path) -> list[InvariantCheck]:
    """Verify invariants in a review decision record."""
    if not decision_path.exists():
        # Review decision is optional — only check if present
        return []

    try:
        data = json.loads(decision_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [InvariantCheck("review_decision", "json", "valid", str(e), False)]

    return check_invariants(data, REVIEW_DECISION_INVARIANTS, "review_decision")


def verify_package_directory(package_dir: Path) -> VerificationResult:
    """Verify all invariants in an assembled package directory."""
    checks = []
    errors = []

    if not package_dir.is_dir():
        return VerificationResult(False, [], [f"Not a directory: {package_dir}"])

    # Check strategy.json
    strategy_path = package_dir / "strategy.json"
    checks.extend(verify_strategy_json(strategy_path))

    # Check manifest.json
    manifest_path = package_dir / "manifest.json"
    checks.extend(verify_manifest_json(manifest_path))

    # Check review decision if present (sibling file pattern)
    decision_path = package_dir.parent / f"{package_dir.name}.review_decision.json"
    checks.extend(verify_review_decision(decision_path))

    # Also check for decision inside package (alternate location)
    internal_decision = package_dir / "review_decision.json"
    if internal_decision.exists():
        checks.extend(verify_review_decision(internal_decision))

    passed = all(c.passed for c in checks)
    return VerificationResult(passed, checks, errors)


def verify_archive(archive_path: Path) -> VerificationResult:
    """Verify all invariants in a package archive."""
    checks = []
    errors = []

    if not archive_path.exists():
        return VerificationResult(False, [], [f"Archive not found: {archive_path}"])

    if not zipfile.is_zipfile(archive_path):
        return VerificationResult(False, [], [f"Not a valid zip file: {archive_path}"])

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(tmp_path)
        except zipfile.BadZipFile as e:
            return VerificationResult(False, [], [f"Failed to extract: {e}"])

        # Find the package directory (should be a single top-level dir or files at root)
        extracted = list(tmp_path.iterdir())
        if len(extracted) == 1 and extracted[0].is_dir():
            package_dir = extracted[0]
        else:
            package_dir = tmp_path

        # Verify as package directory
        result = verify_package_directory(package_dir)

        # Tag checks as coming from archive
        archive_checks = [
            InvariantCheck(
                stage=f"archive:{c.stage}",
                field=c.field,
                expected=c.expected,
                actual=c.actual,
                passed=c.passed,
            )
            for c in result.checks
        ]

        return VerificationResult(result.passed, archive_checks, result.errors)


def verify_strategy_file(strategy_path: Path) -> VerificationResult:
    """Verify invariants in a standalone strategy.json file."""
    checks = verify_strategy_json(strategy_path)
    passed = all(c.passed for c in checks)
    return VerificationResult(passed, checks, [])


def verify_input(input_path: Path) -> VerificationResult:
    """Verify invariants based on input type."""
    if not input_path.exists():
        return VerificationResult(False, [], [f"Path not found: {input_path}"])

    if input_path.is_dir():
        return verify_package_directory(input_path)
    elif input_path.suffix == ".zip":
        return verify_archive(input_path)
    elif input_path.suffix == ".json":
        return verify_strategy_file(input_path)
    else:
        return VerificationResult(False, [], [f"Unknown input type: {input_path}"])


def format_result(result: VerificationResult, quiet: bool = False) -> str:
    """Format verification result for output."""
    lines = []

    if quiet:
        if result.passed:
            return "PASS: All non-execution invariants verified"
        else:
            failed = [c for c in result.checks if not c.passed]
            return f"FAIL: {len(failed)} invariant(s) violated"

    lines.append("Non-Execution Invariant Verification")
    lines.append("=" * 40)

    for check in result.checks:
        status = "[OK]" if check.passed else "[FAIL]"
        lines.append(f"  {status} [{check.stage}] {check.field}")
        if not check.passed:
            lines.append(f"      Expected: {check.expected}")
            lines.append(f"      Actual:   {check.actual}")

    lines.append("")
    if result.passed:
        lines.append(f"PASS: All {len(result.checks)} checks passed")
    else:
        failed = [c for c in result.checks if not c.passed]
        lines.append(f"FAIL: {len(failed)} of {len(result.checks)} checks failed")

    for error in result.errors:
        lines.append(f"ERROR: {error}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify non-execution invariants in CAM Assist packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to strategy.json, package directory, or package.zip",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print pass/fail summary",
    )

    args = parser.parse_args()

    result = verify_input(args.input)
    output = format_result(result, args.quiet)

    if result.passed:
        print(output)
        return 0
    else:
        print(output, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
