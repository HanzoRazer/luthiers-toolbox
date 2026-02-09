"""Adaptive Pocketing Engine - L.1 Robust Offsetting"""
import math
from typing import List, Tuple, Dict, Any, Optional, Literal
import pyclipper

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Clipper integer scaling factor (10,000× for 0.0001mm precision)
SCALE: float = 10_000.0

# Tool diameter bounds (mm)
MIN_TOOL_DIAMETER_MM: float = 0.5    # 0.5mm minimum tool size (micro end mills)
MAX_TOOL_DIAMETER_MM: float = 50.0   # 50mm maximum tool size (face mills)

# Stepover bounds (fraction of tool diameter)
MIN_STEPOVER: float = 0.3            # 30% minimum stepover (aggressive roughing)
MAX_STEPOVER: float = 0.7            # 70% maximum stepover (conservative finishing)

# Geometry validation
MIN_POLYGON_AREA_MM2: float = 0.5    # Degenerate polygon threshold (filter tiny rings)

# =============================================================================
# COORDINATE SPACE CONVERSION
# =============================================================================

def _scale_up(paths: List[List[Tuple[float, float]]]) -> List[List[Tuple[int, int]]]:
    """Convert mm float coordinates to integer space for pyclipper."""
    out = []
    for path in paths:
        out.append([(int(round(x * SCALE)), int(round(y * SCALE))) for x, y in path])
    return out


def _scale_down(paths: List[List[Tuple[int, int]]]) -> List[List[Tuple[float, float]]]:
    """Convert integer coordinates back to mm float space."""
    out = []
    for path in paths:
        out.append([(x / SCALE, y / SCALE) for x, y in path])
    return out


# =============================================================================
# GEOMETRY UTILITY FUNCTIONS
# =============================================================================

def polygon_area(loop: List[Tuple[float, float]]) -> float:
    """Calculate polygon area using shoelace formula."""
    a = 0.0
    n = len(loop)
    for i in range(n):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


# =============================================================================
# POLYGON ORIENTATION AND CLOSURE
# =============================================================================

def _close(path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Ensure polygon is closed (first point equals last point)."""
    if not path:
        return path
    if path[0] != path[-1]:
        return path + [path[0]]
    return path

def _clean_and_orient(
    outer: List[Tuple[float, float]],
    islands: List[List[Tuple[float, float]]]
) -> Tuple[List[Tuple[float, float]], List[List[Tuple[float, float]]]]:
    """Ensure closed rings with proper orientation for pyclipper."""
    def signed_area(polygon: List[Tuple[float, float]]) -> float:
        """Calculate signed area (positive=CCW, negative=CW)"""
        s = 0.0
        for i in range(len(polygon)):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]
            s += x1 * y2 - x2 * y1
        return s / 2.0
    
    # Process outer boundary (make CCW)
    out = _close(outer)
    if signed_area(out) < 0:  # Currently CW, reverse to CCW
        out = out[::-1]
    
    # Process islands (make CW)
    holes = []
    for island in islands:
        h = _close(island)
        if signed_area(h) > 0:  # Currently CCW, reverse to CW
            h = h[::-1]
        holes.append(h)
    
    return out, holes


# =============================================================================
# BOOLEAN POLYGON OPERATIONS
# =============================================================================

def _difference(
    subject: List[List[Tuple[int, int]]],
    clip: List[List[Tuple[int, int]]]
) -> List[List[Tuple[int, int]]]:
    """Compute boolean difference: subject - clip (removes clip from subject)."""
    pc = pyclipper.Pyclipper()
    pc.AddPaths(subject, pyclipper.PT_SUBJECT, True)
    if clip:
        pc.AddPaths(clip, pyclipper.PT_CLIP, True)
    solution = pc.Execute(
        pyclipper.CT_DIFFERENCE,
        pyclipper.PFT_NONZERO,
        pyclipper.PFT_NONZERO
    )
    return solution

# =============================================================================
# ROBUST OFFSET STACK GENERATION
# =============================================================================

def build_offset_stacks_robust(
    outer: List[Tuple[float, float]],
    islands: List[List[Tuple[float, float]]],
    tool_d: float,
    stepover: float,
    margin: float,
    join_type: int = pyclipper.JT_ROUND,
    end_type: int = pyclipper.ET_CLOSEDPOLYGON,
    arc_tolerance_mm: float = 0.2,
    miter_limit: float = 2.0,
) -> List[List[Tuple[float, float]]]:
    """Generate inward offset rings from outer boundary while avoiding islands."""
    # Validate inputs (fail-safe)
    if tool_d <= 0:
        raise ValueError(f"Tool diameter must be positive, got: {tool_d}")
    if not (0.0 < stepover <= 1.0):
        raise ValueError(f"Stepover must be in range (0, 1], got: {stepover}")
    if margin < 0:
        raise ValueError(f"Margin must be non-negative, got: {margin}")
    
    # Clean and orient polygons for pyclipper
    outer, islands = _clean_and_orient(outer, islands)
    
    # Check minimum area requirement
    if polygon_area(outer) < MIN_POLYGON_AREA_MM2:
        return []

    # Calculate step distances
    step = max(0.05, min(0.95, stepover)) * tool_d  # Clamp stepover to sane range
    first_inset = tool_d / 2.0 + margin

    # Initialize pyclipper offset engine
    co = pyclipper.PyclipperOffset(miter_limit, arc_tolerance_mm * SCALE)
    subj = _scale_up([outer])
    holes = _scale_up(islands)

    # Generate initial inset from outer boundary
    co.Clear()
    co.AddPaths(subj, join_type, end_type)
    inset = co.Execute(-first_inset * SCALE)  # Negative = inset (inward)
    if not inset:
        return []

    # Subtract islands (expanded outward by tool radius for clearance)
    if holes:
        co_hole = pyclipper.PyclipperOffset(miter_limit, arc_tolerance_mm * SCALE)
        co_hole.AddPaths(holes, join_type, end_type)
        hole_expand = co_hole.Execute((tool_d / 2.0) * SCALE)
        inset = _difference(inset, hole_expand)

    rings = []
    current = inset[:]

    # Iterate to generate successive inward offset rings
    while current:
        # Convert to mm and filter degenerate polygons
        mm_rings = _scale_down(current)
        mm_rings = [r for r in mm_rings if polygon_area(r) > MIN_POLYGON_AREA_MM2]
        if not mm_rings:
            break
        rings += mm_rings

        # Generate next inset
        co.Clear()
        co.AddPaths(current, join_type, end_type)
        nxt = co.Execute(-step * SCALE)
        if not nxt:
            break
        
        # Subtract island clearance zones (same expansion every step)
        if holes:
            co_hole = pyclipper.PyclipperOffset(miter_limit, arc_tolerance_mm * SCALE)
            co_hole.AddPaths(holes, join_type, end_type)
            hole_expand = co_hole.Execute((tool_d / 2.0) * SCALE)
            nxt = _difference(nxt, hole_expand)
        
        current = nxt

    return rings

# =============================================================================
# TOOLPATH LINKING STRATEGIES
# =============================================================================

def spiralize_linked(rings: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
    """Connect multiple offset rings into a single continuous toolpath."""
    if not rings:
        return []
    
    from math import hypot
    
    path = []
    prev = None
    
    for ring in rings:
        if not ring:
            continue
        
        if prev is None:
            # First ring starts at index 0
            start_idx = 0
        else:
            # Pick closest vertex to previous endpoint
            start_idx = min(
                range(len(ring)),
                key=lambda i: hypot(ring[i][0] - prev[0], ring[i][1] - prev[1])
            )
        
        # Reorder ring to start at closest point
        ordered = ring[start_idx:] + ring[:start_idx]
        path.extend(ordered)
        prev = ordered[-1]
    
    return path


# =============================================================================
# G-CODE MOVE GENERATION
# =============================================================================

def to_toolpath(
    path_pts: List[Tuple[float, float]],
    feed_xy: float,
    z_rough: float,
    safe_z: float,
    lead_r: float = 0.0,
) -> List[Dict[str, Any]]:
    """Convert XY path points to G-code move sequence."""
    # Validate inputs (fail-safe)
    if feed_xy <= 0:
        raise ValueError(f"Feed rate must be positive, got: {feed_xy}")
    if z_rough > 0:
        raise ValueError(f"Cutting depth must be negative, got: {z_rough}")
    if safe_z < 0:
        raise ValueError(f"Safe Z must be positive, got: {safe_z}")
    
    moves = []
    
    if path_pts:
        sx, sy = path_pts[0]
        
        # Retract to safe height
        moves.append({"code": "G0", "z": safe_z})
        
        # Rapid to start XY
        moves.append({"code": "G0", "x": sx, "y": sy})
        
        # Plunge to cutting depth
        moves.append({"code": "G1", "z": z_rough, "f": feed_xy})
        
        # Cutting moves
        for x, y in path_pts[1:]:
            moves.append({"code": "G1", "x": x, "y": y, "f": feed_xy})
    
    # Final retract
    moves.append({"code": "G0", "z": safe_z})
    
    return moves


# =============================================================================
# MAIN PLANNING FUNCTION (L.1 ENTRY POINT)
# =============================================================================

def plan_adaptive_l1(
    loops: List[List[Tuple[float, float]]],
    tool_d: float,
    stepover: float,
    stepdown: float,
    margin: float,
    strategy: Literal["Spiral", "Lanes"],
    smoothing_radius: float,
) -> List[Tuple[float, float]]:
    """Plan adaptive pocket toolpath with robust offsetting and island handling."""
    # Validate inputs (fail-safe)
    if not loops or len(loops[0]) < 3:
        raise ValueError("At least one loop with 3+ vertices required")
    
    if not (MIN_TOOL_DIAMETER_MM <= tool_d <= MAX_TOOL_DIAMETER_MM):
        raise ValueError(
            f"Tool diameter must be in range [{MIN_TOOL_DIAMETER_MM}, {MAX_TOOL_DIAMETER_MM}], "
            f"got: {tool_d}"
        )
    
    if not (MIN_STEPOVER <= stepover <= MAX_STEPOVER):
        raise ValueError(
            f"Stepover must be in range [{MIN_STEPOVER}, {MAX_STEPOVER}], "
            f"got: {stepover}"
        )
    
    # Extract outer boundary and islands
    outer = loops[0]
    islands = loops[1:] if len(loops) > 1 else []
    
    # Validate pocket is large enough for tool
    outer_area = polygon_area(outer)
    if outer_area < MIN_POLYGON_AREA_MM2:
        raise ValueError(f"Outer boundary area too small: {outer_area:.2f} mm²")
    
    # Generate offset rings with island subtraction
    rings = build_offset_stacks_robust(
        outer,
        islands,
        tool_d=tool_d,
        stepover=stepover,
        margin=margin,
        join_type=pyclipper.JT_ROUND,
        end_type=pyclipper.ET_CLOSEDPOLYGON,
        arc_tolerance_mm=max(0.05, min(1.0, smoothing_radius)),  # Clamp to sane range
        miter_limit=2.0,
    )
    
    if not rings:
        raise ValueError("No valid offset rings generated (pocket too small or tool too large)")
    
    # Apply strategy: Spiral (continuous) or Lanes (discrete)
    if strategy.lower().startswith("spiral"):
        path = spiralize_linked(rings)
    else:
        # "lanes": Flatten rings (discrete passes with implicit retracts)
        path = [pt for ring in rings for pt in ring]
    
    return path
