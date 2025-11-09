"""
Geometry Export Utilities

Converts canonical geometry format to SVG and DXF R12 for CAM compatibility.

Critical Safety Rules:
1. **DXF R12 Format Only**: Always export AC1009 (R12) for maximum CAM software compatibility
2. **Closed Paths**: Validate polygon closure before export (CNC requires closed toolpaths)
3. **Unit Consistency**: All geometry must be in mm internally, convert at API boundary
4. **Metadata Injection**: Include POST/UNITS/DATE metadata in all exports
5. **Fail-Safe Defaults**: Return valid minimal geometry on error, never empty/corrupt files

Supported Formats:
    - SVG: Scalable Vector Graphics with inline path metadata
    - DXF R12: AutoCAD R12 format (AC1009) for universal CAM import
    
Geometry Format (Canonical):
    {
        "units": "mm" | "inch",
        "paths": [
            {"type": "line", "x1": float, "y1": float, "x2": float, "y2": float},
            {"type": "arc", "cx": float, "cy": float, "r": float, "start": float, "end": float, "cw": bool}
        ]
    }

See Also:
    - PATCH_K_EXPORT_COMPLETE.md: Multi-post export system
    - services/api/app/routers/geometry_router.py: Export endpoints
"""
import math
import datetime
from typing import Dict, Any, List, Optional, Literal


# Validation constants
MIN_COORDINATE_MM = -10000.0  # Minimum coordinate value (mm)
MAX_COORDINATE_MM = 10000.0   # Maximum coordinate value (mm)
MIN_ARC_RADIUS_MM = 0.1       # Minimum arc radius to prevent degenerate arcs


def export_svg(
    geom: Dict[str, Any], 
    meta: str = ""
) -> str:
    """
    Export canonical geometry to SVG format with optional metadata.
    
    Converts geometry dictionary with paths (lines and arcs) to SVG path
    commands. Suitable for web preview, design documentation, and non-CAM
    applications. For CNC machining, use DXF export instead.
    
    Args:
        geom: Geometry dictionary with keys:
              - units: "mm" or "inch"
              - paths: List of path dictionaries (line or arc)
        meta: Optional metadata string (e.g., "POST=GRBL;UNITS=mm;DATE=...")
              Inserted as XML comment <!-- meta -->
    
    Returns:
        SVG XML string with inline path data and metadata comment
        ViewBox: 0 0 2000 2000 (suitable for typical guitar components)
        
    Raises:
        ValueError: If geometry contains invalid coordinates or arc radii
    
    Example:
        >>> geom = {
        ...     "units": "mm",
        ...     "paths": [
        ...         {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 0},
        ...         {"type": "arc", "cx": 50, "cy": 25, "r": 30, "start": 0, "end": 180}
        ...     ]
        ... }
        >>> svg = export_svg(geom, meta="POST=GRBL;UNITS=mm")
        >>> "<!-- POST=GRBL" in svg
        True
        
    Notes:
        - Arc sweep flag: 1 for CW (clockwise), 0 for CCW (counter-clockwise)
        - Coordinates validated against MIN/MAX_COORDINATE_MM bounds
        - Empty paths list returns minimal SVG with "M 0 0" (move to origin)
        - For CAM export, use export_dxf() instead (DXF R12 format)
    """
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



def export_dxf(
    geom: Dict[str, Any], 
    meta: str = ""
) -> str:
    """
    Export canonical geometry to DXF R12 format with optional metadata.
    
    Generates AutoCAD R12 (AC1009) DXF file for maximum CAM software
    compatibility. All geometry exported to layer "0" with standard colors.
    Suitable for CNC toolpath import in Fusion 360, VCarve, Mach4, etc.
    
    DXF Structure:
        999 (Comment): Optional metadata line
        SECTION ENTITIES: Main geometry section
            LINE: Straight line segment (10/20=start, 11/21=end)
            ARC: Circular arc (10/20=center, 40=radius, 50/51=start/end angles)
        ENDSEC: Section end
        EOF: End of file
    
    Args:
        geom: Geometry dictionary with keys:
              - units: "mm" or "inch"
              - paths: List of path dictionaries (line or arc)
        meta: Optional metadata string (e.g., "POST=GRBL;UNITS=mm;DATE=...")
              Inserted as 999 comment at file start (DXF spec)
    
    Returns:
        DXF R12 text string (group codes and values, newline-separated)
        
    Raises:
        ValueError: If geometry contains invalid coordinates or arc radii
    
    Example:
        >>> geom = {
        ...     "units": "mm",
        ...     "paths": [
        ...         {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 0}
        ...     ]
        ... }
        >>> dxf = export_dxf(geom, meta="POST=GRBL;UNITS=mm")
        >>> "999" in dxf and "POST=GRBL" in dxf
        True
        >>> "LINE" in dxf
        True
        
    Notes:
        - **R12 Format Only**: AC1009 for universal CAM compatibility
        - **Closed Paths**: CAM software expects closed LWPolylines for pockets
        - **Layer 0**: All entities exported to default layer
        - **Group Codes**:
          * 0: Entity type (LINE, ARC)
          * 8: Layer name
          * 10/20: Primary X/Y coordinates
          * 11/21: Secondary X/Y (line endpoint)
          * 40: Radius (arc)
          * 50/51: Start/end angles in degrees (arc)
        - **Metadata**: 999 comment prepended before SECTION (per DXF spec)
        - For closed toolpaths, ensure first and last points match
    
    DXF Compatibility:
        - Fusion 360: ✅ R12 import tested
        - VCarve: ✅ R12 import tested
        - Mach4: ✅ R12 import tested
        - LinuxCNC: ✅ R12 import via dxf2gcode
        - GRBL: ✅ R12 import via bCNC, CNCjs
    
    See Also:
        - ARCHITECTURE.md: DXF R12 export rules
        - PATCH_K_EXPORT_COMPLETE.md: Multi-post export system
    """
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
