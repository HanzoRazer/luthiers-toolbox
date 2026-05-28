#!/usr/bin/env python3
"""
CAM Assist Strategy Package Assembly CLI

Assembles validated CAM Assist artifacts into a portable, reviewable
strategy package directory.

Combines:
- Validated strategy JSON (A2)
- Generated review packet (A3)
- Strategy package manifest (A4)

Usage:
    python scripts/assemble_strategy_package.py examples/valid/fret_slot_strategy.json
    python scripts/assemble_strategy_package.py strategy.json --out ./my_package
    python scripts/assemble_strategy_package.py strategy.json --force

Exit codes:
    0 — Package assembled successfully
    1 — Validation failure
    2 — File/read/write error
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generate_review_packet import generate_review_packet
from validate_manifest import validate_manifest
from validate_strategy_package import validate_strategy_package, load_json
from version import CAM_ASSIST_VERSION


def derive_operation_type(data: dict) -> str | None:
    """Derive operation_type from strategy data."""
    if "operation_type" in data:
        return data["operation_type"]
    if "operation_intent" in data and isinstance(data["operation_intent"], dict):
        if "operation_type" in data["operation_intent"]:
            op_type = data["operation_intent"]["operation_type"]
            if not op_type.endswith("_strategy"):
                return f"{op_type}_strategy"
            return op_type
    if "operation" in data and isinstance(data["operation"], str):
        return f"{data['operation']}_strategy"
    return None


def derive_source_spec_id(data: dict, input_filename: str) -> str:
    """Derive source_spec_id from strategy data or filename."""
    if "strategy_id" in data and data["strategy_id"]:
        return data["strategy_id"]
    return Path(input_filename).stem


def generate_manifest(
    data: dict,
    input_filename: str,
) -> dict:
    """Generate a strategy package manifest from validated strategy data."""
    operation_type = derive_operation_type(data)
    if not operation_type:
        raise ValueError(
            "Cannot derive operation_type: "
            "strategy must have 'operation_type' or 'operation' field"
        )

    return {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": operation_type,
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cam_assist_version": CAM_ASSIST_VERSION,
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": derive_source_spec_id(data, input_filename),
            "created_by": "cam-assist-assembly",
            "derivation_notes": (
                f"Assembled from {input_filename} by CAM-A5 Strategy Package Assembly CLI."
            ),
        },
    }


def assemble_package(
    strategy_path: Path,
    output_dir: Path,
    force: bool = False,
) -> tuple[bool, str]:
    """
    Assemble a strategy package from a validated strategy JSON.

    Returns (success, message).
    """
    # Check output directory
    if output_dir.exists():
        if not force:
            return False, f"Output directory already exists: {output_dir} (use --force to overwrite)"
        shutil.rmtree(output_dir)

    # Load and validate strategy
    data, load_error = load_json(strategy_path)
    if load_error:
        return False, f"Failed to load strategy: {load_error}"

    validation_result = validate_strategy_package(data)
    if not validation_result.valid:
        errors = "; ".join(validation_result.errors)
        return False, f"Strategy validation failed: {errors}"

    # Generate review packet
    try:
        review_packet_content = generate_review_packet(data)
    except Exception as e:
        return False, f"Failed to generate review packet: {e}"

    # Generate manifest
    try:
        manifest_data = generate_manifest(data, strategy_path.name)
    except ValueError as e:
        return False, f"Failed to generate manifest: {e}"

    # Create output directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, f"Failed to create output directory: {e}"

    # Write strategy.json (copy with normalized name)
    strategy_out = output_dir / "strategy.json"
    try:
        with open(strategy_out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except OSError as e:
        return False, f"Failed to write strategy.json: {e}"

    # Write review_packet.md
    review_out = output_dir / "review_packet.md"
    try:
        with open(review_out, "w", encoding="utf-8") as f:
            f.write(review_packet_content)
    except OSError as e:
        return False, f"Failed to write review_packet.md: {e}"

    # Write manifest.json
    manifest_out = output_dir / "manifest.json"
    try:
        with open(manifest_out, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            f.write("\n")
    except OSError as e:
        return False, f"Failed to write manifest.json: {e}"

    # Validate the generated manifest
    manifest_validation = validate_manifest(manifest_data, manifest_out)
    if not manifest_validation.valid:
        errors = "; ".join(manifest_validation.errors)
        return False, f"Generated manifest validation failed: {errors}"

    return True, f"Strategy package assembled: {output_dir}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assemble CAM Assist strategy package from validated strategy JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "strategy_json",
        type=Path,
        help="Path to the strategy JSON file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for the package (default: ./<strategy_stem>_package/)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output directory",
    )

    args = parser.parse_args()
    strategy_path: Path = args.strategy_json

    if not strategy_path.exists():
        print(f"Error: File not found: {strategy_path}", file=sys.stderr)
        return 2

    # Determine output directory
    if args.out:
        output_dir = args.out
    else:
        output_dir = Path.cwd() / f"{strategy_path.stem}_package"

    success, message = assemble_package(strategy_path, output_dir, args.force)

    if success:
        print(f"PASS: {message}")
        return 0
    else:
        print(f"FAIL: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
