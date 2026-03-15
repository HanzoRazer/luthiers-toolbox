# services/api/app/instrument_geometry/pickup/cavity_placement.py

"""
Pickup Cavity-to-Coordinate Mapper (PHYS-03)

Combines pickup positions, body centerline, and bridge placement to produce
CNC-ready cavity center coordinates.

This replaces the inline `spec_to_gcode()` functions in build scripts with a
reusable, testable module.

Input:
    - Pickup positions (from pickup_position_calc.py)
    - Body outline (from body/outlines.py)
    - Bridge saddle position (from bridge/placement.py)

Output:
    - CNC coordinates for each pickup cavity center
    - Routing dimensions and depth
    - Warnings for clearance issues
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Literal
from enum import Enum

from ..body.centerline import compute_body_centerline, CenterlineResult
from ...calculators.pickup_position_calc import (
    PickupSpec,
    PickupLayoutResult,
    PickupType,
    PickupPosition,
)


class BridgeType(str, Enum):
    """Bridge hardware types with typical positions."""
    TOM = "tune_o_matic"       # Gibson TOM - fixed saddle line
    HARDTAIL = "hardtail"     # Fender hardtail - fixed saddle line
    TREMOLO = "tremolo"       # Fender trem - saddle at rear of baseplate
    FLOYD_ROSE = "floyd_rose" # Floyd Rose - saddle at pivot point
    WRAP_AROUND = "wrap_around"  # Wrap-around tailpiece/bridge combo


@dataclass
class BridgeReference:
    """
    Bridge saddle line position for coordinate mapping.

    The saddle line is where string length is measured from (the "theoretical"
    end of the string). All pickup positions are relative to this line.
    """
    # Y coordinate of bridge saddle line in body coordinate system
    # Y=0 is typically the neck pocket or body top edge
    saddle_y_mm: float

    # Bridge hardware type (affects how saddle line is determined)
    bridge_type: BridgeType = BridgeType.TOM

    # For tremolo bridges: distance from mounting screw to saddle
    # This helps compute actual saddle position from bridge mounting location
    saddle_offset_mm: float = 0.0

    # Notes about the bridge position
    notes: str = ""


@dataclass
class CavityCoordinates:
    """
    CNC-ready coordinates for a single pickup cavity.

    All coordinates are in the body's coordinate system where:
    - X=0 is the body centerline
    - Y=0 is typically the neck pocket edge or body top
    - Z=0 is the body top surface
    """
    # Pickup identification
    pickup_position: PickupPosition  # BRIDGE, MIDDLE, NECK
    pickup_type: PickupType

    # Center point in body coordinates (mm)
    center_x_mm: float  # 0 = centerline, positive = treble side
    center_y_mm: float  # Distance from body reference (typically neck pocket)
    center_z_mm: float = 0.0  # Top surface = 0, negative = into body

    # Cavity dimensions
    cavity_width_mm: float   # X direction
    cavity_length_mm: float  # Y direction
    cavity_depth_mm: float   # Z direction (positive = depth into body)

    # Routing corner radius (for CNC fillet)
    corner_radius_mm: float = 3.0

    # Slant angle (degrees, positive = treble side closer to bridge)
    slant_degrees: float = 0.0

    # Distance from bridge saddle (for verification)
    distance_from_bridge_mm: float = 0.0

    # Clearance warnings
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pickup_position": self.pickup_position.value,
            "pickup_type": self.pickup_type.value,
            "center": {
                "x_mm": round(self.center_x_mm, 3),
                "y_mm": round(self.center_y_mm, 3),
                "z_mm": round(self.center_z_mm, 3),
            },
            "cavity": {
                "width_mm": round(self.cavity_width_mm, 2),
                "length_mm": round(self.cavity_length_mm, 2),
                "depth_mm": round(self.cavity_depth_mm, 2),
                "corner_radius_mm": round(self.corner_radius_mm, 2),
            },
            "slant_degrees": round(self.slant_degrees, 1),
            "distance_from_bridge_mm": round(self.distance_from_bridge_mm, 2),
            "warnings": self.warnings,
        }

    def to_gcode_comment(self) -> str:
        """Generate G-code comment header for this cavity."""
        return (
            f"; Pickup Cavity: {self.pickup_position.value.upper()} "
            f"({self.pickup_type.value})\n"
            f"; Center: X={self.center_x_mm:.3f} Y={self.center_y_mm:.3f}\n"
            f"; Size: {self.cavity_width_mm:.2f}W x {self.cavity_length_mm:.2f}L "
            f"x {self.cavity_depth_mm:.2f}D\n"
            f"; Distance from bridge: {self.distance_from_bridge_mm:.2f}mm"
        )


@dataclass
class CavityPlacementResult:
    """
    Complete result of cavity placement calculation.

    Contains all pickup cavities positioned in body coordinates,
    plus reference information for verification.
    """
    # All cavity coordinates
    cavities: List[CavityCoordinates]

    # Reference information
    body_centerline_x_mm: float
    bridge_saddle_y_mm: float
    body_width_mm: float
    body_length_mm: float

    # Scale length used (for verification)
    scale_length_mm: float

    # Any global warnings
    warnings: List[str] = field(default_factory=list)

    # Notes
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cavities": [c.to_dict() for c in self.cavities],
            "reference": {
                "body_centerline_x_mm": round(self.body_centerline_x_mm, 2),
                "bridge_saddle_y_mm": round(self.bridge_saddle_y_mm, 2),
                "body_width_mm": round(self.body_width_mm, 2),
                "body_length_mm": round(self.body_length_mm, 2),
                "scale_length_mm": round(self.scale_length_mm, 2),
            },
            "warnings": self.warnings,
            "notes": self.notes,
        }


# =============================================================================
# STANDARD CAVITY DEPTHS
# =============================================================================

# Standard pickup cavity depths by type (mm)
# These are typical values - actual depth depends on pickup height adjustment range
STANDARD_CAVITY_DEPTHS: Dict[PickupType, float] = {
    PickupType.SINGLE_COIL: 18.0,    # Strat single coil
    PickupType.HUMBUCKER: 20.0,      # Standard humbucker
    PickupType.P90: 19.0,            # Gibson P90
    PickupType.MINI_HUMBUCKER: 18.0,
    PickupType.JAZZMASTER: 16.0,     # Shallow route
    PickupType.TELE_NECK: 16.0,
    PickupType.TELE_BRIDGE: 12.0,    # Very shallow (through pickguard)
}


def get_cavity_depth(pickup_type: PickupType) -> float:
    """Get standard cavity depth for a pickup type."""
    return STANDARD_CAVITY_DEPTHS.get(pickup_type, 18.0)


# =============================================================================
# CORE CALCULATION
# =============================================================================

def compute_pickup_cavity_coordinates(
    pickup_layout: PickupLayoutResult,
    body_outline: List[Tuple[float, float]],
    bridge_reference: BridgeReference,
    body_reference_y: float = 0.0,
    cavity_depth_override: Optional[float] = None,
) -> CavityPlacementResult:
    """
    Compute CNC-ready coordinates for all pickup cavities.

    This is the main API for PHYS-03. It takes pickup positions (from PHYS-01),
    body outline (for centerline), and bridge position to produce complete
    CNC routing coordinates.

    Args:
        pickup_layout: Result from calculate_pickup_layout()
        body_outline: List of (x, y) points forming body outline
        bridge_reference: Bridge saddle position info
        body_reference_y: Y coordinate of body reference point (typically 0)
        cavity_depth_override: Override standard cavity depth (mm)

    Returns:
        CavityPlacementResult with all cavity coordinates

    Example:
        >>> from ...calculators.pickup_position_calc import calculate_pickup_layout
        >>> from ..body.outlines import get_body_outline
        >>> layout = calculate_pickup_layout(647.7, 22, "SSS")
        >>> outline = get_body_outline("stratocaster")
        >>> bridge = BridgeReference(saddle_y_mm=420.0, bridge_type=BridgeType.TREMOLO)
        >>> result = compute_pickup_cavity_coordinates(layout, outline, bridge)
    """
    warnings = []
    notes = []

    # Step 1: Compute body centerline
    centerline_result = compute_body_centerline(body_outline, assume_symmetric=True)
    centerline_x = centerline_result.centerline_x_mm

    # Step 2: Get body dimensions
    body_width = centerline_result.width_mm
    body_length = centerline_result.height_mm

    notes.append(f"Body centerline at X={centerline_x:.2f}mm")
    notes.append(f"Body dimensions: {body_width:.1f}W x {body_length:.1f}L mm")

    # Step 3: Convert each pickup position to cavity coordinates
    cavities = []

    for pickup_spec in pickup_layout.pickups:
        cavity = _convert_pickup_to_cavity(
            pickup_spec=pickup_spec,
            centerline_x=centerline_x,
            bridge_saddle_y=bridge_reference.saddle_y_mm,
            body_ref_y=body_reference_y,
            body_width=body_width,
            cavity_depth=cavity_depth_override,
        )

        # Check for clearance issues
        clearance_warnings = _check_cavity_clearance(
            cavity=cavity,
            body_width=body_width,
            body_length=body_length,
            centerline_x=centerline_x,
        )
        cavity.warnings.extend(clearance_warnings)
        warnings.extend(clearance_warnings)

        cavities.append(cavity)

    # Add notes about configuration
    notes.append(f"Configuration: {pickup_layout.configuration}")
    notes.append(f"Fret count: {pickup_layout.fret_count}")

    if pickup_layout.fret_count >= 24:
        notes.append("24+ frets: neck pickup position adjusted for clearance")

    return CavityPlacementResult(
        cavities=cavities,
        body_centerline_x_mm=centerline_x,
        bridge_saddle_y_mm=bridge_reference.saddle_y_mm,
        body_width_mm=body_width,
        body_length_mm=body_length,
        scale_length_mm=pickup_layout.scale_length_mm,
        warnings=warnings,
        notes=notes,
    )


def _convert_pickup_to_cavity(
    pickup_spec: PickupSpec,
    centerline_x: float,
    bridge_saddle_y: float,
    body_ref_y: float,
    body_width: float,
    cavity_depth: Optional[float] = None,
) -> CavityCoordinates:
    """
    Convert a PickupSpec to CavityCoordinates.

    The key transformation is:
    - Pickup positions are measured FROM the bridge saddle
    - Cavity coordinates are measured FROM the body reference (usually neck pocket)

    So: cavity_y = bridge_saddle_y - pickup.center_from_bridge_mm
    """
    # Y coordinate: bridge saddle position minus distance from bridge
    center_y = bridge_saddle_y - pickup_spec.center_from_bridge_mm

    # X coordinate: centered on centerline (X=0 in output coords)
    # Note: we output relative to centerline, so center_x = 0 for centered pickups
    center_x = 0.0  # Pickups are on the centerline

    # Depth
    depth = cavity_depth if cavity_depth is not None else get_cavity_depth(pickup_spec.pickup_type)

    return CavityCoordinates(
        pickup_position=pickup_spec.position,
        pickup_type=pickup_spec.pickup_type,
        center_x_mm=center_x,
        center_y_mm=center_y,
        center_z_mm=0.0,  # Top surface
        cavity_width_mm=pickup_spec.routing_width_mm,
        cavity_length_mm=pickup_spec.routing_length_mm,
        cavity_depth_mm=depth,
        corner_radius_mm=3.0,  # Standard 3mm fillet
        slant_degrees=pickup_spec.slant_degrees,
        distance_from_bridge_mm=pickup_spec.center_from_bridge_mm,
        warnings=[],
    )


def _check_cavity_clearance(
    cavity: CavityCoordinates,
    body_width: float,
    body_length: float,
    centerline_x: float,
) -> List[str]:
    """
    Check for clearance issues with a cavity.

    Returns list of warning messages.
    """
    warnings = []

    # Check if cavity extends beyond body width
    half_cavity_width = cavity.cavity_width_mm / 2
    cavity_left = centerline_x - half_cavity_width
    cavity_right = centerline_x + half_cavity_width

    # Body edges (assuming centerline is at center of body)
    body_left = centerline_x - (body_width / 2)
    body_right = centerline_x + (body_width / 2)

    # Minimum edge margin (mm)
    MIN_EDGE_MARGIN = 10.0

    if cavity_left < body_left + MIN_EDGE_MARGIN:
        warnings.append(
            f"{cavity.pickup_position.value.upper()} cavity too close to body edge "
            f"(left margin: {cavity_left - body_left:.1f}mm, min: {MIN_EDGE_MARGIN}mm)"
        )

    if cavity_right > body_right - MIN_EDGE_MARGIN:
        warnings.append(
            f"{cavity.pickup_position.value.upper()} cavity too close to body edge "
            f"(right margin: {body_right - cavity_right:.1f}mm, min: {MIN_EDGE_MARGIN}mm)"
        )

    # Check Y position
    half_cavity_length = cavity.cavity_length_mm / 2
    cavity_top = cavity.center_y_mm + half_cavity_length
    cavity_bottom = cavity.center_y_mm - half_cavity_length

    if cavity_bottom < MIN_EDGE_MARGIN:
        warnings.append(
            f"{cavity.pickup_position.value.upper()} cavity too close to body end "
            f"(bottom margin: {cavity_bottom:.1f}mm)"
        )

    if cavity_top > body_length - MIN_EDGE_MARGIN:
        warnings.append(
            f"{cavity.pickup_position.value.upper()} cavity extends beyond body "
            f"(top at {cavity_top:.1f}mm, body length: {body_length:.1f}mm)"
        )

    return warnings


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def compute_simple_pickup_coordinates(
    scale_length_mm: float,
    fret_count: int,
    configuration: Literal["SSS", "HH", "HSS"],
    bridge_y_mm: float,
    body_width_mm: float = 330.0,
) -> CavityPlacementResult:
    """
    Simplified API for common use cases.

    Creates a basic body outline and computes cavity coordinates without
    needing to provide detailed body geometry.

    Args:
        scale_length_mm: Scale length in mm
        fret_count: Number of frets
        configuration: Pickup configuration
        bridge_y_mm: Y position of bridge saddle from body reference
        body_width_mm: Body width (for centerline calculation)

    Returns:
        CavityPlacementResult
    """
    from ...calculators.pickup_position_calc import calculate_pickup_layout

    # Compute pickup layout
    layout = calculate_pickup_layout(
        scale_length_mm=scale_length_mm,
        fret_count=fret_count,
        configuration=configuration,
    )

    # Create simple rectangular body outline
    body_length = bridge_y_mm + 100  # Bridge + 100mm tail
    simple_outline = [
        (0.0, 0.0),
        (body_width_mm, 0.0),
        (body_width_mm, body_length),
        (0.0, body_length),
    ]

    # Bridge reference
    bridge = BridgeReference(
        saddle_y_mm=bridge_y_mm,
        bridge_type=BridgeType.HARDTAIL,
    )

    return compute_pickup_cavity_coordinates(
        pickup_layout=layout,
        body_outline=simple_outline,
        bridge_reference=bridge,
    )


def generate_cavity_gcode_header(result: CavityPlacementResult) -> str:
    """
    Generate G-code header comments for all cavities.

    Useful for adding to the top of a CNC program.
    """
    lines = [
        "; =========================================",
        "; PICKUP CAVITY ROUTING - AUTO-GENERATED",
        "; =========================================",
        f"; Scale length: {result.scale_length_mm:.2f}mm",
        f"; Body centerline: X={result.body_centerline_x_mm:.2f}mm",
        f"; Bridge saddle: Y={result.bridge_saddle_y_mm:.2f}mm",
        ";",
    ]

    for cavity in result.cavities:
        lines.append(cavity.to_gcode_comment())
        lines.append(";")

    if result.warnings:
        lines.append("; WARNINGS:")
        for warning in result.warnings:
            lines.append(f";   - {warning}")

    lines.append("; =========================================")

    return "\n".join(lines)
