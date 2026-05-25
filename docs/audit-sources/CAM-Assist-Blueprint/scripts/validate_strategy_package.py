#!/usr/bin/env python3
"""
CAM Assist Strategy Package Validator

Validates strategy package JSON files against the canonical schema.
This validator is non-executing — it only checks structure and contract compliance.

Version 1.2 (A2) adds semantic contract enforcement:
- operation_intent with non_execution_declaration
- material_context
- safety_boundary with execution authority rejection

Usage:
    python scripts/validate_strategy_package.py <file_or_directory>
    python scripts/validate_strategy_package.py examples/valid/fret_slot_strategy.json
    python scripts/validate_strategy_package.py examples/

Exit codes:
    0 — All files valid
    1 — One or more files invalid
    2 — Usage error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple


SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "strategy.schema.json"

# A2 required top-level fields (operation_type moved into operation_intent)
REQUIRED_TOP_LEVEL_FIELDS = [
    "strategy_version",
    "strategy_id",
    "units",
    "coordinate_frame",
    "provenance",
    "operation_intent",
    "material_context",
    "safety_boundary",
    "geometry",
    "operation",
    "approval_state",
]

REQUIRED_COORDINATE_FRAME_FIELDS = ["origin", "x_axis", "y_axis"]
REQUIRED_PROVENANCE_FIELDS = ["cam_assist_version", "created_at"]
REQUIRED_GEOMETRY_FIELDS = ["dxf_file", "primary_layer"]
REQUIRED_OPERATION_FIELDS = ["type", "tool", "parameters"]

# A2 semantic contract fields
REQUIRED_OPERATION_INTENT_FIELDS = [
    "operation_type",
    "target_feature",
    "cut_intent",
    "non_execution_declaration",
]
REQUIRED_MATERIAL_CONTEXT_FIELDS = ["material_class"]
REQUIRED_SAFETY_BOUNDARY_FIELDS = ["non_execution_declaration", "human_review_required"]

VALID_UNITS = ["inches", "mm"]
VALID_APPROVAL_STATES = ["pending", "in_review", "approved", "rejected"]
VALID_CUT_INTENTS = ["slot", "pocket", "profile", "drill", "contour", "channel"]
VALID_MATERIAL_CLASSES = [
    "softwood", "hardwood", "exotic", "figured", "laminate", "composite", "unknown"
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


def validate_strategy_package(data: dict) -> ValidationResult:
    """Validate a strategy package against the A2 semantic contract."""
    errors: list[str] = []
    warnings: list[str] = []

    # Check required top-level fields
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # If missing critical fields, return early
    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    # Validate units
    if data.get("units") not in VALID_UNITS:
        errors.append(f"Invalid units: {data.get('units')}. Must be one of {VALID_UNITS}")

    # Validate coordinate_frame structure
    coord_frame = data.get("coordinate_frame", {})
    if not isinstance(coord_frame, dict):
        errors.append("coordinate_frame must be an object")
    else:
        for field in REQUIRED_COORDINATE_FRAME_FIELDS:
            if field not in coord_frame:
                errors.append(f"Missing required coordinate_frame field: {field}")

    # Validate provenance structure
    provenance = data.get("provenance", {})
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for field in REQUIRED_PROVENANCE_FIELDS:
            if field not in provenance:
                errors.append(f"Missing required provenance field: {field}")

    # Validate operation_intent structure (A2)
    operation_intent = data.get("operation_intent", {})
    if not isinstance(operation_intent, dict):
        errors.append("operation_intent must be an object")
    else:
        for field in REQUIRED_OPERATION_INTENT_FIELDS:
            if field not in operation_intent:
                errors.append(f"Missing required operation_intent field: {field}")

        # Validate cut_intent enum
        cut_intent = operation_intent.get("cut_intent")
        if cut_intent and cut_intent not in VALID_CUT_INTENTS:
            errors.append(
                f"Invalid cut_intent: {cut_intent}. Must be one of {VALID_CUT_INTENTS}"
            )

        # CRITICAL: Reject execution authority claims
        non_exec = operation_intent.get("non_execution_declaration")
        if non_exec is not True:
            errors.append(
                "EXECUTION AUTHORITY VIOLATION: operation_intent.non_execution_declaration "
                "must be true. Strategy packages cannot claim execution authority."
            )

    # Validate material_context structure (A2)
    material_context = data.get("material_context", {})
    if not isinstance(material_context, dict):
        errors.append("material_context must be an object")
    else:
        for field in REQUIRED_MATERIAL_CONTEXT_FIELDS:
            if field not in material_context:
                errors.append(f"Missing required material_context field: {field}")

        # Validate material_class enum
        material_class = material_context.get("material_class")
        if material_class and material_class not in VALID_MATERIAL_CLASSES:
            errors.append(
                f"Invalid material_class: {material_class}. "
                f"Must be one of {VALID_MATERIAL_CLASSES}"
            )

    # Validate safety_boundary structure (A2)
    safety_boundary = data.get("safety_boundary", {})
    if not isinstance(safety_boundary, dict):
        errors.append("safety_boundary must be an object")
    else:
        for field in REQUIRED_SAFETY_BOUNDARY_FIELDS:
            if field not in safety_boundary:
                errors.append(f"Missing required safety_boundary field: {field}")

        # CRITICAL: Reject execution authority claims
        non_exec = safety_boundary.get("non_execution_declaration")
        if non_exec is not True:
            errors.append(
                "EXECUTION AUTHORITY VIOLATION: safety_boundary.non_execution_declaration "
                "must be true. Strategy packages cannot claim execution authority."
            )

        human_review = safety_boundary.get("human_review_required")
        if human_review is not True:
            errors.append(
                "SAFETY VIOLATION: safety_boundary.human_review_required must be true. "
                "All strategy packages require human review."
            )

        # Reject explicit execution_authority_claim
        exec_claim = safety_boundary.get("execution_authority_claim")
        if exec_claim is True:
            errors.append(
                "EXECUTION AUTHORITY VIOLATION: safety_boundary.execution_authority_claim "
                "must be false or absent. Strategy packages cannot claim execution authority."
            )

    # Validate geometry structure
    geometry = data.get("geometry", {})
    if not isinstance(geometry, dict):
        errors.append("geometry must be an object")
    else:
        for field in REQUIRED_GEOMETRY_FIELDS:
            if field not in geometry:
                errors.append(f"Missing required geometry field: {field}")

    # Validate operation structure
    operation = data.get("operation", {})
    if not isinstance(operation, dict):
        errors.append("operation must be an object")
    else:
        for field in REQUIRED_OPERATION_FIELDS:
            if field not in operation:
                errors.append(f"Missing required operation field: {field}")

    # Validate approval_state
    if data.get("approval_state") not in VALID_APPROVAL_STATES:
        errors.append(
            f"Invalid approval_state: {data.get('approval_state')}. "
            f"Must be one of {VALID_APPROVAL_STATES}"
        )

    # Validate strategy_version
    if data.get("strategy_version") != "1.2":
        warnings.append(
            f"strategy_version is {data.get('strategy_version')}, expected 1.2"
        )

    # Validate strategy_id format
    strategy_id = data.get("strategy_id", "")
    if not isinstance(strategy_id, str) or not strategy_id:
        errors.append("strategy_id must be a non-empty string")
    elif not all(c.isalnum() or c == "-" for c in strategy_id):
        errors.append(
            "strategy_id must contain only lowercase alphanumeric characters and hyphens"
        )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_file(path: Path) -> ValidationResult:
    """Validate a single strategy package file."""
    data, parse_error = load_json(path)

    if parse_error:
        return ValidationResult(valid=False, errors=[parse_error], warnings=[])

    return validate_strategy_package(data)


def validate_directory(directory: Path) -> dict[Path, ValidationResult]:
    """Recursively validate all JSON files in a directory."""
    results: dict[Path, ValidationResult] = {}

    for json_file in directory.rglob("*.json"):
        # Skip schema files
        if "schema" in json_file.name.lower():
            continue
        results[json_file] = validate_file(json_file)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate CAM Assist strategy package files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a JSON file or directory to validate",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output errors, not success messages",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()
    path: Path = args.path

    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        return 2

    if path.is_file():
        results = {path: validate_file(path)}
    elif path.is_dir():
        results = validate_directory(path)
        if not results:
            print(f"No JSON files found in {path}", file=sys.stderr)
            return 2
    else:
        print(f"Error: Path is neither file nor directory: {path}", file=sys.stderr)
        return 2

    # Report results
    all_valid = True
    for file_path, result in sorted(results.items()):
        if result.valid and not args.quiet:
            status = "VALID"
            if result.warnings:
                status += f" (with {len(result.warnings)} warnings)"
            print(f"[OK] {file_path}: {status}")
            for warning in result.warnings:
                print(f"  [WARN] {warning}")
        elif not result.valid:
            all_valid = False
            print(f"[FAIL] {file_path}: INVALID")
            for error in result.errors:
                print(f"  [ERR] {error}")
            for warning in result.warnings:
                print(f"  [WARN] {warning}")

        if args.strict and result.warnings:
            all_valid = False

    # Summary
    total = len(results)
    valid_count = sum(1 for r in results.values() if r.valid)
    invalid_count = total - valid_count

    if not args.quiet or invalid_count > 0:
        print(f"\nValidation complete: {valid_count}/{total} files valid")

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
