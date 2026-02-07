# services/api/app/cad/offset_engine.py
"""
Geometry offset engine using Shapely.

This module provides optional offset/buffer operations for toolpath generation.
Gracefully degrades if Shapely is not installed.

Usage:
    from cad.offset_engine import offset_polyline, is_offset_available
    
    if is_offset_available():
        result = offset_polyline(poly, distance=0.5)
"""

from __future__ import annotations

from typing import List, Optional, Literal
import logging

from .geometry_models import Point2D, Polyline2D
from .exceptions import OffsetEngineNotAvailable, OffsetEngineError

logger = logging.getLogger(__name__)


# =============================================================================
# SHAPELY AVAILABILITY CHECK
# =============================================================================

_SHAPELY_AVAILABLE = False
_LineString = None
_Polygon = None

try:
    from shapely.geometry import LineString, Polygon  # type: ignore[import]
    from shapely.geometry.base import JOIN_STYLE  # type: ignore[import]
    _LineString = LineString
    _Polygon = Polygon
    _SHAPELY_AVAILABLE = True
    logger.debug("Shapely is available for offset operations")
except ImportError:
    logger.info("Shapely not installed - offset operations disabled")


def is_offset_available() -> bool:
    """Check if offset operations are available (Shapely installed)."""
    return _SHAPELY_AVAILABLE


def require_shapely() -> None:
    """Raise OffsetEngineNotAvailable if Shapely is not installed."""
    if not _SHAPELY_AVAILABLE:
        raise OffsetEngineNotAvailable()


# =============================================================================
# JOIN STYLE MAPPING
# =============================================================================

JoinStyleType = Literal["round", "mitre", "miter", "bevel"]


def _get_join_style(style: JoinStyleType) -> int:
    """
    Map join style string to Shapely constant.
    
    Args:
        style: One of "round", "mitre"/"miter", "bevel"
        
    Returns:
        Shapely JOIN_STYLE enum value
    """
    require_shapely()
    from shapely.geometry.base import JOIN_STYLE
    
    style_lower = style.lower().strip()
    style_map = {
        "round": JOIN_STYLE.round,
        "mitre": JOIN_STYLE.mitre,
        "miter": JOIN_STYLE.mitre,
        "bevel": JOIN_STYLE.bevel,
    }
    return style_map.get(style_lower, JOIN_STYLE.round)


# =============================================================================
# OFFSET OPERATIONS
# =============================================================================

def offset_polyline(
    polyline: Polyline2D,
    distance: float,
    join_style: JoinStyleType = "round",
    resolution: int = 16,
    single_sided: bool = False,
) -> List[Polyline2D]:
    """
    Offset a polyline by a given distance.
    
    Positive distance = outward (for closed) or left (for open)
    Negative distance = inward (for closed) or right (for open)
    
    Args:
        polyline: Input polyline
        distance: Offset distance (positive = outward/left)
        join_style: Corner style ("round", "mitre", "bevel")
        resolution: Number of segments for curved corners
        single_sided: If True, only offset one side (for open polylines)
        
    Returns:
        List of resulting polylines (may be multiple if geometry splits)
        
    Raises:
        OffsetEngineNotAvailable: If Shapely not installed
        OffsetEngineError: If offset operation fails
    """
    require_shapely()
    
    points = [(p.x, p.y) for p in polyline.points]
    
    try:
        if polyline.closed:
            # Use Polygon for closed polylines
            geom = _Polygon(points)
            if single_sided:
                buffer_geom = geom.buffer(
                    distance, 
                    resolution=resolution,
                    join_style=_get_join_style(join_style),
                    single_sided=True,
                )
            else:
                buffer_geom = geom.buffer(
                    distance,
                    resolution=resolution,
                    join_style=_get_join_style(join_style),
                )
        else:
            # Use LineString for open polylines
            geom = _LineString(points)
            buffer_geom = geom.buffer(
                abs(distance),
                resolution=resolution,
                join_style=_get_join_style(join_style),
                single_sided=single_sided,
            )
        
        return _shapely_to_polylines(buffer_geom)
        
    except (ValueError, TypeError) as exc:  # WP-1: narrowed from except Exception
        raise OffsetEngineError(
            f"Offset operation failed: {exc}",
            details={"distance": distance, "point_count": len(points)}
        ) from exc


def parallel_offset(
    polyline: Polyline2D,
    distance: float,
    side: Literal["left", "right"] = "left",
    resolution: int = 16,
    join_style: JoinStyleType = "round",
) -> Optional[Polyline2D]:
    """
    Create a parallel offset of an open polyline.
    
    This is specifically for toolpath generation where you want a single
    offset line rather than a buffer polygon.
    
    Args:
        polyline: Input polyline (should be open)
        distance: Offset distance
        side: Which side to offset ("left" or "right")
        resolution: Curve resolution
        join_style: Corner style
        
    Returns:
        Single offset polyline, or None if operation produces invalid geometry
        
    Raises:
        OffsetEngineNotAvailable: If Shapely not installed
    """
    require_shapely()
    
    points = [(p.x, p.y) for p in polyline.points]
    
    try:
        geom = _LineString(points)
        
        # Shapely's parallel_offset
        offset_geom = geom.parallel_offset(
            distance,
            side=side,
            resolution=resolution,
            join_style=_get_join_style(join_style),
        )
        
        if offset_geom.is_empty:
            return None
        
        # Extract coordinates
        if hasattr(offset_geom, 'coords'):
            coords = list(offset_geom.coords)
            pts = [Point2D(x=x, y=y) for x, y in coords]
            return Polyline2D(points=pts, closed=False)
        
        return None
        
    except (ValueError, TypeError) as exc:  # WP-1: narrowed from except Exception
        logger.warning(f"Parallel offset failed: {exc}")
        return None


def inset_polygon(
    polyline: Polyline2D,
    distance: float,
    resolution: int = 16,
) -> List[Polyline2D]:
    """
    Inset a closed polygon by a given distance.
    
    This is a convenience wrapper for negative offset on closed polylines.
    
    Args:
        polyline: Closed polyline to inset
        distance: Inset distance (positive = inward)
        resolution: Curve resolution
        
    Returns:
        List of inset polylines (may be empty if polygon collapses)
    """
    if not polyline.closed:
        raise OffsetEngineError(
            "inset_polygon requires a closed polyline",
            details={"closed": polyline.closed}
        )
    
    # Negative offset = inset
    return offset_polyline(polyline, -abs(distance), resolution=resolution)


# =============================================================================
# BOOLEAN OPERATIONS (if needed later)
# =============================================================================

def union_polylines(polylines: List[Polyline2D]) -> List[Polyline2D]:
    """
    Compute union of multiple closed polylines.
    
    Args:
        polylines: List of closed polylines
        
    Returns:
        Unified polylines
    """
    require_shapely()
    from shapely.ops import unary_union
    
    polygons = []
    for poly in polylines:
        if poly.closed:
            points = [(p.x, p.y) for p in poly.points]
            polygons.append(_Polygon(points))
    
    if not polygons:
        return []
    
    result = unary_union(polygons)
    return _shapely_to_polylines(result)


def difference_polylines(
    base: Polyline2D, 
    subtract: List[Polyline2D]
) -> List[Polyline2D]:
    """
    Subtract polylines from a base polygon.
    
    Args:
        base: Base closed polyline
        subtract: List of closed polylines to subtract
        
    Returns:
        Resulting polylines after subtraction
    """
    require_shapely()
    
    if not base.closed:
        raise OffsetEngineError("Base must be a closed polyline")
    
    base_points = [(p.x, p.y) for p in base.points]
    base_poly = _Polygon(base_points)
    
    for sub in subtract:
        if sub.closed:
            sub_points = [(p.x, p.y) for p in sub.points]
            sub_poly = _Polygon(sub_points)
            base_poly = base_poly.difference(sub_poly)
    
    return _shapely_to_polylines(base_poly)


# =============================================================================
# HELPERS
# =============================================================================

def _shapely_to_polylines(geom) -> List[Polyline2D]:
    """
    Convert Shapely geometry to list of Polyline2D.
    
    Handles Polygon, MultiPolygon, LineString, MultiLineString.
    """
    result: List[Polyline2D] = []
    
    if geom.is_empty:
        return result
    
    geom_type = geom.geom_type
    
    if geom_type == "Polygon":
        # Extract exterior ring
        coords = list(geom.exterior.coords)
        if len(coords) >= 2:
            pts = [Point2D(x=x, y=y) for x, y in coords[:-1]]  # Skip duplicate last point
            if pts:
                result.append(Polyline2D(points=pts, closed=True))
        
        # Also extract holes if any
        for interior in geom.interiors:
            coords = list(interior.coords)
            if len(coords) >= 2:
                pts = [Point2D(x=x, y=y) for x, y in coords[:-1]]
                if pts:
                    result.append(Polyline2D(points=pts, closed=True))
    
    elif geom_type == "MultiPolygon":
        for poly in geom.geoms:
            result.extend(_shapely_to_polylines(poly))
    
    elif geom_type == "LineString":
        coords = list(geom.coords)
        if len(coords) >= 2:
            pts = [Point2D(x=x, y=y) for x, y in coords]
            result.append(Polyline2D(points=pts, closed=False))
    
    elif geom_type == "MultiLineString":
        for line in geom.geoms:
            result.extend(_shapely_to_polylines(line))
    
    elif geom_type == "GeometryCollection":
        for g in geom.geoms:
            result.extend(_shapely_to_polylines(g))
    
    return result


def simplify_polyline(
    polyline: Polyline2D, 
    tolerance: float = 0.1
) -> Polyline2D:
    """
    Simplify a polyline using Douglas-Peucker algorithm.
    
    Args:
        polyline: Input polyline
        tolerance: Simplification tolerance in model units
        
    Returns:
        Simplified polyline
    """
    require_shapely()
    
    points = [(p.x, p.y) for p in polyline.points]
    
    if polyline.closed:
        geom = _Polygon(points)
        simplified = geom.simplify(tolerance, preserve_topology=True)
        coords = list(simplified.exterior.coords)[:-1]
    else:
        geom = _LineString(points)
        simplified = geom.simplify(tolerance, preserve_topology=True)
        coords = list(simplified.coords)
    
    pts = [Point2D(x=x, y=y) for x, y in coords]
    return Polyline2D(points=pts, closed=polyline.closed)
