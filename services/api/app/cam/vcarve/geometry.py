"""
V-Bit Geometry Calculations

V-bits cut a V-shaped groove. The width of the cut depends on the
bit angle and the depth of cut:

    width = 2 * depth * tan(angle/2)
    depth = width / (2 * tan(angle/2))

Common V-bit angles:
- 60°: Sharp detail, deep cuts for narrow lines
- 90°: General purpose, 1:1 depth-to-width ratio
- 120°: Shallow cuts, wide lines

For text and line art, the desired line width determines the cut depth.
"""

from __future__ import annotations

import math
from typing import Tuple


def vbit_depth_for_width(
    line_width_mm: float,
    bit_angle_deg: float,
) -> float:
    """
    Calculate cut depth needed to achieve desired line width.

    Args:
        line_width_mm: Desired width of the V-groove at surface
        bit_angle_deg: V-bit included angle in degrees

    Returns:
        Required cut depth in mm

    Example:
        >>> vbit_depth_for_width(2.0, 90.0)
        1.0  # 90° bit: depth = width/2
    """
    half_angle_rad = math.radians(bit_angle_deg / 2.0)
    tan_half = math.tan(half_angle_rad)

    if tan_half < 1e-9:
        return 0.0

    return line_width_mm / (2.0 * tan_half)


def vbit_width_at_depth(
    depth_mm: float,
    bit_angle_deg: float,
) -> float:
    """
    Calculate line width at a given cut depth.

    Args:
        depth_mm: Cut depth in mm
        bit_angle_deg: V-bit included angle in degrees

    Returns:
        Width of V-groove at surface in mm

    Example:
        >>> vbit_width_at_depth(1.0, 90.0)
        2.0  # 90° bit: width = 2 * depth
    """
    half_angle_rad = math.radians(bit_angle_deg / 2.0)
    return 2.0 * depth_mm * math.tan(half_angle_rad)


def vbit_tip_offset(
    bit_angle_deg: float,
    tip_diameter_mm: float = 0.0,
) -> float:
    """
    Calculate effective tip offset for flat-bottom V-bits.

    Some V-bits have a small flat at the tip (not perfectly sharp).
    This affects the minimum line width and depth calculations.

    Args:
        bit_angle_deg: V-bit included angle
        tip_diameter_mm: Diameter of flat tip (0 for sharp tip)

    Returns:
        Depth offset in mm (add to calculated depth)
    """
    if tip_diameter_mm <= 0:
        return 0.0

    half_angle_rad = math.radians(bit_angle_deg / 2.0)
    tan_half = math.tan(half_angle_rad)

    if tan_half < 1e-9:
        return 0.0

    # The flat tip is at depth = (tip_diameter/2) / tan(half_angle)
    return (tip_diameter_mm / 2.0) / tan_half


def calculate_stepdown(
    total_depth_mm: float,
    bit_angle_deg: float,
    max_stepdown_mm: float = 2.0,
    min_passes: int = 1,
) -> Tuple[int, float]:
    """
    Calculate number of passes and stepdown for multi-pass V-carving.

    For deep cuts, multiple passes prevent tool breakage and improve
    surface finish. Shallower angles need smaller stepdowns.

    Args:
        total_depth_mm: Total depth to cut
        bit_angle_deg: V-bit angle (shallower = smaller stepdown)
        max_stepdown_mm: Maximum depth per pass
        min_passes: Minimum number of passes

    Returns:
        Tuple of (pass_count, stepdown_mm)
    """
    # Adjust max stepdown based on bit angle
    # Sharper bits (smaller angle) need smaller stepdowns
    angle_factor = min(1.0, bit_angle_deg / 90.0)
    adjusted_max = max_stepdown_mm * angle_factor

    # Calculate passes
    if total_depth_mm <= adjusted_max:
        passes = max(min_passes, 1)
    else:
        passes = max(min_passes, math.ceil(total_depth_mm / adjusted_max))

    stepdown = total_depth_mm / passes

    return (passes, stepdown)


def corner_radius_for_vbit(
    bit_angle_deg: float,
    depth_mm: float,
) -> float:
    """
    Calculate the minimum inside corner radius a V-bit can cut.

    V-bits can cut sharp outside corners but leave rounded inside
    corners. The radius depends on depth and angle.

    Args:
        bit_angle_deg: V-bit included angle
        depth_mm: Cut depth

    Returns:
        Minimum inside corner radius in mm
    """
    # At full depth, the corner radius equals the half-width at that depth
    half_angle_rad = math.radians(bit_angle_deg / 2.0)
    return depth_mm * math.tan(half_angle_rad)
