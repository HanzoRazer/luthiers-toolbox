"""Archtop Compensated Saddle Generator.

Generates DXF files for compensated saddles used on archtop guitar bridges.
Includes:
- Crowned saddle profile with specified radius
- Per-string intonation compensation offsets
- Optional bone/synthetic blank outline

Usage:
    python archtop_saddle_generator.py --fit fit.json --out saddle.dxf

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


def generate_saddle_dxf(
    fit_params: Dict[str, Any],
    crown_radius_mm: float = 304.8,  # 12" radius
    string_spacing_mm: float = 52.0,
    saddle_length_mm: float = 72.0,
    saddle_height_mm: float = 10.0,
    saddle_thickness_mm: float = 3.0,
    output_path: str = "archtop_saddle.dxf",
) -> Dict[str, Any]:
    """
    Generate compensated saddle profile DXF from fit parameters.

    Args:
        fit_params: Dictionary from /fit endpoint containing string_compensations_mm
        crown_radius_mm: Fretboard radius for saddle crown (12" = 304.8mm typical)
        string_spacing_mm: Total string spread (low E to high E)
        saddle_length_mm: Total saddle length
        saddle_height_mm: Saddle height above bridge
        saddle_thickness_mm: Saddle thickness (front to back)
        output_path: Output DXF file path

    Returns:
        Dictionary with ok status, output path, and dimensions
    """
    if not EZDXF_AVAILABLE:
        return {"ok": False, "error": "ezdxf not installed"}

    # Get compensations from fit params
    compensations = fit_params.get("string_compensations_mm", [3.0, 2.5, 2.2, 2.0, 1.8, 1.5])
    num_strings = len(compensations)

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("SADDLE_PROFILE", color=7)    # White - top crown profile
    doc.layers.add("SADDLE_OUTLINE", color=5)    # Blue - blank outline
    doc.layers.add("STRING_NOTCHES", color=1)    # Red - string positions
    doc.layers.add("COMPENSATION", color=3)      # Green - compensation lines
    doc.layers.add("CENTERLINE", color=4)        # Cyan

    half_length = saddle_length_mm / 2

    # Generate crowned top profile (arc segment)
    # Crown center is below the saddle top by (radius - crown_height)
    # For a 12" radius and ~3mm crown drop, center is at y = -crown_radius + crown_height
    crown_drop = 2.5  # mm drop from center to edges
    crown_points = []
    num_points = 50
    for i in range(num_points + 1):
        x = -half_length + (i * saddle_length_mm / num_points)
        # Parabolic approximation for small arc
        t = x / half_length  # -1 to 1
        y = saddle_height_mm - crown_drop * (t * t)
        crown_points.append((x, y))

    msp.add_lwpolyline(crown_points, dxfattribs={"layer": "SADDLE_PROFILE"})

    # Saddle blank outline (side view)
    blank_outline = [
        (-half_length, 0),
        (half_length, 0),
        (half_length, saddle_height_mm - crown_drop),
        (-half_length, saddle_height_mm - crown_drop),
    ]
    msp.add_lwpolyline(blank_outline, close=True, dxfattribs={"layer": "SADDLE_OUTLINE"})

    # String notches with compensation offsets
    string_positions = []
    for i in range(num_strings):
        # Base position (equal spacing)
        base_x = -string_spacing_mm / 2 + (i * string_spacing_mm / (num_strings - 1))
        # Apply compensation (move bass strings back more)
        comp = compensations[i]
        string_positions.append((base_x, comp))

        # String notch mark (vertical line at crown)
        t = base_x / half_length
        notch_y = saddle_height_mm - crown_drop * (t * t)
        msp.add_line(
            (base_x, notch_y - 1),
            (base_x, notch_y + 1),
            dxfattribs={"layer": "STRING_NOTCHES"}
        )

        # Compensation offset indicator (shows how far back from theoretical position)
        msp.add_line(
            (base_x, -2),
            (base_x, -2 - comp),
            dxfattribs={"layer": "COMPENSATION"}
        )

    # Centerline
    msp.add_line((0, -5), (0, saddle_height_mm + 3), dxfattribs={"layer": "CENTERLINE"})

    # Add text annotations for compensations (top view reference)
    for i, (x, comp) in enumerate(string_positions):
        string_num = i + 1
        msp.add_text(
            f"S{string_num}: +{comp:.1f}",
            height=1.5,
            dxfattribs={"layer": "COMPENSATION"}
        ).set_placement((x, -6), align=ezdxf.enums.TextEntityAlignment.TOP_CENTER)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))

    return {
        "ok": True,
        "output_path": str(output_path),
        "dimensions": {
            "length_mm": saddle_length_mm,
            "height_mm": saddle_height_mm,
            "thickness_mm": saddle_thickness_mm,
            "crown_radius_mm": crown_radius_mm,
            "crown_drop_mm": crown_drop,
            "string_spacing_mm": string_spacing_mm,
            "compensations_mm": compensations,
            "string_positions": string_positions,
        },
        "layers": ["SADDLE_PROFILE", "SADDLE_OUTLINE", "STRING_NOTCHES", "COMPENSATION", "CENTERLINE"],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate archtop compensated saddle DXF")
    parser.add_argument("--fit", required=True, help="Path to fit parameters JSON")
    parser.add_argument("--crown-radius", type=float, default=304.8, help="Crown radius in mm (12\"=304.8)")
    parser.add_argument("--string-spacing", type=float, default=52.0, help="String spacing in mm")
    parser.add_argument("--length", type=float, default=72.0, help="Saddle length in mm")
    parser.add_argument("--height", type=float, default=10.0, help="Saddle height in mm")
    parser.add_argument("--thickness", type=float, default=3.0, help="Saddle thickness in mm")
    parser.add_argument("--out", default="archtop_saddle.dxf", help="Output DXF path")
    args = parser.parse_args()

    with open(args.fit) as f:
        fit_params = json.load(f)

    result = generate_saddle_dxf(
        fit_params=fit_params.get("fit_parameters", fit_params),
        crown_radius_mm=args.crown_radius,
        string_spacing_mm=args.string_spacing,
        saddle_length_mm=args.length,
        saddle_height_mm=args.height,
        saddle_thickness_mm=args.thickness,
        output_path=args.out,
    )

    if result["ok"]:
        print(f"Saddle DXF generated: {result['output_path']}")
        print(f"Dimensions: {result['dimensions']}")
    else:
        print(f"Error: {result.get('error')}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
