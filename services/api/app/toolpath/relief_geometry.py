# services/api/app/toolpath/relief_geometry.py

"""
Relief Geometry Handler

Handles relief geometry conversion to MLPaths.

For Wave 3, we only handle 2D XY contour geometry.
Z/height mapping will be added in future waves.

Features:
- Polyline to MLPath conversion
- Relief design specification
- Statistics calculation for preview
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from . import MLPath, Point2D


@dataclass
class ReliefPolylineSpec:
    """
    Simple relief polyline specification.

    For Wave 3, we only handle 2D XY contour geometry.
    Z/height mapping will be added later.

    Attributes:
        points: List of (x, y) coordinate tuples
    """

    points: List[Point2D]


@dataclass
class ReliefDesignSpec:
    """
    Relief design composed of multiple polylines.

    For now, each polyline is an outline at Z=0.0.

    Attributes:
        polylines: List of polyline specifications
    """

    polylines: List[ReliefPolylineSpec]


def relief_design_to_mlpaths(design: ReliefDesignSpec) -> List[MLPath]:
    """
    Convert relief design specification to MLPaths.

    Args:
        design: Relief design specification

    Returns:
        List of MLPath objects
    """
    mlpaths: List[MLPath] = []

    for poly in design.polylines:
        if not poly.points:
            continue

        # Check if path is closed (first point == last point)
        is_closed = (
            len(poly.points) > 2 and poly.points[0] == poly.points[-1]
        )

        mlpaths.append(
            MLPath(points=list(poly.points), is_closed=is_closed)
        )

    return mlpaths


def relief_stats(mlpaths: Iterable[MLPath]) -> Dict[str, Any]:
    """
    Calculate statistics for relief geometry.

    Stats include:
    - path_count: Number of paths
    - bbox: Bounding box (min_x, min_y, max_x, max_y)
    - total_length: Total path length

    Args:
        mlpaths: Iterable of MLPath objects

    Returns:
        Dictionary with statistics
    """
    paths = list(mlpaths)

    if not paths:
        return {
            "path_count": 0,
            "bbox": None,
            "total_length": 0.0,
        }

    xs: List[float] = []
    ys: List[float] = []
    total_length = 0.0

    for p in paths:
        for x, y in p.points:
            xs.append(x)
            ys.append(y)

        # Calculate path length
        pts = p.points
        if len(pts) >= 2:
            for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
                dx = x2 - x1
                dy = y2 - y1
                total_length += (dx * dx + dy * dy) ** 0.5

    if not xs or not ys:
        bbox = None
    else:
        bbox = {
            "min_x": min(xs),
            "min_y": min(ys),
            "max_x": max(xs),
            "max_y": max(ys),
        }

    return {
        "path_count": len(paths),
        "bbox": bbox,
        "total_length": total_length,
    }
