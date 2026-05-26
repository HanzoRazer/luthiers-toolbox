#!/usr/bin/env python3
"""
CAM Assist LTB CAM Output Importer

Transforms luthiers-toolbox CAM output into CAM-Assist strategy JSON.

This is a one-way, file-based bridge. It reads LTB output, validates against
the LTB_CAM_OUTPUT_CONTRACT.md specification, and produces a strategy.json
file that can be assembled into a strategy package.

Usage:
    python scripts/import_ltb_cam_output.py <ltb_output.json> --out strategy.json
    python scripts/import_ltb_cam_output.py <ltb_output_dir>/ --out strategy.json
    python scripts/import_ltb_cam_output.py <ltb_output.json> --out strategy.json --units inches

Exit codes:
    0 — Import successful
    1 — Validation error (missing required field, malformed input)
    2 — File/read/write error
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Required fields per LTB_CAM_OUTPUT_CONTRACT.md
REQUIRED_FIELDS = {
    "operation.operation_type": "operation type (feature being machined)",
    "operation.target_feature": "target feature (instrument part)",
    "operation.cut_intent": "cut intent (geometric intent)",
    "operation.method": "machining method",
    "geometry.dxf_file": "DXF geometry file reference",
    "geometry.primary_layer": "primary DXF layer",
    "tool.tool_type": "tool type",
    "tool.diameter_mm": "tool diameter",
    "parameters.depth_mm": "cut depth",
    "parameters.feed_mm_min": "feed rate",
    "material.material_class": "material class",
    "units.linear": "linear units",
    "units.angular": "angular units",
    "coordinate_frame.origin": "coordinate origin",
    "coordinate_frame.x_axis": "X axis direction",
    "coordinate_frame.y_axis": "Y axis direction",
    "provenance.source_spec_id": "source specification ID",
    "provenance.ltb_version": "LTB version",
    "provenance.created_at": "creation timestamp",
}

# CAM-Assist constitutional properties — injected, never read from LTB
CAM_ASSIST_INJECTED = {
    "operation_intent.non_execution_declaration": True,
    "safety_boundary.non_execution_declaration": True,
    "safety_boundary.human_review_required": True,
    "safety_boundary.execution_authority_claim": False,
    "approval_state": "pending",
}

MM_TO_INCHES = 0.0393701


def get_nested(data: dict, path: str) -> Any:
    """Get a nested value by dot-separated path."""
    keys = path.split(".")
    value = data
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def validate_ltb_output(data: dict) -> list[str]:
    """
    Validate LTB output against the contract.
    Returns list of error messages. Empty list means valid.
    """
    errors = []

    for field_path, description in REQUIRED_FIELDS.items():
        value = get_nested(data, field_path)
        if value is None:
            errors.append(f"Missing required field '{field_path}' ({description})")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"Empty required field '{field_path}' ({description})")

    # Validate units are metric (per contract)
    linear_units = get_nested(data, "units.linear")
    if linear_units and linear_units != "mm":
        errors.append(f"Linear units must be 'mm', got '{linear_units}'")

    return errors


def convert_mm_to_inches(value: float | None) -> float | None:
    """Convert millimeters to inches."""
    if value is None:
        return None
    return round(value * MM_TO_INCHES, 6)


def transform_ltb_to_strategy(
    ltb_data: dict,
    target_units: str = "inches",
) -> dict:
    """
    Transform LTB CAM output to CAM-Assist strategy format.

    CAM-Assist constitutional properties are injected unconditionally.
    They are never read from LTB output.
    """
    convert = target_units == "inches"

    # Extract values from LTB output
    operation = ltb_data.get("operation", {})
    geometry = ltb_data.get("geometry", {})
    tool = ltb_data.get("tool", {})
    parameters = ltb_data.get("parameters", {})
    material = ltb_data.get("material", {})
    coord_frame = ltb_data.get("coordinate_frame", {})
    provenance = ltb_data.get("provenance", {})
    toolpath = ltb_data.get("toolpath", {})

    # Convert dimensions if needed
    if convert:
        depth = convert_mm_to_inches(parameters.get("depth_mm"))
        depth_per_pass = convert_mm_to_inches(parameters.get("depth_per_pass_mm"))
        tool_diameter = convert_mm_to_inches(tool.get("diameter_mm"))
        feed_rate = convert_mm_to_inches(parameters.get("feed_mm_min"))
    else:
        depth = parameters.get("depth_mm")
        depth_per_pass = parameters.get("depth_per_pass_mm")
        tool_diameter = tool.get("diameter_mm")
        feed_rate = parameters.get("feed_mm_min")

    # Build strategy JSON
    strategy = {
        "strategy_version": "1.2",

        "strategy_id": f"{operation.get('operation_type', 'unknown')}-{provenance.get('source_spec_id', 'unknown')}",

        "units": target_units,

        "coordinate_frame": {
            "origin": coord_frame.get("origin", ""),
            "x_axis": coord_frame.get("x_axis", ""),
            "y_axis": coord_frame.get("y_axis", ""),
            "z_axis": coord_frame.get("z_axis", "into_material"),
            "datum_point": {"x": 0, "y": 0, "z": 0},
        },

        "provenance": {
            "source_spec_id": provenance.get("source_spec_id", ""),
            "cam_assist_version": "1.0.0",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "created_by": "import_ltb_cam_output",
            "ltb_version": provenance.get("ltb_version", ""),
            "ltb_created_at": provenance.get("created_at", ""),
        },

        # CAM-Assist constitutional property — injected, never read from LTB
        "operation_intent": {
            "operation_type": operation.get("operation_type", ""),
            "target_feature": operation.get("target_feature", ""),
            "cut_intent": operation.get("cut_intent", ""),
            "non_execution_declaration": True,  # INJECTED
        },

        "material_context": {
            "material_class": material.get("material_class", "unknown"),
            "species": material.get("species"),
            "hardness_janka": material.get("hardness_janka"),
            "grain_direction": material.get("grain_direction"),
        },

        # CAM-Assist constitutional properties — injected, never read from LTB
        "safety_boundary": {
            "non_execution_declaration": True,  # INJECTED
            "human_review_required": True,  # INJECTED
            "execution_authority_claim": False,  # INJECTED
            "max_depth_inches": depth if convert else convert_mm_to_inches(depth),
            "tool_diameter_inches": tool_diameter if convert else convert_mm_to_inches(tool_diameter),
        },

        "geometry": {
            "dxf_file": geometry.get("dxf_file", "geometry.dxf"),
            "primary_layer": geometry.get("primary_layer", ""),
            "reference_layers": geometry.get("reference_layers", []),
        },

        "operation": {
            "type": operation.get("cut_intent", ""),
            "method": operation.get("method", ""),
            "tool": {
                "reference_type": "dimension_spec",
                "tool_type": tool.get("tool_type", ""),
                "diameter": tool_diameter,
                "angle_deg": tool.get("angle_deg"),
                "description": tool.get("description", ""),
            },
            "parameters": {
                "depth": depth,
                "depth_per_pass": depth_per_pass,
                "feed_rate_ipm": feed_rate,
                "spindle_rpm": parameters.get("spindle_rpm"),
                "basis": "ltb_cam_output",
            },
        },

        # Include toolpath for provenance/review (not for execution)
        "toolpath_reference": {
            "format": toolpath.get("format", "ltb_toolpath_v1"),
            "included_for": "review_and_provenance",
            "not_for_execution": True,
        },

        "warnings": [],

        # CAM-Assist constitutional property — injected, never read from LTB
        "approval_state": "pending",  # INJECTED
    }

    # Remove None values from nested dicts
    strategy = _clean_none_values(strategy)

    return strategy


def _clean_none_values(obj: Any) -> Any:
    """Recursively remove None values from dicts."""
    if isinstance(obj, dict):
        return {k: _clean_none_values(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [_clean_none_values(item) for item in obj]
    return obj


def import_ltb_cam_output(
    input_path: Path,
    output_path: Path,
    target_units: str = "inches",
    copy_dxf: bool = True,
) -> dict:
    """
    Import LTB CAM output and produce strategy JSON.

    Args:
        input_path: Path to LTB output JSON or directory containing cam_output.json
        output_path: Path for output strategy.json
        target_units: Target unit system ('inches' or 'mm')
        copy_dxf: Whether to copy DXF file to output directory

    Returns:
        The generated strategy dict

    Raises:
        ValueError: On validation errors (missing required fields)
        FileNotFoundError: On missing input files
    """
    # Handle directory input
    if input_path.is_dir():
        json_path = input_path / "cam_output.json"
        dxf_dir = input_path
    else:
        json_path = input_path
        dxf_dir = input_path.parent

    if not json_path.exists():
        raise FileNotFoundError(f"LTB output not found: {json_path}")

    # Load and validate LTB output
    with open(json_path, "r", encoding="utf-8") as f:
        ltb_data = json.load(f)

    errors = validate_ltb_output(ltb_data)
    if errors:
        error_msg = "LTB output validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    # Transform to strategy format
    strategy = transform_ltb_to_strategy(ltb_data, target_units)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(strategy, f, indent=2)

    # Copy DXF if requested and exists
    if copy_dxf:
        dxf_filename = ltb_data.get("geometry", {}).get("dxf_file", "geometry.dxf")
        dxf_source = dxf_dir / dxf_filename
        if dxf_source.exists():
            dxf_dest = output_path.parent / dxf_filename
            shutil.copy2(dxf_source, dxf_dest)

    return strategy


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import luthiers-toolbox CAM output into CAM-Assist strategy format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to LTB output JSON file or directory containing cam_output.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for strategy.json",
    )
    parser.add_argument(
        "--units",
        choices=["inches", "mm"],
        default="inches",
        help="Target unit system (default: inches)",
    )
    parser.add_argument(
        "--no-copy-dxf",
        action="store_true",
        help="Don't copy DXF file to output directory",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print errors",
    )

    args = parser.parse_args()

    try:
        strategy = import_ltb_cam_output(
            input_path=args.input,
            output_path=args.out,
            target_units=args.units,
            copy_dxf=not args.no_copy_dxf,
        )

        if not args.quiet:
            print(f"Strategy imported: {args.out}")
            print(f"  Operation: {strategy.get('operation_intent', {}).get('operation_type', 'unknown')}")
            print(f"  Units: {strategy.get('units', 'unknown')}")
            print(f"  Non-execution declared: {strategy.get('operation_intent', {}).get('non_execution_declaration', False)}")

        return 0

    except ValueError as e:
        print(f"Import error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"File error: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"File error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
