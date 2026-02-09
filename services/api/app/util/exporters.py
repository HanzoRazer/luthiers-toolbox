"""================================================================================"""
import math
import datetime
from typing import Dict, Any, List, Optional, Literal


# ============================================================================
# VALIDATION CONSTANTS (COORDINATE BOUNDS)
# ============================================================================

# Validation constants
MIN_COORDINATE_MM = -10000.0  # Minimum coordinate value (mm)
MAX_COORDINATE_MM = 10000.0   # Maximum coordinate value (mm)
MIN_ARC_RADIUS_MM = 0.1       # Minimum arc radius to prevent degenerate arcs


# ============================================================================
# SVG EXPORT (WEB PREVIEW & DOCUMENTATION)
# ============================================================================


def export_svg(
    geom: Dict[str, Any], 
    meta: str = ""
) -> str:
    """Export canonical geometry to SVG format with optional metadata."""
    paths = []
    for s in geom.get("paths", []):
        if s.get("type") == "line":
            # Validate line coordinates
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            if not all(MIN_COORDINATE_MM <= c <= MAX_COORDINATE_MM for c in [x1, y1, x2, y2]):
                raise ValueError(
                    f"Line coordinates out of range ({MIN_COORDINATE_MM} to {MAX_COORDINATE_MM}): "
                    f"({x1}, {y1}) to ({x2}, {y2})"
                )
            paths.append(f"M {x1} {y1} L {x2} {y2}")
            
        elif s.get("type") == "arc":
            # Validate arc parameters
            cx, cy, r = s["cx"], s["cy"], s["r"]
            if not all(MIN_COORDINATE_MM <= c <= MAX_COORDINATE_MM for c in [cx, cy]):
                raise ValueError(
                    f"Arc center out of range ({MIN_COORDINATE_MM} to {MAX_COORDINATE_MM}): "
                    f"({cx}, {cy})"
                )
            if abs(r) < MIN_ARC_RADIUS_MM:
                raise ValueError(
                    f"Arc radius too small (min {MIN_ARC_RADIUS_MM}mm): {abs(r)}mm"
                )
            
            # Compute arc endpoints from center, radius, and angles
            a0 = math.radians(s["start"])
            a1 = math.radians(s["end"])
            sx, sy = cx + r * math.cos(a0), cy + r * math.sin(a0)
            ex, ey = cx + r * math.cos(a1), cy + r * math.sin(a1)
            sweep = 1 if s.get("cw") else 0  # CW=1, CCW=0
            paths.append(f"M {sx} {sy} A {abs(r)} {abs(r)} 0 0 {sweep} {ex} {ey}")
            
    # Join paths or fallback to origin move
    d = " ".join(paths) or "M 0 0"
    
    # Add metadata comment if provided
    meta_comment = f"<!-- {meta} -->" if meta else ""
    
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2000 2000">'
        f'{meta_comment}'
        f'<path d="{d}" fill="none" stroke="black"/>'
        f'</svg>'
    )


# ============================================================================
# DXF R12 EXPORT (CAM SOFTWARE COMPATIBILITY)
# ============================================================================

def export_dxf(
    geom: Dict[str, Any], 
    meta: str = ""
) -> str:
    """Export canonical geometry to DXF R12 format with optional metadata."""
    out = ["0", "SECTION", "2", "ENTITIES"]
    
    for s in geom.get("paths", []):
        if s.get("type") == "line":
            # Validate line coordinates
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            if not all(MIN_COORDINATE_MM <= c <= MAX_COORDINATE_MM for c in [x1, y1, x2, y2]):
                raise ValueError(
                    f"Line coordinates out of range ({MIN_COORDINATE_MM} to {MAX_COORDINATE_MM}): "
                    f"({x1}, {y1}) to ({x2}, {y2})"
                )
            
            # DXF LINE entity (group codes: 0=type, 8=layer, 10/20=start, 11/21=end)
            out += [
                "0", "LINE",
                "8", "0",           # Layer 0 (default)
                "10", str(x1),      # Start X
                "20", str(y1),      # Start Y
                "11", str(x2),      # End X
                "21", str(y2)       # End Y
            ]
            
        elif s.get("type") == "arc":
            # Validate arc parameters
            cx, cy, r = s["cx"], s["cy"], s["r"]
            if not all(MIN_COORDINATE_MM <= c <= MAX_COORDINATE_MM for c in [cx, cy]):
                raise ValueError(
                    f"Arc center out of range ({MIN_COORDINATE_MM} to {MAX_COORDINATE_MM}): "
                    f"({cx}, {cy})"
                )
            if abs(r) < MIN_ARC_RADIUS_MM:
                raise ValueError(
                    f"Arc radius too small (min {MIN_ARC_RADIUS_MM}mm): {abs(r)}mm"
                )
            
            # DXF ARC entity (group codes: 0=type, 8=layer, 10/20=center, 40=radius, 50/51=angles)
            out += [
                "0", "ARC",
                "8", "0",                # Layer 0 (default)
                "10", str(cx),           # Center X
                "20", str(cy),           # Center Y
                "40", str(abs(r)),       # Radius (always positive)
                "50", str(s["start"]),   # Start angle (degrees)
                "51", str(s["end"])      # End angle (degrees)
            ]
    
    # Close DXF file structure
    out += ["0", "ENDSEC", "0", "EOF"]
    
    # Join with newlines (DXF requires one value per line)
    txt = "\n".join(out)
    
    # Prepend metadata as 999 comment if provided (per DXF spec)
    if meta:
        txt = "999\n" + meta + "\n" + txt
    
    return txt
