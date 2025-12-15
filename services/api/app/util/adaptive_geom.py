# server/util/adaptive_geom.py
from __future__ import annotations
from typing import List, Tuple, Optional
import math

Pt = Tuple[float, float]


def rect_offset_path(width: float, height: float, offset: float) -> List[Pt]:
    """Return rectangle loop at given inward offset (centered on origin)."""
    w = max(0.0, width - 2 * offset)
    h = max(0.0, height - 2 * offset)
    if w <= 0 or h <= 0:
        return []
    x0, y0 = -w / 2, -h / 2
    x1, y1 = w / 2, h / 2
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def link_spiral(rings: List[List[Pt]]) -> List[Pt]:
    """
    Link successive rings end-to-start to form a single continuous spiral-like path.
    Alternates direction for each ring to create continuous motion.
    """
    out: List[Pt] = []
    flip = False
    prev_end: Optional[Pt] = None
    
    for loop in rings:
        if not loop:
            continue
        
        # Alternate direction for continuous spiral
        seg = loop if not flip else list(reversed(loop))
        
        # Connect to previous ring
        if out and prev_end is not None and seg:
            out.append(seg[0])
        
        out.extend(seg)
        prev_end = seg[-1] if seg else prev_end
        flip = not flip
    
    return out


def fillet_polyline(poly: List[Pt], rad: float) -> List[Pt]:
    """
    Lightweight fillet: trim 'rad' at corners and insert a midpoint (approximate).
    Smooths sharp corners in toolpaths.
    """
    if len(poly) < 3:
        return poly[:]
    
    out: List[Pt] = []
    n = len(poly)
    
    for i in range(1, n - 1):
        p0, p1, p2 = poly[i - 1], poly[i], poly[i + 1]
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        
        def norm(v):
            l = math.hypot(v[0], v[1])
            return (v[0] / l, v[1] / l) if l > 1e-9 else (0.0, 0.0)
        
        n1 = norm(v1)
        n2 = norm(v2)
        t1 = (p1[0] - n1[0] * rad, p1[1] - n1[1] * rad)
        t2 = (p1[0] + n2[0] * rad, p1[1] + n2[1] * rad)
        mid = ((t1[0] + t2[0]) * 0.5, (t1[1] + t2[1]) * 0.5)
        
        if i == 1:
            out.append((t1[0], t1[1]))
        out.append(mid)
        if i == n - 2:
            out.append((t2[0], t2[1]))
    
    # Close the loop if input was closed
    if poly[0] == poly[-1]:
        out.append(out[0])
    
    return out


def inward_offset_spiral_rect(
    width: float,
    height: float,
    tool_dia: float,
    stepover: float,
    corner_fillet: float = 0.0
) -> List[Pt]:
    """
    Generate successive inward offsets of a rectangle, spaced by stepover from tool radius.
    Stitches rings into a continuous spiral path.
    
    Args:
        width: Rectangle width (mm)
        height: Rectangle height (mm)
        tool_dia: Tool diameter (mm)
        stepover: Distance between passes (mm)
        corner_fillet: Optional corner rounding radius (mm)
        
    Returns:
        List of points forming continuous spiral toolpath
    """
    r = tool_dia * 0.5
    rings: List[List[Pt]] = []
    k = 0
    
    # Generate inward offset rings
    while True:
        off = r + k * stepover
        loop = rect_offset_path(width, height, off)
        
        if not loop or len(loop) < 2:
            break  # Area collapsed
        
        # Optional corner filleting
        if corner_fillet > 0 and len(loop) >= 4:
            loop = fillet_polyline(loop, corner_fillet)
        
        rings.append(loop)
        k += 1
    
    return link_spiral(rings)


def trochoid_corner_loops(
    poly: List[Pt],
    tool_dia: float,
    loop_pitch: float,
    amp: float
) -> List[Pt]:
    """
    Generate small sine-like loops around interior corners to reduce chip load.
    Illustrative trochoidal corner manager.
    
    Args:
        poly: Input polygon (boundary)
        tool_dia: Tool diameter (mm)
        loop_pitch: Spacing between loop points (mm)
        amp: Loop amplitude (mm)
        
    Returns:
        List of points with trochoidal loops at corners
    """
    pts: List[Pt] = []
    
    if len(poly) < 3:
        return pts
    
    r = tool_dia * 0.5
    
    for i in range(1, len(poly) - 1):
        cx, cy = poly[i]
        
        # Generate sine-modulated loop around corner
        steps = max(16, int(2 * math.pi * r / (loop_pitch if loop_pitch > 0 else 1.0)))
        
        for k in range(steps + 1):
            th = 2 * math.pi * k / steps
            rad = r + amp * math.sin(3 * th)  # Sine modulation
            pts.append((cx + rad * math.cos(th), cy + rad * math.sin(th)))
        
        pts.append(poly[i + 1])
    
    return pts


def svg_polyline(points: List[Pt], stroke: str = "black") -> str:
    """
    Generate SVG polyline from list of points.
    Auto-scales viewbox to fit content.
    
    Args:
        points: List of (x, y) points
        stroke: SVG stroke color
        
    Returns:
        SVG string
    """
    if not points:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    
    pad = 10.0
    w = (maxx - minx) + 2 * pad
    h = (maxy - miny) + 2 * pad
    
    # Transform points to SVG coordinates (flip Y axis)
    pts = " ".join([f"{x-minx+pad:.2f},{h-(y-miny+pad):.2f}" for x, y in points])
    
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.0f} {h:.0f}">'
        f'<polyline fill="none" stroke="{stroke}" stroke-width="1" points="{pts}" />'
        f'</svg>'
    )
