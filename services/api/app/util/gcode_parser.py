"""
G-code Parser and Simulator

Parses G-code and simulates XY toolpath motion with time estimation.
Supports G0/G1 (linear), G2/G3 (arcs), G20/G21 (units), F (feed rate).

Features:
- Modal state tracking (G, F, units, plane)
- Arc handling (IJ center specification + R fallback)
- Travel vs cutting distance separation
- Time estimation (rapid vs feed rates)
- XY path point generation for backplot

Author: Patch N.15
Integrated: November 2025
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional
import math
import re

Modal = Dict[str, Any]

NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
TOKEN_RE = re.compile(rf"([A-Za-z])\s*({NUM})")


def parse_lines(gcode: str) -> List[Dict[str, Any]]:
    """
    Parse G-code into structured lines with word tokens.
    
    Filters comments (parentheses and semicolon) and empty lines.
    Returns list of dicts with 'raw' line and 'words' [(letter, value), ...]
    
    Example:
        >>> parse_lines("G0 X10 Y20\\nG1 Z-1 F500")
        [{'raw': 'G0 X10 Y20', 'words': [('G', 0.0), ('X', 10.0), ('Y', 20.0)]},
         {'raw': 'G1 Z-1 F500', 'words': [('G', 1.0), ('Z', -1.0), ('F', 500.0)]}]
    """
    out = []
    for raw in gcode.splitlines():
        line = raw.strip()
        if not line or line.startswith('(') or line.startswith(';'):
            continue
        # Remove inline comments
        line = re.sub(r"\(.*?\)", "", line)
        line = line.split(';', 1)[0].strip()
        if not line:
            continue
        
        # Extract word tokens (letter + number)
        words = [(m.group(1).upper(), float(m.group(2))) for m in TOKEN_RE.finditer(line)]
        if not words:
            continue
        
        out.append({"raw": raw, "words": words})
    
    return out


def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Calculate 2D Euclidean distance."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _arc_center_from_ijk(p: Tuple[float, float], i: float, j: float) -> Tuple[float, float]:
    """Calculate arc center from current point and IJ offsets."""
    return (p[0] + i, p[1] + j)


def _arc_len(center: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float], cw: bool) -> float:
    """
    Calculate arc length from point a to point b around center.
    
    Args:
        center: Arc center point (cx, cy)
        a: Start point (x1, y1)
        b: End point (x2, y2)
        cw: True for clockwise (G2), False for counterclockwise (G3)
    
    Returns:
        Arc length in current units
    """
    ax, ay = a[0] - center[0], a[1] - center[1]
    bx, by = b[0] - center[0], b[1] - center[1]
    
    ra = math.atan2(ay, ax)
    rb = math.atan2(by, bx)
    d = rb - ra
    
    # Adjust angle based on direction
    if cw:
        if d > 0:
            d -= 2 * math.pi
    else:
        if d < 0:
            d += 2 * math.pi
    
    r = math.hypot(ax, ay)
    return abs(d) * r


def simulate(
    gcode: str,
    *,
    rapid_mm_min: float = 3000.0,
    default_feed_mm_min: float = 500.0,
    units: str = "mm"
) -> Dict[str, Any]:
    """
    Simulate G-code execution and calculate statistics.
    
    Args:
        gcode: G-code program text
        rapid_mm_min: Rapid traverse rate (G0) in mm/min
        default_feed_mm_min: Default feed rate when F not specified
        units: Input units ("mm" or "inch")
    
    Returns:
        Dict with:
        - travel_mm: Rapid traverse distance
        - cut_mm: Cutting (feed) distance
        - t_rapid_min: Rapid time in minutes
        - t_feed_min: Feed time in minutes
        - t_total_min: Total cycle time in minutes
        - points_xy: List of (x, y) points for backplot
    
    Example:
        >>> result = simulate("G0 X10 Y10\\nG1 X20 F600")
        >>> result['cut_mm']
        10.0
        >>> len(result['points_xy'])
        3
    """
    # Unit conversion factor (inch to mm)
    u = 1.0 if units.lower().startswith('mm') else 25.4
    
    prog = parse_lines(gcode)
    
    # Modal state
    modal: Modal = {
        "G": 0,
        "F": default_feed_mm_min,
        "units": u,
        "plane": 17  # G17 = XY plane
    }
    
    pos = (0.0, 0.0, 0.0)
    path_xy: List[Tuple[float, float]] = [(pos[0], pos[1])]
    
    # Accumulators
    travel = 0.0
    cut = 0.0
    t_rapid = 0.0
    t_feed = 0.0
    
    for blk in prog:
        # Parse words in this block
        g = None
        x = y = z = f = i = j = r = None
        
        for (letter, val) in blk["words"]:
            if letter == 'G':
                g = int(val)
            elif letter == 'X':
                x = val * u
            elif letter == 'Y':
                y = val * u
            elif letter == 'Z':
                z = val * u
            elif letter == 'F':
                f = val * (u / 1.0)  # Feed rate in units/min
            elif letter == 'I':
                i = val * u
            elif letter == 'J':
                j = val * u
            elif letter == 'R':
                r = val * u
        
        # Update modal feed rate
        if f is not None:
            modal["F"] = max(0.1, float(f))
        
        # Update modal state
        if g is not None:
            if g in (0, 1, 2, 3):
                modal["G"] = g
            elif g == 20:
                modal["units"] = 25.4  # Inches
            elif g == 21:
                modal["units"] = 1.0  # Millimeters
            elif g in (17, 18, 19):
                modal["plane"] = g
        
        u = modal["units"]
        
        # Calculate next position (modal: use current if not specified)
        nx = pos[0] if x is None else x
        ny = pos[1] if y is None else y
        nz = pos[2] if z is None else z
        
        code = modal["G"]
        
        # Process motion commands
        if code in (0, 1, 2, 3) and (nx != pos[0] or ny != pos[1] or nz != pos[2]):
            if code in (0, 1):  # Linear motion
                dxy = _dist((pos[0], pos[1]), (nx, ny))
                
                if code == 0:  # Rapid
                    t = dxy / max(1e-6, rapid_mm_min)
                    t_rapid += t
                    travel += dxy
                else:  # Feed (G1)
                    t = dxy / max(1e-6, modal["F"])
                    t_feed += t
                    cut += dxy
                
                path_xy.append((nx, ny))
                pos = (nx, ny, nz)
                
            elif code in (2, 3) and modal["plane"] == 17:  # Arc in XY plane
                if i is not None and j is not None:  # IJ center specification
                    c = _arc_center_from_ijk((pos[0], pos[1]), i, j)
                    length = _arc_len(c, (pos[0], pos[1]), (nx, ny), cw=(code == 2))
                    
                elif r is not None:  # R radius specification
                    c_len = _dist((pos[0], pos[1]), (nx, ny))
                    if c_len > 2 * abs(r):
                        # Invalid radius, use chord length
                        length = c_len
                    else:
                        # Calculate arc length from radius
                        theta = 2 * math.asin(max(-1.0, min(1.0, c_len / (2 * abs(r)))))
                        length = abs(theta) * abs(r)
                else:
                    # No center/radius specified, use chord length
                    length = _dist((pos[0], pos[1]), (nx, ny))
                
                t = length / max(1e-6, modal["F"])
                t_feed += t
                cut += length
                path_xy.append((nx, ny))
                pos = (nx, ny, nz)
    
    return {
        "travel_mm": travel,
        "cut_mm": cut,
        "t_rapid_min": t_rapid,
        "t_feed_min": t_feed,
        "t_total_min": t_rapid + t_feed,
        "points_xy": path_xy
    }


def svg_from_points(points: List[Tuple[float, float]], stroke: str = "black") -> str:
    """
    Generate SVG polyline from XY points.
    
    Args:
        points: List of (x, y) coordinates
        stroke: SVG stroke color
    
    Returns:
        SVG string with polyline element
    
    Example:
        >>> svg = svg_from_points([(0,0), (10,0), (10,10)])
        >>> 'polyline' in svg
        True
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
    
    # Flip Y axis for SVG (Y increases downward)
    pts = " ".join([f"{x - minx + pad:.2f},{h - (y - miny + pad):.2f}" for x, y in points])
    
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">'
        f'<polyline fill="none" stroke="{stroke}" stroke-width="1" points="{pts}" />'
        f'</svg>'
    )
