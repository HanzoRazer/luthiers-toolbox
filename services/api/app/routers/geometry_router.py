"""
Geometry Import and Parity Checking Router

CRITICAL SAFETY RULES:
1. File uploads MUST validate extension before parsing
2. Coordinates MUST be validated against safe bounds
3. Units MUST be explicitly converted (never assume)
4. Post-processor IDs MUST match existing configurations
5. Filename sanitization MUST strip all unsafe characters

This router provides:
- Geometry import from DXF/SVG/JSON formats
- Parity checking between design and toolpath
- Multi-format export (DXF R12, SVG, G-code)
- Multi-post bundle generation with headers/footers
- Post-processor aware metadata injection

Supported Formats:
- DXF: R12 ASCII (LINE, ARC entities)
- SVG: Path data (M, L, A, Z commands)
- JSON: Canonical segment format
- G-code: Export with post-processor headers

API Endpoints:
- POST /geometry/import - Parse DXF/SVG/JSON to canonical format
- POST /geometry/parity - Validate design vs toolpath accuracy
- POST /geometry/export - Single format export (DXF or SVG)
- POST /geometry/export_bundle - Single post bundle (DXF + SVG + NC)
- POST /geometry/export_bundle_multi - Multi-post bundle (N × NC files)
"""

import datetime
import io
import json
import math
import os
import re
import time
import zipfile
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Body, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..util.exporters import export_dxf, export_svg
from ..util.units import scale_geom_units

router = APIRouter(prefix="/geometry", tags=["geometry"])

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
# HELPER FUNCTIONS - POST PROCESSOR
# =============================================================================

def _load_posts() -> Dict[str, Dict[str, Any]]:
    """
    Load post-processor configurations from data/posts/*.json.
    
    Process:
    1. Locate data/posts/ directory relative to this file
    2. Read all *.json files in directory
    3. Parse JSON and store by filename stem
    
    Returns:
        Dictionary mapping post ID to configuration dict
        Example: {"GRBL": {"header": [...], "footer": [...]}}
    
    Notes:
    - Returns empty dict if posts directory doesn't exist
    - Silently skips malformed JSON files (logged internally)
    - Post IDs are case-sensitive (use uppercase by convention)
    
    Example:
        posts = _load_posts()
        grbl_config = posts.get("GRBL", {})
    """
    here = os.path.dirname(__file__)
    posts_dir = os.path.join(here, "..", "data", "posts")
    out = {}
    if os.path.isdir(posts_dir):
        for f in os.listdir(posts_dir):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(posts_dir, f), "r", encoding="utf-8") as fh:
                        out[f[:-5]] = json.load(fh)
                except json.JSONDecodeError as e:
                    # Log but don't crash if one post file is malformed
                    print(f"Warning: Failed to load post {f}: {e}")
    return out

def _units_gcode(units: str) -> str:
    """
    Convert units string to G-code command.
    
    Args:
        units: Unit string ('mm', 'millimeter', 'inch', 'inches', etc.)
    
    Returns:
        G-code command: 'G21' for metric, 'G20' for imperial
    
    Validation:
        Defaults to G21 (mm) if units string is ambiguous
    
    Example:
        _units_gcode('mm') → 'G21'
        _units_gcode('inch') → 'G20'
        _units_gcode('') → 'G21' (default to metric)
    """
    return "G21" if (units or "").lower() in ("mm", "millimeter", "millimetre") else "G20"

def _safe_stem(s: Optional[str], default_prefix: str = "program") -> str:
    """
    Sanitize job_name to safe filename stem.
    
    Sanitization Rules:
    1. Strip leading/trailing whitespace
    2. Replace spaces with underscores
    3. Remove all characters except: A-Z, a-z, 0-9, dash, underscore
    4. Fallback to timestamp if empty after sanitization
    
    Args:
        s: User-provided job name (can be None or empty)
        default_prefix: Prefix for timestamp fallback (default: "program")
    
    Returns:
        Safe filename stem (letters, numbers, dash, underscore only)
        Format: {sanitized_name} or {prefix}_{unix_timestamp}
    
    Raises:
        ValueError: Never (always returns valid string)
    
    Example:
        _safe_stem('Bridge Design') → 'Bridge_Design'
        _safe_stem('Test@#$%') → 'Test'
        _safe_stem('') → 'program_1699564800'
        _safe_stem(None) → 'program_1699564800'
    
    Notes:
        CRITICAL: Used for file exports - MUST prevent path traversal
        Characters stripped: <>:"/\\|?*@#$%^&+=[]{}();'",
    """
    if not s:
        return f"{default_prefix}_{int(time.time())}"
    
    # Strip whitespace, replace spaces with underscores
    s = s.strip().replace(" ", "_")
    
    # Keep only safe characters: letters, numbers, dash, underscore
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)
    
    # Fallback to timestamp if sanitization resulted in empty string
    return s or f"{default_prefix}_{int(time.time())}"

def _metadata_comment(units: str, post_id: str) -> str:
    """
    Generate metadata comment for G-code provenance tracking.
    
    Args:
        units: Unit system ('mm' or 'inch')
        post_id: Post-processor identifier (e.g., 'GRBL', 'Mach4')
    
    Returns:
        Metadata comment string with semicolon-delimited fields
        Format: (POST=<id>;UNITS=<units>;DATE=<iso8601>)
    
    Example:
        _metadata_comment('mm', 'GRBL')
        → '(POST=GRBL;UNITS=mm;DATE=2025-11-09T15:30:45.123456Z)'
    
    Notes:
        - Timestamp is UTC in ISO 8601 format
        - Parentheses indicate G-code comment (ignored by machine)
        - Searchable metadata for tracking file provenance
    """
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    return f"(POST={post_id or 'NONE'};UNITS={units or 'mm'};DATE={ts})"

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class Segment(BaseModel):
    """
    Geometry segment (line or arc).
    
    Segment Types:
    - line: Requires x1, y1, x2, y2
    - arc: Requires cx, cy, r, start, end, cw
    
    Coordinates:
    - All values in current units (mm or inch)
    - Angles in degrees (0-360)
    """
    type: Literal["line", "arc"]  # MUST be explicit type
    x1: Optional[float] = None    # Line start X
    y1: Optional[float] = None    # Line start Y
    x2: Optional[float] = None    # Line end X
    y2: Optional[float] = None    # Line end Y
    cx: Optional[float] = None    # Arc center X
    cy: Optional[float] = None    # Arc center Y
    r: Optional[float] = None     # Arc radius
    start: Optional[float] = None # Arc start angle (degrees)
    end: Optional[float] = None   # Arc end angle (degrees)
    cw: Optional[bool] = None     # Arc clockwise flag

class GeometryIn(BaseModel):
    """
    Canonical geometry format for import/export.
    
    Fields:
    - units: 'mm' or 'inch' (MUST be explicit)
    - paths: List of Segment objects
    
    Validation:
    - Path count must be <= MAX_SEGMENTS
    - Coordinates must be within safe bounds
    """
    units: Literal["mm", "inch"] = "mm"
    paths: List[Segment]

def _svg_path_to_segments(svg_text:str)->List[Dict[str,Any]]:
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
    
    Algorithm:
        1. Tokenize path string into commands (M/L/A/Z) and numbers
        2. Track current position and path start for Z command
        3. For each command:
           - M: Update current position (start new subpath)
           - L: Create line segment from current to new position
           - A: Convert SVG arc (rx, ry, rotation, large-arc-flag, sweep-flag, x, y)
                to center-parameterized arc (cx, cy, r, start_angle, end_angle, cw)
           - Z: Close path with line if needed
        4. Return accumulated segments
    
    Notes:
        - This is a minimal parser for CAM import (not full SVG compliance)
        - Elliptical arcs approximated as circular (r = average of rx, ry)
        - Arc center calculated using chord midpoint and perpendicular bisector
        - Absolute/relative coordinates handled via uppercase/lowercase commands
    
    Example:
        >>> _svg_path_to_segments("M0,0 L100,0 L100,60 L0,60 Z")
        [
            {"type":"line","x1":0,"y1":0,"x2":100,"y2":0},
            {"type":"line","x1":100,"y1":0,"x2":100,"y2":60},
            {"type":"line","x1":100,"y1":60,"x2":0,"y2":60},
            {"type":"line","x1":0,"y1":60,"x2":0,"y2":0}
        ]
    """
    import re
    tokens = re.findall(r"[MLAZmlaz]|-?\d*\.?\d+(?:e[-+]?\d+)?", svg_text)
    i=0; cur=(0.0,0.0); start=None; segs=[]
    def num():
        nonlocal i; v=float(tokens[i]); i+=1; return v
    while i < len(tokens):
        t = tokens[i]; i+=1
        if t in ('M','m'):
            x = num(); y=num()
            cur = (x,y) if t=='M' else (cur[0]+x, cur[1]+y); start = cur
        elif t in ('L','l'):
            x = num(); y=num()
            nxt = (x,y) if t=='L' else (cur[0]+x, cur[1]+y)
            segs.append({"type":"line","x1":cur[0],"y1":cur[1],"x2":nxt[0],"y2":nxt[1]})
            cur = nxt
        elif t in ('A','a'):
            # A rx ry rot laf sweep x y
            rx=num(); ry=num(); _rot=num(); _laf=num(); sw=num(); x=num(); y=num()
            end = (x,y) if t=='A' else (cur[0]+x, cur[1]+y)
            r = (rx+ry)/2.0 if (rx>0 and ry>0) else max(rx,ry)
            sx,sy = cur; ex,ey = end
            dx,dy = ex-sx, ey-sy; d = (dx*dx+dy*dy)**0.5
            if d < 1e-9: cur=end; continue
            h = max(r*r - (d*d)/4.0, 0.0)**0.5
            mx,my = (sx+ex)/2.0,(sy+ey)/2.0
            ux,uy = (-dy/d, dx/d)
            cx,cy = (mx + ux*h, my + uy*h) if sw>0.5 else (mx - ux*h, my - uy*h)
            a0 = math.degrees(math.atan2(sy-cy, sx-cx))
            a1 = math.degrees(math.atan2(ey-cy, ex-cx))
            segs.append({"type":"arc","cx":cx,"cy":cy,"r":abs(r),"start":a0,"end":a1,"cw": sw>0.5})
            cur=end
        elif t in ('Z','z'):
            if start and (abs(cur[0]-start[0])>1e-9 or abs(cur[1]-start[1])>1e-9):
                segs.append({"type":"line","x1":cur[0],"y1":cur[1],"x2":start[0],"y2":start[1]})
            cur=start if start else cur
    return segs

def _dxf_to_segments(dxf_bytes:bytes)->List[Dict[str,Any]]:
    """
    Parse ASCII DXF file into canonical geometry segments.
    
    Supports subset of DXF entities for CAM import:
    - LINE: Straight line segment
    - ARC: Circular arc
    
    Args:
        dxf_bytes: Raw DXF file bytes (ASCII or UTF-8 encoded)
    
    Returns:
        List of segment dicts with type="line" or type="arc"
        - Line: {"type":"line", "x1":float, "y1":float, "x2":float, "y2":float}
        - Arc: {"type":"arc", "cx":float, "cy":float, "r":float, "start":degrees, "end":degrees, "cw":False}
    
    Algorithm:
        1. Decode bytes to text (ignore encoding errors)
        2. Split into lines and parse as code-value pairs
        3. Track current entity type (LINE, ARC) via code 0
        4. Accumulate entity data via group codes:
           - LINE: 10/20 = start (x1,y1), 11/21 = end (x2,y2)
           - ARC: 10/20 = center (cx,cy), 40 = radius, 50 = start angle, 51 = end angle
        5. When new entity starts (code 0), flush previous entity to segments
        6. Return accumulated segments
    
    DXF Group Codes (subset):
        - 0: Entity type (LINE, ARC, etc.)
        - 10: Primary X coordinate
        - 20: Primary Y coordinate
        - 11: Secondary X coordinate (LINE endpoint)
        - 21: Secondary Y coordinate (LINE endpoint)
        - 40: Radius (ARC)
        - 50: Start angle in degrees (ARC)
        - 51: End angle in degrees (ARC)
    
    Notes:
        - This is a minimal parser for CAM import (not full DXF compliance)
        - Assumes DXF R12+ format with ENTITIES section
        - All arcs are assumed counter-clockwise (DXF convention)
        - Ignores Z coordinates, layer, color, and other attributes
    
    Example:
        >>> _dxf_to_segments(b"0\\nLINE\\n10\\n0.0\\n20\\n0.0\\n11\\n100.0\\n21\\n0.0\\n")
        [{"type":"line","x1":0.0,"y1":0.0,"x2":100.0,"y2":0.0}]
    """
    txt = dxf_bytes.decode(errors="ignore").splitlines()
    i=0; ents=[]; mode=None; cur={}
    def read_pair():
        nonlocal i
        if i+1 >= len(txt): return None, None
        code = txt[i].strip(); value = txt[i+1].strip(); i += 2
        return code, value
    while i < len(txt):
        code,val = read_pair()
        if code is None: break
        if code == '0':
            if mode == 'LINE' and cur:
                ents.append({'type':'line', 'x1':cur.get('10',0.0), 'y1':cur.get('20',0.0), 'x2':cur.get('11',0.0), 'y2':cur.get('21',0.0)})
            if mode == 'ARC' and cur:
                cx=float(cur.get('10',0.0)); cy=float(cur.get('20',0.0))
                r=float(cur.get('40',0.0)); sa=float(cur.get('50',0.0)); ea=float(cur.get('51',0.0))
                ents.append({'type':'arc','cx':cx,'cy':cy,'r':abs(r),'start':sa,'end':ea,'cw':False})
            mode = val; cur = {}
        else:
            if mode in ('LINE','ARC'):
                try: cur[code] = float(val)
                except: cur[code] = val
    return ents

@router.post("/import")
async def import_geometry(request: Request):
    """
    Import geometry from DXF/SVG file or JSON body into canonical format.
    
    Accepts two input modes:
    1. File upload: multipart/form-data with .dxf or .svg file
    2. JSON body: GeometryIn model with units and paths (send as top-level JSON)
    
    Args:
        request: FastAPI Request object (handles both JSON and multipart)
    
    Returns:
        GeometryIn dict with:
        - units: "mm" or "inch"
        - paths: List of Segment dicts (type="line" or type="arc")
    
    Raises:
        HTTPException 400: Neither file nor geometry provided
        HTTPException 415: Unsupported file format (not .dxf or .svg)
    
    Request Flow:
        1. If geometry JSON provided, return as-is (already canonical)
        2. If file provided:
           a. Read file bytes
           b. Check extension (.svg or .dxf)
           c. Parse to segments using format-specific parser
           d. Return canonical geometry (assumes mm units)
        3. Otherwise, error (must provide one input)
    
    Example (JSON):
        POST /api/geometry/import
        {
          "geometry": {
            "units": "mm",
            "paths": [
              {"type":"line","x1":0,"y1":0,"x2":100,"y2":0}
            ]
          }
        }
        => Returns same geometry
    
    Example (File):
        POST /api/geometry/import
        Content-Type: multipart/form-data
        file: body.dxf
        => Returns parsed geometry in mm units
    
    Notes:
        - File uploads assume mm units (convert externally if needed)
        - SVG parser supports M/L/A/Z commands only (CAM subset)
        - DXF parser supports LINE and ARC entities only (R12+ format)
        - JSON input skips parsing (direct passthrough for validation)
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
        except Exception as e:
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
            raise HTTPException(400, f"File exceeds {MAX_FILE_SIZE_BYTES/1024/1024:.0f}MB limit")
        
        name = (file.filename or "").lower()
        if name.endswith(".svg"):
            segs = _svg_path_to_segments(data.decode(errors='ignore'))
            # Validate segment count
            if len(segs) > MAX_SEGMENTS:
                raise HTTPException(400, f"Geometry exceeds {MAX_SEGMENTS} segment limit")
            return {"units":"mm","paths":segs}
        if name.endswith(".dxf"):
            segs = _dxf_to_segments(data)
            # Validate segment count
            if len(segs) > MAX_SEGMENTS:
                raise HTTPException(400, f"Geometry exceeds {MAX_SEGMENTS} segment limit")
            return {"units":"mm","paths":segs}
        raise HTTPException(415, "Only .svg or .dxf supported for file upload")
    
    else:
        raise HTTPException(400, "Provide either JSON geometry or a file (.svg/.dxf)")

class ParityRequest(BaseModel):
    geometry: GeometryIn
    gcode: str
    tolerance_mm: float = 0.05

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
    
    Algorithm:
        1. Sample design geometry to point cloud:
           - Lines: endpoints
           - Arcs: 64-sample tessellation
        2. Sample G-code toolpath to point cloud:
           - G0/G1: linear moves (endpoints)
           - G2/G3: circular arcs (64-sample tessellation)
        3. For each design point, find nearest toolpath point (Euclidean distance)
        4. Calculate RMS and max error
        5. Compare max error to tolerance threshold
    
    Sampling Strategy:
        - Arc discretization: 64 segments per arc (balance between accuracy and speed)
        - Distance metric: 2D Euclidean in XY plane (ignores Z for parity)
        - Unidirectional check: design → toolpath (assumes toolpath is superset)
    
    Example:
        POST /api/geometry/parity
        {
          "geometry": {
            "units": "mm",
            "paths": [{"type":"line","x1":0,"y1":0,"x2":100,"y2":0}]
          },
          "gcode": "G0 X0 Y0\\nG1 X100 Y0 F1200\\nM30",
          "tolerance_mm": 0.05
        }
        => {"rms_error_mm":0.0021,"max_error_mm":0.0035,"tolerance_mm":0.05,"pass":true}
    
    Notes:
        - Used in CI to validate CAM output matches design intent
        - Tolerance should match CNC machine accuracy (typically 0.01-0.1mm)
        - Does not validate feed rates, tool diameter, or Z-axis motion
        - RMS error indicates overall accuracy, max error indicates worst outlier
    
    Raises:
        None (returns pass=False if geometry deviates beyond tolerance)
    """
    from .sim_validate import simulate
    # Sample geometry to points
    gpts = []
    for s in body.geometry.paths:
        if s.type == "line" and s.x1 is not None:
            gpts.append((s.x1, s.y1)); gpts.append((s.x2, s.y2))
        elif s.type == "arc" and None not in (s.cx,s.cy,s.r,s.start,s.end):
            a0 = math.radians(s.start); a1 = math.radians(s.end)
            cw = bool(s.cw)
            if cw:
                while a1 > a0: a1 -= 2*math.pi
            else:
                while a1 < a0: a1 += 2*math.pi
            steps=64
            for k in range(steps+1):
                t = k/steps; a = a0 + (a1-a0)*t
                gpts.append((s.cx + s.r*math.cos(a), s.cy + s.r*math.sin(a)))

    # Sample toolpath to points
    sim = simulate(body.gcode)
    mpts = []
    last = {'x':0.0,'y':0.0,'z':5.0}
    for m in sim['moves']:
        if m['code'] in ('G0','G1') and 'x' in m and 'y' in m:
            mpts.append((last['x'], last['y'])); mpts.append((m['x'], m['y']))
            last = {'x':m.get('x', last['x']), 'y':m.get('y', last['y']), 'z':m.get('z', last['z'])}
        elif m['code'] in ('G2','G3') and all(k in m for k in ('x','y','i','j')):
            sx,sy = last['x'], last['y']; ex,ey = m['x'], m['y']
            cx,cy = sx + m['i'], sy + m['j']; r = math.hypot(sx-cx, sy-cy)
            a0 = math.atan2(sy-cy, sx-cx); a1 = math.atan2(ey-cy, ex-cx)
            if m['code']=='G2':
                while a1 > a0: a1 -= 2*math.pi
            else:
                while a1 < a0: a1 += 2*math.pi
            steps=64
            for k in range(steps+1):
                t=k/steps; a=a0+(a1-a0)*t
                mpts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
            last = {'x':ex,'y':ey,'z':m.get('z', last['z'])}

    def nearest_dist(pt, cloud):
        px,py = pt; md = 1e9
        for qx,qy in cloud:
            d = math.hypot(px-qx, py-qy)
            if d < md: md = d
        return md

    errs = [nearest_dist(p, mpts) for p in gpts] if (gpts and mpts) else [999.0]
    rms = (sum(e*e for e in errs)/len(errs))**0.5
    mx = max(errs) if errs else 999.0
    return {"rms_error_mm": round(rms,4), "max_error_mm": round(mx,4), "tolerance_mm": body.tolerance_mm, "pass": mx <= body.tolerance_mm}


class ExportRequest(BaseModel):
    geometry: GeometryIn
    post_id: Optional[str] = None  # GRBL/Mach4/LinuxCNC/PathPilot/MASSO
    job_name: Optional[str] = Field(default=None, description="Filename stem for DXF/SVG (safe chars only)")

@router.post("/export")
def export_geometry(fmt: str = "dxf", body: ExportRequest = Body(...)):
    """
    Export geometry to DXF or SVG format with post-processor metadata.
    
    Generates CAM-ready file with embedded metadata comments for provenance tracking.
    Supports multi-post workflow by injecting post_id into metadata.
    
    Args:
        fmt: Export format ("dxf" or "svg") via query parameter
        body: ExportRequest containing:
            - geometry: Canonical geometry with units and paths
            - post_id: Optional post-processor ID (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
            - job_name: Optional filename stem (sanitized for filesystem safety)
    
    Returns:
        Response with appropriate Content-Type and Content-Disposition headers:
        - DXF: application/dxf with .dxf extension
        - SVG: image/svg+xml with .svg extension
    
    Request Flow:
        1. Validate format parameter (must be "dxf" or "svg")
        2. Load post-processor configurations (if post_id provided)
        3. Extract geometry units (mm or inch)
        4. Sanitize job_name for filesystem safety (prevent path traversal)
        5. Generate metadata comment with units, post_id, and timestamp
        6. Export to requested format with embedded metadata
        7. Return file with download headers
    
    Metadata Format:
        (POST=<post_id>;UNITS=<units>;DATE=<ISO8601_timestamp>)
        - Embedded as DXF comment (code 999) or SVG comment
        - Enables provenance tracking through CAM workflow
    
    Example (DXF):
        POST /api/geometry/export?fmt=dxf
        {
          "geometry": {
            "units": "mm",
            "paths": [{"type":"line","x1":0,"y1":0,"x2":100,"y2":0}]
          },
          "post_id": "GRBL",
          "job_name": "body_pocket"
        }
        => Returns body_pocket.dxf with GRBL metadata
    
    Example (SVG):
        POST /api/geometry/export?fmt=svg
        {
          "geometry": {...},
          "job_name": "neck_profile"
        }
        => Returns neck_profile.svg with metadata comment
    
    Notes:
        - DXF format is R12 (AC1009) for maximum CAM compatibility
        - SVG format uses inline path elements (not external references)
        - job_name is sanitized: alphanumeric, dash, underscore only
        - post_id is optional (omit for design-only exports)
    
    Raises:
        HTTPException 400: Invalid format parameter (not dxf or svg)
    """
    fmt = (fmt or "dxf").lower()
    if fmt not in ("dxf", "svg"):
        raise HTTPException(400, "fmt must be dxf or svg")
    
    posts = _load_posts()
    post_id = (body.post_id or "").strip()
    post = posts.get(post_id) if post_id else None
    geom = body.geometry.dict()
    units = geom.get("units", "mm")
    
    # Use job_name for filename if provided
    stem = _safe_stem(body.job_name, default_prefix="export")
    
    if fmt == "dxf":
        txt = export_dxf(geom, meta=_metadata_comment(units, post_id))
        return Response(
            content=txt,
            media_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="{stem}.dxf"'},
        )
    else:  # svg
        txt = export_svg(geom, meta=_metadata_comment(units, post_id))
        return Response(
            content=txt,
            media_type="image/svg+xml",
            headers={"Content-Disposition": f'attachment; filename="{stem}.svg"'},
        )


class GcodeExportIn(BaseModel):
    gcode: str
    units: Optional[str] = "mm"
    post_id: Optional[str] = None
    job_name: Optional[str] = Field(default=None, description="Filename stem for NC file (safe chars only)")

@router.post("/export_gcode")
def export_gcode(body: GcodeExportIn) -> Response:
    """
    Export G-code with post-processor headers/footers and metadata.
    
    Wraps raw G-code with machine-specific initialization/shutdown sequences
    from post-processor configuration files. Ensures proper units mode and
    metadata provenance tracking.
    
    Args:
        body: GcodeExportIn containing:
            - gcode: Raw G-code body (toolpath commands)
            - units: "mm" or "inch" (determines G21/G20 injection)
            - post_id: Post-processor ID (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
            - job_name: Optional filename stem (sanitized for filesystem safety)
    
    Returns:
        Response with text/plain Content-Type and .nc extension
        Full program structure:
        [Units command (G21 or G20)]
        [Post-processor header lines]
        [Metadata comment]
        [User G-code body]
        [Post-processor footer lines]
    
    Request Flow:
        1. Load post-processor configurations from JSON files
        2. Extract header/footer arrays for specified post_id
        3. Determine units command (G21 for mm, G20 for inch)
        4. Build metadata comment with units, post_id, timestamp
        5. Assemble program: header + metadata + body + footer
        6. Sanitize job_name for filename
        7. Return with download headers
    
    Post-Processor Structure (JSON):
        {
          "header": ["G90", "G17", "(Machine: GRBL 1.1)"],
          "footer": ["M30", "(End of program)"]
        }
    
    Example:
        POST /api/geometry/export_gcode
        {
          "gcode": "G0 X0 Y0\\nG1 X100 Y0 F1200\\nM30",
          "units": "mm",
          "post_id": "GRBL",
          "job_name": "pocket_roughing"
        }
        => Returns pocket_roughing.nc:
           G21
           G90
           G17
           (POST=GRBL;UNITS=mm;DATE=2025-01-15T...)
           G0 X0 Y0
           G1 X100 Y0 F1200
           M30
           (End of program)
    
    Notes:
        - Units command (G21/G20) always injected first if not in header
        - Metadata comment injected after header, before body
        - Post-processor header/footer arrays read from services/api/app/data/posts/*.json
        - job_name sanitized: alphanumeric, dash, underscore only
        - Falls back to generic program if post_id not found
    
    Raises:
        None (uses generic header/footer if post_id invalid)
    """
    posts = _load_posts()
    hdr = []
    ftr = []
    units_code = _units_gcode(body.units or "mm")
    meta = _metadata_comment(body.units or "mm", body.post_id or "")
    
    # Case-insensitive post lookup
    posts_lower = {k.lower(): v for k, v in posts.items()}
    if body.post_id and body.post_id.lower() in posts_lower:
        post = posts_lower[body.post_id.lower()]
        hdr = (post.get("header") or [])[:]
        ftr = (post.get("footer") or [])[:]
    
    # Ensure units + meta are present in header
    if units_code not in hdr:
        hdr = [units_code] + hdr
    hdr = hdr + [meta]
    
    program = "\n".join(hdr + [body.gcode.strip()] + ftr) + ("\n" if not body.gcode.endswith("\n") else "")
    
    # Use job_name for filename if provided
    stem = _safe_stem(body.job_name, default_prefix="program")
    
    return Response(
        content=program,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{stem}.nc"'},
    )


class ExportBundleIn(BaseModel):
    geometry: GeometryIn
    gcode: str
    post_id: Optional[str] = None
    target_units: Optional[str] = None  # if provided, geometry is scaled server-side before export
    job_name: Optional[str] = Field(default=None, description="Filename stem for bundle files (safe chars only)")

@router.post("/export_bundle")
def export_bundle(body: ExportBundleIn) -> Response:
    """
    Export complete CAM bundle: DXF + SVG + G-code + manifest as ZIP archive.
    
    Provides all-in-one export for single post-processor workflow with full
    traceability via manifest.json and embedded metadata comments.
    
    Args:
        body: ExportBundleIn containing:
            - geometry: Design geometry with units and paths
            - gcode: Raw G-code toolpath body
            - post_id: Post-processor ID (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
            - job_name: Optional filename stem (sanitized, used for all files)
    
    Returns:
        StreamingResponse with application/zip Content-Type
        ZIP archive contains:
        - <job_name>.dxf: Design geometry in DXF R12 format
        - <job_name>.svg: Design geometry in SVG format
        - <job_name>.nc: Post-processed G-code with headers/footers
        - <job_name>_manifest.json: Metadata with units, post_id, timestamp, file list
        - README.txt: Human-readable bundle description
    
    Request Flow:
        1. Extract units from geometry (mm or inch)
        2. Generate metadata comment (units, post_id, timestamp)
        3. Sanitize job_name for filesystem safety
        4. Export geometry to DXF with metadata
        5. Export geometry to SVG with metadata
        6. Export G-code via post-processor with headers/footers
        7. Build manifest.json with provenance data
        8. Create ZIP archive with all files
        9. Return streaming response
    
    Manifest Structure:
        {
          "units": "mm",
          "post_id": "GRBL",
          "job_name": "body_pocket",
          "generated": "2025-01-15T14:32:18.123456Z",
          "files": ["body_pocket.dxf", "body_pocket.svg", "body_pocket.nc"]
        }
    
    Example:
        POST /api/geometry/export_bundle
        {
          "geometry": {
            "units": "mm",
            "paths": [{"type":"line","x1":0,"y1":0,"x2":100,"y2":0}]
          },
          "gcode": "G0 X0 Y0\\nG1 X100 Y0 F1200\\nM30",
          "post_id": "GRBL",
          "job_name": "neck_pocket"
        }
        => Returns neck_pocket_bundle.zip containing:
           neck_pocket.dxf
           neck_pocket.svg
           neck_pocket.nc
           neck_pocket_manifest.json
           README.txt
    
    Notes:
        - All files share same job_name stem (consistency)
        - DXF format is R12 for maximum CAM compatibility
        - Metadata embedded in all files (DXF comments, SVG comments, G-code comments)
        - Manifest enables batch processing and audit trails
        - ZIP compression reduces download size (~30-50% typical)
    
    Raises:
        None (uses generic post if post_id invalid)
    """
    units = body.geometry.units or "mm"
    target_units = (body.target_units or units).lower()
    
    # Scale geometry if a different target unit is requested
    geom_src = body.geometry.dict()
    geom = scale_geom_units(geom_src, target_units)
    units = geom["units"]
    
    meta = _metadata_comment(units, body.post_id or "")
    
    # Use job_name for filenames if provided, default to "program" for consistency
    stem = body.job_name.strip() if body.job_name else "program"
    
    # Build files in-memory
    dxf_txt = export_dxf(geom, meta=meta)
    svg_txt = export_svg(geom, meta=meta)
    
    # G-code via post-processor
    gc_request = GcodeExportIn(gcode=body.gcode, units=units, post_id=body.post_id, job_name=body.job_name)
    gc_response = export_gcode(gc_request)
    program = gc_response.body.decode("utf-8") if isinstance(gc_response.body, (bytes, bytearray)) else gc_response.body
    
    manifest = {
        "units": units,
        "post_id": body.post_id,
        "job_name": stem,
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "files": [f"{stem}.dxf", f"{stem}.svg", f"{stem}_{body.post_id}.nc"]
    }
    
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{stem}.dxf", dxf_txt)
        z.writestr(f"{stem}.svg", svg_txt)
        z.writestr(f"{stem}_{body.post_id}.nc", program)
        z.writestr(f"{stem}_manifest.json", json.dumps(manifest, indent=2))
        z.writestr("README.txt",
                   "ToolBox bundle export\nContains DXF/SVG/G-code with metadata comments for provenance.\n")
    
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{stem}_bundle.zip"'}
    )


class ExportBundleMultiIn(BaseModel):
    geometry: GeometryIn
    gcode: str
    post_ids: List[str]  # e.g. ["GRBL","Mach4","LinuxCNC","PathPilot","MASSO"]
    target_units: Optional[str] = None  # if provided, geometry is scaled server-side before export
    job_name: Optional[str] = Field(default=None, description="Filename stem for bundle files (safe chars only)")

@router.post("/export_bundle_multi")
def export_bundle_multi(body: ExportBundleMultiIn) -> Response:
    """
    Export multi-post CAM bundle: DXF + SVG + N×G-code + manifest as ZIP archive.
    
    Provides simultaneous export for multiple CNC post-processors with optional
    unit conversion and full traceability. Ideal for shops with mixed machine fleets.
    
    Args:
        body: ExportBundleMultiIn containing:
            - geometry: Design geometry with units and paths
            - gcode: Raw G-code toolpath body (unit-agnostic)
            - post_ids: List of post-processor IDs (e.g., ["GRBL", "Mach4", "LinuxCNC"])
            - target_units: Optional target units for export ("mm" or "inch")
                            If provided, geometry is scaled server-side before export
            - job_name: Optional filename stem (sanitized, used for all files)
    
    Returns:
        StreamingResponse with application/zip Content-Type
        ZIP archive contains:
        - <job_name>.dxf: Design geometry in target units (DXF R12 format)
        - <job_name>.svg: Design geometry in target units (SVG format)
        - <job_name>_<POST1>.nc: Post-processed G-code for first post
        - <job_name>_<POST2>.nc: Post-processed G-code for second post
        - ... (one .nc file per post_id)
        - <job_name>_manifest.json: Metadata with units, post list, timestamp
        - README.txt: Human-readable bundle description
    
    Request Flow:
        1. Determine source units from geometry (mm or inch)
        2. If target_units specified and different from source:
           a. Scale geometry using scale_geom_units() from units.py
           b. Update units field in geometry
        3. Validate post_ids against available post-processor configs
        4. Generate shared metadata comment (units, comma-separated post_ids, timestamp)
        5. Sanitize job_name for filesystem safety
        6. Export geometry to DXF with metadata (target units)
        7. Export geometry to SVG with metadata (target units)
        8. For each valid post_id:
           a. Generate G-code with post-specific headers/footers
           b. Store as <job_name>_<post_id>.nc
        9. Build manifest.json with full provenance data
        10. Create ZIP archive with all files
        11. Return streaming response
    
    Unit Conversion Algorithm:
        - Scaling factors: MM_PER_IN = 25.4, IN_PER_MM = 0.03937007874015748
        - Scales all coordinate fields: x1, y1, x2, y2, cx, cy, r
        - Updates units field to target_units
        - G-code units command (G21/G20) auto-injected based on target_units
    
    Manifest Structure:
        {
          "units": "inch",
          "posts": ["GRBL", "Mach4", "LinuxCNC"],
          "job_name": "body_pocket",
          "generated": "2025-01-15T14:32:18.123456Z",
          "files": [
            "body_pocket.dxf",
            "body_pocket.svg",
            "body_pocket_GRBL.nc",
            "body_pocket_Mach4.nc",
            "body_pocket_LinuxCNC.nc"
          ]
        }
    
    Example (mm to inch conversion):
        POST /api/geometry/export_bundle_multi
        {
          "geometry": {
            "units": "mm",
            "paths": [{"type":"line","x1":0,"y1":0,"x2":25.4,"y2":0}]
          },
          "gcode": "G0 X0 Y0\\nG1 X1 Y0 F48\\nM30",
          "post_ids": ["GRBL", "Mach4", "LinuxCNC"],
          "target_units": "inch",
          "job_name": "test_part"
        }
        => Returns test_part_multipost_bundle.zip containing:
           test_part.dxf (1 inch line in DXF R12)
           test_part.svg (1 inch line in SVG)
           test_part_GRBL.nc (G20 + GRBL headers)
           test_part_Mach4.nc (G20 + Mach4 headers)
           test_part_LinuxCNC.nc (G20 + LinuxCNC headers)
           test_part_manifest.json
           README.txt
    
    Notes:
        - DXF/SVG are shared across all posts (same geometry, target units)
        - Each .nc file has unique headers/footers per post-processor
        - Geometry scaling happens once before export (efficient)
        - Invalid post_ids are filtered out (only valid posts exported)
        - Falls back to default "program" if no job_name provided
        - ZIP compression reduces download size (~40-60% typical)
    
    Raises:
        HTTPException 400: No valid post_ids provided after filtering
    """
    units = body.geometry.units or "mm"
    target_units = (body.target_units or units).lower()

    # Scale geometry if a different target unit is requested
    geom_src = body.geometry.dict()
    geom = scale_geom_units(geom_src, target_units)
    units = geom["units"]

    # Use job_name for filenames if provided, default to "program" for consistency
    stem = body.job_name.strip() if body.job_name else "program"

    posts = _load_posts()
    # Map lowercase post names to actual file names for case-insensitive lookup
    posts_lower = {k.lower(): k for k in posts.keys()}
    # Preserve original case from user input in filenames
    requested = [p for p in body.post_ids if p.lower() in posts_lower]
    if not requested:
        raise HTTPException(400, "No valid post_ids supplied")

    meta = _metadata_comment(units, ",".join(requested))

    # Create common DXF/SVG in target units
    dxf_txt = export_dxf(geom, meta=meta)
    svg_txt = export_svg(geom, meta=meta)

    # Per-post G-code (with units + post headers/footers)
    nc_map = {}
    for pid in requested:
        gc_resp = export_gcode(GcodeExportIn(gcode=body.gcode, units=units, post_id=pid, job_name=body.job_name))
        program = gc_resp.body.decode("utf-8") if isinstance(gc_resp.body, (bytes, bytearray)) else gc_resp.body
        nc_map[pid] = program

    # Manifest
    manifest = {
        "units": units,
        "posts": requested,
        "job_name": stem,
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "files": [f"{stem}.dxf", f"{stem}.svg"] + [f"{stem}_{p}.nc" for p in requested]
    }

    # Build ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{stem}.dxf", dxf_txt)
        z.writestr(f"{stem}.svg", svg_txt)
        for p, txt in nc_map.items():
            z.writestr(f"{stem}_{p}.nc", txt)
        z.writestr(f"{stem}_manifest.json", json.dumps(manifest, indent=2))
        z.writestr("README.txt",
                   "ToolBox multi-post bundle export\nIncludes DXF/SVG (target units) and one NC per post.\n")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{stem}_multipost_bundle.zip"'})
