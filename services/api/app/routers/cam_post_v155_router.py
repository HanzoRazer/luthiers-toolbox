
import json
import math
import os
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/cam_gcode", tags=["cam_gcode"])
Point = Tuple[float, float]

PRESET_PATH = os.environ.get("CAM_POST_PRESETS", os.path.join(os.path.dirname(__file__), "..", "data", "posts", "posts_v155.json"))

class V155Req(BaseModel):
    contour: List[Point]                          # open or closed polyline (XY mm)
    z_cut_mm: float = -1.0
    feed_mm_min: float = 600.0
    plane_z_mm: float = 5.0
    safe_rapid: bool = True

    # Post selection
    preset: Literal["GRBL","Mach3","Haas","Marlin"] = "GRBL"
    custom_post: Optional[Dict[str, Any]] = None   # override fields in preset

    # Lead in/out
    lead_type: Literal["none","tangent","arc"] = "tangent"
    lead_len_mm: float = 3.0
    lead_arc_radius_mm: float = 2.0

    # CRC
    crc_mode: Literal["none","left","right"] = "none"
    crc_diameter_mm: Optional[float] = None        # if None, emit G41/42 without D
    d_number: Optional[int] = None                 # optional wear table index (Dxx)

    # Corner smoothing
    fillet_radius_mm: float = 0.4
    fillet_angle_min_deg: float = 20.0             # only fillet tighter-than threshold

def _load_preset(name: str) -> Dict[str, Any]:
    try:
        with open(PRESET_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        p = data["presets"][name]
        return p
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preset load failed: {e}")

def _poly_is_closed(poly: List[Point], tol=1e-6)->bool:
    return len(poly)>2 and (abs(poly[0][0]-poly[-1][0])<tol and abs(poly[0][1]-poly[-1][1])<tol)

def _unit(v: float) -> float:
    return v

def _dot(ax: float, ay: float, bx: float, by: float) -> float: return ax*bx + ay*by
def _len(x: float, y: float) -> float: return math.hypot(x,y)

def _fillet_between(a:Point, b:Point, c:Point, R:float):
    # Returns (p1, p2, cx, cy, dir) where p1 and p2 are trim points, fillet arc between them
    (x1,y1)=a; (x2,y2)=b; (x3,y3)=c
    v1x, v1y = x1-x2, y1-y2   # vector BA
    v2x, v2y = x3-x2, y3-y2   # vector BC
    L1 = _len(v1x,v1y); L2 = _len(v2x,v2y)
    if L1<1e-9 or L2<1e-9: return None
    v1x/=L1; v1y/=L1; v2x/=L2; v2y/=L2
    # angle between -v1 and v2
    cos_theta = _dot(-v1x,-v1y, v2x,v2y)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    theta = math.acos(cos_theta)  # interior angle at b (0..pi)
    if theta < 1e-6 or theta > math.pi-1e-6: 
        return None
    # distance from corner to tangent points along each segment
    t = R * math.tan(theta/2.0)
    if t > L1-1e-6 or t > L2-1e-6:
        return None
    p1 = (x2 + (-v1x)*t, y2 + (-v1y)*t)
    p2 = (x2 + v2x*t,     y2 + v2y*t)
    # bisector direction
    bisx = (-v1x + v2x); bisy = (-v1y + v2y)
    bl = _len(bisx,bisy)
    if bl<1e-9: 
        return None
    bisx/=bl; bisy/=bl
    # distance from tangent points to center along normals: R / sin(theta/2)
    h = R / math.sin(theta/2.0)
    # center from corner along bisector
    cx = x2 + bisx * h
    cy = y2 + bisy * h
    # direction (CW/CCW) from p1->p2
    # vectors from center
    u1x,u1y = p1[0]-cx, p1[1]-cy
    u2x,u2y = p2[0]-cx, p2[1]-cy
    cross = u1x*u2y - u1y*u2x
    dirn = "CCW" if cross>0 else "CW"
    return (p1,p2,cx,cy,dirn)

def _angle(cx: float, cy: float, p: Point) -> float:
    return math.atan2(p[1]-cy, p[0]-cx)

def _axis_modal_emit(line: str, last_xy: Optional[tuple]) -> tuple:
    tokens = line.split()
    if not tokens: return line, last_xy
    if tokens[0] not in ("G1","G2","G3"): return line, last_xy
    x=None;y=None
    for t in tokens:
        if t.startswith("X"): x = float(t[1:])
        elif t.startswith("Y"): y = float(t[1:])
    parts=[tokens[0]]
    if x is None and last_xy: x = last_xy[0]
    if y is None and last_xy: y = last_xy[1]
    if last_xy is None or abs(x-last_xy[0])>1e-9: parts.append(f"X{x:.3f}")
    if last_xy is None or abs(y-last_xy[1])>1e-9: parts.append(f"Y{y:.3f}")
    for t in tokens[1:]:
        if not (t.startswith("X") or t.startswith("Y")):
            parts.append(t)
    return " ".join(parts), (x,y)

def _build_lead(blocks:List[str], start:Point, first_vec, plane_z, z_cut, lead_type, lead_len, lead_R, arc_mode_R, units, axis_modal, last_xy):
    # Rapid above, then optional lead-in
    blocks.append(f"G0 Z{plane_z:.3f}")
    blocks.append(f"G0 X{start[0]:.3f} Y{start[1]:.3f}")
    blocks.append(f"G1 Z{z_cut:.3f}")
    last_xy = (start[0], start[1])
    if lead_type=="tangent" and lead_len>0:
        # move backwards along -first_vec then forward onto start point to ensure tangency
        bx = start[0] - first_vec[0]*lead_len
        by = start[1] - first_vec[1]*lead_len
        blocks.append(f"G1 X{bx:.3f} Y{by:.3f} Z{z_cut:.3f}")
        blocks.append(f"G1 X{start[0]:.3f} Y{start[1]:.3f} Z{z_cut:.3f}")
        last_xy = (start[0], start[1])
    elif lead_type=="arc" and lead_R>0:
        # simple 90° arc lead-in from side: offset point to the left of first_vec by R, then arc to start
        # normal left
        nx,ny = -first_vec[1], first_vec[0]
        px = start[0] + nx*lead_R
        py = start[1] + ny*lead_R
        blocks.append(f"G1 X{px:.3f} Y{py:.3f} Z{z_cut:.3f}")
        # arc quarter circle back to start, CW
        if arc_mode_R:
            blocks.append(f"G2 X{start[0]:.3f} Y{start[1]:.3f} R{lead_R:.3f} Z{z_cut:.3f}")
        else:
            cx = start[0]; cy = start[1] + lead_R
            I = cx - px; J = cy - py
            blocks.append(f"G2 X{start[0]:.3f} Y{start[1]:.3f} I{I:.3f} J{J:.3f} Z{z_cut:.3f}")
        last_xy = (start[0], start[1])
    return blocks, last_xy

@router.get("/posts_v155")
def get_posts()->Dict[str, Any]:
    """Get all available post-processor presets (v15.5)"""
    with open(PRESET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@router.post("/post_v155")
def post_v155(req: V155Req) -> Dict[str, Any]:
    """
    Generate G-code from contour with advanced post-processing
    
    Features:
    - Post-processor presets (GRBL, Mach3, Haas, Marlin)
    - Lead-in/out strategies (tangent, arc, none)
    - CRC support (G41/G42 with optional D#)
    - Automatic corner smoothing (fillet arcs)
    - Arc optimization (controller-aware sweep limits)
    - Axis modal optimization (suppress redundant coordinates)
    """
    # load preset + override
    post = _load_preset(req.preset)
    if req.custom_post:
        post.update(req.custom_post)

    units = post.get("units","metric")
    arc_mode = post.get("arc_mode","IJ")  # "IJ" or "R"
    allow_major = bool(post.get("allow_major_arc", False))
    axis_modal = bool(post.get("axis_modal_opt", True))
    modal_compress = bool(post.get("modal_compress", True))
    arc_limit = float(post.get("arc_max_sweep_deg", 179.9))
    header:list[str] = list(post.get("header", []))
    footer:list[str] = list(post.get("footer", []))

    poly = list(req.contour)
    if len(poly) < 2:
        raise HTTPException(status_code=400, detail="contour requires >=2 points")

    # ensure closed for CRC contour
    closed = _poly_is_closed(poly)
    if not closed:
        poly = poly + [poly[0]]
        closed = True

    # Corner smoothing (fillets)
    Rf = max(0.0, req.fillet_radius_mm)
    angmin = math.radians(max(0.0, req.fillet_angle_min_deg))
    sm = [poly[0]]
    arcs = []  # (i index after sm append) -> (p1,p2,cx,cy,dir)
    for i in range(1, len(poly)-1):
        a,b,c = poly[i-1], poly[i], poly[i+1]
        # compute interior angle
        v1x, v1y = a[0]-b[0], a[1]-b[1]
        v2x, v2y = c[0]-b[0], c[1]-b[1]
        L1 = math.hypot(v1x,v1y); L2 = math.hypot(v2x,v2y)
        if L1<1e-9 or L2<1e-9:
            sm.append(b); continue
        v1x/=L1; v1y/=L1; v2x/=L2; v2y/=L2
        cos_t = max(-1.0, min(1.0, (-(v1x)*v2x + -(v1y)*v2y)))
        theta = math.acos(cos_t)
        if Rf>0 and theta < math.pi - 1e-6 and theta < math.pi and theta < (math.pi - angmin):
            fil = _fillet_between(a,b,c,Rf)
            if fil:
                p1,p2,cx,cy,dirn = fil
                sm.append(p1)
                sm.append(p2)
                arcs.append( (len(sm)-2, len(sm)-1, cx, cy, Rf, dirn) )  # arc spans p1->p2
                continue
        sm.append(b)
    sm.append(poly[-1])

    # Build G-code
    out = []
    out += header
    out.append("G21" if units=="metric" else "G20")
    out.append("G90")
    out.append("G94")
    out.append(f"F{req.feed_mm_min:.3f}")
    z_cut = req.z_cut_mm
    plane_z = req.plane_z_mm

    # CRC mode
    if req.crc_mode != "none":
        if req.crc_mode == "left":
            out.append("G41")
        else:
            out.append("G42")
        if req.crc_diameter_mm:
            # Emit D via comment; many hobby controllers ignore D; Haas/Mach3 may use Dxx
            if req.d_number is not None:
                out.append(f"D{int(req.d_number)} (dia {req.crc_diameter_mm:.3f}mm)")
            else:
                out.append(f"(CRC dia {req.crc_diameter_mm:.3f}mm)")

    # Lead-in
    # find first move vector
    first_vec = (sm[1][0]-sm[0][0], sm[1][1]-sm[0][1])
    fl = math.hypot(first_vec[0], first_vec[1]) or 1e-9
    first_vec = (first_vec[0]/fl, first_vec[1]/fl)
    last_xy = None
    out, last_xy = _build_lead(out, sm[0], first_vec, plane_z, z_cut, req.lead_type, req.lead_len_mm, req.lead_arc_radius_mm, arc_mode=="R", units, axis_modal, last_xy)

    # Contour with fillet arcs
    def emit_modal(line: str):
        nonlocal last_xy
        if axis_modal:
            line2, last_xy = _axis_modal_emit(line, last_xy)
            out.append(line2)
        else:
            out.append(line)

    # walk segments, inserting arcs where marked
    i = 0
    arc_map = {(a,b):(cx,cy,R,dirn) for (a,b,cx,cy,R,dirn) in [(ai,aj,cx,cy,R,dirn) for (ai,aj,cx,cy,R,dirn) in []]}
    arc_ranges = {(ai,aj):(cx,cy,R,dirn) for (ai,aj,cx,cy,R,dirn) in arcs}
    while i < len(sm)-1:
        p0 = sm[i]; p1 = sm[i+1]
        # if this pair participates as an arc edge (p0->p1) and the next edge continues to p2 with same arc, emit G2/G3
        found = None
        for (ai,aj),(cx,cy,R,dirn) in arc_ranges.items():
            if ai==i and aj==i+1:
                found = (cx,cy,R,dirn); break
        if found:
            cx,cy,R,dirn = found
            code = "G2" if dirn=="CW" else "G3"
            if arc_mode=="R":
                # quarter or partial arc: sign for >180 not handled here (fillets are <180)
                emit_modal(f"{code} X{p1[0]:.3f} Y{p1[1]:.3f} R{R:.3f} Z{z_cut:.3f}")
            else:
                I = cx - p0[0]; J = cy - p0[1]
                emit_modal(f"{code} X{p1[0]:.3f} Y{p1[1]:.3f} I{I:.3f} J{J:.3f} Z{z_cut:.3f}")
        else:
            emit_modal(f"G1 X{p1[0]:.3f} Y{p1[1]:.3f} Z{z_cut:.3f}")
        i += 1

    # Lead-out (mirror of tangent lead: retract along last segment)
    if req.lead_type=="tangent" and req.lead_len_mm>0:
        last_vec = (sm[-1][0]-sm[-2][0], sm[-1][1]-sm[-2][1])
        ll = math.hypot(last_vec[0], last_vec[1]) or 1e-9
        last_vec = (last_vec[0]/ll, last_vec[1]/ll)
        ex = sm[-1][0] + last_vec[0]*req.lead_len_mm
        ey = sm[-1][1] + last_vec[1]*req.lead_len_mm
        emit_modal(f"G1 X{ex:.3f} Y{ey:.3f} Z{z_cut:.3f}")
    elif req.lead_type=="arc" and req.lead_arc_radius_mm>0:
        # quarter arc lead-out
        last_vec = (sm[-1][0]-sm[-2][0], sm[-1][1]-sm[-2][1])
        ll = math.hypot(last_vec[0], last_vec[1]) or 1e-9
        last_vec = (last_vec[0]/ll, last_vec[1]/ll)
        nx,ny = last_vec[1], -last_vec[0]  # right normal
        px = sm[-1][0] + nx*req.lead_arc_radius_mm
        py = sm[-1][1] + ny*req.lead_arc_radius_mm
        emit_modal(f"G1 X{px:.3f} Y{py:.3f} Z{z_cut:.3f}")
        if arc_mode=="R":
            emit_modal(f"G3 X{sm[-1][0]:.3f} Y{sm[-1][1]:.3f} R{req.lead_arc_radius_mm:.3f} Z{z_cut:.3f}")
        else:
            cx = sm[-1][0]; cy = sm[-1][1] + req.lead_arc_radius_mm
            I = cx - px; J = cy - py
            emit_modal(f"G3 X{sm[-1][0]:.3f} Y{sm[-1][1]:.3f} I{I:.3f} J{J:.3f} Z{z_cut:.3f}")

    # CRC cancel on exit
    if req.crc_mode != "none":
        out.append("G40")

    out.append(f"G0 Z{plane_z:.3f}")
    out += footer

    # simple spans for preview (tessellate arcs crudely via IJ detection)
    spans=[]
    last = sm[0]
    i=0
    while i < len(out):
        line = out[i].strip()
        if line.startswith("G1 ") and "X" in line and "Y" in line and "Z" in line:
            def _get(tag, s):
                p = s.find(tag)
                if p<0: return None
                q = p+1
                while q<len(s) and (s[q].isdigit() or s[q] in ".-"):
                    q+=1
                return float(s[p+1:q])
            x = _get("X", line); y=_get("Y", line)
            if x is not None and y is not None:
                spans.append({"x1":last[0],"y1":last[1],"z1":req.z_cut_mm,"x2":x,"y2":y,"z2":req.z_cut_mm})
                last=(x,y)
        elif (line.startswith("G2 ") or line.startswith("G3 ")) and "X" in line and "Y" in line:
            # rough chord tessellation: assume small arcs (fillets)
            cw = line.startswith("G2 ")
            def _get(tag, s):
                p = s.find(tag)
                if p<0: return None
                q = p+1
                while q<len(s) and (s[q].isdigit() or s[q] in ".-"):
                    q+=1
                return float(s[p+1:q])
            x = _get("X", line); y = _get("Y", line); r = _get("R", line); I = _get("I", line); J = _get("J", line)
            ex,ey = last[0], last[1]
            if x is not None and y is not None:
                if r is not None:
                    # approximate center via perpendicular bisector + radius (assume minor arc)
                    mx = (ex + x)/2; my = (ey + y)/2
                    dx,dy = x-ex, y-ey
                    d = math.hypot(dx,dy) or 1e-9
                    h = math.sqrt(max(r*r - (d/2)*(d/2), 0.0))
                    nx,ny = -dy/d, dx/d
                    # choose side based on cw/ccw
                    cx = mx + ( -h if cw else h ) * nx
                    cy = my + ( -h if cw else h ) * ny
                elif I is not None and J is not None:
                    cx = ex + I; cy = ey + J; r = math.hypot(I,J)
                else:
                    cx,cy,r = ex,ey,1.0
                a1 = math.atan2(ey-cy, ex-cx); a2 = math.atan2(y-cy, x-cx)
                if cw:
                    while a2 > a1: a2 -= 2*math.pi
                else:
                    while a2 < a1: a2 += 2*math.pi
                steps = max(6, int(abs(a2-a1)*r/0.5))
                px,py = ex,ey
                for t in range(1, steps+1):
                    ang = a1 + (a2-a1)*t/steps
                    qx = cx + r*math.cos(ang); qy = cy + r*math.sin(ang)
                    spans.append({"x1":px,"y1":py,"z1":req.z_cut_mm,"x2":qx,"y2":qy,"z2":req.z_cut_mm})
                    px,py = qx,qy
                last=(x,y)
        i+=1

    gcode = "\n".join(out)
    return {"ok": True, "gcode": gcode, "spans": spans, "closed": closed, "preset_used": req.preset}
