# services/api/app/calculators/saw_bridge.py

"""
Saw Lab Physics Bridge

Entry point for all physics coming from Saw Lab calculators.

This is the official place where Saw Lab calculators plug into RMOS/Art Studio.
Right now it:
- Uses tool & material profiles for flutes and chipload bands
- Returns a usable physics summary even if the Saw Lab modules aren't in place yet

Future:
- Replace the inner block with calls into actual Saw Lab calculators
  (bite, heat, deflection, kickback, etc.)

CURRENT IMPLEMENTATION (Wave 6):
- Uses tool & material profiles for:
  - flute count
  - ideal chipload band (min/max)
  - heat sensitivity weighting
- Still a placeholder approximation, but now parameterized by
  real tool/material data instead of pure constants.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from .tool_profiles import (
    resolve_flute_count,
    resolve_chipload_band,
    resolve_heat_weight_for_material,
)


@dataclass
class SawPhysicsResult:
    """
    Physics bundle coming from Saw Lab calculators.

    Fields:
      - chipload_mm      : chip thickness per tooth (mm)
      - heat_index       : 0–1 (0 = cool, 1 = very hot)
      - deflection_index : 0–1 (0 = very rigid, 1 = very flexible)
      - risk_flags       : list of symbolic risk codes
    """

    chipload_mm: float
    heat_index: float
    deflection_index: float
    risk_flags: list[str]


def evaluate_operation_feasibility(
    *,
    operation: str,
    material_id: str,
    tool_id: str,
    spindle_rpm: float,
    feed_mm_min: float,
    path_length_mm: float,
) -> Optional[Dict[str, Any]]:
    """
    Entry point for all physics coming from Saw Lab.

    Parameters:
      - operation      : e.g. "rosette_vcarve", "relief_outline"
      - material_id    : saw_lab material key
      - tool_id        : saw_lab tool key
      - spindle_rpm    : actual RPM
      - feed_mm_min    : programmed feed (mm/min)
      - path_length_mm : total toolpath length

    Returns:
      - dict(SawPhysicsResult) with additional metadata, or None if invalid params

    CURRENT IMPLEMENTATION (Wave 6):
      - Uses tool & material profiles for:
        - flute count
        - ideal chipload band (min/max)
        - heat sensitivity weighting
      - Still a placeholder approximation, but now parameterized by
        real tool/material data instead of pure constants.

    FUTURE:
      - Replace the inner block with calls into actual Saw Lab
        calculators (bite, heat, deflection, kickback, etc.).
    """
    if spindle_rpm <= 0 or feed_mm_min <= 0:
        return None

    # Resolve flute count and "ideal" chipload band from tool profiles
    flutes = float(resolve_flute_count(tool_id, default=2))
    ideal_min, ideal_max = resolve_chipload_band(
        tool_id,
        default_min=0.01,
        default_max=0.04,
    )

    # Basic chipload estimate
    chipload_mm = feed_mm_min / (spindle_rpm * flutes)

    def _band_distance(x: float, lo: float, hi: float) -> float:
        if lo <= x <= hi:
            return 0.0
        if x < lo:
            return (lo - x) / max(lo, 1e-6)
        return (x - hi) / max(hi, 1e-6)

    base_dist = _band_distance(chipload_mm, ideal_min, ideal_max)

    # Material heat sensitivity weighting (ebony vs spruce, etc.)
    heat_weight = resolve_heat_weight_for_material(material_id)

    # Heat grows with deviation from ideal chipload and with path length
    raw_heat = base_dist * 0.7 + (path_length_mm / 8000.0) * 0.3
    heat_index = _clamp01(raw_heat * heat_weight)

    # Deflection grows with path length and chipload
    deflection_index = _clamp01((path_length_mm / 5000.0) * (chipload_mm / 0.02))

    risk_flags: list[str] = []

    # Tool-profile-aware chipload risk
    if chipload_mm < ideal_min * 0.5:
        risk_flags.append("chipload_too_low")
    elif chipload_mm > ideal_max * 1.5:
        risk_flags.append("chipload_too_high")

    if heat_index > 0.7:
        risk_flags.append("heat_risk_high")

    if deflection_index > 0.7:
        risk_flags.append("deflection_risk_high")

    result = SawPhysicsResult(
        chipload_mm=chipload_mm,
        heat_index=heat_index,
        deflection_index=deflection_index,
        risk_flags=risk_flags,
    )

    data = asdict(result)
    data.update(
        operation=operation,
        material_id=material_id,
        tool_id=tool_id,
        spindle_rpm=spindle_rpm,
        feed_mm_min=feed_mm_min,
        path_length_mm=path_length_mm,
        ideal_chipload_min_mm=ideal_min,
        ideal_chipload_max_mm=ideal_max,
        flutes=int(flutes),
    )

    return data


def _clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))
