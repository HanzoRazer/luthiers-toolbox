# services/api/app/calculators/pickup_position_calc.py

"""
Pickup Position Calculator — Computes optimal pickup placements.

Calculates pickup positions based on scale length, fret count, and pickup type.
Supports standard configurations (Strat SSS, Les Paul HH, HSS, etc.) and custom layouts.

Key formulas:
- Fret position: scale_length - (scale_length / 2^(fret/12))
- Bridge pickup: typically 1.5-2" from bridge saddle
- Neck pickup: near neck/body junction (varies by fret count)
- Middle pickup: between neck and bridge positions

References:
- Fender Strat: 25.5" scale, SSS, pickups at ~1.75", ~3.75", ~6.375" from bridge
- Gibson Les Paul: 24.75" scale, HH, pickups at ~1.5", ~5.5" from bridge
- 24-fret guitars: neck pickup moves bridgeward to clear extended fretboard

GAP-04: Pickup position calculator for 24-fret Strat and other configurations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any
from enum import Enum


class PickupType(str, Enum):
    """Standard pickup types with typical dimensions."""
    SINGLE_COIL = "single_coil"      # Fender-style: ~19mm wide
    HUMBUCKER = "humbucker"          # Gibson-style: ~38mm wide
    P90 = "p90"                      # Gibson P90: ~33mm wide
    MINI_HUMBUCKER = "mini_humbucker"  # ~29mm wide
    JAZZMASTER = "jazzmaster"        # Wide single: ~40mm wide
    TELE_NECK = "tele_neck"          # Tele neck: ~32mm wide
    TELE_BRIDGE = "tele_bridge"      # Tele bridge: ~20mm wide


# Standard pickup widths (mm) - housing width, not pole piece span
PICKUP_WIDTHS_MM: Dict[PickupType, float] = {
    PickupType.SINGLE_COIL: 19.0,
    PickupType.HUMBUCKER: 38.0,
    PickupType.P90: 33.0,
    PickupType.MINI_HUMBUCKER: 29.0,
    PickupType.JAZZMASTER: 40.0,
    PickupType.TELE_NECK: 32.0,
    PickupType.TELE_BRIDGE: 20.0,
}


class PickupPosition(str, Enum):
    """Standard pickup position names."""
    BRIDGE = "bridge"
    MIDDLE = "middle"
    NECK = "neck"


@dataclass
class PickupSpec:
    """Specification for a single pickup placement."""
    position: PickupPosition
    pickup_type: PickupType
    center_from_bridge_mm: float
    center_from_nut_mm: float
    routing_width_mm: float
    routing_length_mm: float
    slant_degrees: float = 0.0  # Positive = treble side closer to bridge
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position.value,
            "pickup_type": self.pickup_type.value,
            "center_from_bridge_mm": round(self.center_from_bridge_mm, 2),
            "center_from_nut_mm": round(self.center_from_nut_mm, 2),
            "routing_width_mm": round(self.routing_width_mm, 2),
            "routing_length_mm": round(self.routing_length_mm, 2),
            "slant_degrees": round(self.slant_degrees, 1),
            "notes": self.notes,
        }


@dataclass
class PickupLayoutResult:
    """Complete pickup layout calculation result."""
    scale_length_mm: float
    fret_count: int
    configuration: str  # e.g., "SSS", "HH", "HSS"
    pickups: List[PickupSpec]
    fret_24_position_mm: Optional[float]  # Distance from nut to 24th fret
    neck_body_junction_mm: float  # Where neck meets body
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scale_length_mm": round(self.scale_length_mm, 2),
            "fret_count": self.fret_count,
            "configuration": self.configuration,
            "pickups": [p.to_dict() for p in self.pickups],
            "fret_24_position_mm": round(self.fret_24_position_mm, 2) if self.fret_24_position_mm else None,
            "neck_body_junction_mm": round(self.neck_body_junction_mm, 2),
            "notes": self.notes,
        }


# =============================================================================
# CORE CALCULATIONS
# =============================================================================

def fret_position_from_nut_mm(scale_length_mm: float, fret_number: int) -> float:
    """
    Calculate fret position from nut using 12-TET formula.

    Formula: position = scale_length * (1 - 1/2^(fret/12))

    Args:
        scale_length_mm: Scale length in mm
        fret_number: Fret number (1 = first fret)

    Returns:
        Distance from nut to fret in mm
    """
    if fret_number <= 0:
        return 0.0
    return scale_length_mm * (1 - 1 / (2 ** (fret_number / 12)))


def fret_position_from_bridge_mm(scale_length_mm: float, fret_number: int) -> float:
    """
    Calculate fret position from bridge.

    Args:
        scale_length_mm: Scale length in mm
        fret_number: Fret number (1 = first fret)

    Returns:
        Distance from bridge to fret in mm
    """
    return scale_length_mm - fret_position_from_nut_mm(scale_length_mm, fret_number)


def neck_body_junction_mm(scale_length_mm: float, fret_count: int) -> float:
    """
    Estimate neck/body junction position.

    For bolt-on necks, the junction is typically:
    - 21-fret: around fret 16-17
    - 22-fret: around fret 17-18
    - 24-fret: around fret 19-20

    For set-neck/neck-through, junction is less defined but pickup
    placement follows similar rules.

    Args:
        scale_length_mm: Scale length in mm
        fret_count: Total number of frets

    Returns:
        Estimated distance from nut to neck/body junction in mm
    """
    # Heuristic: junction at (fret_count - 5) to (fret_count - 4)
    junction_fret = fret_count - 4.5
    return fret_position_from_nut_mm(scale_length_mm, junction_fret)


# =============================================================================
# PICKUP POSITION PRESETS
# =============================================================================

def calculate_strat_sss_positions(
    scale_length_mm: float,
    fret_count: int = 21,
) -> List[PickupSpec]:
    """
    Calculate classic Strat SSS pickup positions.

    Traditional Strat spacing (21/22 fret):
    - Bridge: 1.625" (41.3mm) from bridge
    - Middle: 3.625" (92.1mm) from bridge
    - Neck: 6.375" (161.9mm) from bridge

    For 24-fret, neck pickup moves bridgeward to clear fretboard extension.
    """
    pickups = []

    # Bridge pickup - relatively fixed position
    bridge_offset_mm = 41.3  # 1.625"

    if fret_count <= 22:
        # Traditional spacing
        middle_offset_mm = 92.1   # 3.625"
        neck_offset_mm = 161.9    # 6.375"
    else:
        # 24-fret: compress toward bridge
        # Neck pickup can't go past ~22nd fret position
        fret_22_from_bridge = fret_position_from_bridge_mm(scale_length_mm, 22)
        neck_offset_mm = fret_22_from_bridge - 10  # 10mm margin from fret

        # Middle splits the difference
        middle_offset_mm = (bridge_offset_mm + neck_offset_mm) / 2

    # Bridge pickup (slanted for intonation compensation)
    pickups.append(PickupSpec(
        position=PickupPosition.BRIDGE,
        pickup_type=PickupType.SINGLE_COIL,
        center_from_bridge_mm=bridge_offset_mm,
        center_from_nut_mm=scale_length_mm - bridge_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.SINGLE_COIL] + 3,  # +3mm clearance
        routing_length_mm=85.0,  # Standard Strat routing length
        slant_degrees=10.0,  # Treble side closer to bridge
        notes="Bridge single-coil, standard Strat slant",
    ))

    # Middle pickup
    pickups.append(PickupSpec(
        position=PickupPosition.MIDDLE,
        pickup_type=PickupType.SINGLE_COIL,
        center_from_bridge_mm=middle_offset_mm,
        center_from_nut_mm=scale_length_mm - middle_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.SINGLE_COIL] + 3,
        routing_length_mm=85.0,
        slant_degrees=0.0,  # Middle is typically straight
        notes="Middle single-coil, RWRP for hum cancellation in positions 2/4",
    ))

    # Neck pickup
    pickups.append(PickupSpec(
        position=PickupPosition.NECK,
        pickup_type=PickupType.SINGLE_COIL,
        center_from_bridge_mm=neck_offset_mm,
        center_from_nut_mm=scale_length_mm - neck_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.SINGLE_COIL] + 3,
        routing_length_mm=85.0,
        slant_degrees=0.0,
        notes="Neck single-coil" + (" (moved bridgeward for 24-fret clearance)" if fret_count > 22 else ""),
    ))

    return pickups


def calculate_lespaul_hh_positions(
    scale_length_mm: float,
    fret_count: int = 22,
) -> List[PickupSpec]:
    """
    Calculate Gibson Les Paul HH pickup positions.

    Traditional LP spacing:
    - Bridge: 1.5" (38.1mm) from bridge
    - Neck: 5.75" (146.1mm) from bridge
    """
    pickups = []

    bridge_offset_mm = 38.1  # 1.5"

    if fret_count <= 22:
        neck_offset_mm = 146.1  # 5.75" traditional
    else:
        # 24-fret: move neck pickup bridgeward
        fret_22_from_bridge = fret_position_from_bridge_mm(scale_length_mm, 22)
        neck_offset_mm = fret_22_from_bridge - 15  # 15mm margin (humbucker is wider)

    # Bridge humbucker
    pickups.append(PickupSpec(
        position=PickupPosition.BRIDGE,
        pickup_type=PickupType.HUMBUCKER,
        center_from_bridge_mm=bridge_offset_mm,
        center_from_nut_mm=scale_length_mm - bridge_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.HUMBUCKER] + 4,
        routing_length_mm=92.0,  # Standard humbucker routing
        slant_degrees=0.0,
        notes="Bridge humbucker",
    ))

    # Neck humbucker
    pickups.append(PickupSpec(
        position=PickupPosition.NECK,
        pickup_type=PickupType.HUMBUCKER,
        center_from_bridge_mm=neck_offset_mm,
        center_from_nut_mm=scale_length_mm - neck_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.HUMBUCKER] + 4,
        routing_length_mm=92.0,
        slant_degrees=0.0,
        notes="Neck humbucker" + (" (moved bridgeward for 24-fret clearance)" if fret_count > 22 else ""),
    ))

    return pickups


def calculate_hss_positions(
    scale_length_mm: float,
    fret_count: int = 22,
) -> List[PickupSpec]:
    """
    Calculate HSS (humbucker-single-single) positions.

    Common in "Super Strat" guitars. Bridge humbucker with Strat-style
    middle and neck single coils.
    """
    pickups = []

    # Bridge humbucker - slightly further back than Strat bridge single
    bridge_offset_mm = 45.0  # ~1.77"

    if fret_count <= 22:
        middle_offset_mm = 95.0
        neck_offset_mm = 158.0
    else:
        fret_22_from_bridge = fret_position_from_bridge_mm(scale_length_mm, 22)
        neck_offset_mm = fret_22_from_bridge - 10
        middle_offset_mm = (bridge_offset_mm + neck_offset_mm) / 2

    # Bridge humbucker
    pickups.append(PickupSpec(
        position=PickupPosition.BRIDGE,
        pickup_type=PickupType.HUMBUCKER,
        center_from_bridge_mm=bridge_offset_mm,
        center_from_nut_mm=scale_length_mm - bridge_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.HUMBUCKER] + 4,
        routing_length_mm=92.0,
        slant_degrees=0.0,
        notes="Bridge humbucker (HSS configuration)",
    ))

    # Middle single
    pickups.append(PickupSpec(
        position=PickupPosition.MIDDLE,
        pickup_type=PickupType.SINGLE_COIL,
        center_from_bridge_mm=middle_offset_mm,
        center_from_nut_mm=scale_length_mm - middle_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.SINGLE_COIL] + 3,
        routing_length_mm=85.0,
        slant_degrees=0.0,
        notes="Middle single-coil, RWRP recommended",
    ))

    # Neck single
    pickups.append(PickupSpec(
        position=PickupPosition.NECK,
        pickup_type=PickupType.SINGLE_COIL,
        center_from_bridge_mm=neck_offset_mm,
        center_from_nut_mm=scale_length_mm - neck_offset_mm,
        routing_width_mm=PICKUP_WIDTHS_MM[PickupType.SINGLE_COIL] + 3,
        routing_length_mm=85.0,
        slant_degrees=0.0,
        notes="Neck single-coil" + (" (24-fret adjusted)" if fret_count > 22 else ""),
    ))

    return pickups


# =============================================================================
# PUBLIC API
# =============================================================================

CONFIGURATIONS = {
    "SSS": calculate_strat_sss_positions,
    "HH": calculate_lespaul_hh_positions,
    "HSS": calculate_hss_positions,
}


def calculate_pickup_layout(
    scale_length_mm: float = 647.7,  # 25.5" Fender default
    fret_count: int = 21,
    configuration: Literal["SSS", "HH", "HSS"] = "SSS",
) -> PickupLayoutResult:
    """
    Calculate complete pickup layout for a guitar.

    Args:
        scale_length_mm: Scale length in millimeters (default: 647.7mm / 25.5")
        fret_count: Number of frets (typically 21, 22, or 24)
        configuration: Pickup configuration ("SSS", "HH", "HSS")

    Returns:
        PickupLayoutResult with all pickup positions and metadata

    Example:
        >>> result = calculate_pickup_layout(647.7, 24, "SSS")
        >>> for p in result.pickups:
        ...     print(f"{p.position.value}: {p.center_from_bridge_mm}mm from bridge")
    """
    if configuration not in CONFIGURATIONS:
        raise ValueError(f"Unknown configuration: {configuration}. Valid: {list(CONFIGURATIONS.keys())}")

    calc_func = CONFIGURATIONS[configuration]
    pickups = calc_func(scale_length_mm, fret_count)

    # Calculate reference points
    junction = neck_body_junction_mm(scale_length_mm, fret_count)
    fret_24_pos = fret_position_from_nut_mm(scale_length_mm, 24) if fret_count >= 24 else None

    notes = []
    if fret_count > 22:
        notes.append(f"Extended range: {fret_count} frets requires adjusted neck pickup position")
    if configuration == "HSS":
        notes.append("HSS: Consider coil-split for bridge humbucker versatility")

    return PickupLayoutResult(
        scale_length_mm=scale_length_mm,
        fret_count=fret_count,
        configuration=configuration,
        pickups=pickups,
        fret_24_position_mm=fret_24_pos,
        neck_body_junction_mm=junction,
        notes=notes,
    )


def calculate_custom_pickup_position(
    scale_length_mm: float,
    pickup_type: PickupType,
    target_harmonic_node: Optional[int] = None,
    offset_from_bridge_mm: Optional[float] = None,
) -> PickupSpec:
    """
    Calculate a single pickup position with custom parameters.

    Either specify a harmonic node (fret position) or explicit offset from bridge.

    Args:
        scale_length_mm: Scale length in mm
        pickup_type: Type of pickup
        target_harmonic_node: Place pickup at this fret's harmonic position
        offset_from_bridge_mm: Explicit distance from bridge in mm

    Returns:
        PickupSpec for the calculated position
    """
    if offset_from_bridge_mm is not None:
        center_from_bridge = offset_from_bridge_mm
    elif target_harmonic_node is not None:
        center_from_bridge = fret_position_from_bridge_mm(scale_length_mm, target_harmonic_node)
    else:
        raise ValueError("Must specify either target_harmonic_node or offset_from_bridge_mm")

    width = PICKUP_WIDTHS_MM.get(pickup_type, 25.0)

    return PickupSpec(
        position=PickupPosition.BRIDGE,  # Generic, caller should override
        pickup_type=pickup_type,
        center_from_bridge_mm=center_from_bridge,
        center_from_nut_mm=scale_length_mm - center_from_bridge,
        routing_width_mm=width + 3,
        routing_length_mm=92.0 if "humbucker" in pickup_type.value else 85.0,
        slant_degrees=0.0,
        notes=f"Custom position: {target_harmonic_node}th fret harmonic" if target_harmonic_node else "Custom offset",
    )


# =============================================================================
# SCALE LENGTH PRESETS
# =============================================================================

SCALE_LENGTHS_MM = {
    "fender_25.5": 647.7,      # Strat, Tele, Jazzmaster
    "gibson_24.75": 628.65,    # Les Paul, SG, ES-335
    "prs_25": 635.0,           # PRS standard
    "gibson_sg_special": 625.0, # Shorter SG variant
    "fender_jaguar": 609.6,    # 24" Jaguar/Mustang
    "baritone_27": 685.8,      # 27" baritone
    "multiscale_25.5_27": (647.7, 685.8),  # Fanned frets
}


def get_scale_length_mm(preset: str) -> float:
    """Get scale length in mm from preset name."""
    value = SCALE_LENGTHS_MM.get(preset)
    if value is None:
        raise ValueError(f"Unknown scale preset: {preset}. Valid: {list(SCALE_LENGTHS_MM.keys())}")
    if isinstance(value, tuple):
        return value[0]  # Return treble side for multiscale
    return value
