"""
Geometry Import Router
======================

Handles geometry import from DXF/SVG/JSON and parity checking.

Endpoints:
- POST /import - Parse DXF/SVG/JSON to canonical format
- POST /parity - Validate design vs toolpath accuracy

CRITICAL SAFETY RULES:
1. File uploads MUST validate extension before parsing
2. Coordinates MUST be validated against safe bounds
3. Units MUST be explicitly converted (never assume)
"""

import math
import re
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request, UploadFile

from ..geometry_schemas import (
    GeometryIn,
    ParityRequest,
)

# Import canonical geometry functions - NO inline math in routers (Fortran Rule)
from ...geometry.arc_utils import tessellate_arc_radians, nearest_point_distance

router = APIRouter(tags=["geometry"])

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Maximum file upload size in bytes (10 MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Maximum number of segments per geometry (prevent memory issues)
MAX_SEGMENTS = 100000

# Maximum coordinate value (prevent overflow)
MAX_COORDINATE = 10000.0

# Supported file extensions for upload
SUPPORTED_EXTENSIONS = {".svg", ".dxf"}


# =============================================================================
# PARSER FUNCTIONS
# =============================================================================

def _svg_path_to_segments(svg_text: str) -> List[Dict[str, Any]]:
    """
    Parse SVG path data into canonical geometry segments.

    Supports subset of SVG path commands for CAM import:
    - M/m: MoveTo (absolute/relative)
    - L/l: LineTo (absolute/relative)
    - A/a: EllipticalArc (absolute/relative)
    - Z/z: ClosePath

    Args:
        svg_text: SVG path 'd' attribute string (e.g., "M0,0 L100,0 A50,50 0 0,1 100,100 Z")

    Returns:
        List of segment dicts with type="line" or type="arc"
        - Line: {"type":"line", "x1":float, "y1":float, "x2":float, "y2":float}
        - Arc: {"type":"arc", "cx":float, "cy":float, "r":float, "start":degrees, "end":degrees, "cw":bool}
    """
    tokens = re.findall(r"[MLAZmlaz]|-?\d*\.?\d+(?:e[-+]?\d+)?", svg_text)
    i = 0
    cur = (0.0, 0.0)
    start = None
    segs = []

    def num():
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t in ('M', 'm'):
            x = num()
            y = num()
            cur = (x, y) if t == 'M' else (cur[0] + x, cur[1] + y)
            start = cur
        elif t in ('L', 'l'):
            x = num()
            y = num()
            nxt = (x, y) if t == 'L' else (cur[0] + x, cur[1] + y)
            segs.append({"type": "line", "x1": cur[0], "y1": cur[1], "x2": nxt[0], "y2": nxt[1]})
            cur = nxt
        elif t in ('A', 'a'):
            # A rx ry rot laf sweep x y
            rx = num()
            ry = num()
            _rot = num()
            _laf = num()
            sw = num()
            x = num()
            y = num()
            end = (x, y) if t == 'A' else (cur[0] + x, cur[1] + y)
            r = (rx + ry) / 2.0 if (rx > 0 and ry > 0) else max(rx, ry)
            sx, sy = cur
            ex, ey = end
            dx, dy = ex - sx, ey - sy
            d = (dx * dx + dy * dy) ** 0.5
            if d < 1e-9:
                cur = end
                continue
            h = max(r * r - (d * d) / 4.0, 0.0) ** 0.5
            mx, my = (sx + ex) / 2.0, (sy + ey) / 2.0
            ux, uy = (-dy / d, dx / d)
            cx, cy = (mx + ux * h, my + uy * h) if sw > 0.5 else (mx - ux * h, my - uy * h)
            a0 = math.degrees(math.atan2(sy - cy, sx - cx))
            a1 = math.degrees(math.atan2(ey - cy, ex - cx))
            segs.append({"type": "arc", "cx": cx, "cy": cy, "r": abs(r), "start": a0, "end": a1, "cw": sw > 0.5})
            cur = end
        elif t in ('Z', 'z'):
            if start and (abs(cur[0] - start[0]) > 1e-9 or abs(cur[1] - start[1]) > 1e-9):
                segs.append({"type": "line", "x1": cur[0], "y1": cur[1], "x2": start[0], "y2": start[1]})
            cur = start if start else cur
    return segs


def _dxf_to_segments(dxf_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Parse ASCII DXF file into canonical geometry segments.

    Supports subset of DXF entities for CAM import:
    - LINE: Straight line segment
    - ARC: Circular arc

    Args:
        dxf_bytes: Raw DXF file bytes (ASCII or UTF-8 encoded)

    Returns:
        List of segment dicts with type="line" or type="arc"
    """
    txt = dxf_bytes.decode(errors="ignore").splitlines()
    i = 0
    ents = []
    mode = None
    cur = {}

    def read_pair():
        nonlocal i
        if i + 1 >= len(txt):
            return None, None
        code = txt[i].strip()
        value = txt[i + 1].strip()
        i += 2
        return code, value

    while i < len(txt):
        code, val = read_pair()
        if code is None:
            break
        if code == '0':
            if mode == 'LINE' and cur:
                ents.append({
                    'type': 'line',
                    'x1': cur.get('10', 0.0),
                    'y1': cur.get('20', 0.0),
                    'x2': cur.get('11', 0.0),
                    'y2': cur.get('21', 0.0)
                })
            if mode == 'ARC' and cur:
                cx = float(cur.get('10', 0.0))
                cy = float(cur.get('20', 0.0))
                r = float(cur.get('40', 0.0))
                sa = float(cur.get('50', 0.0))
                ea = float(cur.get('51', 0.0))
                ents.append({
                    'type': 'arc',
                    'cx': cx,
                    'cy': cy,
                    'r': abs(r),
                    'start': sa,
                    'end': ea,
                    'cw': False
                })
            mode = val
            cur = {}
        else:
            if mode in ('LINE', 'ARC'):
                try:
                    cur[code] = float(val)
                except (ValueError, TypeError):
                    cur[code] = val
    return ents


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/import")
async def import_geometry(request: Request):
    """
    Import geometry from DXF/SVG file or JSON body into canonical format.

    Accepts two input modes:
    1. File upload: multipart/form-data with .dxf or .svg file
    2. JSON body: GeometryIn model with units and paths (send as top-level JSON)

    Returns:
        GeometryIn dict with:
        - units: "mm" or "inch"
        - paths: List of Segment dicts (type="line" or type="arc")

    Raises:
        HTTPException 400: Neither file nor geometry provided
        HTTPException 415: Unsupported file format (not .dxf or .svg)
    """
    content_type = request.headers.get("content-type", "")

    # Handle JSON body
    if "application/json" in content_type:
        body = await request.json()
        geometry_data = body.get("geometry") or body  # Support both nested and flat

        if not geometry_data or not geometry_data.get("paths"):
            raise HTTPException(400, "JSON body must contain geometry with paths")

        try:
            geometry = GeometryIn(**geometry_data)
            return geometry.dict()
        except HTTPException:  # WP-1: pass through HTTPException
            raise
        except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
            raise HTTPException(400, f"Invalid geometry format: {str(e)}")

    # Handle file upload
    elif "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")

        if not file or not isinstance(file, UploadFile):
            raise HTTPException(400, "Provide either JSON geometry or a file (.svg/.dxf)")

        data = await file.read()

        # Validate file size
        if len(data) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(400, f"File exceeds {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f}MB limit")

        name = (file.filename or "").lower()
        if name.endswith(".svg"):
            segs = _svg_path_to_segments(data.decode(errors='ignore'))
            # Validate segment count
            if len(segs) > MAX_SEGMENTS:
                raise HTTPException(400, f"Geometry exceeds {MAX_SEGMENTS} segment limit")
            return {"units": "mm", "paths": segs}
        if name.endswith(".dxf"):
            segs = _dxf_to_segments(data)
            # Validate segment count
            if len(segs) > MAX_SEGMENTS:
                raise HTTPException(400, f"Geometry exceeds {MAX_SEGMENTS} segment limit")
            return {"units": "mm", "paths": segs}
        raise HTTPException(415, "Only .svg or .dxf supported for file upload")

    else:
        raise HTTPException(400, "Provide either JSON geometry or a file (.svg/.dxf)")


@router.post("/parity")
def parity(body: ParityRequest) -> Dict[str, Any]:
    """
    Validate toolpath fidelity against design geometry (parity checking).

    Compares design geometry (CAD) with generated G-code toolpath (CAM) to ensure
    machining will match intended design within specified tolerance.

    Args:
        body: ParityRequest containing:
            - geometry: Design geometry in canonical format
            - gcode: Generated G-code toolpath
            - tolerance_mm: Maximum acceptable deviation (default 0.05mm)

    Returns:
        dict with:
        - rms_error_mm: Root mean square error (accuracy metric)
        - max_error_mm: Maximum point-to-point error (worst case)
        - tolerance_mm: Input tolerance threshold
        - pass: bool (True if max_error <= tolerance)
    """
    from ..sim_validate import simulate

    # Sample geometry to points - Arc tessellation delegated to geometry/arc_utils.py
    gpts = []
    for s in body.geometry.paths:
        if s.type == "line" and s.x1 is not None:
            gpts.append((s.x1, s.y1))
            gpts.append((s.x2, s.y2))
        elif s.type == "arc" and None not in (s.cx, s.cy, s.r, s.start, s.end):
            arc_pts = tessellate_arc_radians(
                s.cx, s.cy, s.r,
                math.radians(s.start), math.radians(s.end),
                clockwise=bool(s.cw), steps=64
            )
            gpts.extend(arc_pts)

    # Sample toolpath to points
    sim = simulate(body.gcode)
    mpts = []
    last = {'x': 0.0, 'y': 0.0, 'z': 5.0}
    for m in sim['moves']:
        if m['code'] in ('G0', 'G1') and 'x' in m and 'y' in m:
            mpts.append((last['x'], last['y']))
            mpts.append((m['x'], m['y']))
            last = {'x': m.get('x', last['x']), 'y': m.get('y', last['y']), 'z': m.get('z', last['z'])}
        elif m['code'] in ('G2', 'G3') and all(k in m for k in ('x', 'y', 'i', 'j')):
            sx, sy = last['x'], last['y']
            ex, ey = m['x'], m['y']
            cx, cy = sx + m['i'], sy + m['j']
            r = math.hypot(sx - cx, sy - cy)
            a0 = math.atan2(sy - cy, sx - cx)
            a1 = math.atan2(ey - cy, ex - cx)
            cw = m['code'] == 'G2'
            arc_pts = tessellate_arc_radians(cx, cy, r, a0, a1, clockwise=cw, steps=64)
            mpts.extend(arc_pts)
            last = {'x': ex, 'y': ey, 'z': m.get('z', last['z'])}

    # Calculate errors using canonical nearest_point_distance
    errs = [nearest_point_distance(p, mpts) for p in gpts] if (gpts and mpts) else [999.0]
    rms = (sum(e * e for e in errs) / len(errs)) ** 0.5
    mx = max(errs) if errs else 999.0
    return {
        "rms_error_mm": round(rms, 4),
        "max_error_mm": round(mx, 4),
        "tolerance_mm": body.tolerance_mm,
        "pass": mx <= body.tolerance_mm
    }
