# services/api/app/calculators/tool_profiles.py

"""
Tool & Material Profile Helpers

Adapter module that calculators & the Saw Bridge call to get:
- Flute counts
- Ideal chipload bands
- Heat sensitivity weights

Provides sensible defaults if the library entry is missing.
"""

from __future__ import annotations

from typing import Tuple

from ..data.tool_library import (
    get_tool_profile,
    get_material_profile,
)


def resolve_flute_count(tool_id: str, default: int = 2) -> int:
    """
    Get flute count for a tool, with fallback to default.

    Args:
        tool_id: Tool identifier (e.g., "vbit_60_3mm")
        default: Default flute count if tool not found

    Returns:
        Number of flutes (minimum 1)
    """
    profile = get_tool_profile(tool_id)
    if profile is None:
        return default
    return max(1, profile.flutes)


def resolve_chipload_band(
    tool_id: str,
    default_min: float = 0.01,
    default_max: float = 0.04,
) -> Tuple[float, float]:
    """
    Get recommended chipload band for a tool.

    Args:
        tool_id: Tool identifier
        default_min: Default minimum chipload if tool not found
        default_max: Default maximum chipload if tool not found

    Returns:
        Tuple of (min_chipload_mm, max_chipload_mm)
    """
    profile = get_tool_profile(tool_id)
    if profile is None:
        return default_min, default_max
    return profile.chipload_min_mm, profile.chipload_max_mm


def resolve_heat_weight_for_material(material_id: str) -> float:
    """
    Get heat sensitivity weighting factor for a material.

    - "high"   → 1.2 (more heat-sensitive, e.g., ebony)
    - "medium" → 1.0 (standard)
    - "low"    → 0.8 (heat-tolerant)

    This can be used to scale heat_index in Saw Lab bridge.

    Args:
        material_id: Material identifier (e.g., "ebony", "maple")

    Returns:
        Heat weighting factor (0.8 to 1.2)
    """
    profile = get_material_profile(material_id)
    if profile is None:
        return 1.0

    sensitivity = profile.heat_sensitivity.lower()
    if sensitivity == "high":
        return 1.2
    if sensitivity == "low":
        return 0.8
    return 1.0
