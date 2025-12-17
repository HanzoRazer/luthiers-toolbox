"""
Basic Rings Generator - Bundle 31.0.2

Simple concentric rings generator with configurable widths.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ...schemas.rosette_params import RosetteParamSpec, RingParam
from .registry import register_generator


def basic_rings_v1(
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    params: Dict[str, Any],
) -> RosetteParamSpec:
    """
    Generate a simple concentric rings pattern.

    Params:
        ring_count: int - Number of rings (default: 3)
        ring_widths: List[float] - Explicit widths per ring (optional)
        pattern_types: List[str] - Pattern type per ring (optional)
        auto_fill: bool - If True, auto-distribute widths to fill span (default: True)
    """
    ring_count = int(params.get("ring_count", 3))
    ring_widths = params.get("ring_widths") or []
    pattern_types = params.get("pattern_types") or []
    auto_fill = params.get("auto_fill", True)

    # Calculate available radial span
    outer_r = outer_diameter_mm / 2.0
    inner_r = inner_diameter_mm / 2.0
    span = max(0.1, outer_r - inner_r)

    # Generate ring params
    rings: List[RingParam] = []

    if ring_widths and len(ring_widths) >= ring_count:
        # Use explicit widths
        for i in range(ring_count):
            width = float(ring_widths[i])
            pattern = pattern_types[i] if i < len(pattern_types) else "SOLID"
            rings.append(RingParam(
                ring_index=i,
                width_mm=max(0.1, width),
                pattern_type=str(pattern),
            ))
    elif auto_fill:
        # Auto-distribute widths evenly
        width_each = span / max(1, ring_count)
        for i in range(ring_count):
            pattern = pattern_types[i] if i < len(pattern_types) else "SOLID"
            rings.append(RingParam(
                ring_index=i,
                width_mm=width_each,
                pattern_type=str(pattern),
            ))
    else:
        # Default fixed width
        default_width = min(2.0, span / max(1, ring_count))
        for i in range(ring_count):
            pattern = pattern_types[i] if i < len(pattern_types) else "SOLID"
            rings.append(RingParam(
                ring_index=i,
                width_mm=default_width,
                pattern_type=str(pattern),
            ))

    return RosetteParamSpec(
        outer_diameter_mm=outer_diameter_mm,
        inner_diameter_mm=inner_diameter_mm,
        ring_params=rings,
    )


# Register the generator
register_generator(
    key="basic_rings@1",
    fn=basic_rings_v1,
    name="Basic Rings",
    description="Simple concentric rings with configurable count and widths",
    param_hints={
        "ring_count": {"type": "int", "default": 3, "min": 1, "max": 20},
        "ring_widths": {"type": "list[float]", "optional": True},
        "pattern_types": {"type": "list[str]", "optional": True, "values": ["SOLID", "MOSAIC", "HATCH", "DOTS"]},
        "auto_fill": {"type": "bool", "default": True},
    },
)
