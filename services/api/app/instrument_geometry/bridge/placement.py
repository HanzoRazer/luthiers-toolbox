"""
Bridge Placement: Compute bridge position based on scale length and body geometry.

Wave 14 Module - Instrument Geometry Core

Provides helpers for computing bridge placement considering:
- Scale length
- Body geometry
- Pickup routing positions
- Acoustic considerations
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

from ..neck.neck_profiles import InstrumentSpec


@dataclass
class BridgePlacement:
    """
    Result of bridge placement calculation.
    
    Attributes:
        x_mm: X position from body reference (typically neck pocket)
        y_mm: Y position (centerline = 0)
        angle_deg: Rotation angle in degrees (0 = parallel to nut)
        nominal_scale_mm: The scale length used for calculation
    """
    x_mm: float
    y_mm: float = 0.0
    angle_deg: float = 0.0
    nominal_scale_mm: float = 0.0


def compute_bridge_placement(
    spec: InstrumentSpec,
    neck_pocket_to_nut_mm: float = 0.0,
    angled: bool = False,
    angle_deg: float = 0.0,
) -> BridgePlacement:
    """
    Compute the bridge placement position.
    
    The bridge is positioned so that the saddles can be adjusted
    to achieve proper intonation at the nominal scale length.
    
    Args:
        spec: InstrumentSpec with scale_length_mm
        neck_pocket_to_nut_mm: Distance from neck pocket edge to nut
            (used to compute bridge position relative to body)
        angled: Whether to angle the bridge (common on Telecasters)
        angle_deg: Angle in degrees if angled=True
        
    Returns:
        BridgePlacement with position and angle
        
    Example:
        >>> spec = InstrumentSpec("electric", 648.0, 22, 6)
        >>> placement = compute_bridge_placement(spec, neck_pocket_to_nut_mm=100.0)
        >>> placement.x_mm  # From neck pocket
        548.0
    """
    # Bridge reference line is at scale length from nut
    bridge_from_nut = spec.scale_length_mm
    
    # Convert to position from neck pocket
    bridge_from_pocket = bridge_from_nut - neck_pocket_to_nut_mm
    
    return BridgePlacement(
        x_mm=bridge_from_pocket,
        y_mm=0.0,
        angle_deg=angle_deg if angled else 0.0,
        nominal_scale_mm=spec.scale_length_mm,
    )


def compute_bridge_placement_acoustic(
    spec: InstrumentSpec,
    soundhole_center_mm: float,
    body_length_mm: float,
) -> BridgePlacement:
    """
    Compute bridge placement for an acoustic guitar.
    
    Acoustic bridge placement must consider:
    - Proper scale length
    - Position relative to soundhole
    - Structural requirements (bracing pattern)
    
    Args:
        spec: InstrumentSpec with scale_length_mm
        soundhole_center_mm: Distance from nut to soundhole center
        body_length_mm: Total body length
        
    Returns:
        BridgePlacement with position
    """
    # Bridge is at scale length from nut
    # On acoustics, this is typically ~100-150mm below soundhole center
    bridge_from_nut = spec.scale_length_mm
    
    return BridgePlacement(
        x_mm=bridge_from_nut,
        y_mm=0.0,
        angle_deg=0.0,
        nominal_scale_mm=spec.scale_length_mm,
    )


def get_saddle_adjustment_range(
    string_count: int = 6,
) -> Dict[str, Tuple[float, float]]:
    """
    Get typical saddle adjustment ranges for intonation.
    
    Args:
        string_count: Number of strings
        
    Returns:
        Dict mapping string position to (min, max) adjustment in mm.
        Positive values = away from nut.
    """
    if string_count == 6:
        return {
            "E6": (1.5, 4.0),   # Low E needs most compensation
            "A5": (1.0, 3.5),
            "D4": (0.5, 3.0),
            "G3": (0.0, 2.5),   # G varies (wound vs plain)
            "B2": (0.5, 2.5),
            "E1": (1.0, 3.0),   # High E
        }
    elif string_count == 4:  # Bass
        return {
            "E4": (2.0, 5.0),
            "A3": (1.5, 4.0),
            "D2": (1.0, 3.5),
            "G1": (0.5, 3.0),
        }
    else:
        # Generic range
        return {f"S{i+1}": (0.5, 3.5) for i in range(string_count)}
