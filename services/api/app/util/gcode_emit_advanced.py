from __future__ import annotations
from typing import List, Tuple, Optional
import math

Pt = Tuple[float, float]


def _angle(a: Pt, b: Pt, c: Pt) -> float:
    """Calculate angle at point b between vectors ba and bc"""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.hypot(*v1) or 1.0
    n2 = math.hypot(*v2) or 1.0
    cosv = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.acos(cosv)


def _fillet_points(a: Pt, b: Pt, c: Pt, r: float):
    """
    Calculate fillet arc parameters at corner b between points a-b-c.
    
    Returns:
        Tuple of (p1, p2, ccw, center) where:
        - p1: Arc start point
        - p2: Arc end point
        - ccw: 1 for CCW arc (G3), -1 for CW arc (G2)
        - center: Arc center point
        
        Returns None if fillet cannot be computed (straight line, etc)
    """
    ang = _angle(a, b, c)
    if ang <= 1e-6 or ang >= math.pi - 1e-6:
        return None  # Straight line or 180° turn
    
    t = r / math.tan(ang / 2.0)
    ab_len = math.hypot(a[0] - b[0], a[1] - b[1])
    cb_len = math.hypot(c[0] - b[0], c[1] - b[1])
    
    if ab_len < 1e-6 or cb_len < 1e-6:
        return None
    
    # Clamp tangent length to avoid overshooting
    t = min(t, ab_len * 0.49, cb_len * 0.49)
    
    # Unit vectors from b to a and b to c
    ux1, uy1 = (a[0] - b[0]) / ab_len, (a[1] - b[1]) / ab_len
    ux2, uy2 = (c[0] - b[0]) / cb_len, (c[1] - b[1]) / cb_len
    
    # Fillet start/end points
    p1 = (b[0] + (-ux1) * t, b[1] + (-uy1) * t)
    p2 = (b[0] + (-ux2) * t, b[1] + (-uy2) * t)
    
    # Bisector direction
    vx = ux1 + ux2
    vy = uy1 + uy2
    nv = math.hypot(vx, vy) or 1.0
    bx, by = vx / nv, vy / nv
    
    # Determine arc direction (CCW or CW)
    cross = ux1 * uy2 - uy1 * ux2
    ccw = 1 if cross < 0 else -1
    
    # Arc center distance from corner
    d = r / math.sin(ang / 2.0)
    center = (b[0] + bx * d, b[1] + by * d)
    
    return p1, p2, ccw, center


def emit_xy_with_arcs(
    paths: List[List[Pt]],
    *,
    z: float = -1.0,
    safe_z: float = 5.0,
    units: str = "mm",
    feed: float = 600.0,
    feed_arc: Optional[float] = None,
    feed_floor: Optional[float] = None,
    link_radius: float = 1.0
) -> str:
    """
    Generate G-code with arc fillets at corners for smooth motion.
    
    Args:
        paths: List of polygons (each polygon is list of points)
        z: Cutting depth in mm
        safe_z: Retract height in mm
        units: "mm" or "inch"
        feed: Linear feed rate (mm/min or in/min)
        feed_arc: Optional arc feed rate (defaults to feed)
        feed_floor: Optional minimum feed for tight arcs
        link_radius: Fillet radius for corner arcs in mm/inch
        
    Returns:
        G-code string with G2/G3 arc commands at corners
    """
    u = "G21" if units.lower().startswith("mm") else "G20"
    lines = [
        "(N17 Polygon Offset — arcs + feed floors)",
        u,
        "G90",  # Absolute positioning
        "G17",  # XY plane
        f"G0 Z{safe_z:.3f}"
    ]
    
    f_lin = f"F{feed:.1f}"
    f_arc = f"F{(feed_arc if feed_arc else feed):.1f}"
    
    for poly in paths:
        if not poly or len(poly) < 2:
            continue
        
        # Ensure closed polygon
        if poly[0] != poly[-1]:
            poly = poly + [poly[0]]
        
        # Rapid to start, plunge
        x0, y0 = poly[0]
        lines += [
            f"G0 X{x0:.3f} Y{y0:.3f}",
            f"G1 Z{z:.3f} {f_lin}"
        ]
        
        n = len(poly) - 1
        for i in range(1, n):
            a = poly[i - 1]
            b = poly[i]
            c = poly[(i + 1) % n]
            
            # Try to compute fillet arc
            fil = _fillet_points(a, b, c, link_radius)
            
            if fil is None:
                # No fillet possible, use straight line
                lines.append(f"G1 X{b[0]:.3f} Y{b[1]:.3f}")
                continue
            
            p1, p2, ccw, center = fil
            
            # Move to arc start
            lines.append(f"G1 X{p1[0]:.3f} Y{p1[1]:.3f}")
            
            # Compute arc feed rate (reduce for tight radii)
            r = link_radius
            f_use = feed_arc if feed_arc else feed
            if feed_floor is not None and r < 1.0:
                f_use = max(feed_floor, f_use * 0.6)
            
            # Emit arc command (G2=CW, G3=CCW)
            i_off = center[0] - p1[0]
            j_off = center[1] - p1[1]
            g = "G3" if ccw > 0 else "G2"
            lines.append(f"{g} X{p2[0]:.3f} Y{p2[1]:.3f} I{i_off:.3f} J{j_off:.3f} F{f_use:.1f}")
        
        # Retract
        lines.append(f"G0 Z{safe_z:.3f}")
    
    lines += ["M30"]
    return "\n".join(lines)
