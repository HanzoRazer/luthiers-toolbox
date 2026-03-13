"""Stratocaster Body Generator Configuration

GAP-07: Configuration for Stratocaster body CNC generation.
Defines tool settings, cavity positions, and machine parameters.

Coordinate System:
- Origin (0,0) at body centerline, bottom of body
- X+ towards treble side
- Y+ towards neck
- All dimensions in mm (G21)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Literal
from enum import Enum


class PickupConfig(str, Enum):
    """Stratocaster pickup configurations."""
    SSS = "sss"      # 3 single coils (classic)
    HSS = "hss"      # Humbucker bridge + 2 single coils
    HSH = "hsh"      # 2 humbuckers + single middle
    HH = "hh"        # 2 humbuckers (no middle)


@dataclass
class StratToolConfig:
    """Tool configuration for a specific operation."""
    diameter_mm: float
    flutes: int = 2
    stepover_pct: float = 0.45  # 45% stepover for pocketing
    feed_xy_mmpm: float = 1200.0
    feed_z_mmpm: float = 300.0
    stepdown_mm: float = 3.0
    rpm: int = 18000


@dataclass
class StratMachineConfig:
    """Machine configuration."""
    name: str
    safe_z: float = 25.0
    retract_z: float = 5.0
    work_offset: str = "G54"
    spindle_warmup_s: int = 3


# Standard Stratocaster dimensions (1954-present, pre-CBS style)
STRAT_BODY_DIMS = {
    "width_mm": 322.3,
    "length_mm": 458.8,
    "thickness_mm": 44.45,  # 1.75"
    "belly_contour_depth_mm": 9.5,
    "arm_contour_depth_mm": 6.4,
}

# Neck pocket dimensions
NECK_POCKET = {
    "width_mm": 56.0,        # Standard Fender neck width at heel
    "length_mm": 76.0,       # Pocket length
    "depth_mm": 15.9,        # ~5/8" standard
    "y_from_bottom_mm": 380.0,  # Distance from bottom of body
    "corner_radius_mm": 6.35,   # 1/4" radius
}

# Pickup cavity dimensions (single-coil standard)
SINGLE_COIL_CAVITY = {
    "length_mm": 88.0,
    "width_mm": 17.5,
    "depth_mm": 17.5,
    "corner_radius_mm": 3.0,
}

HUMBUCKER_CAVITY = {
    "length_mm": 74.0,
    "width_mm": 38.0,
    "depth_mm": 20.0,
    "corner_radius_mm": 4.0,
}

# Pickup positions (Y distance from bridge saddles)
# Based on 25.5" (647.7mm) scale length
PICKUP_POSITIONS_SSS = {
    "bridge": 28.5,     # 1-1/8" from bridge
    "middle": 92.0,     # Between bridge and neck
    "neck": 165.0,      # ~6.5" from bridge
}

PICKUP_POSITIONS_HSS = {
    "bridge": 32.0,     # Humbucker centered
    "middle": 92.0,
    "neck": 165.0,
}

# Tremolo cavity (front - 2-point modern or 6-screw vintage)
TREMOLO_CAVITY = {
    "length_mm": 90.0,
    "width_mm": 56.0,
    "depth_mm": 12.7,   # 1/2" typical
    "y_from_bottom_mm": 115.0,
}

# Spring cavity (back)
SPRING_CAVITY = {
    "length_mm": 88.0,
    "width_mm": 75.0,
    "depth_mm": 38.0,   # Through to tremolo cavity
    "y_from_bottom_mm": 110.0,
}

# Control cavity (back)
CONTROL_CAVITY = {
    "length_mm": 85.0,
    "width_mm": 45.0,
    "depth_mm": 35.0,
    "y_from_bottom_mm": 200.0,
    "x_offset_mm": 50.0,  # Offset towards bass side
}

# Output jack bore
JACK_BORE = {
    "diameter_mm": 9.5,  # 3/8" standard
    "depth_mm": 25.0,
    "y_from_bottom_mm": 95.0,
    "x_offset_mm": 80.0,  # Side of body
    "angle_deg": 0.0,  # 0 = perpendicular to face
}


# Standard tools
STRAT_TOOLS: Dict[str, StratToolConfig] = {
    "roughing_6mm": StratToolConfig(
        diameter_mm=6.0,
        flutes=2,
        stepover_pct=0.50,
        feed_xy_mmpm=1500,
        feed_z_mmpm=400,
        stepdown_mm=4.0,
        rpm=18000,
    ),
    "finishing_6mm": StratToolConfig(
        diameter_mm=6.0,
        flutes=2,
        stepover_pct=0.15,
        feed_xy_mmpm=1800,
        feed_z_mmpm=300,
        stepdown_mm=1.5,
        rpm=20000,
    ),
    "perimeter_6mm": StratToolConfig(
        diameter_mm=6.0,
        flutes=2,
        stepover_pct=1.0,  # Single pass
        feed_xy_mmpm=1200,
        feed_z_mmpm=300,
        stepdown_mm=3.0,
        rpm=18000,
    ),
    "drilling_3mm": StratToolConfig(
        diameter_mm=3.0,
        flutes=2,
        stepover_pct=1.0,
        feed_xy_mmpm=600,
        feed_z_mmpm=150,
        stepdown_mm=2.0,
        rpm=12000,
    ),
}

# Machine presets
STRAT_MACHINES: Dict[str, StratMachineConfig] = {
    "generic_router": StratMachineConfig(
        name="Generic CNC Router",
        safe_z=25.0,
        retract_z=5.0,
    ),
    "shapeoko": StratMachineConfig(
        name="Shapeoko 4 XXL",
        safe_z=20.0,
        retract_z=3.0,
    ),
    "avid": StratMachineConfig(
        name="Avid CNC",
        safe_z=30.0,
        retract_z=5.0,
    ),
}


@dataclass
class StratBodySpec:
    """Complete Stratocaster body specification."""

    pickup_config: PickupConfig = PickupConfig.SSS
    fret_count: int = 22
    scale_length_mm: float = 647.7  # 25.5"

    # Body options
    belly_contour: bool = True
    arm_contour: bool = True

    # Back routing or top routing for electronics
    rear_routed: bool = True

    # Tremolo style
    tremolo_style: Literal["vintage_6screw", "2point", "hardtail"] = "vintage_6screw"

    # Stock thickness
    stock_thickness_mm: float = 44.45

    def get_pickup_positions(self) -> Dict[str, float]:
        """Get pickup positions based on configuration."""
        if self.pickup_config == PickupConfig.SSS:
            return PICKUP_POSITIONS_SSS.copy()
        elif self.pickup_config in (PickupConfig.HSS, PickupConfig.HSH):
            return PICKUP_POSITIONS_HSS.copy()
        else:
            return {"bridge": 32.0, "neck": 165.0}

    def get_pickup_cavities(self) -> List[Dict]:
        """Get pickup cavity specs based on configuration."""
        cavities = []
        positions = self.get_pickup_positions()

        if self.pickup_config == PickupConfig.SSS:
            for pos_name in ["bridge", "middle", "neck"]:
                cavities.append({
                    "type": "single_coil",
                    "y_from_bridge_mm": positions[pos_name],
                    **SINGLE_COIL_CAVITY,
                })
        elif self.pickup_config == PickupConfig.HSS:
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_mm": positions["bridge"],
                **HUMBUCKER_CAVITY,
            })
            for pos_name in ["middle", "neck"]:
                cavities.append({
                    "type": "single_coil",
                    "y_from_bridge_mm": positions[pos_name],
                    **SINGLE_COIL_CAVITY,
                })
        elif self.pickup_config == PickupConfig.HSH:
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_mm": positions["bridge"],
                **HUMBUCKER_CAVITY,
            })
            cavities.append({
                "type": "single_coil",
                "y_from_bridge_mm": positions["middle"],
                **SINGLE_COIL_CAVITY,
            })
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_mm": positions["neck"],
                **HUMBUCKER_CAVITY,
            })
        else:  # HH
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_mm": positions["bridge"],
                **HUMBUCKER_CAVITY,
            })
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_mm": positions["neck"],
                **HUMBUCKER_CAVITY,
            })

        return cavities

    def get_neck_pocket_adjustment(self) -> float:
        """Get neck pocket Y adjustment for extended fretboards."""
        if self.fret_count <= 22:
            return 0.0
        # 24-fret: shift neck pocket ~12mm towards bridge
        # to accommodate extended fretboard over body
        return -12.0
