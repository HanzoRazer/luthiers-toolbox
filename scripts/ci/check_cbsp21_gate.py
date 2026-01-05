#!/usr/bin/env python3
"""
CBSP21 Gate Check Script

Enforces CBSP21 patch manifest requirements:
1. Manifest file must exist (.cbsp21/patch_input.json)
2. All changed files must be declared in manifest (coverage check)
3. coverage_min threshold must be met
4. Anti-regression: behavior_change fields must be present for medium/high risk
5. Architecture scan integration (Phase 2):
   - Validates architecture_scan block shape when present
   - Blocks only when critical > 0 AND _experimental/ files touched

Usage:
    python scripts/ci/check_cbsp21_gate.py --manifest .cbsp21/patch_input.json --changed-files file1.py file2.ts

Exit codes:
    0 = Pass
    1 = Fail (manifest missing, coverage too low, etc.)
    2 = Error (invalid JSON, etc.)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Set, Tuple, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_manifest(manifest_path: str) -> dict:
    """Load and validate the CBSP21 manifest."""
    path = Path(manifest_path)
    if not path.exists():
        print(f"❌ CBSP21 FAIL: Manifest not found: {manifest_path}")
        print()
        print("Create a manifest using .cbsp21/patch_input.json.example as a template.")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ CBSP21 ERROR: Invalid JSON in manifest: {e}")
        sys.exit(2)

    # Validate schema
    if manifest.get("schema") != "cbsp21_patch_input_v1":
        print(f"❌ CBSP21 FAIL: Invalid schema. Expected 'cbsp21_patch_input_v1', got '{manifest.get('schema')}'")
        sys.exit(1)

    return manifest


def get_declared_files(manifest: dict) -> Set[str]:
    """Extract all declared file paths from manifest."""
    declared = set()
    for file_entry in manifest.get("files", []):
        declared.add(file_entry.get("path", ""))
        # Also count scan_targets as "covered"
        for target in file_entry.get("scan_targets", []):
            declared.add(target)
    return declared


def check_coverage(changed_files: List[str], declared_files: Set[str], coverage_min: float) -> tuple:
    """
    Check if changed files are covered by manifest declarations.

    Returns: (passed: bool, coverage: float, uncovered: List[str])
    """
    if not changed_files:
        return True, 1.0, []

    # Normalize paths
    changed_set = set(f.strip() for f in changed_files if f.strip())
    declared_normalized = set(f.strip() for f in declared_files if f.strip())

    # Exempt certain files from coverage requirement
    EXEMPT_PATTERNS = [
        ".cbsp21/",           # Manifest itself
        ".gitignore",
        "README.md",
        "CHANGELOG.md",
        "*.lock",
        "package-lock.json",
        "pnpm-lock.yaml",
    ]

    def is_exempt(filepath: str) -> bool:
        for pattern in EXEMPT_PATTERNS:
            if pattern.endswith("/") and filepath.startswith(pattern):
                return True
            if pattern.startswith("*") and filepath.endswith(pattern[1:]):
                return True
            if filepath == pattern:
                return True
        return False

    # Filter out exempt files
    non_exempt_changed = set(f for f in changed_set if not is_exempt(f))

    if not non_exempt_changed:
        return True, 1.0, []

    covered = non_exempt_changed & declared_normalized
    uncovered = non_exempt_changed - declared_normalized

    coverage = len(covered) / len(non_exempt_changed) if non_exempt_changed else 1.0
    passed = coverage >= coverage_min

    return passed, coverage, sorted(uncovered)


def check_behavior_changes(manifest: dict) -> tuple:
    """
    Check that medium/high risk files have behavior_change documented.

    Returns: (passed: bool, issues: List[str])
    """
    issues = []
    for file_entry in manifest.get("files", []):
        risk = file_entry.get("risk", "low")
        behavior_change = file_entry.get("behavior_change", "")
        path = file_entry.get("path", "unknown")

        if risk in ("medium", "high"):
            if not behavior_change or behavior_change.lower() == "none":
                issues.append(f"{path}: risk={risk} but behavior_change is empty/none")

    return len(issues) == 0, issues


# =============================================================================
# Phase 2: Architecture Scan Integration
# =============================================================================

def validate_architecture_scan_block(scan_block: Optional[dict]) -> Tuple[bool, List[str]]:
    """
    Validate the shape of the architecture_scan block when present.

    Returns: (valid: bool, errors: List[str])
    """
    if scan_block is None:
        # Block is optional - absence is valid
        return True, []

    errors = []

    # Required fields
    if "scan_id" not in scan_block:
        errors.append("architecture_scan.scan_id is required")

    if "risk_summary" not in scan_block:
        errors.append("architecture_scan.risk_summary is required")
    else:
        risk_summary = scan_block["risk_summary"]
        if not isinstance(risk_summary, dict):
            errors.append("architecture_scan.risk_summary must be an object")
        else:
            for level in ("critical", "high", "medium", "low"):
                if level not in risk_summary:
                    errors.append(f"architecture_scan.risk_summary.{level} is required")
                elif not isinstance(risk_summary[level], int):
                    errors.append(f"architecture_scan.risk_summary.{level} must be an integer")

    # Optional but type-checked fields
    if "findings" in scan_block and not isinstance(scan_block["findings"], list):
        errors.append("architecture_scan.findings must be an array")

    if "acknowledged" in scan_block and not isinstance(scan_block["acknowledged"], bool):
        errors.append("architecture_scan.acknowledged must be a boolean")

    if "acknowledgement_notes" in scan_block and not isinstance(scan_block["acknowledgement_notes"], str):
        errors.append("architecture_scan.acknowledgement_notes must be a string")

    return len(errors) == 0, errors


def touched_experimental(changed_files: List[str]) -> bool:
    """
    Check if any changed files are in the _experimental/ sandbox.

    Normalizes path separators and checks for _experimental/ anywhere in path.
    """
    for f in changed_files:
        normalized = f.replace("\\", "/")
        if "/_experimental/" in normalized or normalized.startswith("_experimental/"):
            return True
    return False


def check_architecture_policy_breach(
    manifest: dict,
    changed_files: List[str],
) -> Tuple[bool, Optional[str]]:
    """
    Check for architecture policy breach that should block the PR.

    Policy: Block when BOTH conditions are true:
      1. architecture_scan.risk_summary.critical > 0
      2. Changed files include _experimental/ paths

    When blocked, manifest must have acknowledged=true to proceed.

    Returns: (passed: bool, reason: Optional[str])
    """
    scan_block = manifest.get("architecture_scan")

    if scan_block is None:
        # No scan data - pass (scan is advisory, not mandatory)
        return True, None

    risk_summary = scan_block.get("risk_summary", {})
    critical_count = risk_summary.get("critical", 0)

    if critical_count == 0:
        # No critical findings - pass
        return True, None

    if not touched_experimental(changed_files):
        # No _experimental/ touched - pass (warn but don't block)
        return True, None

    # Both conditions met: critical > 0 AND _experimental/ touched
    # Check for acknowledgement
    acknowledged = scan_block.get("acknowledged", False)

    if acknowledged:
        notes = scan_block.get("acknowledgement_notes", "")
        if notes:
            print(f"⚠️  Architecture scan critical findings acknowledged: {notes}")
        return True, None

    reason = (
        f"Architecture policy breach: {critical_count} critical finding(s) "
        f"with _experimental/ files touched. "
        f"Set architecture_scan.acknowledged=true with acknowledgement_notes to proceed."
    )
    return False, reason


def main():
    parser = argparse.ArgumentParser(description="CBSP21 Gate Check")
    parser.add_argument("--manifest", required=True, help="Path to patch_input.json manifest")
    parser.add_argument("--changed-files", nargs="*", default=[], help="List of changed files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 60)
    print("CBSP21 Gate Check")
    print("=" * 60)
    print()

    # Load manifest
    manifest = load_manifest(args.manifest)
    coverage_min = manifest.get("coverage_min", 0.95)
    declared_files = get_declared_files(manifest)

    print(f"📋 Manifest: {args.manifest}")
    print(f"📊 Coverage minimum: {coverage_min * 100:.0f}%")
    print(f"📁 Declared files: {len(declared_files)}")
    print()

    if args.verbose:
        print("Declared paths:")
        for f in sorted(declared_files):
            print(f"  - {f}")
        print()

    # Check coverage
    passed_coverage, coverage, uncovered = check_coverage(
        args.changed_files, declared_files, coverage_min
    )

    print(f"🔍 Changed files: {len(args.changed_files)}")
    print(f"📈 Coverage: {coverage * 100:.1f}%")

    if uncovered:
        print()
        print("⚠️  Uncovered files (not in manifest):")
        for f in uncovered:
            print(f"  - {f}")

    # Check behavior changes
    passed_behavior, behavior_issues = check_behavior_changes(manifest)

    if behavior_issues:
        print()
        print("⚠️  Behavior change documentation issues:")
        for issue in behavior_issues:
            print(f"  - {issue}")

    # Phase 2: Architecture scan checks
    scan_block = manifest.get("architecture_scan")
    passed_scan_shape, scan_shape_errors = validate_architecture_scan_block(scan_block)
    passed_arch_policy, arch_breach_reason = check_architecture_policy_breach(
        manifest, args.changed_files
    )

    # Display architecture scan info if present
    if scan_block:
        print()
        print("🏗️  Architecture Scan:")
        print(f"   Scan ID: {scan_block.get('scan_id', 'N/A')}")
        risk_summary = scan_block.get("risk_summary", {})
        print(f"   Risk: critical={risk_summary.get('critical', 0)}, "
              f"high={risk_summary.get('high', 0)}, "
              f"medium={risk_summary.get('medium', 0)}, "
              f"low={risk_summary.get('low', 0)}")
        if touched_experimental(args.changed_files):
            print("   ⚠️  _experimental/ files touched")
        if scan_block.get("acknowledged"):
            print("   ✓ Acknowledged")

    if scan_shape_errors:
        print()
        print("⚠️  Architecture scan block validation errors:")
        for err in scan_shape_errors:
            print(f"  - {err}")

    if arch_breach_reason:
        print()
        print(f"🚫 {arch_breach_reason}")

    # Final result
    print()
    print("=" * 60)

    all_passed = (
        passed_coverage
        and passed_behavior
        and passed_scan_shape
        and passed_arch_policy
    )

    if all_passed:
        print("✅ CBSP21 Gate: PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ CBSP21 Gate: FAILED")
        if not passed_coverage:
            print(f"   - Coverage {coverage * 100:.1f}% < {coverage_min * 100:.0f}% minimum")
        if not passed_behavior:
            print(f"   - {len(behavior_issues)} behavior change documentation issue(s)")
        if not passed_scan_shape:
            print(f"   - {len(scan_shape_errors)} architecture scan validation error(s)")
        if not passed_arch_policy:
            print("   - Architecture policy breach (critical findings + _experimental/)")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
