"""
CP-S56.5 — Advanced Offset Engine

Provides production-grade polygon offsetting using shapely.geometry.LineString.buffer()
with support for miter/round/bevel join styles, arc tessellation, and self-intersection cleanup.

Falls back to simple vector offset when shapely unavailable.

Key Features:
- Join styles: miter (sharp corners), round (arc segments), bevel (chamfered)
- Miter limit control for sharp joins
- Arc segment density control (max_arc_segment_deg)
- Automatic self-intersection resolution via unary_union
- Arc length tessellation for uniform segment density

Dependencies:
- shapely>=2.0.0 (optional, falls back gracefully)

Usage:
```python
from cam_core.geometry.advanced_offset import offset_polyline_advanced, HAVE_SHAPELY

if HAVE_SHAPELY:
    offset_pts = offset_polyline_advanced(
        points=[(0,0), (100,0), (100,50), (0,50)],
        offset_dist_mm=5.0,
        join_style="round",
        miter_limit=4.0,
        max_arc_segment_deg=10.0
    )
```
"""

from __future__ import annotations

from typing import List, Literal, Tuple
from math import pi, ceil, sqrt

from .geometry_models import Point

# Optional shapely integration
try:
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    HAVE_SHAPELY = True
except ImportError:
    HAVE_SHAPELY = False


JoinStyle = Literal["miter", "round", "bevel"]


def _join_style_to_shapely(style: JoinStyle) -> int:
    """
    Map string join style to shapely buffer join_style parameter.

    Shapely's buffer uses:
    - join_style=1: round (circular arcs at corners)
    - join_style=2: mitre (sharp corners with miter limit)
    - join_style=3: bevel (flat chamfer at corners)

    Args:
        style: "miter", "round", or "bevel"

    Returns:
        int: shapely join_style code (1, 2, or 3)
    """
    if style == "round":
        return 1
    if style == "miter":
        return 2
    if style == "bevel":
        return 3
    return 2  # Default to miter


def _extract_exterior_coords(geom) -> List[Point]:
    """
    Extract exterior coordinates from shapely geometry.

    Handles Polygon, MultiPolygon, and LineString geometries.
    For MultiPolygon, returns largest polygon by area.

    Args:
        geom: shapely geometry (Polygon, MultiPolygon, or LineString)

    Returns:
        List of (x, y) point tuples
    """
    if geom is None:
        return []

    if geom.geom_type == "Polygon":
        return [(float(x), float(y)) for (x, y, *_) in geom.exterior.coords]

    if geom.geom_type == "MultiPolygon":
        # Take largest polygon by area
        polys = list(geom.geoms)
        if not polys:
            return []
        biggest = max(polys, key=lambda g: g.area)
        return [(float(x), float(y)) for (x, y, *_) in biggest.exterior.coords]

    if geom.geom_type == "LineString":
        return [(float(x), float(y)) for (x, y, *_) in geom.coords]

    # Unknown geometry type
    return []


def _tessellate_arc_length(coords: List[Point], max_segment_len_mm: float = 1.0) -> List[Point]:
    """
    Resample polyline with uniform arc-length segments.

    Ensures no segment exceeds max_segment_len_mm. Useful for densifying
    round joins to maintain smooth curves in G-code output.

    Args:
        coords: Input polyline points
        max_segment_len_mm: Maximum segment length (default 1.0 mm)

    Returns:
        Resampled polyline with uniform segment density
    """
    if len(coords) < 2:
        return coords

    result = [coords[0]]

    for i in range(len(coords) - 1):
        p1 = coords[i]
        p2 = coords[i + 1]

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        seg_len = sqrt(dx * dx + dy * dy)

        if seg_len <= max_segment_len_mm:
            # Segment short enough, keep as is
            result.append(p2)
        else:
            # Subdivide segment
            num_subseg = int(ceil(seg_len / max_segment_len_mm))
            for j in range(1, num_subseg + 1):
                t = j / num_subseg
                x = p1[0] + t * dx
                y = p1[1] + t * dy
                result.append((x, y))

    return result


def offset_polyline_advanced(
    points: List[Point],
    offset_dist_mm: float,
    join_style: JoinStyle = "miter",
    miter_limit: float = 4.0,
    max_arc_segment_deg: float = 10.0,
) -> List[Point]:
    """
    Compute advanced polygon offset using shapely.

    Features:
    - Join styles (miter/round/bevel)
    - Automatic self-intersection cleanup
    - Arc segment control for round joins
    - Miter limit for sharp corners

    Args:
        points: Input polyline [(x, y), ...]
        offset_dist_mm: Offset distance (positive = outward, negative = inward)
        join_style: "miter" (sharp), "round" (arcs), or "bevel" (flat)
        miter_limit: Maximum miter extension (as multiple of offset distance)
        max_arc_segment_deg: Maximum arc segment angle (degrees) for round joins

    Returns:
        Offset polyline as list of (x, y) points

    Raises:
        ImportError: If shapely not available (fallback to simple offset recommended)
        ValueError: If input polyline invalid or offset produces degenerate geometry
    """
    if not HAVE_SHAPELY:
        raise ImportError(
            "shapely not available - cannot use advanced offset. "
            "Install with: pip install shapely>=2.0.0"
        )

    if len(points) < 3:
        raise ValueError("Advanced offset requires at least 3 points")

    # Create LineString from input points
    ls = LineString(points)

    # Calculate shapely resolution parameter
    # resolution controls segments per quadrant (90 degrees)
    # resolution = 4 => 22.5 deg segments
    # Want max_arc_segment_deg, so resolution ≈ 90 / max_arc_segment_deg
    resolution = max(1, int(ceil(90.0 / max_arc_segment_deg)))

    # Apply buffer with specified join style
    # buffer distance: positive = outward, negative = inward
    geom = ls.buffer(
        offset_dist_mm,
        join_style=_join_style_to_shapely(join_style),
        mitre_limit=miter_limit,
        resolution=resolution,
    )

    # Normalize geometry (resolves self-intersections)
    geom = unary_union(geom)

    # Extract exterior coordinates
    coords = _extract_exterior_coords(geom)

    if not coords:
        raise ValueError(
            f"Offset {offset_dist_mm}mm produced degenerate geometry. "
            "Try reducing offset distance or check input geometry."
        )

    # Tessellate arc-length for uniform segment density
    # Use max_arc_segment_deg converted to mm (approximation)
    max_seg_len = abs(offset_dist_mm) * (max_arc_segment_deg / 90.0) * 2.0
    max_seg_len = max(0.1, max_seg_len)  # Clamp to at least 0.1mm
    coords = _tessellate_arc_length(coords, max_seg_len)

    return coords


# Convenience function for fallback compatibility
def offset_polyline_safe(
    points: List[Point],
    offset_dist_mm: float,
    join_style: JoinStyle = "miter",
    miter_limit: float = 4.0,
    max_arc_segment_deg: float = 10.0,
    fallback_simple=None,
) -> List[Point]:
    """
    Safe wrapper for offset_polyline_advanced with fallback.

    Attempts advanced offset via shapely. If shapely unavailable or operation fails,
    falls back to simple offset function if provided.

    Args:
        points: Input polyline
        offset_dist_mm: Offset distance
        join_style: Join style (ignored if fallback used)
        miter_limit: Miter limit (ignored if fallback used)
        max_arc_segment_deg: Arc segment control (ignored if fallback used)
        fallback_simple: Optional simple offset function(points, offset) -> points

    Returns:
        Offset polyline, using advanced method if available, otherwise fallback

    Example:
    ```python
    from cam_core.geometry.offset_curve import offset_polyline  # simple version

    offset_pts = offset_polyline_safe(
        points=my_points,
        offset_dist_mm=5.0,
        join_style="round",
        fallback_simple=offset_polyline  # Simple vector offset fallback
    )
    ```
    """
    try:
        if HAVE_SHAPELY:
            return offset_polyline_advanced(
                points, offset_dist_mm, join_style, miter_limit, max_arc_segment_deg
            )
    except (ImportError, ValueError, Exception) as e:
        # Advanced offset failed, use fallback if available
        if fallback_simple is not None:
            return fallback_simple(points, offset_dist_mm)
        raise  # Re-raise if no fallback

    # Shapely not available and no fallback
    if fallback_simple is not None:
        return fallback_simple(points, offset_dist_mm)

    raise ImportError("Advanced offset requires shapely or fallback function")
