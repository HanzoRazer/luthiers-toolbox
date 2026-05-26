#!/usr/bin/env python3
"""
CAM Assist Strategy Package Manifest Validator

Validates strategy package manifest files for:
- Correct manifest structure
- Execution authority declarations
- Referenced file existence

All artifact paths in a manifest are resolved relative to the manifest file.

Usage:
    python scripts/validate_manifest.py <manifest_json>
    python scripts/validate_manifest.py examples/valid/fret_slot_strategy_manifest.json

Exit codes:
    0 — Manifest is valid
    1 — Validation failed (structure or authority violation)
    2 — File/read/schema error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple


REQUIRED_FIELDS = [
    "manifest_version",
    "package_type",
    "operation_type",
    "strategy_file",
    "review_packet_file",
    "authority",
    "created_at",
]

REQUIRED_AUTHORITY_FIELDS = [
    "non_execution_declaration",
    "execution_authority_claim",
    "requires_human_review",
]


class ValidationResult(NamedTuple):
    valid: bool
    errors: list[str]
    warnings: list[str]


def load_json(path: Path) -> tuple[dict | None, str | None]:
    """Load and parse JSON file. Returns (data, error)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except Exception as e:
        return None, f"Error reading file: {e}"


def validate_manifest(data: dict, manifest_path: Path) -> ValidationResult:
    """Validate a strategy package manifest."""
    errors: list[str] = []
    warnings: list[str] = []
    manifest_dir = manifest_path.parent

    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    # Validate package_type
    if data.get("package_type") != "cam_assist_strategy_package":
        errors.append(
            f"Invalid package_type: {data.get('package_type')}. "
            "Must be 'cam_assist_strategy_package'"
        )

    # Validate manifest_version format
    version = data.get("manifest_version", "")
    if not version or not all(
        part.isdigit() for part in version.split(".") if part
    ) or version.count(".") != 2:
        errors.append(
            f"Invalid manifest_version format: {version}. "
            "Must be semantic version (e.g., 1.0.0)"
        )

    # Validate authority block
    authority = data.get("authority", {})
    if not isinstance(authority, dict):
        errors.append("authority must be an object")
    else:
        for field in REQUIRED_AUTHORITY_FIELDS:
            if field not in authority:
                errors.append(f"Missing required authority field: {field}")

        # CRITICAL: Execution authority checks
        if authority.get("non_execution_declaration") is not True:
            errors.append(
                "EXECUTION AUTHORITY VIOLATION: authority.non_execution_declaration "
                "must be true"
            )

        if authority.get("execution_authority_claim") is not False:
            errors.append(
                "EXECUTION AUTHORITY VIOLATION: authority.execution_authority_claim "
                "must be false"
            )

        if authority.get("requires_human_review") is not True:
            errors.append(
                "AUTHORITY VIOLATION: authority.requires_human_review must be true"
            )

    # Validate referenced files exist
    strategy_file = data.get("strategy_file", "")
    if strategy_file:
        strategy_path = manifest_dir / strategy_file
        if not strategy_path.exists():
            errors.append(f"Referenced strategy file not found: {strategy_file}")
    else:
        errors.append("strategy_file is empty")

    review_file = data.get("review_packet_file", "")
    if review_file:
        review_path = manifest_dir / review_file
        if not review_path.exists():
            errors.append(f"Referenced review packet file not found: {review_file}")
    else:
        errors.append("review_packet_file is empty")

    # Check source geometry files if present
    geometry_files = data.get("source_geometry_files", [])
    if isinstance(geometry_files, list):
        for geom_file in geometry_files:
            geom_path = manifest_dir / geom_file
            if not geom_path.exists():
                errors.append(f"Referenced geometry file not found: {geom_file}")
    else:
        errors.append("source_geometry_files must be an array")

    # Warnings for missing optional fields
    if not geometry_files:
        warnings.append(
            "source_geometry_files is empty. Geometry may be referenced in strategy JSON."
        )

    provenance = data.get("provenance", {})
    if not provenance.get("created_by"):
        warnings.append("provenance.created_by is empty")
    if not provenance.get("derivation_notes"):
        warnings.append("provenance.derivation_notes is empty")

    if not data.get("cam_assist_version"):
        warnings.append("cam_assist_version is missing")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_manifest_file(path: Path) -> ValidationResult:
    """Validate a manifest file."""
    data, load_error = load_json(path)

    if load_error:
        return ValidationResult(valid=False, errors=[load_error], warnings=[])

    return validate_manifest(data, path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate CAM Assist strategy package manifests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "manifest_json",
        type=Path,
        help="Path to the manifest JSON file",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output errors, not success messages or warnings",
    )

    args = parser.parse_args()
    manifest_path: Path = args.manifest_json

    if not manifest_path.exists():
        print(f"Error: File not found: {manifest_path}", file=sys.stderr)
        return 2

    result = validate_manifest_file(manifest_path)

    if result.valid:
        if not args.quiet:
            print("PASS: strategy package manifest is valid")
            for warning in result.warnings:
                print(f"  [WARN] {warning}")
        return 0
    else:
        print("FAIL: manifest validation failed", file=sys.stderr)
        for error in result.errors:
            print(f"  [ERR] {error}", file=sys.stderr)
        for warning in result.warnings:
            print(f"  [WARN] {warning}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
