#!/usr/bin/env python3
"""
CAM Assist LTB CAM Output Importer

Transforms luthiers-toolbox CAM output into CAM-Assist strategy JSON.

Usage:
    python scripts/import_ltb_cam_output.py <ltb_output.json> --out strategy.json
    python scripts/import_ltb_cam_output.py <ltb_output_dir>/ --out strategy.json

Exit codes:
    0 — Import successful
    1 — Validation error (missing required field)
    2 — File/read/write error
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "operation.operation_type": "operation type",
    "operation.target_feature": "target feature",
    "operation.cut_intent": "cut intent",
    "operation.method": "machining method",
    "geometry.dxf_file": "DXF file",
    "geometry.primary_layer": "primary layer",
    "tool.tool_type": "tool type",
    "tool.diameter_mm": "tool diameter",
    "parameters.depth_mm": "cut depth",
    "parameters.feed_mm_min": "feed rate",
    "material.material_class": "material class",
    "units.linear": "linear units",
    "coordinate_frame.origin": "coordinate origin",
    "coordinate_frame.x_axis": "X axis",
    "coordinate_frame.y_axis": "Y axis",
    "provenance.source_spec_id": "source spec ID",
    "provenance.ltb_version": "LTB version",
    "provenance.created_at": "creation timestamp",
}

MM_TO_INCHES = 0.0393701


def get_nested(data: dict, path: str) -> Any:
    """Get nested value by dot path."""
    keys = path.split(".")
    value = data
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def validate_ltb_output(data: dict) -> list[str]:
    """Validate LTB output. Returns list of errors."""
    errors = []
    for field_path, description in REQUIRED_FIELDS.items():
        value = get_nested(data, field_path)
        if value is None:
            errors.append(f"Missing required field '{field_path}' ({description})")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"Empty required field '{field_path}' ({description})")

    linear_units = get_nested(data, "units.linear")
    if linear_units and linear_units != "mm":
        errors.append(f"Linear units must be 'mm', got '{linear_units}'")

    return errors


def mm_to_inches(value: float | None) -> float | None:
    """Convert mm to inches."""
    if value is None:
        return None
    return round(value * MM_TO_INCHES, 6)


def transform_to_strategy(ltb_data: dict, target_units: str = "inches") -> dict:
    """Transform LTB output to strategy format."""
    convert = target_units == "inches"

    operation = ltb_data.get("operation", {})
    geometry = ltb_data.get("geometry", {})
    tool = ltb_data.get("tool", {})
    parameters = ltb_data.get("parameters", {})
    material = ltb_data.get("material", {})
    coord_frame = ltb_data.get("coordinate_frame", {})
    provenance = ltb_data.get("provenance", {})

    if convert:
        depth = mm_to_inches(parameters.get("depth_mm"))
        tool_diameter = mm_to_inches(tool.get("diameter_mm"))
    else:
        depth = parameters.get("depth_mm")
        tool_diameter = tool.get("diameter_mm")

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
        },

        "operation_intent": {
            "operation_type": operation.get("operation_type", ""),
            "target_feature": operation.get("target_feature", ""),
            "cut_intent": operation.get("cut_intent", ""),
            "non_execution_declaration": True,
        },

        "material_context": {
            "material_class": material.get("material_class", "unknown"),
            "species": material.get("species"),
            "hardness_janka": material.get("hardness_janka"),
        },

        "safety_boundary": {
            "non_execution_declaration": True,
            "human_review_required": True,
            "execution_authority_claim": False,
            "max_depth_inches": depth if convert else mm_to_inches(depth),
            "tool_diameter_inches": tool_diameter if convert else mm_to_inches(tool_diameter),
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
            },
            "parameters": {
                "depth": depth,
                "feed_rate_ipm": mm_to_inches(parameters.get("feed_mm_min")) * 60 if convert else parameters.get("feed_mm_min"),
                "spindle_rpm": parameters.get("spindle_rpm"),
            },
        },

        "warnings": [],
        "approval_state": "pending",
    }

    return _clean_none(strategy)


def _clean_none(obj: Any) -> Any:
    """Remove None values from nested dicts."""
    if isinstance(obj, dict):
        return {k: _clean_none(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [_clean_none(item) for item in obj]
    return obj


def import_ltb_output(
    input_path: Path,
    output_path: Path,
    target_units: str = "inches",
) -> dict:
    """Import LTB output and produce strategy JSON."""
    if input_path.is_dir():
        json_path = input_path / "cam_output.json"
        dxf_dir = input_path
    else:
        json_path = input_path
        dxf_dir = input_path.parent

    if not json_path.exists():
        raise FileNotFoundError(f"LTB output not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ltb_data = json.load(f)

    errors = validate_ltb_output(ltb_data)
    if errors:
        raise ValueError("LTB output validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    strategy = transform_to_strategy(ltb_data, target_units)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(strategy, f, indent=2)

    dxf_filename = ltb_data.get("geometry", {}).get("dxf_file", "geometry.dxf")
    dxf_source = dxf_dir / dxf_filename
    if dxf_source.exists():
        shutil.copy2(dxf_source, output_path.parent / dxf_filename)

    return strategy


def main() -> int:
    parser = argparse.ArgumentParser(description="Import LTB CAM output to CAM-Assist strategy")
    parser.add_argument("input", type=Path, help="LTB output JSON or directory")
    parser.add_argument("--out", type=Path, required=True, help="Output strategy.json path")
    parser.add_argument("--units", choices=["inches", "mm"], default="inches")
    parser.add_argument("--quiet", "-q", action="store_true")

    args = parser.parse_args()

    try:
        strategy = import_ltb_output(args.input, args.out, args.units)
        if not args.quiet:
            print(f"Imported: {args.out}")
            print(f"  Operation: {strategy.get('operation_intent', {}).get('operation_type')}")
        return 0
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1
    except (FileNotFoundError, OSError) as e:
        print(f"File error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
