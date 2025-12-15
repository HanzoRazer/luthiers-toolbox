"""
Neck Taper Suite: Outline Generator

Wave 17 - Instrument Geometry Integration

Converts taper math into actual 2D CAD coordinates suitable for:
- DXF export
- GeometryEngine integration
- Art Studio visualization
- CNC toolpath generation
"""

from __future__ import annotations
from typing import List, Tuple

from .taper_math import compute_taper_table, TaperInputs, FretWidth


Point = Tuple[float, float]   # (x, y)


def generate_neck_outline(inputs: TaperInputs, frets: List[int]) -> List[Point]:
    """
    Generate left- and right-edge points forming a polyline outline
    of the tapered fingerboard.
    
    The outline is suitable for:
    - Conversion to DXF POLYLINE
    - GeometryEngine MLPath
    - SVG path generation
    - CNC perimeter toolpaths
    
    Coordinate System:
        - X axis: Distance from nut (longitudinal)
        - Y axis: Width across fretboard (transverse)
        - Origin: Nut centerline
        - Y negative: Bass side (left edge)
        - Y positive: Treble side (right edge)
    
    Args:
        inputs: Taper input parameters
        frets: List of fret numbers to include in outline
        
    Returns:
        Single list of (x, y) points tracing:
            left edge (nut → end) → end cap → right edge (end → nut) → nut cap → close
            
    Example:
        >>> inputs = TaperInputs(scale_length=647.7, nut_width=42.0,
        ...                      end_fret=12, end_width=57.0)
        >>> outline = generate_neck_outline(inputs, range(0, 13))
        >>> len(outline)  # 13 left + 13 right + 1 close = 27
        27
    """
    table: List[FretWidth] = compute_taper_table(inputs, frets)

    # Left edge: nut to end fret (bass side, negative Y)
    left_edge = [(fw.distance_from_nut, -fw.half_width) for fw in table]
    
    # Right edge: end fret to nut (treble side, positive Y) - reversed order
    right_edge = [(fw.distance_from_nut, fw.half_width) for fw in reversed(table)]

    # Full closed outline
    outline = left_edge + right_edge + [left_edge[0]]
    return outline
