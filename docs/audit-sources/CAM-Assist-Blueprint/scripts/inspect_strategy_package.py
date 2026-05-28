#!/usr/bin/env python3
"""
CAM Assist Strategy Package Inspection CLI

Inspects assembled strategy packages and produces human-readable summaries.

This is a read-only inspection tool. It does not mutate, regenerate,
repair, or normalize package contents.

Usage:
    python scripts/inspect_strategy_package.py examples/packages/fret_slot_strategy_example/
    python scripts/inspect_strategy_package.py <package_dir> --json
    python scripts/inspect_strategy_package.py <package_dir> --quiet

Exit codes:
    0 — Inspection successful
    1 — Validation failure
    2 — File/read error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple

KNOWN_MANIFEST_VERSIONS = ["1.0.0"]
MIN_REVIEW_PACKET_SIZE = 1024  # 1 KB


class InspectionResult(NamedTuple):
    valid: bool
    package_type: str | None
    operation_type: str | None
    manifest_version: str | None
    authority: dict | None
    files: dict
    provenance: dict | None
    warnings: list[str]
    errors: list[str]


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


def inspect_package(package_dir: Path) -> InspectionResult:
    """Inspect a strategy package directory."""
    errors: list[str] = []
    warnings: list[str] = []
    files: dict = {}

    # Check package directory exists
    if not package_dir.exists():
        return InspectionResult(
            valid=False,
            package_type=None,
            operation_type=None,
            manifest_version=None,
            authority=None,
            files={},
            provenance=None,
            warnings=[],
            errors=[f"Package directory not found: {package_dir}"],
        )

    if not package_dir.is_dir():
        return InspectionResult(
            valid=False,
            package_type=None,
            operation_type=None,
            manifest_version=None,
            authority=None,
            files={},
            provenance=None,
            warnings=[],
            errors=[f"Path is not a directory: {package_dir}"],
        )

    # Check manifest.json
    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        errors.append("manifest.json is missing")
        files["manifest"] = "missing"
    else:
        files["manifest"] = "present"

    # Load manifest
    manifest_data = None
    if files.get("manifest") == "present":
        manifest_data, load_error = load_json(manifest_path)
        if load_error:
            errors.append(f"Failed to load manifest: {load_error}")
            files["manifest"] = "invalid"

    # Extract manifest fields
    package_type = None
    operation_type = None
    manifest_version = None
    authority = None
    provenance = None

    if manifest_data:
        package_type = manifest_data.get("package_type")
        operation_type = manifest_data.get("operation_type")
        manifest_version = manifest_data.get("manifest_version")
        authority = manifest_data.get("authority", {})
        provenance = manifest_data.get("provenance", {})

        # Validate package_type
        if package_type != "cam_assist_strategy_package":
            errors.append(
                f"Invalid package_type: {package_type}. "
                "Expected 'cam_assist_strategy_package'"
            )

        # Validate manifest version
        if manifest_version and manifest_version not in KNOWN_MANIFEST_VERSIONS:
            warnings.append(f"Unknown manifest version: {manifest_version}")

        # Check authority block
        if not authority:
            errors.append("Authority block missing from manifest")
        else:
            if authority.get("non_execution_declaration") is not True:
                errors.append(
                    "AUTHORITY VIOLATION: non_execution_declaration must be true"
                )
            if authority.get("execution_authority_claim") is not False:
                errors.append(
                    "AUTHORITY VIOLATION: execution_authority_claim must be false"
                )
            if authority.get("requires_human_review") is not True:
                errors.append(
                    "AUTHORITY VIOLATION: requires_human_review must be true"
                )

        # Check strategy file
        strategy_file = manifest_data.get("strategy_file")
        if strategy_file:
            strategy_path = package_dir / strategy_file
            if strategy_path.exists():
                files["strategy"] = "present"
            else:
                files["strategy"] = "missing"
                errors.append(f"Strategy file not found: {strategy_file}")
        else:
            files["strategy"] = "missing"
            errors.append("strategy_file not specified in manifest")

        # Check review packet file
        review_file = manifest_data.get("review_packet_file")
        if review_file:
            review_path = package_dir / review_file
            if review_path.exists():
                files["review_packet"] = "present"
                # Check size
                try:
                    size = review_path.stat().st_size
                    if size < MIN_REVIEW_PACKET_SIZE:
                        warnings.append(
                            f"Review packet is unusually small ({size} bytes)"
                        )
                except OSError:
                    pass
            else:
                files["review_packet"] = "missing"
                errors.append(f"Review packet file not found: {review_file}")
        else:
            files["review_packet"] = "missing"
            errors.append("review_packet_file not specified in manifest")

        # Check source geometry files
        geometry_files = manifest_data.get("source_geometry_files", [])
        if not geometry_files:
            warnings.append("source_geometry_files is empty")

        # Check provenance
        if provenance:
            if not provenance.get("derivation_notes"):
                warnings.append("provenance.derivation_notes is empty")
            # Include created_at from top-level if not in provenance
            if "created_at" not in provenance and manifest_data.get("created_at"):
                provenance["created_at"] = manifest_data["created_at"]
        else:
            warnings.append("provenance metadata is missing")

    return InspectionResult(
        valid=len(errors) == 0,
        package_type=package_type,
        operation_type=operation_type,
        manifest_version=manifest_version,
        authority=authority,
        files=files,
        provenance=provenance,
        warnings=warnings,
        errors=errors,
    )


def format_terminal_output(result: InspectionResult) -> str:
    """Format inspection result for terminal display."""
    lines = []
    lines.append("CAM Assist Strategy Package Inspection")
    lines.append("=" * 39)
    lines.append("")

    # Package type
    lines.append("Package Type:")
    lines.append(f"  {result.package_type or 'unknown'}")
    lines.append("")

    # Operation type
    lines.append("Operation Type:")
    lines.append(f"  {result.operation_type or 'unknown'}")
    lines.append("")

    # Manifest version
    lines.append("Manifest Version:")
    lines.append(f"  {result.manifest_version or 'unknown'}")
    lines.append("")

    # Authority status
    lines.append("Authority Status:")
    if result.authority:
        if result.authority.get("non_execution_declaration") is True:
            lines.append("  NON-EXECUTION PACKAGE")
        if result.authority.get("requires_human_review") is True:
            lines.append("  Human review required")
        if result.authority.get("execution_authority_claim") is False:
            lines.append("  Execution authority denied")
    else:
        lines.append("  [MISSING]")
    lines.append("")

    # Files
    lines.append("Files:")
    for file_name, status in result.files.items():
        if status == "present":
            lines.append(f"  [OK] {file_name}")
        elif status == "missing":
            lines.append(f"  [MISSING] {file_name}")
        else:
            lines.append(f"  [FAIL] {file_name}")
    lines.append("")

    # Provenance
    lines.append("Provenance:")
    if result.provenance:
        lines.append(f"  created_by: {result.provenance.get('created_by', 'unknown')}")
        lines.append(
            f"  source_spec_id: {result.provenance.get('source_spec_id', 'unknown')}"
        )
        lines.append(f"  created_at: {result.provenance.get('created_at', 'unknown')}")
    else:
        lines.append("  [MISSING]")
    lines.append("")

    # Warnings
    lines.append("Warnings:")
    if result.warnings:
        for warning in result.warnings:
            lines.append(f"  [WARN] {warning}")
    else:
        lines.append("  none")
    lines.append("")

    # Errors (if any)
    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  [FAIL] {error}")
        lines.append("")

    # Non-execution notice
    lines.append("-" * 39)
    lines.append("This package is advisory only.")
    lines.append("No machine execution authority is present.")
    lines.append("Human review is required before downstream CAM use.")

    return "\n".join(lines)


def format_json_output(result: InspectionResult) -> str:
    """Format inspection result as JSON."""
    output = {
        "valid": result.valid,
        "package_type": result.package_type,
        "operation_type": result.operation_type,
        "manifest_version": result.manifest_version,
        "authority": result.authority,
        "files": result.files,
        "provenance": result.provenance,
        "warnings": result.warnings,
    }
    if result.errors:
        output["errors"] = result.errors
    return json.dumps(output, indent=2)


def format_quiet_output(result: InspectionResult, package_dir: Path) -> str:
    """Format minimal pass/fail output."""
    if result.valid:
        return f"PASS: {package_dir}"
    else:
        return f"FAIL: {package_dir}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect CAM Assist strategy package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "package_dir",
        type=Path,
        help="Path to the strategy package directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only print pass/fail summary",
    )

    args = parser.parse_args()
    package_dir: Path = args.package_dir

    if not package_dir.exists():
        print(f"Error: Package directory not found: {package_dir}", file=sys.stderr)
        return 2

    result = inspect_package(package_dir)

    if args.json:
        print(format_json_output(result))
    elif args.quiet:
        output = format_quiet_output(result, package_dir)
        if result.valid:
            print(output)
        else:
            print(output, file=sys.stderr)
    else:
        print(format_terminal_output(result))

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
