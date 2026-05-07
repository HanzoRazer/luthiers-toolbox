"""
aperture_geometry.py
Common output model for all aperture types (round, oval, spiral, f-hole).

This module provides a normalized geometry representation that wraps
type-specific calculations. It enables unified comparison, export,
and acoustic analysis across aperture types.

Usage:
    from app.instrument_geometry.soundhole.aperture_geometry import (
        ApertureGeometry,
        equivalent_diameter_from_area,
        aperture_from_spiral_geometry,
    )

    # Convert spiral geometry to common format
    spiral_geo = compute_spiral_geometry(spec)
    aperture = aperture_from_spiral_geometry(spiral_geo)
    print(f"Equivalent diameter: {aperture.equivalent_diameter_mm:.1f} mm")
"""

import math
from dataclasses import asdict, dataclass
from typing import Dict, Optional

from app.instrument_geometry.soundhole.spiral_geometry import SpiralGeometry


@dataclass
class ApertureGeometry:
    """
    Normalized aperture geometry for cross-type comparison.

    Fields:
        aperture_type: Type identifier ("round", "oval", "spiral", "fhole")
        area_mm2: Open area in square millimeters
        perimeter_mm: Total perimeter length in millimeters
        equivalent_diameter_mm: Diameter of circle with same area
        characteristic_width_mm: Type-specific width (slot width for spiral,
            minor axis for oval, None for round)
        path_length_mm: Total path length (arc length for spiral, None for round)
        pa_ratio_mm_inv: Perimeter-to-area ratio in mm⁻¹ (acoustic efficiency metric)
    """

    aperture_type: str
    area_mm2: float
    perimeter_mm: float
    equivalent_diameter_mm: float
    characteristic_width_mm: Optional[float] = None
    path_length_mm: Optional[float] = None
    pa_ratio_mm_inv: Optional[float] = None


def equivalent_diameter_from_area(area_mm2: float) -> float:
    """
    Compute diameter of a circle with the given area.

    Formula: d = 2 * sqrt(area / pi)

    This enables comparison of non-circular apertures to traditional
    round soundholes by answering: "What size round hole has the same area?"

    Args:
        area_mm2: Aperture area in square millimeters

    Returns:
        Equivalent diameter in millimeters
    """
    if area_mm2 <= 0:
        return 0.0
    return 2.0 * math.sqrt(area_mm2 / math.pi)


def aperture_from_spiral_geometry(geo: SpiralGeometry) -> ApertureGeometry:
    """
    Convert SpiralGeometry to normalized ApertureGeometry.

    Gracefully handles missing spec metadata by setting
    characteristic_width_mm to None.

    Args:
        geo: Computed spiral geometry from compute_spiral_geometry()

    Returns:
        Normalized ApertureGeometry with spiral-specific fields populated
    """
    return ApertureGeometry(
        aperture_type="spiral",
        area_mm2=geo.area_mm2,
        perimeter_mm=geo.perimeter_mm,
        equivalent_diameter_mm=equivalent_diameter_from_area(geo.area_mm2),
        characteristic_width_mm=geo.spec.slot_width_mm if geo.spec else None,
        path_length_mm=geo.total_length_mm,
        pa_ratio_mm_inv=geo.pa_ratio_mm_inv,
    )


def aperture_geometry_to_dict(ap: ApertureGeometry) -> Dict:
    """
    Serialize ApertureGeometry to dict for API response.

    Args:
        ap: ApertureGeometry instance

    Returns:
        Dictionary suitable for JSON serialization
    """
    return asdict(ap)
