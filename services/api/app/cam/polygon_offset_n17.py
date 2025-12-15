from __future__ import annotations
from typing import List, Tuple, Optional
import math

Pt = Tuple[float, float]

# Try pyclipper for robust offsetting, fallback to simple miter
try:
    import pyclipper
    HAS_PYCLIPPER = True
except ImportError:
    HAS_PYCLIPPER = False

SCALE = 1000.0  # Integer scaling for pyclipper

def offset_polygon_mm(
    poly: List[Pt],
    offset: float,
    join_type: str = "miter",
    arc_tolerance: float = 0.25,
    miter_limit: float = 2.0
) -> Optional[List[List[Pt]]]:
    """
    Offset a closed polygon by `offset` mm (positive=outward, negative=inward).
    
    Args:
        poly: Closed polygon as list of (x,y) points in mm
        offset: Offset distance in mm (+ outward, - inward)
        join_type: "miter", "round", or "bevel"
        arc_tolerance: For round joins, max deviation in mm
        miter_limit: Max miter extension as multiple of offset
        
    Returns:
        List of offset polygons (may be multiple if self-intersecting input)
        None if offsetting fails or produces empty result
    """
    if not poly or len(poly) < 3:
        return None
    
    if HAS_PYCLIPPER:
        # Robust pyclipper offsetting
        pc = pyclipper.PyclipperOffset(miter_limit=miter_limit, arc_tolerance=arc_tolerance*SCALE)
        
        join_map = {
            "miter": pyclipper.JT_MITER,
            "round": pyclipper.JT_ROUND,
            "bevel": pyclipper.JT_SQUARE
        }
        jt = join_map.get(join_type.lower(), pyclipper.JT_MITER)
        
        # Scale to integer space
        poly_scaled = [(int(x * SCALE), int(y * SCALE)) for x, y in poly]
        
        pc.AddPath(poly_scaled, jt, pyclipper.ET_CLOSEDPOLYGON)
        result = pc.Execute(offset * SCALE)
        
        if not result:
            return None
        
        # Scale back to mm and convert to list of polygons
        result_mm = []
        for path in result:
            if len(path) >= 3:
                result_mm.append([(x / SCALE, y / SCALE) for x, y in path])
        
        # Return largest polygon by area if multiple results
        if len(result_mm) > 1:
            result_mm.sort(key=lambda p: abs(_polygon_area(p)), reverse=True)
        
        return result_mm if result_mm else None
    else:
        # Fallback: simple miter offsetting (no self-intersection handling)
        return _offset_fallback(poly, offset, miter_limit)


def _offset_fallback(poly: List[Pt], offset: float, miter_limit: float) -> Optional[List[List[Pt]]]:
    """Simple miter offset fallback when pyclipper unavailable"""
    n = len(poly)
    if n < 3:
        return None
    
    result = []
    for i in range(n):
        p1 = poly[(i - 1) % n]
        p2 = poly[i]
        p3 = poly[(i + 1) % n]
        
        # Edge vectors
        v1 = (p2[0] - p1[0], p2[1] - p1[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        # Normals (left perpendicular)
        n1_len = math.hypot(v1[0], v1[1]) or 1.0
        n1 = (-v1[1] / n1_len, v1[0] / n1_len)
        
        n2_len = math.hypot(v2[0], v2[1]) or 1.0
        n2 = (-v2[1] / n2_len, v2[0] / n2_len)
        
        # Bisector (average of normals)
        bx = (n1[0] + n2[0]) / 2.0
        by = (n1[1] + n2[1]) / 2.0
        b_len = math.hypot(bx, by) or 1.0
        
        # Miter offset distance
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        angle = math.atan2(cross, v1[0] * v2[0] + v1[1] * v2[1])
        sin_half = math.sin(angle / 2.0)
        
        if abs(sin_half) < 1e-6:
            # Straight line, use normal
            d = abs(offset)
        else:
            d = abs(offset) / abs(sin_half)
            # Clamp miter to limit
            d = min(d, abs(offset) * miter_limit)
        
        # Apply offset in bisector direction
        sign = 1 if offset > 0 else -1
        result.append((
            p2[0] + sign * (bx / b_len) * d,
            p2[1] + sign * (by / b_len) * d
        ))
    
    return [result] if result else None


def _polygon_area(poly: List[Pt]) -> float:
    """Calculate signed area of polygon (positive=CCW, negative=CW)"""
    area = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def toolpath_offsets(
    poly: List[Pt],
    tool_dia: float,
    stepover: float,
    inward: bool = True,
    join_type: str = "round",
    arc_tolerance: float = 0.25
) -> List[List[Pt]]:
    """
    Generate multiple offset passes for pocketing/profiling.
    
    Args:
        poly: Boundary polygon (closed)
        tool_dia: Tool diameter in mm
        stepover: Distance between passes in mm
        inward: True for pocketing (offset inward), False for profiling (offset outward)
        join_type: "miter", "round", or "bevel"
        arc_tolerance: For round joins, max deviation in mm
        
    Returns:
        List of offset paths (outer to inner for pocketing)
    """
    if not poly or tool_dia <= 0 or stepover <= 0:
        return []
    
    # Early exit: check if polygon is too small to offset
    initial_area = abs(_polygon_area(poly))
    if initial_area < 1.0:  # Less than 1 mm²
        return []
    
    paths = []
    current = poly[:]
    offset_dist = -stepover if inward else stepover  # Negative for inward
    
    # Calculate reasonable max passes based on geometry
    # Estimate: area / (stepover * perimeter)
    perimeter = sum(math.hypot(poly[i][0]-poly[i-1][0], poly[i][1]-poly[i-1][1]) for i in range(len(poly)))
    estimated_passes = max(5, min(50, int(initial_area / (stepover * perimeter / 4))))
    
    # Generate successive offsets until area collapses
    for pass_num in range(estimated_passes):
        result = offset_polygon_mm(current, offset_dist, join_type, arc_tolerance)
        
        if not result or len(result) == 0:
            break  # No more valid offsets
        
        # Take largest polygon (in case of splits)
        offset_poly = result[0]
        
        # Check if area is too small (collapsed)
        area = abs(_polygon_area(offset_poly))
        if area < 0.5:  # Less than 0.5 mm² (essentially degenerate)
            break
        
        # Early exit if polygon has too few vertices (degenerate)
        if len(offset_poly) < 3:
            break
        
        paths.append(offset_poly)
        current = offset_poly
    
    return paths
