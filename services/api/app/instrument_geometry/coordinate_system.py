# services/api/app/instrument_geometry/coordinate_system.py

"""
Unified Coordinate System — Bridges fretboard and headstock coordinate spaces (VINE-05).

Establishes a single coordinate space for the entire neck assembly:
- Fretboard coordinates: Y=0 at nut, positive Y toward bridge
- Headstock coordinates: Y=0 at nut, negative Y toward headstock tip
- X=0 is always centerline

This enables:
- Continuous inlay patterns spanning fretboard → headstock
- Unified CAM toolpath generation
- Consistent positioning in design tools

Coordinate Conventions:
    - Origin: Nut centerline (0, 0)
    - X-axis: Positive = treble side, Negative = bass side
    - Y-axis: Positive = toward bridge, Negative = toward headstock tip
    - Z-axis: Positive = above fretboard surface

GAP Resolutions:
    - VINE-05: Unified fretboard↔headstock coordinate canvas
    - INLAY-04: Unified coordinate space for inlay positioning
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Literal
from enum import Enum


class CoordinateRegion(str, Enum):
    """Region identifiers for the neck assembly."""
    HEADSTOCK = "headstock"
    NUT = "nut"
    FRETBOARD = "fretboard"
    BODY_JOINT = "body_joint"


@dataclass
class Point2D:
    """2D point in unified coordinate space."""
    x: float  # mm, 0 = centerline, + = treble, - = bass
    y: float  # mm, 0 = nut, + = bridge, - = headstock tip

    def __add__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x - other.x, self.y - other.y)

    def distance_to(self, other: "Point2D") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def to_dict(self) -> Dict[str, float]:
        return {"x": round(self.x, 4), "y": round(self.y, 4)}

    @classmethod
    def from_tuple(cls, xy: Tuple[float, float]) -> "Point2D":
        return cls(xy[0], xy[1])


@dataclass
class Point3D:
    """3D point with Z depth/height."""
    x: float
    y: float
    z: float  # mm, 0 = surface, + = above, - = below (into material)

    def to_2d(self) -> Point2D:
        return Point2D(self.x, self.y)

    def to_dict(self) -> Dict[str, float]:
        return {"x": round(self.x, 4), "y": round(self.y, 4), "z": round(self.z, 4)}


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center(self) -> Point2D:
        return Point2D(
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2
        )

    def contains(self, point: Point2D) -> bool:
        return (self.min_x <= point.x <= self.max_x and
                self.min_y <= point.y <= self.max_y)

    def to_dict(self) -> Dict[str, float]:
        return {
            "min_x": round(self.min_x, 4),
            "max_x": round(self.max_x, 4),
            "min_y": round(self.min_y, 4),
            "max_y": round(self.max_y, 4),
            "width": round(self.width, 4),
            "height": round(self.height, 4),
        }


@dataclass
class HeadstockOriginSpec:
    """
    Headstock origin specification for coordinate unification.

    The origin_offset_mm is the key field that enables unified coordinates.
    It defines where the headstock's local origin sits relative to the nut.
    """
    origin_offset_mm: float = 0.0  # Y offset from nut (typically 0 for nut-aligned)
    angle_deg: float = 0.0  # Headstock angle relative to neck (e.g., 13° for Strat)
    thickness_transition_mm: float = 0.0  # Volute/scarf zone length

    def to_dict(self) -> Dict[str, float]:
        return {
            "origin_offset_mm": self.origin_offset_mm,
            "angle_deg": self.angle_deg,
            "thickness_transition_mm": self.thickness_transition_mm,
        }


@dataclass
class UnifiedNeckGeometry:
    """
    Complete geometry specification for unified coordinate system.

    This is the central data structure that bridges fretboard and headstock.
    """
    # Scale and fret info
    scale_length_mm: float = 647.7  # Fender 25.5"
    fret_count: int = 22

    # Fretboard dimensions
    nut_width_mm: float = 43.0
    fretboard_width_at_last_fret_mm: float = 56.0
    fretboard_length_mm: float = 0.0  # Calculated from frets if 0

    # Headstock dimensions
    headstock_length_mm: float = 178.0
    headstock_width_max_mm: float = 85.0
    headstock_angle_deg: float = 13.0

    # Origin specification
    headstock_origin: HeadstockOriginSpec = field(default_factory=HeadstockOriginSpec)

    # Calculated bounds (populated by compute_bounds)
    _fretboard_bounds: Optional[BoundingBox] = field(default=None, repr=False)
    _headstock_bounds: Optional[BoundingBox] = field(default=None, repr=False)
    _total_bounds: Optional[BoundingBox] = field(default=None, repr=False)

    def __post_init__(self):
        if self.fretboard_length_mm == 0:
            # Calculate fretboard length from scale and fret count
            self.fretboard_length_mm = self._fret_position(self.fret_count) + 15  # + margin

    def _fret_position(self, fret_number: int) -> float:
        """Calculate fret position from nut using 12-TET formula."""
        if fret_number <= 0:
            return 0.0
        return self.scale_length_mm * (1 - (1 / (2 ** (fret_number / 12))))

    def compute_bounds(self) -> None:
        """Compute bounding boxes for all regions."""
        # Fretboard bounds (Y: 0 to fretboard_length_mm)
        self._fretboard_bounds = BoundingBox(
            min_x=-self.fretboard_width_at_last_fret_mm / 2,
            max_x=self.fretboard_width_at_last_fret_mm / 2,
            min_y=0.0,
            max_y=self.fretboard_length_mm,
        )

        # Headstock bounds (Y: -headstock_length_mm to 0)
        self._headstock_bounds = BoundingBox(
            min_x=-self.headstock_width_max_mm / 2,
            max_x=self.headstock_width_max_mm / 2,
            min_y=-self.headstock_length_mm + self.headstock_origin.origin_offset_mm,
            max_y=self.headstock_origin.origin_offset_mm,
        )

        # Total bounds
        self._total_bounds = BoundingBox(
            min_x=min(self._fretboard_bounds.min_x, self._headstock_bounds.min_x),
            max_x=max(self._fretboard_bounds.max_x, self._headstock_bounds.max_x),
            min_y=self._headstock_bounds.min_y,
            max_y=self._fretboard_bounds.max_y,
        )

    @property
    def fretboard_bounds(self) -> BoundingBox:
        if self._fretboard_bounds is None:
            self.compute_bounds()
        return self._fretboard_bounds  # type: ignore

    @property
    def headstock_bounds(self) -> BoundingBox:
        if self._headstock_bounds is None:
            self.compute_bounds()
        return self._headstock_bounds  # type: ignore

    @property
    def total_bounds(self) -> BoundingBox:
        if self._total_bounds is None:
            self.compute_bounds()
        return self._total_bounds  # type: ignore

    def get_region(self, point: Point2D) -> CoordinateRegion:
        """Determine which region a point falls into."""
        if point.y < self.headstock_origin.origin_offset_mm:
            return CoordinateRegion.HEADSTOCK
        elif point.y <= 0.5:  # Small tolerance around nut
            return CoordinateRegion.NUT
        elif point.y <= self.fretboard_length_mm:
            return CoordinateRegion.FRETBOARD
        else:
            return CoordinateRegion.BODY_JOINT

    def to_dict(self) -> Dict[str, Any]:
        self.compute_bounds()
        return {
            "scale_length_mm": self.scale_length_mm,
            "fret_count": self.fret_count,
            "nut_width_mm": self.nut_width_mm,
            "fretboard_width_at_last_fret_mm": self.fretboard_width_at_last_fret_mm,
            "fretboard_length_mm": round(self.fretboard_length_mm, 2),
            "headstock_length_mm": self.headstock_length_mm,
            "headstock_width_max_mm": self.headstock_width_max_mm,
            "headstock_angle_deg": self.headstock_angle_deg,
            "headstock_origin": self.headstock_origin.to_dict(),
            "bounds": {
                "fretboard": self.fretboard_bounds.to_dict(),
                "headstock": self.headstock_bounds.to_dict(),
                "total": self.total_bounds.to_dict(),
            },
        }


# =============================================================================
# COORDINATE TRANSFORMATION FUNCTIONS
# =============================================================================

def fret_to_unified_y(fret_number: float, scale_length_mm: float) -> float:
    """
    Convert fret number to unified Y coordinate.

    Args:
        fret_number: Fret position (0 = nut, can be fractional)
        scale_length_mm: Scale length in mm

    Returns:
        Y coordinate in mm (0 = nut, positive = toward bridge)
    """
    if fret_number <= 0:
        return 0.0
    return scale_length_mm * (1 - (1 / (2 ** (fret_number / 12))))


def unified_y_to_fret(y_mm: float, scale_length_mm: float) -> float:
    """
    Convert unified Y coordinate to fret number.

    Args:
        y_mm: Y coordinate in mm (0 = nut)
        scale_length_mm: Scale length in mm

    Returns:
        Fret number (can be fractional, 0 = nut)
    """
    if y_mm <= 0:
        return 0.0
    if y_mm >= scale_length_mm:
        return float('inf')  # Past the bridge

    ratio = 1 - (y_mm / scale_length_mm)
    return -12 * math.log2(ratio)


def string_to_unified_x(
    string_number: int,
    y_mm: float,
    nut_width_mm: float,
    width_at_y_mm: float,
    string_count: int = 6,
) -> float:
    """
    Convert string number to unified X coordinate at given Y position.

    Args:
        string_number: 1 = low E (bass), 6 = high E (treble) for 6-string
        y_mm: Y position (for calculating taper)
        nut_width_mm: Width at nut
        width_at_y_mm: Width at current Y position
        string_count: Total number of strings

    Returns:
        X coordinate in mm (0 = centerline, + = treble, - = bass)
    """
    if string_count < 2:
        return 0.0

    # String spacing (edge to edge, not E-to-E)
    # Typical: ~3.5mm from edge to first/last string
    edge_margin = 3.5
    string_spacing = (width_at_y_mm - 2 * edge_margin) / (string_count - 1)

    # Calculate X position (string 1 = bass side = negative X)
    center_string = (string_count + 1) / 2  # e.g., 3.5 for 6 strings
    offset_from_center = string_number - center_string  # -2.5 to +2.5 for 6 strings

    return offset_from_center * string_spacing


def headstock_local_to_unified(
    local_point: Point2D,
    headstock_origin: HeadstockOriginSpec,
) -> Point2D:
    """
    Transform headstock local coordinates to unified coordinates.

    Headstock local coords: (0, 0) = nut end of headstock
    Unified coords: (0, 0) = nut centerline

    Args:
        local_point: Point in headstock local coordinates
        headstock_origin: Origin specification

    Returns:
        Point in unified coordinates
    """
    # Apply origin offset (shifts Y)
    unified_y = local_point.y + headstock_origin.origin_offset_mm

    # Note: headstock angle affects Z, not X/Y in plan view
    # For 3D, we'd need to account for angle

    return Point2D(local_point.x, unified_y)


def unified_to_headstock_local(
    unified_point: Point2D,
    headstock_origin: HeadstockOriginSpec,
) -> Point2D:
    """
    Transform unified coordinates to headstock local coordinates.

    Args:
        unified_point: Point in unified coordinates
        headstock_origin: Origin specification

    Returns:
        Point in headstock local coordinates
    """
    local_y = unified_point.y - headstock_origin.origin_offset_mm
    return Point2D(unified_point.x, local_y)


def fretboard_width_at_y(
    y_mm: float,
    nut_width_mm: float,
    width_at_last_fret_mm: float,
    fretboard_length_mm: float,
) -> float:
    """
    Calculate fretboard width at given Y position (linear taper).

    Args:
        y_mm: Y position (0 = nut)
        nut_width_mm: Width at nut
        width_at_last_fret_mm: Width at last fret
        fretboard_length_mm: Total fretboard length

    Returns:
        Width in mm at Y position
    """
    if y_mm <= 0:
        return nut_width_mm
    if y_mm >= fretboard_length_mm:
        return width_at_last_fret_mm

    # Linear interpolation
    t = y_mm / fretboard_length_mm
    return nut_width_mm + t * (width_at_last_fret_mm - nut_width_mm)


# =============================================================================
# INLAY POSITION HELPERS
# =============================================================================

@dataclass
class InlayPosition:
    """Position specification for a single inlay."""
    center: Point2D
    fret_number: Optional[float] = None  # For fretboard inlays
    string_number: Optional[int] = None  # For dot inlays on specific strings
    region: CoordinateRegion = CoordinateRegion.FRETBOARD
    rotation_deg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "center": self.center.to_dict(),
            "fret_number": self.fret_number,
            "string_number": self.string_number,
            "region": self.region.value,
            "rotation_deg": self.rotation_deg,
        }


def compute_dot_inlay_position(
    fret_number: float,
    geometry: UnifiedNeckGeometry,
    side: Literal["center", "bass", "treble"] = "center",
) -> InlayPosition:
    """
    Compute position for a dot inlay at given fret.

    Args:
        fret_number: Fret number (e.g., 3, 5, 7, 9, 12)
        geometry: Neck geometry specification
        side: "center" for single dots, "bass"/"treble" for double dots

    Returns:
        InlayPosition with unified coordinates
    """
    # Y position: midpoint between frets
    y_before = fret_to_unified_y(fret_number - 1, geometry.scale_length_mm)
    y_at = fret_to_unified_y(fret_number, geometry.scale_length_mm)
    y_center = (y_before + y_at) / 2

    # X position based on side
    width_at_y = fretboard_width_at_y(
        y_center,
        geometry.nut_width_mm,
        geometry.fretboard_width_at_last_fret_mm,
        geometry.fretboard_length_mm,
    )

    if side == "center":
        x = 0.0
    elif side == "bass":
        x = -width_at_y / 6  # ~1/3 from center toward bass
    else:  # treble
        x = width_at_y / 6

    return InlayPosition(
        center=Point2D(x, y_center),
        fret_number=fret_number,
        region=CoordinateRegion.FRETBOARD,
    )


def compute_block_inlay_position(
    fret_number: float,
    geometry: UnifiedNeckGeometry,
) -> InlayPosition:
    """
    Compute position for a block inlay at given fret.

    Block inlays are centered and span most of the fret space.
    """
    y_before = fret_to_unified_y(fret_number - 1, geometry.scale_length_mm)
    y_at = fret_to_unified_y(fret_number, geometry.scale_length_mm)
    y_center = (y_before + y_at) / 2

    return InlayPosition(
        center=Point2D(0.0, y_center),
        fret_number=fret_number,
        region=CoordinateRegion.FRETBOARD,
    )


def compute_headstock_inlay_position(
    y_offset_from_nut_mm: float,
    geometry: UnifiedNeckGeometry,
    x_offset_mm: float = 0.0,
) -> InlayPosition:
    """
    Compute position for a headstock inlay.

    Args:
        y_offset_from_nut_mm: Distance from nut (positive = into headstock)
        geometry: Neck geometry
        x_offset_mm: X offset from centerline

    Returns:
        InlayPosition in unified coordinates
    """
    # Headstock Y is negative in unified coords
    y_unified = geometry.headstock_origin.origin_offset_mm - y_offset_from_nut_mm

    return InlayPosition(
        center=Point2D(x_offset_mm, y_unified),
        region=CoordinateRegion.HEADSTOCK,
    )


def compute_all_standard_inlay_positions(
    geometry: UnifiedNeckGeometry,
    pattern: Literal["dots", "blocks", "trapezoids"] = "dots",
    double_dots_at_12: bool = True,
) -> List[InlayPosition]:
    """
    Compute all inlay positions for standard patterns.

    Args:
        geometry: Neck geometry
        pattern: Inlay pattern type
        double_dots_at_12: Whether fret 12 has double dots

    Returns:
        List of InlayPosition objects in unified coordinates
    """
    # Standard inlay frets
    standard_frets = [3, 5, 7, 9, 12, 15, 17, 19, 21]
    # Filter to available frets
    frets = [f for f in standard_frets if f <= geometry.fret_count]

    positions = []

    for fret in frets:
        if pattern == "dots":
            if fret == 12 and double_dots_at_12:
                # Double dots
                positions.append(compute_dot_inlay_position(fret, geometry, "bass"))
                positions.append(compute_dot_inlay_position(fret, geometry, "treble"))
            else:
                positions.append(compute_dot_inlay_position(fret, geometry, "center"))
        else:
            # Blocks or trapezoids are always centered
            positions.append(compute_block_inlay_position(fret, geometry))

    return positions


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_strat_geometry() -> UnifiedNeckGeometry:
    """Create geometry for Stratocaster-style neck."""
    return UnifiedNeckGeometry(
        scale_length_mm=647.7,  # 25.5"
        fret_count=22,
        nut_width_mm=43.0,
        fretboard_width_at_last_fret_mm=56.0,
        headstock_length_mm=178.0,
        headstock_width_max_mm=85.0,
        headstock_angle_deg=13.0,
        headstock_origin=HeadstockOriginSpec(
            origin_offset_mm=0.0,
            angle_deg=13.0,
        ),
    )


def create_lespaul_geometry() -> UnifiedNeckGeometry:
    """Create geometry for Les Paul-style neck."""
    return UnifiedNeckGeometry(
        scale_length_mm=628.65,  # 24.75"
        fret_count=22,
        nut_width_mm=43.0,
        fretboard_width_at_last_fret_mm=54.0,
        headstock_length_mm=190.0,
        headstock_width_max_mm=115.0,
        headstock_angle_deg=17.0,
        headstock_origin=HeadstockOriginSpec(
            origin_offset_mm=0.0,
            angle_deg=17.0,
        ),
    )


def create_classical_geometry() -> UnifiedNeckGeometry:
    """Create geometry for classical guitar neck."""
    return UnifiedNeckGeometry(
        scale_length_mm=650.0,  # 25.6"
        fret_count=19,
        nut_width_mm=52.0,
        fretboard_width_at_last_fret_mm=62.0,
        headstock_length_mm=200.0,
        headstock_width_max_mm=85.0,
        headstock_angle_deg=14.0,
        headstock_origin=HeadstockOriginSpec(
            origin_offset_mm=0.0,
            angle_deg=14.0,
        ),
    )


def create_geometry_from_specs(
    scale_length_mm: float,
    fret_count: int,
    nut_width_mm: float,
    width_at_last_fret_mm: float,
    headstock_length_mm: float,
    headstock_width_mm: float,
    headstock_angle_deg: float = 13.0,
) -> UnifiedNeckGeometry:
    """Create custom geometry from specifications."""
    return UnifiedNeckGeometry(
        scale_length_mm=scale_length_mm,
        fret_count=fret_count,
        nut_width_mm=nut_width_mm,
        fretboard_width_at_last_fret_mm=width_at_last_fret_mm,
        headstock_length_mm=headstock_length_mm,
        headstock_width_max_mm=headstock_width_mm,
        headstock_angle_deg=headstock_angle_deg,
        headstock_origin=HeadstockOriginSpec(
            origin_offset_mm=0.0,
            angle_deg=headstock_angle_deg,
        ),
    )
