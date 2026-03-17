# services/api/app/schemas/smart_guitar_cam.py

"""
Smart Guitar CAM-specific schemas (SG-GAP-09)

CAM models for Smart Guitar edge routing and complex cavity operations.
These supplement the sg-spec canonical schemas with CAM-specific details.

SG-GAP-09: USB-C 3+1 axis routing
- USB-C port requires edge slot routed from body side
- Standard 3-axis mill needs 4th axis indexer OR
- 3+1 approach: flip workpiece for edge access
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class EdgeRoutingApproach(str, Enum):
    """Strategy for routing ports into body edge."""
    FOUR_AXIS = "4_axis"           # True 4th axis rotary indexer
    THREE_PLUS_ONE = "3+1"         # Flip workpiece for edge access
    FIXTURE_TILT = "fixture_tilt"  # Angled fixture holds body at angle
    HAND_ROUTE = "hand_route"      # Router template, manual operation


class USBCPortSpec(BaseModel):
    """
    USB-C port edge slot specification for Smart Guitar (SG-GAP-09).

    The USB-C port is routed into the body edge for charging and data.
    Requires edge access - standard 3-axis CNC cannot reach body sides
    without workpiece repositioning or 4th axis.

    Default values match Smart Guitar v1 spec.
    """
    # Port opening dimensions (at body edge)
    port_width_mm: float = Field(
        default=12.0,
        ge=8.0,
        le=20.0,
        description="Width of port opening (USB-C ~9mm, plus clearance)"
    )
    port_height_mm: float = Field(
        default=6.5,
        ge=3.5,
        le=10.0,
        description="Height of port opening (USB-C ~3.5mm, plus clearance)"
    )
    slot_depth_mm: float = Field(
        default=7.0,
        ge=5.0,
        le=15.0,
        description="Depth of slot into body edge"
    )
    corner_radius_mm: float = Field(
        default=1.5,
        ge=0.5,
        le=3.0,
        description="Corner radius of slot (tool-limited)"
    )
    wall_thickness_mm: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Wall thickness around receptacle"
    )

    # Position on body
    position: Literal["lower_bout_side", "upper_bout_side", "waist_side"] = Field(
        default="lower_bout_side",
        description="Location on body edge"
    )
    y_from_top_mm: float = Field(
        default=239.4,
        description="Y distance from top of body to port center"
    )

    # CAM approach
    routing_approach: EdgeRoutingApproach = Field(
        default=EdgeRoutingApproach.THREE_PLUS_ONE,
        description="Strategy for edge routing operation"
    )

    # Internal wiring
    internal_cable_length_mm: float = Field(
        default=60.0,
        description="Cable length to main electronics cavity"
    )
    connects_to: str = Field(
        default="rear_electronics_cavity",
        description="Target cavity for USB-C cable"
    )

    # Cover
    cover_type: str = Field(
        default="silicone_dust_plug",
        description="Protective cover type"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port_width_mm": self.port_width_mm,
            "port_height_mm": self.port_height_mm,
            "slot_depth_mm": self.slot_depth_mm,
            "corner_radius_mm": self.corner_radius_mm,
            "wall_thickness_mm": self.wall_thickness_mm,
            "position": self.position,
            "y_from_top_mm": self.y_from_top_mm,
            "routing_approach": self.routing_approach.value,
            "internal_cable_length_mm": self.internal_cable_length_mm,
            "connects_to": self.connects_to,
            "cover_type": self.cover_type,
        }


class SmartGuitarCAMState(BaseModel):
    """
    Extended state for Smart Guitar CAM operations.

    Adds CAM-specific fields to the canonical SmartGuitarSpec from sg-spec.
    Use this when generating G-code for Smart Guitar features.
    """
    # USB-C port (SG-GAP-09)
    usbc_port: Optional[USBCPortSpec] = Field(
        default=None,
        description="USB-C charging port edge slot specification"
    )

    # Additional CAM features can be added here
    # (antenna recess, wiring channels, etc.)

    class Config:
        # Allow extra fields from sg-spec models
        extra = "allow"

    @classmethod
    def with_defaults(cls) -> "SmartGuitarCAMState":
        """Create state with default Smart Guitar v1 USB-C port."""
        return cls(usbc_port=USBCPortSpec())


# Pre-configured USB-C specs for common scenarios
USBC_PORT_PRESETS: Dict[str, USBCPortSpec] = {
    "smart_guitar_v1": USBCPortSpec(
        port_width_mm=12.0,
        port_height_mm=6.5,
        slot_depth_mm=7.0,
        corner_radius_mm=1.5,
        wall_thickness_mm=2.0,
        position="lower_bout_side",
        y_from_top_mm=239.4,
        routing_approach=EdgeRoutingApproach.THREE_PLUS_ONE,
        internal_cable_length_mm=60.0,
        connects_to="rear_electronics_cavity",
        cover_type="silicone_dust_plug",
    ),
    "compact": USBCPortSpec(
        port_width_mm=10.0,
        port_height_mm=5.0,
        slot_depth_mm=6.0,
        corner_radius_mm=1.0,
        wall_thickness_mm=1.5,
        position="lower_bout_side",
        routing_approach=EdgeRoutingApproach.THREE_PLUS_ONE,
    ),
}


__all__ = [
    "EdgeRoutingApproach",
    "USBCPortSpec",
    "SmartGuitarCAMState",
    "USBC_PORT_PRESETS",
]
