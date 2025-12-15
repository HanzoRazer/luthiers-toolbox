# services/api/app/toolpath/rosette_geometry.py

"""
Rosette Geometry Generator

Generates concentric rosette ring geometry as MLPaths.

Features:
- Parametric rosette design specification
- Concentric ring generation
- Polygon approximation of circles
- Statistics calculation for preview
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from . import MLPath, Point2D


@dataclass
class RosetteRingSpec:
    """
    One rosette ring, defined by center, radius, and polygon resolution.

    Attributes:
        center_x_mm: X coordinate of ring center
        center_y_mm: Y coordinate of ring center
        radius_mm: Radius of the ring
        segments: Number of polygon segments (default 128)
    """

    center_x_mm: float
    center_y_mm: float
    radius_mm: float
    segments: int = 128


@dataclass
class RosetteDesignSpec:
    """
    High-level rosette design specification.

    Attributes:
        outer_diameter_mm: Overall outer diameter of the rosette
        inner_diameter_mm: Inner opening diameter (e.g., soundhole edge)
        ring_count: Number of concentric rings between inner and outer
        center_x_mm: X offset from (0,0)
        center_y_mm: Y offset from (0,0)
        segments_per_ring: Polygon resolution per ring
    """

    outer_diameter_mm: float
    inner_diameter_mm: float
    ring_count: int
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
    segments_per_ring: int = 128

    def to_ring_specs(self) -> List[RosetteRingSpec]:
        """
        Convert design spec to individual ring specifications.

        Returns:
            List of RosetteRingSpec for each concentric ring

        Raises:
            ValueError: If inner diameter >= outer diameter or ring_count <= 0
        """
        if self.ring_count <= 0:
            return []

        outer_r = self.outer_diameter_mm / 2.0
        inner_r = self.inner_diameter_mm / 2.0

        if inner_r < 0 or outer_r <= inner_r:
            raise ValueError("Invalid inner/outer diameters for rosette.")

        # Equal radial spacing between inner and outer
        step = (outer_r - inner_r) / self.ring_count
        specs: List[RosetteRingSpec] = []

        for i in range(self.ring_count):
            r = inner_r + (i + 0.5) * step
            specs.append(
                RosetteRingSpec(
                    center_x_mm=self.center_x_mm,
                    center_y_mm=self.center_y_mm,
                    radius_mm=r,
                    segments=self.segments_per_ring,
                )
            )

        return specs


def ring_spec_to_mlpath(spec: RosetteRingSpec) -> MLPath:
    """
    Convert a ring specification to an MLPath (closed polygon).

    Args:
        spec: Ring specification

    Returns:
        MLPath representing the ring as a closed polygon
    """
    pts: List[Point2D] = []
    n = max(12, spec.segments)

    for k in range(n):
        ang = 2.0 * math.pi * k / n
        x = spec.center_x_mm + spec.radius_mm * math.cos(ang)
        y = spec.center_y_mm + spec.radius_mm * math.sin(ang)
        pts.append((x, y))

    # Close loop
    pts.append(pts[0])

    return MLPath(points=pts, is_closed=True)


def build_rosette_mlpaths(design: RosetteDesignSpec) -> List[MLPath]:
    """
    Generate rosette geometry from design specification.

    This is the high-level entrypoint: design spec → list of ring MLPaths.

    Args:
        design: Rosette design specification

    Returns:
        List of MLPath objects, one per concentric ring
    """
    mlpaths: List[MLPath] = []

    for ring_spec in design.to_ring_specs():
        mlpaths.append(ring_spec_to_mlpath(ring_spec))

    return mlpaths


def rosette_stats(paths: Iterable[MLPath]) -> Dict[str, Any]:
    """
    Calculate statistics for rosette geometry.

    Stats include:
    - ring_count: Number of rings
    - bbox: Bounding box (min_x, min_y, max_x, max_y)
    - approx_circumference_sum: Total circumference of all rings

    Args:
        paths: Iterable of MLPath objects

    Returns:
        Dictionary with statistics
    """
    paths_list = list(paths)
    ring_count = len(paths_list)

    if not paths_list:
        return {
            "ring_count": 0,
            "bbox": None,
            "approx_circumference_sum": 0.0,
        }

    xs: List[float] = []
    ys: List[float] = []
    length_sum = 0.0

    for path in paths_list:
        pts = path.points
        if not pts:
            continue

        for (x, y) in pts:
            xs.append(x)
            ys.append(y)

        for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
            dx = x2 - x1
            dy = y2 - y1
            length_sum += math.hypot(dx, dy)

    if xs and ys:
        bbox = {
            "min_x": min(xs),
            "min_y": min(ys),
            "max_x": max(xs),
            "max_y": max(ys),
        }
    else:
        bbox = None

    return {
        "ring_count": ring_count,
        "bbox": bbox,
        "approx_circumference_sum": length_sum,
    }
