# services/api/app/cad/dxf_validators.py
"""
Geometry validation functions with configurable guardrails.

These validators run BEFORE geometry is added to DXF documents,
preventing invalid or dangerous geometry from reaching the export stage.
"""

from __future__ import annotations

from typing import Iterable, Optional, List, Tuple
import math

from .exceptions import DxfValidationError, GeometryError
from .geometry_models import (
    Point2D, Polyline2D, Circle2D, Arc2D, Line2D,
    DxfDocumentConfig, EntityList,
)


# =============================================================================
# ENTITY COUNT VALIDATION
# =============================================================================

def ensure_entity_limit(entity_count: int, config: DxfDocumentConfig) -> None:
    """
    Verify entity count doesn't exceed configured maximum.
    
    Raises:
        DxfValidationError: If entity_count > config.max_entities
    """
    if entity_count > config.max_entities:
        raise DxfValidationError(
            f"Entity limit exceeded: {entity_count} > {config.max_entities}",
            field="max_entities",
            value=entity_count,
            constraint=f"<= {config.max_entities}",
        )


# =============================================================================
# COORDINATE BOUNDS VALIDATION
# =============================================================================

def ensure_point_within_bounds(point: Point2D, config: DxfDocumentConfig) -> None:
    """
    Verify a single point is within coordinate limits.
    
    Raises:
        DxfValidationError: If point coordinates exceed config.coord_limit
    """
    limit = config.coord_limit
    if abs(point.x) > limit:
        raise DxfValidationError(
            f"X coordinate {point.x} exceeds limit ±{limit}",
            field="x",
            value=point.x,
            constraint=f"abs(x) <= {limit}",
        )
    if abs(point.y) > limit:
        raise DxfValidationError(
            f"Y coordinate {point.y} exceeds limit ±{limit}",
            field="y",
            value=point.y,
            constraint=f"abs(y) <= {limit}",
        )


def ensure_points_within_bounds(
    points: Iterable[Point2D], 
    config: DxfDocumentConfig
) -> None:
    """
    Verify all points are within coordinate limits.
    
    Raises:
        DxfValidationError: If any point exceeds config.coord_limit
    """
    for point in points:
        ensure_point_within_bounds(point, config)


# =============================================================================
# POLYLINE VALIDATION
# =============================================================================

def validate_polyline(poly: Polyline2D, config: DxfDocumentConfig) -> None:
    """
    Comprehensive polyline validation.
    
    Checks:
      - Minimum point count
      - All points within bounds
      - No degenerate segments (zero length)
    
    Raises:
        DxfValidationError: If validation fails
    """
    if len(poly.points) < 2:
        raise DxfValidationError(
            "Polyline must have at least 2 points",
            field="points",
            value=len(poly.points),
            constraint=">= 2",
        )
    
    ensure_points_within_bounds(poly.points, config)
    
    # Check for degenerate (zero-length) segments
    for i in range(len(poly.points) - 1):
        if poly.points[i].distance_to(poly.points[i + 1]) < 1e-9:
            raise DxfValidationError(
                f"Degenerate segment at index {i}: points are identical",
                field="points",
                value=i,
                constraint="adjacent points must be distinct",
            )


# =============================================================================
# CIRCLE/ARC VALIDATION
# =============================================================================

def validate_circle(circle: Circle2D, config: DxfDocumentConfig) -> None:
    """
    Circle validation.
    
    Checks:
      - Center within bounds
      - Radius is positive and reasonable
      - Full circle fits within bounds
    """
    ensure_point_within_bounds(circle.center, config)
    
    if circle.radius <= 0:
        raise DxfValidationError(
            "Circle radius must be positive",
            field="radius",
            value=circle.radius,
            constraint="> 0",
        )
    
    # Check if full circle fits within bounds
    limit = config.coord_limit
    if abs(circle.center.x) + circle.radius > limit:
        raise DxfValidationError(
            "Circle extends beyond X coordinate limit",
            field="radius",
            value=circle.radius,
            constraint=f"center.x + radius <= {limit}",
        )
    if abs(circle.center.y) + circle.radius > limit:
        raise DxfValidationError(
            "Circle extends beyond Y coordinate limit",
            field="radius",
            value=circle.radius,
            constraint=f"center.y + radius <= {limit}",
        )


def validate_arc(arc: Arc2D, config: DxfDocumentConfig) -> None:
    """
    Arc validation.
    
    Checks:
      - Center within bounds
      - Radius is positive
      - Arc endpoints within bounds
    """
    ensure_point_within_bounds(arc.center, config)
    
    if arc.radius <= 0:
        raise DxfValidationError(
            "Arc radius must be positive",
            field="radius",
            value=arc.radius,
            constraint="> 0",
        )
    
    # Same bounding check as circle
    limit = config.coord_limit
    if abs(arc.center.x) + arc.radius > limit or abs(arc.center.y) + arc.radius > limit:
        raise DxfValidationError(
            "Arc extends beyond coordinate limits",
            field="radius",
            value=arc.radius,
        )


# =============================================================================
# LINE VALIDATION
# =============================================================================

def validate_line(line: Line2D, config: DxfDocumentConfig) -> None:
    """
    Line validation.
    
    Checks:
      - Both endpoints within bounds
      - Line has non-zero length
    """
    ensure_point_within_bounds(line.start, config)
    ensure_point_within_bounds(line.end, config)
    
    if line.length() < 1e-9:
        raise DxfValidationError(
            "Line has zero length (start and end are identical)",
            field="length",
            value=line.length(),
            constraint="> 0",
        )


# =============================================================================
# BATCH VALIDATION
# =============================================================================

def validate_entity(entity, config: DxfDocumentConfig) -> None:
    """
    Validate any supported entity type.
    """
    if isinstance(entity, Polyline2D):
        validate_polyline(entity, config)
    elif isinstance(entity, Circle2D):
        validate_circle(entity, config)
    elif isinstance(entity, Arc2D):
        validate_arc(entity, config)
    elif isinstance(entity, Line2D):
        validate_line(entity, config)
    else:
        raise DxfValidationError(
            f"Unsupported entity type: {type(entity).__name__}",
            field="entity_type",
            value=type(entity).__name__,
        )


def validate_entities(entities: EntityList, config: DxfDocumentConfig) -> None:
    """
    Validate a list of entities.
    
    Also checks total entity count against limit.
    """
    ensure_entity_limit(len(entities), config)
    
    for i, entity in enumerate(entities):
        try:
            validate_entity(entity, config)
        except DxfValidationError as e:
            # Add index context to the error
            e.details["entity_index"] = i
            raise


# =============================================================================
# GEOMETRY SANITY CHECKS
# =============================================================================

def check_self_intersection(poly: Polyline2D) -> bool:
    """
    Check if a polyline self-intersects.
    
    Returns True if self-intersecting, False otherwise.
    Note: This is a basic O(n²) check. For complex polygons, use Shapely.
    """
    points = poly.to_tuples()
    n = len(points)
    
    if n < 4:
        return False
    
    def segments_intersect(p1, p2, p3, p4) -> bool:
        """Check if line segment p1-p2 intersects p3-p4."""
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    # Check all non-adjacent segment pairs
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue  # Skip first/last for closed polylines
            if segments_intersect(points[i], points[i + 1], points[j], points[j + 1]):
                return True
    
    return False


def compute_bounds(entities: EntityList) -> Optional[Tuple[float, float, float, float]]:
    """
    Compute bounding box for a list of entities.
    
    Returns (min_x, min_y, max_x, max_y) or None if empty.
    """
    if not entities:
        return None
    
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')
    
    for entity in entities:
        if hasattr(entity, 'bounds'):
            ex_min, ey_min, ex_max, ey_max = entity.bounds()
            min_x = min(min_x, ex_min)
            min_y = min(min_y, ey_min)
            max_x = max(max_x, ex_max)
            max_y = max(max_y, ey_max)
        elif isinstance(entity, Line2D):
            min_x = min(min_x, entity.start.x, entity.end.x)
            min_y = min(min_y, entity.start.y, entity.end.y)
            max_x = max(max_x, entity.start.x, entity.end.x)
            max_y = max(max_y, entity.start.y, entity.end.y)
    
    if min_x == float('inf'):
        return None
    
    return (min_x, min_y, max_x, max_y)


def compute_total_length(entities: EntityList) -> float:
    """
    Compute total length of all entities.
    """
    total = 0.0
    
    for entity in entities:
        if isinstance(entity, Polyline2D):
            total += entity.total_length()
        elif isinstance(entity, Circle2D):
            total += entity.circumference()
        elif isinstance(entity, Arc2D):
            total += entity.arc_length()
        elif isinstance(entity, Line2D):
            total += entity.length()
    
    return total
