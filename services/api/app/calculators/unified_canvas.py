# services/api/app/calculators/unified_canvas.py

"""
Unified Inlay Canvas (VINE-05)

Provides a single coordinate system for designing inlays that span both
fretboard and headstock regions. This enables continuous designs like the
Gibson J-45 "Vine of Life" pattern that flows from fretboard to headstock.

Coordinate System:
- Origin (X=0) at the nut
- Positive X extends toward the bridge (fretboard)
- Negative X extends toward the tuners (headstock)
- Y=0 is the centerline
- All measurements in millimeters

The headstock angle (e.g., 17° on Gibson acoustics) is handled by projecting
headstock coordinates appropriately. For 2D design purposes (DXF/CAM), we
treat this as a planar projection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from ..generators.neck_headstock_config import (
    HeadstockStyle,
    NeckDimensions,
    generate_headstock_outline,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class FretboardParams:
    """Fretboard geometry parameters."""
    scale_length_mm: float = 648.0  # 25.5" Fender scale
    nut_width_mm: float = 43.0
    heel_width_mm: float = 57.0  # Width at body joint (~14th fret)
    fret_count: int = 22

    # Fretboard radius for curved surface (optional)
    radius_mm: Optional[float] = None  # None = flat
    compound_radius_start_mm: Optional[float] = None
    compound_radius_end_mm: Optional[float] = None


@dataclass
class HeadstockParams:
    """Headstock geometry parameters."""
    style: HeadstockStyle = HeadstockStyle.GIBSON_SOLID
    length_mm: float = 178.0  # 7 inches
    width_mm: float = 89.0    # 3.5 inches at widest
    angle_deg: float = 17.0   # Gibson-style angled headstock
    thickness_mm: float = 14.0

    # For creating NeckDimensions (headstock outline uses inches internally)
    nut_width_in: float = 1.6875  # 43mm ≈ 1.6875"


# =============================================================================
# CANVAS REGIONS
# =============================================================================

class CanvasRegion(str, Enum):
    """Identifies which region of the canvas a point is in."""
    HEADSTOCK = "headstock"
    NUT_TRANSITION = "nut_transition"
    FRETBOARD = "fretboard"
    BEYOND_HEEL = "beyond_heel"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _fret_position_mm(fret_number: int, scale_length_mm: float) -> float:
    """Calculate distance from nut to fret using 12-TET formula."""
    if fret_number <= 0:
        return 0.0
    return scale_length_mm * (1.0 - pow(2, -fret_number / 12.0))


def _interpolate_fretboard_width(
    x_mm: float,
    scale_length_mm: float,
    nut_width_mm: float,
    heel_width_mm: float,
    fret_count: int = 22
) -> float:
    """
    Interpolate fretboard width at position x_mm from nut.

    Linear interpolation from nut width to heel width.
    Returns nut width for x <= 0.
    """
    if x_mm <= 0:
        return nut_width_mm

    # Calculate heel position (typically around 14th fret for bolt-on, body joint)
    # For simplicity, use the last fret position
    heel_position = _fret_position_mm(fret_count, scale_length_mm)

    if x_mm >= heel_position:
        return heel_width_mm

    t = x_mm / heel_position
    return nut_width_mm + t * (heel_width_mm - nut_width_mm)


def _mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm / 25.4


def _inches_to_mm(inches: float) -> float:
    """Convert inches to millimeters."""
    return inches * 25.4


# =============================================================================
# UNIFIED CANVAS
# =============================================================================

class UnifiedInlayCanvas:
    """
    Unified coordinate canvas for fretboard and headstock inlay design.

    This class provides a single coordinate system where:
    - X=0 is the nut
    - Positive X is the fretboard (toward bridge)
    - Negative X is the headstock (toward tuners)
    - Y=0 is the centerline

    Example:
        canvas = UnifiedInlayCanvas(
            fretboard=FretboardParams(scale_length_mm=628.65, nut_width_mm=43.0),
            headstock=HeadstockParams(style=HeadstockStyle.GIBSON_SOLID, angle_deg=17.0)
        )

        # Get bounding width at any position
        width_at_5th = canvas.get_bounding_width_at_x(canvas.fret_position_mm(5))
        width_at_headstock = canvas.get_bounding_width_at_x(-50)

        # Check region
        region = canvas.get_region(-50)  # Returns CanvasRegion.HEADSTOCK
    """

    def __init__(
        self,
        fretboard: Optional[FretboardParams] = None,
        headstock: Optional[HeadstockParams] = None,
    ):
        """
        Initialize unified canvas.

        Args:
            fretboard: Fretboard geometry parameters
            headstock: Headstock geometry parameters
        """
        self.fretboard = fretboard or FretboardParams()
        self.headstock = headstock or HeadstockParams()

        # Pre-calculate headstock outline (converted to mm)
        self._headstock_outline_mm = self._calculate_headstock_outline_mm()
        self._headstock_bounds = self._calculate_headstock_bounds()

    def _calculate_headstock_outline_mm(self) -> List[Tuple[float, float]]:
        """Generate headstock outline in millimeters."""
        # Create NeckDimensions for headstock generation
        dims = NeckDimensions(
            scale_length_in=_mm_to_inches(self.fretboard.scale_length_mm),
            nut_width_in=self.headstock.nut_width_in,
            headstock_length_in=_mm_to_inches(self.headstock.length_mm),
            blank_width_in=_mm_to_inches(self.headstock.width_mm),
        )

        # Get outline points (in inches)
        points_in = generate_headstock_outline(self.headstock.style, dims)

        # Convert to mm
        return [(_inches_to_mm(x), _inches_to_mm(y)) for x, y in points_in]

    def _calculate_headstock_bounds(self) -> dict:
        """Calculate headstock bounding box."""
        if not self._headstock_outline_mm:
            return {"x_min": 0, "x_max": 0, "y_min": 0, "y_max": 0}

        xs = [p[0] for p in self._headstock_outline_mm]
        ys = [p[1] for p in self._headstock_outline_mm]

        return {
            "x_min": min(xs),
            "x_max": max(xs),
            "y_min": min(ys),
            "y_max": max(ys),
        }

    # -------------------------------------------------------------------------
    # REGION QUERIES
    # -------------------------------------------------------------------------

    def get_region(self, x_mm: float) -> CanvasRegion:
        """
        Determine which region a given X coordinate falls into.

        Args:
            x_mm: X coordinate in mm (0 = nut)

        Returns:
            CanvasRegion enum value
        """
        # Nut transition zone: -5mm to +5mm around the nut
        if -5.0 <= x_mm <= 5.0:
            return CanvasRegion.NUT_TRANSITION

        if x_mm < -5.0:
            return CanvasRegion.HEADSTOCK

        # Check if beyond fretboard
        heel_position = _fret_position_mm(
            self.fretboard.fret_count,
            self.fretboard.scale_length_mm
        )

        if x_mm > heel_position:
            return CanvasRegion.BEYOND_HEEL

        return CanvasRegion.FRETBOARD

    # -------------------------------------------------------------------------
    # FRETBOARD GEOMETRY
    # -------------------------------------------------------------------------

    def fret_position_mm(self, fret_number: int) -> float:
        """Get X position of a fret number."""
        return _fret_position_mm(fret_number, self.fretboard.scale_length_mm)

    def fret_midpoint_mm(self, fret_number: int) -> float:
        """Get X position at midpoint between fret and previous fret (inlay position)."""
        if fret_number <= 1:
            return _fret_position_mm(1, self.fretboard.scale_length_mm) / 2.0
        pos_current = _fret_position_mm(fret_number, self.fretboard.scale_length_mm)
        pos_prev = _fret_position_mm(fret_number - 1, self.fretboard.scale_length_mm)
        return (pos_current + pos_prev) / 2.0

    def get_fretboard_width_at_x(self, x_mm: float) -> float:
        """
        Get fretboard width at a given X position.

        Returns nut width for x <= 0.
        """
        return _interpolate_fretboard_width(
            x_mm,
            self.fretboard.scale_length_mm,
            self.fretboard.nut_width_mm,
            self.fretboard.heel_width_mm,
            self.fretboard.fret_count,
        )

    # -------------------------------------------------------------------------
    # HEADSTOCK GEOMETRY
    # -------------------------------------------------------------------------

    def get_headstock_width_at_x(self, x_mm: float) -> Tuple[float, float]:
        """
        Get headstock Y bounds at a given X position.

        For X >= 0, returns (0, 0) since that's fretboard territory.

        Args:
            x_mm: X coordinate (should be negative for headstock)

        Returns:
            Tuple of (y_min, y_max) representing headstock bounds at that X
        """
        if x_mm >= 0:
            return (0.0, 0.0)

        # Find intersections with the headstock outline at this X
        # This is a simplified approach - for complex shapes, we'd need
        # proper polygon intersection

        outline = self._headstock_outline_mm
        if not outline:
            return (0.0, 0.0)

        y_values_at_x = []

        for i in range(len(outline)):
            p1 = outline[i]
            p2 = outline[(i + 1) % len(outline)]

            # Check if this edge crosses our X value
            if (p1[0] <= x_mm <= p2[0]) or (p2[0] <= x_mm <= p1[0]):
                if abs(p2[0] - p1[0]) < 0.001:
                    # Vertical edge
                    y_values_at_x.extend([p1[1], p2[1]])
                else:
                    # Interpolate Y at our X
                    t = (x_mm - p1[0]) / (p2[0] - p1[0])
                    y = p1[1] + t * (p2[1] - p1[1])
                    y_values_at_x.append(y)

        if not y_values_at_x:
            # No intersection - X is outside headstock
            return (0.0, 0.0)

        return (min(y_values_at_x), max(y_values_at_x))

    def get_headstock_outline_mm(self) -> List[Tuple[float, float]]:
        """Get the headstock outline points in mm."""
        return self._headstock_outline_mm.copy()

    # -------------------------------------------------------------------------
    # UNIFIED QUERIES
    # -------------------------------------------------------------------------

    def get_bounding_contour_at_x(self, x_mm: float) -> Tuple[float, float]:
        """
        Get the bounding Y coordinates at any X position.

        This is the main API for unified design - it returns the available
        Y range at any X coordinate, whether in fretboard or headstock.

        Args:
            x_mm: X coordinate (0 = nut, + = fretboard, - = headstock)

        Returns:
            Tuple of (y_min, y_max)
        """
        region = self.get_region(x_mm)

        if region == CanvasRegion.FRETBOARD or region == CanvasRegion.BEYOND_HEEL:
            # Fretboard - symmetric around centerline
            half_width = self.get_fretboard_width_at_x(x_mm) / 2.0
            return (-half_width, half_width)

        elif region == CanvasRegion.HEADSTOCK:
            return self.get_headstock_width_at_x(x_mm)

        elif region == CanvasRegion.NUT_TRANSITION:
            # Transition zone - blend between headstock and fretboard
            # At x=0 (nut), use nut width
            # Smoothly transition to headstock/fretboard on either side

            if x_mm >= 0:
                # Fretboard side of transition
                half_width = self.fretboard.nut_width_mm / 2.0
                return (-half_width, half_width)
            else:
                # Headstock side - use headstock bounds
                hs_bounds = self.get_headstock_width_at_x(x_mm)
                if hs_bounds == (0.0, 0.0):
                    # Fallback to nut width
                    half_width = self.fretboard.nut_width_mm / 2.0
                    return (-half_width, half_width)
                return hs_bounds

        # Fallback
        return (0.0, 0.0)

    def get_bounding_width_at_x(self, x_mm: float) -> float:
        """
        Get the total width at any X position.

        Convenience method that returns width rather than min/max Y.
        """
        y_min, y_max = self.get_bounding_contour_at_x(x_mm)
        return y_max - y_min

    def is_point_in_bounds(self, x_mm: float, y_mm: float) -> bool:
        """
        Check if a point is within the canvas bounds (fretboard or headstock).

        Args:
            x_mm: X coordinate
            y_mm: Y coordinate

        Returns:
            True if point is within bounds
        """
        y_min, y_max = self.get_bounding_contour_at_x(x_mm)
        return y_min <= y_mm <= y_max

    # -------------------------------------------------------------------------
    # COORDINATE TRANSFORMS
    # -------------------------------------------------------------------------

    def apply_headstock_angle_2d(
        self,
        x_mm: float,
        y_mm: float
    ) -> Tuple[float, float]:
        """
        Apply headstock angle rotation for 2D projection.

        For a 17° headstock, points on the headstock face are rotated
        around the nut (X=0). This is useful for visualizing the headstock
        as if looking straight down at it.

        Note: For 3D modeling, you'd use a full 3D transform. This 2D
        version is for flat DXF export and CAM toolpath planning.

        Args:
            x_mm: Original X coordinate
            y_mm: Original Y coordinate

        Returns:
            Transformed (x, y) coordinates
        """
        if x_mm >= 0:
            # Fretboard - no rotation
            return (x_mm, y_mm)

        # Headstock region - apply rotation
        angle_rad = math.radians(self.headstock.angle_deg)

        # The headstock angle tilts the headstock back (rotation around Y axis)
        # For 2D projection, this shortens the X dimension by cos(angle)
        # Y remains unchanged (we're projecting onto the XY plane)

        # Apply foreshortening to X coordinate
        x_projected = x_mm * math.cos(angle_rad)

        return (x_projected, y_mm)

    def headstock_3d_z_at_x(self, x_mm: float) -> float:
        """
        Get the Z height at a given X position on the headstock.

        For an angled headstock, the surface drops as you move toward
        the tuners. Returns 0 for fretboard positions.

        Args:
            x_mm: X coordinate (negative for headstock)

        Returns:
            Z height in mm (negative = below fretboard plane)
        """
        if x_mm >= 0:
            return 0.0

        # Z drops as you move toward tuners
        angle_rad = math.radians(self.headstock.angle_deg)
        z = x_mm * math.sin(angle_rad)  # x is negative, so z is negative

        return z

    # -------------------------------------------------------------------------
    # FULL BOUNDS
    # -------------------------------------------------------------------------

    def get_canvas_bounds(self) -> dict:
        """
        Get the complete bounding box for the entire canvas.

        Returns:
            Dict with x_min, x_max, y_min, y_max in mm
        """
        # Headstock bounds
        hs = self._headstock_bounds

        # Fretboard bounds
        heel_x = _fret_position_mm(
            self.fretboard.fret_count,
            self.fretboard.scale_length_mm
        )
        half_heel = self.fretboard.heel_width_mm / 2.0

        return {
            "x_min": hs["x_min"],  # Headstock tip
            "x_max": heel_x,       # End of fretboard
            "y_min": min(hs["y_min"], -half_heel),
            "y_max": max(hs["y_max"], half_heel),
        }


# =============================================================================
# PYDANTIC MODELS FOR API
# =============================================================================

class UnifiedCanvasRequest(BaseModel):
    """Request for unified canvas creation via API."""

    # Fretboard
    scale_length_mm: float = Field(default=648.0, ge=400, le=900)
    nut_width_mm: float = Field(default=43.0, ge=30, le=60)
    heel_width_mm: float = Field(default=57.0, ge=40, le=80)
    fret_count: int = Field(default=22, ge=12, le=36)

    # Headstock
    headstock_style: str = Field(default="gibson_solid")
    headstock_angle_deg: float = Field(default=17.0, ge=0, le=25)
    headstock_length_mm: float = Field(default=178.0, ge=100, le=250)
    headstock_width_mm: float = Field(default=89.0, ge=60, le=120)


class CanvasBoundsResponse(BaseModel):
    """Response with canvas bounds."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    # Region info
    fret_count: int
    headstock_style: str
    headstock_angle_deg: float


class ContourAtXResponse(BaseModel):
    """Response for get_bounding_contour_at_x."""
    x_mm: float
    y_min: float
    y_max: float
    width_mm: float
    region: str


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_unified_canvas(request: UnifiedCanvasRequest) -> UnifiedInlayCanvas:
    """
    Factory function to create UnifiedInlayCanvas from API request.

    Resolves: VINE-05 (Unified fretboard↔headstock canvas)
    """
    # Map headstock style string to enum
    style_map = {s.value: s for s in HeadstockStyle}
    headstock_style = style_map.get(
        request.headstock_style,
        HeadstockStyle.GIBSON_SOLID
    )

    fretboard = FretboardParams(
        scale_length_mm=request.scale_length_mm,
        nut_width_mm=request.nut_width_mm,
        heel_width_mm=request.heel_width_mm,
        fret_count=request.fret_count,
    )

    headstock = HeadstockParams(
        style=headstock_style,
        length_mm=request.headstock_length_mm,
        width_mm=request.headstock_width_mm,
        angle_deg=request.headstock_angle_deg,
        nut_width_in=_mm_to_inches(request.nut_width_mm),
    )

    return UnifiedInlayCanvas(fretboard=fretboard, headstock=headstock)
