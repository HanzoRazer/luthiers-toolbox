"""
VINE-11: Bridge between instrument BracePattern specs and BracingPreset for UI.

This module converts instrument-specific bracing data from x_brace.py
(extracted from DXF construction drawings) to BracingPreset format
used by the /art-studio/bracing/presets endpoint.
"""

from __future__ import annotations

import math
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .bracing_router import BracingPreset, BracingPreviewRequest

from ..instrument_geometry.bracing.x_brace import (
    BracePattern,
    get_j45_bracing,
    get_dreadnought_bracing,
    get_jumbo_bracing,
)


def _brace_length_from_endpoints(start: tuple, end: tuple) -> float:
    """Calculate brace length from start/end coordinates."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    return math.sqrt(dx * dx + dy * dy)


def brace_pattern_to_preset(
    pattern: BracePattern,
    preset_id: str,
    preset_name: str,
    description: str,
    density_kg_m3: float = 420.0,
):
    """
    Convert a BracePattern from instrument specs to a BracingPreset.

    VINE-11: Bridges instrument geometry specs to UI presets.
    """
    # Import here to avoid circular imports
    from .bracing_router import BracingPreset, BracingPreviewRequest

    braces = []
    for brace_dict in pattern.braces:
        start = brace_dict.get("start", (0, 0))
        end = brace_dict.get("end", (0, 0))
        length_mm = _brace_length_from_endpoints(start, end)
        profile_type = "scalloped" if brace_dict.get("scalloped", False) else "rectangular"

        braces.append(BracingPreviewRequest(
            profile_type=profile_type,
            width_mm=brace_dict.get("width_mm", 12.0),
            height_mm=brace_dict.get("height_mm", 8.0),
            length_mm=round(length_mm, 1),
            density_kg_m3=density_kg_m3,
        ))

    return BracingPreset(
        id=preset_id,
        name=preset_name,
        description=description,
        braces=braces,
        source="instrument-spec",
    )


def get_instrument_presets():
    """
    Load bracing presets from instrument geometry specs.

    VINE-11: These presets use actual measured dimensions from
    construction drawings (DXF extractions).

    Returns:
        List of BracingPreset with source="instrument-spec"
    """
    presets = []

    # Gibson J-45 (from J45 DIMS.dxf)
    j45_pattern = get_j45_bracing()
    presets.append(brace_pattern_to_preset(
        pattern=j45_pattern,
        preset_id="gibson-j45-x",
        preset_name="Gibson J-45 X-Brace",
        description="J-45 round-shoulder dreadnought (6.35mm x 12.70mm braces)",
        density_kg_m3=420.0,
    ))

    # Dreadnought (standard)
    dread_pattern = get_dreadnought_bracing()
    presets.append(brace_pattern_to_preset(
        pattern=dread_pattern,
        preset_id="dreadnought-scalloped-x",
        preset_name="Dreadnought Scalloped X",
        description="Standard dreadnought X-bracing pattern",
        density_kg_m3=420.0,
    ))

    # Jumbo (J-200 style)
    jumbo_pattern = get_jumbo_bracing()
    presets.append(brace_pattern_to_preset(
        pattern=jumbo_pattern,
        preset_id="jumbo-j200-x",
        preset_name="Jumbo J-200 X-Brace",
        description="J-200 style jumbo X-bracing pattern",
        density_kg_m3=420.0,
    ))

    return presets
