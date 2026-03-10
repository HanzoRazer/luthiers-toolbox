"""
Chipload Calculation for V-Carving

Chipload is the thickness of material removed per cutting edge per revolution:

    chipload = feed_rate / (RPM * flute_count)
    feed_rate = chipload * RPM * flute_count

Proper chipload ensures:
- Clean cuts (not too slow = rubbing/burning)
- Tool life (not too fast = chipping/breakage)
- Surface finish quality

Material-specific chipload ranges (mm per tooth):
- Softwood: 0.08 - 0.15
- Hardwood: 0.05 - 0.10
- MDF/Plywood: 0.10 - 0.20
- Acrylic: 0.05 - 0.10
- Aluminum: 0.02 - 0.05
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


# Chipload ranges by material (min, max) in mm per tooth
MATERIAL_CHIPLOAD: Dict[str, Tuple[float, float]] = {
    "softwood": (0.08, 0.15),
    "hardwood": (0.05, 0.10),
    "mdf": (0.10, 0.20),
    "plywood": (0.10, 0.18),
    "acrylic": (0.05, 0.10),
    "plastic": (0.08, 0.15),
    "aluminum": (0.02, 0.05),
    "brass": (0.02, 0.04),
    "carbon_fiber": (0.03, 0.06),
    "default": (0.05, 0.10),
}


@dataclass
class ChiploadParams:
    """Parameters for chipload calculation."""

    material: str = "hardwood"
    spindle_rpm: int = 18000
    flute_count: int = 2
    chipload_factor: float = 0.8  # 0.0-1.0, where to fall in range


def get_chipload_for_material(
    material: str,
    factor: float = 0.8,
) -> float:
    """
    Get recommended chipload for a material.

    Args:
        material: Material name (softwood, hardwood, mdf, etc.)
        factor: Where to fall in the range (0.0 = min, 1.0 = max)

    Returns:
        Chipload in mm per tooth
    """
    material_key = material.lower().replace(" ", "_").replace("-", "_")

    if material_key in MATERIAL_CHIPLOAD:
        min_cl, max_cl = MATERIAL_CHIPLOAD[material_key]
    else:
        min_cl, max_cl = MATERIAL_CHIPLOAD["default"]

    # Interpolate within range
    factor = max(0.0, min(1.0, factor))
    return min_cl + factor * (max_cl - min_cl)


def calculate_chipload(
    feed_rate_mm_min: float,
    spindle_rpm: int,
    flute_count: int,
) -> float:
    """
    Calculate actual chipload from cutting parameters.

    Args:
        feed_rate_mm_min: Feed rate in mm/min
        spindle_rpm: Spindle speed in RPM
        flute_count: Number of cutting edges

    Returns:
        Chipload in mm per tooth
    """
    if spindle_rpm <= 0 or flute_count <= 0:
        return 0.0

    return feed_rate_mm_min / (spindle_rpm * flute_count)


def calculate_feed_rate(
    params: ChiploadParams,
) -> float:
    """
    Calculate recommended feed rate from chipload parameters.

    Args:
        params: Chipload calculation parameters

    Returns:
        Feed rate in mm/min
    """
    chipload = get_chipload_for_material(params.material, params.chipload_factor)
    return chipload * params.spindle_rpm * params.flute_count


def validate_chipload(
    chipload: float,
    material: str,
) -> Tuple[bool, str]:
    """
    Validate chipload is within acceptable range for material.

    Args:
        chipload: Actual chipload in mm per tooth
        material: Material name

    Returns:
        Tuple of (is_valid, message)
    """
    material_key = material.lower().replace(" ", "_").replace("-", "_")

    if material_key in MATERIAL_CHIPLOAD:
        min_cl, max_cl = MATERIAL_CHIPLOAD[material_key]
    else:
        min_cl, max_cl = MATERIAL_CHIPLOAD["default"]

    if chipload < min_cl * 0.5:
        return (False, f"Chipload {chipload:.4f}mm too low - risk of rubbing/burning")

    if chipload < min_cl:
        return (True, f"Chipload {chipload:.4f}mm below optimal range")

    if chipload > max_cl * 1.5:
        return (False, f"Chipload {chipload:.4f}mm too high - risk of tool breakage")

    if chipload > max_cl:
        return (True, f"Chipload {chipload:.4f}mm above optimal range")

    return (True, f"Chipload {chipload:.4f}mm within optimal range")


def adjust_feed_for_depth(
    base_feed_rate: float,
    depth_mm: float,
    bit_angle_deg: float,
    max_depth_mm: float = 5.0,
) -> float:
    """
    Reduce feed rate for deep cuts.

    Deeper cuts engage more of the V-bit and require slower feeds.

    Args:
        base_feed_rate: Base feed rate in mm/min
        depth_mm: Current cut depth
        bit_angle_deg: V-bit angle
        max_depth_mm: Depth at which feed is reduced to 50%

    Returns:
        Adjusted feed rate in mm/min
    """
    if depth_mm <= 0:
        return base_feed_rate

    # Linear reduction: 100% at surface, 50% at max_depth
    reduction = 1.0 - 0.5 * min(1.0, depth_mm / max_depth_mm)

    # Sharper bits (smaller angle) need more reduction
    angle_factor = min(1.0, bit_angle_deg / 90.0)
    reduction = reduction * (0.7 + 0.3 * angle_factor)

    return base_feed_rate * reduction
