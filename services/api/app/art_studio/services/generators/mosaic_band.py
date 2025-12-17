"""
Mosaic Band Generator - Bundle 31.0.2

Patterned band generator with tile configuration for mosaic-style rosettes.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ...schemas.rosette_params import RosetteParamSpec, RingParam
from .registry import register_generator


def mosaic_band_v1(
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    params: Dict[str, Any],
) -> RosetteParamSpec:
    """
    Generate a mosaic-style banded pattern.

    Params:
        outer_solid_width: float - Width of outer solid border (default: 1.0)
        inner_solid_width: float - Width of inner solid border (default: 1.0)
        mosaic_width: float - Width of central mosaic band (default: auto-fill)
        tile_length_mm: float - Tile length for mosaic band (default: 2.0)
        accent_rings: int - Number of accent rings in mosaic area (default: 0)
        accent_pattern: str - Pattern for accent rings (default: "DOTS")
    """
    outer_solid_width = float(params.get("outer_solid_width", 1.0))
    inner_solid_width = float(params.get("inner_solid_width", 1.0))
    mosaic_width = params.get("mosaic_width")  # None means auto-fill
    tile_length_mm = float(params.get("tile_length_mm", 2.0))
    accent_rings = int(params.get("accent_rings", 0))
    accent_pattern = str(params.get("accent_pattern", "DOTS"))

    # Calculate available radial span
    outer_r = outer_diameter_mm / 2.0
    inner_r = inner_diameter_mm / 2.0
    span = max(0.1, outer_r - inner_r)

    # Clamp border widths
    outer_solid_width = min(outer_solid_width, span * 0.4)
    inner_solid_width = min(inner_solid_width, span * 0.4)

    # Calculate mosaic width
    if mosaic_width is None:
        mosaic_width = span - outer_solid_width - inner_solid_width
    mosaic_width = max(0.5, float(mosaic_width))

    rings: List[RingParam] = []
    ring_index = 0

    # Inner solid border
    if inner_solid_width > 0:
        rings.append(RingParam(
            ring_index=ring_index,
            width_mm=inner_solid_width,
            pattern_type="SOLID",
        ))
        ring_index += 1

    # Mosaic band (possibly with accent rings interspersed)
    if accent_rings > 0 and mosaic_width > 1.0:
        # Divide mosaic into sections with accent rings
        section_count = accent_rings + 1
        section_width = mosaic_width / section_count
        accent_width = min(0.5, section_width * 0.3)
        mosaic_section_width = (mosaic_width - accent_width * accent_rings) / section_count

        for i in range(section_count):
            # Mosaic section
            rings.append(RingParam(
                ring_index=ring_index,
                width_mm=mosaic_section_width,
                pattern_type="MOSAIC",
                tile_length_mm=tile_length_mm,
            ))
            ring_index += 1

            # Accent ring (except after last section)
            if i < accent_rings:
                rings.append(RingParam(
                    ring_index=ring_index,
                    width_mm=accent_width,
                    pattern_type=accent_pattern,
                ))
                ring_index += 1
    else:
        # Single mosaic band
        rings.append(RingParam(
            ring_index=ring_index,
            width_mm=mosaic_width,
            pattern_type="MOSAIC",
            tile_length_mm=tile_length_mm,
        ))
        ring_index += 1

    # Outer solid border
    if outer_solid_width > 0:
        rings.append(RingParam(
            ring_index=ring_index,
            width_mm=outer_solid_width,
            pattern_type="SOLID",
        ))

    return RosetteParamSpec(
        outer_diameter_mm=outer_diameter_mm,
        inner_diameter_mm=inner_diameter_mm,
        ring_params=rings,
    )


# Register the generator
register_generator(
    key="mosaic_band@1",
    fn=mosaic_band_v1,
    name="Mosaic Band",
    description="Classic mosaic-style rosette with solid borders and patterned center band",
    param_hints={
        "outer_solid_width": {"type": "float", "default": 1.0, "min": 0, "max": 10},
        "inner_solid_width": {"type": "float", "default": 1.0, "min": 0, "max": 10},
        "mosaic_width": {"type": "float", "optional": True, "description": "Auto-fills if not specified"},
        "tile_length_mm": {"type": "float", "default": 2.0, "min": 0.5, "max": 10},
        "accent_rings": {"type": "int", "default": 0, "min": 0, "max": 5},
        "accent_pattern": {"type": "str", "default": "DOTS", "values": ["SOLID", "DOTS", "HATCH"]},
    },
)
