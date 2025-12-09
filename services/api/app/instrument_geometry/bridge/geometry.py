"""
Instrument Geometry: Bridge Geometry

Functions for computing bridge location, saddle positions, and compensation.

See docs/KnowledgeBase/Instrument_Geometry/Bridge_Compensation_Notes.md
for theory and references.

Bridge Compensation Theory:
    When a string is fretted, it stretches slightly, increasing tension.
    This causes the pitch to go sharp. To compensate, the saddle is
    moved back (away from the nut) so the string length is slightly longer.

    Wound strings need more compensation than plain strings due to
    their greater stiffness.

    Typical compensation values (mm):
    - Low E (wound): 2.0 - 3.0 mm
    - A, D (wound): 1.5 - 2.5 mm
    - G (wound or plain): 1.0 - 2.0 mm
    - B (plain): 1.0 - 1.5 mm
    - High E (plain): 1.5 - 2.0 mm

Moved from: instrument_geometry/bridge_geometry.py (Wave 14 reorg)
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional

from ..neck.neck_profiles import BridgeSpec


def compute_bridge_location_mm(scale_length_mm: float) -> float:
    """
    Compute the theoretical bridge reference line position.

    This is the nominal scale length position. Actual saddle positions
    will vary by string due to intonation compensation.

    Args:
        scale_length_mm: Full scale length in mm.

    Returns:
        Distance from nut to bridge reference line in mm.
    """
    return scale_length_mm


def compute_saddle_positions_mm(
    scale_length_mm: float,
    compensations_mm: Dict[str, float],
) -> Dict[str, float]:
    """
    Compute the actual saddle position for each string.

    Args:
        scale_length_mm: Nominal scale length.
        compensations_mm: Dict of string_id -> compensation in mm.
            Positive values move the saddle away from the nut.

    Returns:
        Dict of string_id -> distance from nut to saddle.

    Example:
        >>> comps = {"E6": 2.5, "A5": 2.0, "D4": 1.5, "G3": 1.0, "B2": 1.5, "E1": 2.0}
        >>> positions = compute_saddle_positions_mm(648.0, comps)
        >>> positions["E6"]
        650.5
    """
    positions: Dict[str, float] = {}
    for string_id, comp in compensations_mm.items():
        positions[string_id] = scale_length_mm + comp
    return positions


def compute_bridge_height_profile(
    width_mm: float,
    string_count: int,
    radius_mm: Optional[float],
    base_height_mm: float,
) -> List[Tuple[float, float]]:
    """
    Compute the bridge top profile (saddle heights) for a radiused bridge.

    Args:
        width_mm: Bridge width (string spread).
        string_count: Number of strings.
        radius_mm: Saddle radius. None or infinity for flat.
        base_height_mm: Height at the center of the bridge.

    Returns:
        List of (y_position, height) tuples for each string position.
        Y positions are centered (negative = bass side).

    Example:
        >>> profile = compute_bridge_height_profile(52.0, 6, 241.3, 12.0)
        >>> len(profile)
        6
    """
    if string_count <= 0:
        return []

    half_width = width_mm / 2.0
    positions: List[Tuple[float, float]] = []

    if string_count == 1:
        return [(0.0, base_height_mm)]

    spacing = width_mm / (string_count - 1)

    for i in range(string_count):
        y = -half_width + (i * spacing)

        # Calculate height adjustment for radius
        if radius_mm is None or radius_mm == float("inf"):
            height = base_height_mm
        else:
            # Height drop from center due to radius
            # Using circular arc approximation: h = r - sqrt(r^2 - y^2)
            # For small y relative to r, approximately: h ≈ y^2 / (2r)
            if abs(y) < radius_mm:
                import math
                height_drop = radius_mm - math.sqrt(radius_mm**2 - y**2)
                height = base_height_mm - height_drop
            else:
                height = base_height_mm

        positions.append((y, height))

    return positions


def compute_archtop_bridge_placement(
    body_length_mm: float,
    scale_length_mm: float,
    soundhole_position_mm: float,
) -> Tuple[float, float]:
    """
    Compute recommended bridge placement for an archtop guitar.

    On archtop guitars, the bridge position affects both intonation
    and the acoustic coupling to the top.

    Args:
        body_length_mm: Total body length.
        scale_length_mm: Scale length.
        soundhole_position_mm: F-hole or soundhole centerline from body edge.

    Returns:
        Tuple of (min_position, max_position) for bridge placement,
        as distances from the neck joint.

    Note:
        This is a simplified calculation. Real placement depends on
        the specific instrument design and top graduation.
    """
    # Bridge should be positioned for proper scale length
    # Allow some adjustment range for intonation
    nominal_position = scale_length_mm
    adjustment_range = 5.0  # mm

    return (nominal_position - adjustment_range, nominal_position + adjustment_range)


def compute_compensation_estimate(
    string_gauge_mm: float,
    is_wound: bool,
    action_mm: float = 2.0,
) -> float:
    """
    Estimate intonation compensation for a string.

    This is a rough approximation. Actual compensation depends on
    many factors including:
    - String construction and materials
    - Scale length
    - Setup preferences
    - Playing style

    Args:
        string_gauge_mm: String diameter in mm.
        is_wound: Whether the string is wound.
        action_mm: String height at 12th fret.

    Returns:
        Estimated compensation in mm.

    Note:
        For accurate intonation, always set up with a tuner.
        These estimates are starting points only.
    """
    base_comp = string_gauge_mm * 30.0  # Rough scaling factor

    if is_wound:
        base_comp *= 1.3  # Wound strings need more compensation

    # Higher action requires more compensation
    action_factor = 1.0 + (action_mm - 2.0) * 0.1

    return base_comp * action_factor


# Standard 6-string compensation estimates (mm)
STANDARD_6_STRING_COMPENSATION = {
    "E6": 2.5,   # Low E (wound)
    "A5": 2.0,   # A (wound)
    "D4": 1.8,   # D (wound)
    "G3": 1.2,   # G (wound or plain)
    "B2": 1.5,   # B (plain)
    "E1": 2.0,   # High E (plain)
}

# Standard bass compensation estimates (mm)
STANDARD_4_STRING_BASS_COMPENSATION = {
    "E4": 3.0,   # Low E
    "A3": 2.5,   # A
    "D2": 2.0,   # D
    "G1": 1.5,   # G
}
