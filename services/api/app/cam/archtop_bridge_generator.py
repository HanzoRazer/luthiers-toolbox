"""Archtop Floating Bridge Generator.

Generates DXF files for floating bridges used on archtop guitars.
Includes:
- Bridge base plate with post holes
- String slots at specified spacing
- Optional thumb wheel cutouts

Usage:
    python archtop_bridge_generator.py --fit fit.json --out bridge.dxf

Author: The Production Shop
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


def generate_bridge_dxf(
    fit_params: Dict[str, Any],
    post_spacing_mm: float = 75.0,
    bridge_base_length_mm: float = 120.0,
    bridge_base_width_mm: float = 20.0,
    string_spacing_mm: float = 52.0,
    output_path: str = "archtop_bridge.dxf",
) -> Dict[str, Any]:
    """
    Generate floating bridge DXF from fit parameters.

    Args:
        fit_params: Dictionary from /fit endpoint containing bridge_height_mm, etc.
        post_spacing_mm: Distance between thumb wheel posts
        bridge_base_length_mm: Total bridge length
        bridge_base_width_mm: Bridge width (front to back)
        string_spacing_mm: Total string spread (low E to high E)
        output_path: Output DXF file path

    Returns:
        Dictionary with ok status, output path, and dimensions
    """
    if not EZDXF_AVAILABLE:
        return {"ok": False, "error": "ezdxf not installed"}

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("BRIDGE_OUTLINE", color=7)  # White
    doc.layers.add("POST_HOLES", color=1)      # Red
    doc.layers.add("STRING_SLOTS", color=3)    # Green
    doc.layers.add("CENTERLINE", color=5)      # Blue

    # Bridge base rectangle centered at origin
    half_length = bridge_base_length_mm / 2
    half_width = bridge_base_width_mm / 2

    # Main outline with rounded ends
    corner_radius = 3.0
    outline_points = [
        (-half_length + corner_radius, -half_width),
        (half_length - corner_radius, -half_width),
        (half_length, -half_width + corner_radius),
        (half_length, half_width - corner_radius),
        (half_length - corner_radius, half_width),
        (-half_length + corner_radius, half_width),
        (-half_length, half_width - corner_radius),
        (-half_length, -half_width + corner_radius),
    ]
    msp.add_lwpolyline(outline_points, close=True, dxfattribs={"layer": "BRIDGE_OUTLINE"})

    # Post holes (for thumb wheels)
    post_hole_diameter = 6.0  # M6 thread typical
    post_y = 0  # Centered
    for x in [-post_spacing_mm / 2, post_spacing_mm / 2]:
        msp.add_circle((x, post_y), post_hole_diameter / 2, dxfattribs={"layer": "POST_HOLES"})

    # String slots (6 strings)
    num_strings = 6
    string_positions = []
    for i in range(num_strings):
        x = -string_spacing_mm / 2 + (i * string_spacing_mm / (num_strings - 1))
        string_positions.append(x)
        # Slot as small rectangle
        slot_width = 1.5
        slot_depth = 2.0
        slot_y = half_width - 2  # Near top edge
        msp.add_lwpolyline([
            (x - slot_width / 2, slot_y),
            (x + slot_width / 2, slot_y),
            (x + slot_width / 2, slot_y - slot_depth),
            (x - slot_width / 2, slot_y - slot_depth),
        ], close=True, dxfattribs={"layer": "STRING_SLOTS"})

    # Centerline
    msp.add_line((-half_length - 5, 0), (half_length + 5, 0), dxfattribs={"layer": "CENTERLINE"})

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))

    return {
        "ok": True,
        "output_path": str(output_path),
        "dimensions": {
            "length_mm": bridge_base_length_mm,
            "width_mm": bridge_base_width_mm,
            "post_spacing_mm": post_spacing_mm,
            "string_spacing_mm": string_spacing_mm,
            "post_hole_diameter_mm": post_hole_diameter,
            "string_positions_mm": string_positions,
        },
        "layers": ["BRIDGE_OUTLINE", "POST_HOLES", "STRING_SLOTS", "CENTERLINE"],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate archtop floating bridge DXF")
    parser.add_argument("--fit", required=True, help="Path to fit parameters JSON")
    parser.add_argument("--post-spacing", type=float, default=75.0, help="Post spacing in mm")
    parser.add_argument("--length", type=float, default=120.0, help="Bridge length in mm")
    parser.add_argument("--width", type=float, default=20.0, help="Bridge width in mm")
    parser.add_argument("--string-spacing", type=float, default=52.0, help="String spacing in mm")
    parser.add_argument("--out", default="archtop_bridge.dxf", help="Output DXF path")
    args = parser.parse_args()

    with open(args.fit) as f:
        fit_params = json.load(f)

    result = generate_bridge_dxf(
        fit_params=fit_params.get("fit_parameters", fit_params),
        post_spacing_mm=args.post_spacing,
        bridge_base_length_mm=args.length,
        bridge_base_width_mm=args.width,
        string_spacing_mm=args.string_spacing,
        output_path=args.out,
    )

    if result["ok"]:
        print(f"Bridge DXF generated: {result['output_path']}")
        print(f"Dimensions: {result['dimensions']}")
    else:
        print(f"Error: {result.get('error')}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
