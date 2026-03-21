"""WP-3: Les Paul CNC configuration — tool library and machine profiles.

Extracted from lespaul_body_generator.py to reduce god-object size.

UNIT SYSTEM NOTE (LP-GAP-10):
This module uses INCHES internally for G-code generation (G20 mode).
Tool names reference metric sizes (e.g., "10mm") for human readability,
but all dimensional values (_in suffix) are in inches.

Conversion: 1 inch = 25.4 mm

The repo convention is mm (G21), but this legacy generator uses inches
to maintain compatibility with existing toolpath verification data.
Future refactoring should convert to mm throughout.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


class LesPaulPickupConfig(str, Enum):
    """Les Paul pickup configurations."""
    HH = "hh"           # 2 humbuckers (classic)
    P90_HH = "p90_hh"   # 2 P90s
    HHH = "hhh"         # 3 humbuckers (custom)
    HSH = "hsh"         # Bridge humbucker, middle single, neck humbucker
    SINGLE_H = "h"      # Single humbucker (junior)


@dataclass
class ToolConfig:
    """Tool configuration from your Fusion360 setup."""
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float
    stepover_pct: float

    @property
    def stepover_in(self) -> float:
        return self.diameter_in * (self.stepover_pct / 100)


@dataclass
class MachineConfig:
    """Machine configuration."""
    name: str
    max_x_in: float
    max_y_in: float
    max_z_in: float
    safe_z_in: float = 0.75
    retract_z_in: float = 0.25
    rapid_rate: float = 200.0  # IPM


# Default tool library (from your Tool_List_LP.csv, converted to inches)
TOOLS = {
    1: ToolConfig(1, "10mm Flat End Mill", 0.394, 18000, 220, 31, 0.22, 45),
    2: ToolConfig(2, "6mm Flat End Mill", 0.236, 18000, 150, 24, 0.06, 18),
    3: ToolConfig(3, "3mm Flat/Drill", 0.118, 20000, 60, 16, 0.03, 20),
}

# Machine configurations
MACHINES = {
    "txrx_router": MachineConfig("TXRX Labs Router", 48, 48, 4, 0.75, 0.25),
    "bcamcnc_2030ca": MachineConfig("BCAMCNC 2030CA", 48, 24, 4, 0.6, 0.2),
}


# =============================================================================
# Les Paul Body Dimensions (inches - legacy compatibility)
# =============================================================================

LP_BODY_DIMS = {
    "width_in": 13.0,           # Body width
    "length_in": 17.5,          # Body length
    "thickness_in": 1.75,       # Standard body thickness
    "carve_depth_in": 0.5,      # Top carve depth (Standard, not Custom)
}

# Neck pocket (set-neck style)
LP_NECK_POCKET = {
    "width_in": 2.2,            # 56mm
    "length_in": 3.0,           # Tenon length
    "depth_in": 0.625,          # 5/8" standard
    "y_from_bottom_in": 14.5,   # Distance from bottom
    "angle_deg": 4.0,           # Neck angle
}

# Pickup cavities (humbucker standard)
LP_HUMBUCKER_CAVITY = {
    "length_in": 2.9,           # ~74mm
    "width_in": 1.5,            # ~38mm
    "depth_in": 0.75,           # Pickup depth
    "corner_radius_in": 0.156,  # ~4mm
}

# Pickup positions (Y from bridge)
LP_PICKUP_POSITIONS = {
    "bridge_y_in": 1.25,        # Bridge pickup
    "neck_y_in": 6.5,           # Neck pickup
}

# Control cavity (back)
LP_CONTROL_CAVITY = {
    "length_in": 3.5,
    "width_in": 2.0,
    "depth_in": 1.25,
    "y_from_bottom_in": 8.0,
    "x_offset_in": 2.5,         # Offset towards bass side
}

# Switch cavity
LP_SWITCH_CAVITY = {
    "length_in": 2.5,
    "width_in": 1.0,
    "depth_in": 1.0,
    "y_from_bottom_in": 13.0,
    "x_offset_in": 3.0,         # Upper bout, treble side
}


@dataclass
class LesPaulBodySpec:
    """Complete Les Paul body specification (GEN-4).

    Used by LesPaulBodyGenerator.from_project() to create a generator
    from InstrumentProjectData.
    """
    pickup_config: LesPaulPickupConfig = LesPaulPickupConfig.HH
    fret_count: int = 22
    scale_length_mm: float = 628.65  # 24.75" Gibson scale

    # Body options
    top_carve: bool = True          # Carved maple top (vs flat)
    binding: bool = True            # Body binding
    neck_angle_deg: float = 4.0     # Set-neck angle

    # Routing
    rear_routed: bool = True        # Control cavity on back

    # Stock thickness (inches for legacy compat)
    stock_thickness_in: float = 1.75

    # DXF template override (if None, uses default LP template)
    dxf_template_path: str = None

    def get_pickup_positions(self) -> Dict[str, float]:
        """Get pickup Y positions in inches from bridge."""
        return LP_PICKUP_POSITIONS.copy()

    def get_pickup_cavities(self) -> List[Dict]:
        """Get pickup cavity specs based on configuration."""
        cavities = []
        positions = self.get_pickup_positions()

        if self.pickup_config in (LesPaulPickupConfig.HH, LesPaulPickupConfig.P90_HH):
            # Standard 2 humbucker layout
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_in": positions["bridge_y_in"],
                **LP_HUMBUCKER_CAVITY,
            })
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_in": positions["neck_y_in"],
                **LP_HUMBUCKER_CAVITY,
            })
        elif self.pickup_config == LesPaulPickupConfig.SINGLE_H:
            # Junior style - single bridge humbucker
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_in": positions["bridge_y_in"],
                **LP_HUMBUCKER_CAVITY,
            })
        elif self.pickup_config == LesPaulPickupConfig.HHH:
            # Triple humbucker (custom)
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_in": positions["bridge_y_in"],
                **LP_HUMBUCKER_CAVITY,
            })
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_in": (positions["bridge_y_in"] + positions["neck_y_in"]) / 2,
                **LP_HUMBUCKER_CAVITY,
            })
            cavities.append({
                "type": "humbucker",
                "y_from_bridge_in": positions["neck_y_in"],
                **LP_HUMBUCKER_CAVITY,
            })

        return cavities

    def get_neck_pocket_adjustment(self) -> float:
        """Get neck pocket Y adjustment for extended fretboards (inches)."""
        if self.fret_count <= 22:
            return 0.0
        # 24-fret: shift pocket ~0.5" towards bridge
        return -0.5
