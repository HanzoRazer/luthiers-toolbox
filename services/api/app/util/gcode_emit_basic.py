from typing import List, Tuple

Pt = Tuple[float, float]


def emit_xy_polyline_nc(
    paths: List[List[Pt]],
    *,
    z: float = -1.0,
    safe_z: float = 5.0,
    units: str = "mm",
    feed: float = 600.0,
    spindle: int = 12000
) -> str:
    """
    Generate basic G-code with linear moves (G1) only.
    
    Args:
        paths: List of polygons (each polygon is list of points)
        z: Cutting depth in mm
        safe_z: Retract height in mm
        units: "mm" or "inch"
        feed: Feed rate (mm/min or in/min)
        spindle: Spindle RPM
        
    Returns:
        G-code string with linear moves only
    """
    u = "G21" if units.lower().startswith("mm") else "G20"
    lines = [
        "(N17 Polygon Offset)",
        u,
        "G90",  # Absolute positioning
        "G17",  # XY plane
        f"S{spindle} M3",  # Spindle on CW
        f"G0 Z{safe_z:.3f}"
    ]
    
    for poly in paths:
        if not poly:
            continue
        
        # Rapid to start
        x0, y0 = poly[0]
        lines += [
            f"G0 X{x0:.3f} Y{y0:.3f}",
            f"G1 Z{z:.3f} F{feed:.1f}"
        ]
        
        # Cut along polygon
        for x, y in poly[1:]:
            lines.append(f"G1 X{x:.3f} Y{y:.3f}")
        
        # Retract
        lines.append(f"G0 Z{safe_z:.3f}")
    
    lines += ["M5", "M30"]  # Spindle off, program end
    return "\n".join(lines)
