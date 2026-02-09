"""Adaptive Pocketing Engine - L.2 True Spiralizer + Adaptive Stepover"""
import math
from typing import List, Tuple, Dict, Any, Optional, Union, Literal
import pyclipper
from .adaptive_core_l1 import (
    build_offset_stacks_robust, polygon_area, spiralize_linked,
    MIN_TOOL_DIAMETER_MM, MAX_TOOL_DIAMETER_MM, MIN_STEPOVER, MAX_STEPOVER
)
from .adaptive_spiralizer_utils import (
    adaptive_respace, compute_slowdown_factors, curvature
)

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Corner fillet bounds (mm)
MIN_CORNER_RADIUS_MM: float = 0.5    # Minimum fillet radius (micro corners)
MAX_CORNER_RADIUS_MM: float = 25.0   # Maximum fillet radius (large rounds)

# Feed slowdown bounds (percentage)
MIN_FEED_SLOWDOWN_PCT: float = 20.0  # Minimum feed reduction (20% slower)
MAX_FEED_SLOWDOWN_PCT: float = 80.0  # Maximum feed reduction (80% slower)

# Feed rate bounds (mm/min)
MIN_FEED_RATE_MM_MIN: float = 50.0       # Minimum feed rate (safety)
MAX_FEED_RATE_MM_MIN: float = 10000.0    # Maximum feed rate (rapid traverse)

# =============================================================================
# GEOMETRIC UTILITY FUNCTIONS
# =============================================================================

def _nearest_index(ring: List[Tuple[float, float]], pt: Tuple[float, float]) -> int:
    """Find index of nearest point in ring to given point."""
    from math import hypot
    return min(
        range(len(ring)),
        key=lambda i: hypot(ring[i][0] - pt[0], ring[i][1] - pt[1])
    )


def _closest_pair(
    a: List[Tuple[float, float]],
    b: List[Tuple[float, float]]
) -> Tuple[int, int]:
    """Find indices of closest point pair between two rings."""
    from math import hypot
    best = (0, 0, 1e18)  # (idx_a, idx_b, distance)
    
    for i, pa in enumerate(a):
        for j, pb in enumerate(b):
            d = hypot(pa[0] - pb[0], pa[1] - pb[1])
            if d < best[2]:
                best = (i, j, d)
    
    return best[0], best[1]


def _angle(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate turn angle at p1 between vectors p0→p1 and p1→p2."""
    ax, ay = p0[0] - p1[0], p0[1] - p1[1]
    bx, by = p2[0] - p1[0], p2[1] - p1[1]
    
    a = math.atan2(ay, ax)
    b = math.atan2(by, bx)
    
    d = b - a
    
    # Normalize to [-π, π]
    while d > math.pi:
        d -= 2 * math.pi
    while d < -math.pi:
        d += 2 * math.pi
    
    return abs(d)

# =============================================================================
# CORNER FILLET GENERATION
# =============================================================================

def _fillet(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    R: float
) -> Optional[Tuple[Dict[str, Any], Tuple[float, float], Tuple[float, float]]]:
    """Generate arc fillet at corner with specified radius."""
    import numpy as np
    
    # Convert to numpy arrays for vector math
    v1 = np.array(p0, dtype=float) - np.array(p1, dtype=float)
    v2 = np.array(p2, dtype=float) - np.array(p1, dtype=float)
    
    # Normalize vectors (add epsilon to avoid division by zero)
    n1 = v1 / (np.linalg.norm(v1) + 1e-12)
    n2 = v2 / (np.linalg.norm(v2) + 1e-12)
    
    # Calculate turn angle
    ang = _angle(p0, p1, p2)
    
    # Reject near-straight lines (no meaningful fillet)
    if ang < 1e-3:
        return None
    
    # Distance from corner to tangency points
    t = R / math.tan(ang / 2.0)
    
    # Check if legs are long enough for fillet (45% safety factor)
    max_t = min(np.linalg.norm(v1), np.linalg.norm(v2)) * 0.45
    if t > max_t:
        return None
    
    # Calculate tangency points
    t1 = np.array(p1, float) + (-n1) * t
    t2 = np.array(p1, float) + (-n2) * t
    
    # Calculate arc center via bisector method
    bisector = n1 + n2
    bisector_len = np.linalg.norm(bisector)
    
    if bisector_len < 1e-9:  # Degenerate (180° turn)
        return None
    
    bisector_unit = bisector / bisector_len
    
    # Center distance from corner
    dc = R / math.sin(ang / 2.0)
    center = np.array(p1, float) + bisector_unit * dc
    cx, cy = float(center[0]), float(center[1])
    
    # Calculate arc start/end angles (degrees for G2/G3)
    start_angle = math.degrees(math.atan2(t1[1] - cy, t1[0] - cx))
    end_angle = math.degrees(math.atan2(t2[1] - cy, t2[0] - cx))
    
    # Determine arc direction (choose shorter path)
    delta_angle = end_angle - start_angle
    
    # Normalize to [-180, 180]
    while delta_angle > 180.0:
        delta_angle -= 360.0
    while delta_angle < -180.0:
        delta_angle += 360.0
    
    cw = delta_angle < 0  # Clockwise if negative delta
    
    arc_dict = {
        "type": "arc",
        "cx": cx,
        "cy": cy,
        "r": R,
        "start": start_angle,
        "end": end_angle,
        "cw": cw
    }
    
    return arc_dict, (float(t1[0]), float(t1[1])), (float(t2[0]), float(t2[1]))

# =============================================================================
# FILLET INJECTION (PATH ENHANCEMENT)
# =============================================================================

def inject_min_fillet(
    path: List[Tuple[float, float]],
    corner_radius_min: float
) -> Tuple[List[Union[Tuple[float, float], Dict[str, Any]]], List[Dict[str, Any]]]:
    """Insert arc fillets at sharp corners to prevent machine jerking."""
    # Validate corner radius
    if not (MIN_CORNER_RADIUS_MM <= corner_radius_min <= MAX_CORNER_RADIUS_MM):
        raise ValueError(
            f"Corner radius must be in range [{MIN_CORNER_RADIUS_MM}, {MAX_CORNER_RADIUS_MM}], "
            f"got: {corner_radius_min}"
        )
    
    if len(path) < 3 or corner_radius_min <= 0:
        return path[:], []
    
    mixed: List[Union[Tuple[float, float], Dict[str, Any]]] = []
    overlays: List[Dict[str, Any]] = []
    n = len(path)
    
    for i in range(n):
        p0 = path[(i - 1) % n]
        p1 = path[i]
        p2 = path[(i + 1) % n]
        
        ang = _angle(p0, p1, p2)
        
        # Only fillet significant turns (< 160° = ~2.79 radians)
        if ang < math.radians(160):
            fillet_result = _fillet(p0, p1, p2, corner_radius_min)
            
            if fillet_result:
                arcdef, t1, t2 = fillet_result
                
                # Insert: tangency_point1 → arc → tangency_point2
                mixed.append(t1)
                mixed.append(arcdef)
                mixed.append(t2)
                
                # Add HUD overlay annotation
                overlays.append({
                    "kind": "fillet",
                    "at": [p1[0], p1[1]],
                    "radius": corner_radius_min
                })
                continue
        
        # No fillet needed/possible, keep original point
        mixed.append(p1)
    
    return mixed, overlays

# =============================================================================
# ADAPTIVE STEPOVER MODULATION
# =============================================================================

def adaptive_local_stepover(
    rings: List[List[Tuple[float, float]]],
    target_stepover: float,
    tool_d: float
) -> List[List[Tuple[float, float]]]:
    """Adjust ring spacing based on local geometry complexity."""
    # Validate inputs
    if not (MIN_STEPOVER <= target_stepover <= MAX_STEPOVER):
        raise ValueError(
            f"Target stepover must be in range [{MIN_STEPOVER}, {MAX_STEPOVER}], "
            f"got: {target_stepover}"
        )
    
    if not (MIN_TOOL_DIAMETER_MM <= tool_d <= MAX_TOOL_DIAMETER_MM):
        raise ValueError(
            f"Tool diameter must be in range [{MIN_TOOL_DIAMETER_MM}, {MAX_TOOL_DIAMETER_MM}], "
            f"got: {tool_d}"
        )
    
    if not rings:
        return rings
    
    def calculate_perimeter(ring: List[Tuple[float, float]]) -> float:
        """Calculate total perimeter of ring"""
        s = 0.0
        for i in range(len(ring)):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % len(ring)]
            s += math.hypot(x2 - x1, y2 - y1)
        return s
    
    out = [rings[0]]  # Always keep first ring
    
    for k in range(1, len(rings)):
        prev = rings[k - 1]
        cur = rings[k]
        
        # Calculate perimeter ratio (curvature heuristic)
        perim_prev = calculate_perimeter(prev)
        perim_cur = calculate_perimeter(cur)
        ratio = perim_cur / (perim_prev + 1e-9)  # Avoid division by zero
        
        # Densify if tight zone detected (ratio > 0.92)
        if ratio > 0.92:
            out.append(cur)
            
            # Insert interpolated mid-ring
            min_len = min(len(prev), len(cur))
            mid = [
                ((prev[i][0] + cur[i][0]) / 2.0, (prev[i][1] + cur[i][1]) / 2.0)
                for i in range(min_len)
            ]
            out.append(mid)
        else:
            # Normal spacing, keep current ring
            out.append(cur)
    
    return out

# =============================================================================
# TRUE SPIRAL STITCHING
# =============================================================================

def true_spiral_from_rings(
    rings: List[List[Tuple[float, float]]]
) -> List[Tuple[float, float]]:
    """Build continuous spiral toolpath by stitching rings with smooth connectors."""
    if not rings:
        return []
    
    path: List[Tuple[float, float]] = []
    
    # Start with outermost ring
    path.extend(rings[0])
    tail = path[-1]
    
    # Stitch each subsequent ring
    for k in range(1, len(rings)):
        ring = rings[k]
        
        # Find closest connection point
        i0, j0 = _closest_pair([tail], ring)
        
        # Connect with short segment (could add micro-arc for smoothness)
        connect = [ring[j0]]
        
        # Reorder ring to start from connection point
        ordered = ring[j0:] + ring[:j0]
        
        path.extend(connect + ordered)
        tail = path[-1]
    
    return path

# =============================================================================
# HUD OVERLAY GENERATION (VISUAL ANALYSIS)
# =============================================================================

def analyze_overloads(
    path: List[Union[Tuple[float, float], Dict[str, Any]]],
    tool_d: float,
    corner_radius_min: float,
    feed_xy: float,
    slowdown_feed_pct: float
) -> List[Dict[str, Any]]:
    """Generate HUD overlay annotations for tight zones and feed slowdowns."""
    # Validate feed rate
    if not (MIN_FEED_RATE_MM_MIN <= feed_xy <= MAX_FEED_RATE_MM_MIN):
        raise ValueError(
            f"Feed rate must be in range [{MIN_FEED_RATE_MM_MIN}, {MAX_FEED_RATE_MM_MIN}], "
            f"got: {feed_xy}"
        )
    
    # Validate slowdown percentage
    if not (MIN_FEED_SLOWDOWN_PCT <= slowdown_feed_pct <= MAX_FEED_SLOWDOWN_PCT):
        raise ValueError(
            f"Feed slowdown must be in range [{MIN_FEED_SLOWDOWN_PCT}, {MAX_FEED_SLOWDOWN_PCT}]%, "
            f"got: {slowdown_feed_pct}"
        )
    
    overlays: List[Dict[str, Any]] = []
    pts: List[Tuple[float, float]] = []
    
    # Extract explicit arcs and points
    for item in path:
        if isinstance(item, dict) and item.get("type") == "arc":
            # Check explicit arc radius
            if item["r"] < corner_radius_min:
                overlays.append({
                    "kind": "tight_radius",
                    "at": [item["cx"], item["cy"]],
                    "radius": item["r"]
                })
        else:
            # Add point (handle both tuple and list)
            pts.append(item if isinstance(item, tuple) else tuple(item))
    
    # Analyze implicit corners from point sequence
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        ang = _angle(p0, p1, p2)
        
        if ang == 0:  # Straight line, skip
            continue
        
        # Infer corner radius using geometric approximation
        # Formula: r ≈ chord / (2 × tan(θ/2))
        chord = min(
            math.hypot(p1[0] - p0[0], p1[1] - p0[1]),
            math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        )
        
        inferred_r = chord / (2.0 * math.tan(max(1e-3, ang / 2.0)))
        
        if inferred_r < corner_radius_min:
            # Mark tight radius
            overlays.append({
                "kind": "tight_radius",
                "at": [p1[0], p1[1]],
                "radius": inferred_r
            })
            
            # Add slowdown annotation
            reduced_feed = feed_xy * (slowdown_feed_pct / 100.0)
            overlays.append({
                "kind": "slowdown",
                "at": [p1[0], p1[1]],
                "feed_xy": reduced_feed
            })
    
    return overlays

# =============================================================================
# MAIN PLANNING FUNCTION (L.2 ENTRY POINT)
# =============================================================================

def plan_adaptive_l2(
    loops: List[List[Tuple[float, float]]],
    tool_d: float,
    stepover: float,
    stepdown: float,
    margin: float,
    strategy: Literal["Spiral", "Lanes"],
    smoothing_radius: float,
    corner_radius_min: float,
    target_stepover: float,
    feed_xy: float,
    slowdown_feed_pct: float
) -> Dict[str, Any]:
    """Plan adaptive pocket with L.2 advanced features."""
    # Generate robust offset rings (L.1)
    rings = build_offset_stacks_robust(
        loops[0],
        loops[1:],
        tool_d=tool_d,
        stepover=stepover,
        margin=margin,
        arc_tolerance_mm=max(0.05, min(1.0, smoothing_radius))
    )
    
    if not rings:
        return {"path": [], "overlays": [], "fillets": 0}

    # Apply adaptive local stepover (densify near tight zones)
    rings2 = adaptive_local_stepover(rings, target_stepover, tool_d)
    
    # Build continuous spiral (true stitching)
    spiral = true_spiral_from_rings(rings2)

    # Curvature-based adaptive respacing (MERGED FEATURE)
    # Densify toolpath near tight curves for uniform engagement
    ds_min = max(0.1, stepover * tool_d * 0.3)  # Min spacing in tight zones
    ds_max = max(ds_min + 0.05, stepover * tool_d * 0.9)  # Max spacing in open zones
    k_thresh = 1.0 / max(1.0, 3.0 * tool_d)  # Curvature threshold (1/R), R = 3× tool_d
    
    spiral = adaptive_respace(spiral, ds_min, ds_max, k_threshold=k_thresh)
    
    # Inject fillets at sharp corners
    mixed, fillet_notes = inject_min_fillet(spiral, corner_radius_min=corner_radius_min)

    # Generate HUD overlays (tight radii + slowdowns)
    overlays = analyze_overloads(mixed, tool_d, corner_radius_min, feed_xy, slowdown_feed_pct)
    overlays.extend(fillet_notes)  # Include fillet markers

    return {
        "path": mixed,
        "overlays": overlays,
        "fillets": len([o for o in fillet_notes if o["kind"] == "fillet"])
    }
