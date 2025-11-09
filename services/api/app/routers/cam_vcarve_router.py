
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, Any
import re

try:
    import pyclipper
    HAVE_PYCLIPPER = True
except Exception:
    HAVE_PYCLIPPER = False

try:
    from shapely.geometry import Polygon, LineString
    from shapely.ops import unary_union
    from shapely.affinity import rotate as shp_rotate, translate as shp_translate
    HAVE_SHAPELY = True
except Exception:
    HAVE_SHAPELY = False

router = APIRouter(prefix="/api/cam_vcarve", tags=["cam_vcarve"])

Point = Tuple[float, float]

class PreviewReq(BaseModel):
    mode: str  # 'raster' or 'contour'
    polygons: Optional[List[List[Point]]] = None
    centerlines_svg: Optional[str] = None
    approx_stroke_width_mm: Optional[float] = None
    raster_angle_deg: float = 0.0
    flat_stepover_mm: float = 1.2

def _parse_svg_polylines(svg: str) -> List[List[Tuple[float,float]]]:
    pl = []
    for m in re.finditer(r'<poly(?:line|gon)[^>]*points="([^"]+)"', svg, re.IGNORECASE):
        pts_str = m.group(1).strip()
        pts = []
        for token in re.split(r'\s+', pts_str):
            if not token: continue
            if "," in token:
                x, y = token.split(",", 1)
            else:
                parts = token.split()
                if len(parts) != 2: continue
                x, y = parts
            try:
                pts.append((float(x), float(y)))
            except:
                pass
        if pts: pl.append(pts)
    return pl

def _polylines_to_svg(polylines: List[List[Tuple[float,float]]], stroke="royalblue", stroke_width=0.6) -> str:
    xs, ys = [], []
    for poly in polylines:
        for x,y in poly:
            xs.append(x); ys.append(y)
    if not xs: xs=[0,1]; ys=[0,1]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    w = max(1.0, maxx - minx); h = max(1.0, maxy - miny)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx} {miny} {w} {h}">']
    for poly in polylines:
        pts = " ".join(f"{x:.3f},{y:.3f}" for x,y in poly)
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>')
    parts.append("</svg>")
    return "\\n".join(parts)

def _estimate_len(polylines: List[List[Tuple[float,float]]]) -> float:
    import math
    tot = 0.0
    for pl in polylines:
        for (x1,y1),(x2,y2) in zip(pl, pl[1:]):
            dx, dy = x2-x1, y2-y1
            tot += math.hypot(dx,dy)
    return tot

@router.post("/preview_infill")
def preview_infill(req: PreviewReq) -> Dict[str, Any]:
    regions = req.polygons or []
    if not regions and req.centerlines_svg and req.approx_stroke_width_mm and HAVE_PYCLIPPER:
        delta = req.approx_stroke_width_mm / 2.0
        co = pyclipper.PyclipperOffset(miterLimit=2.0, arcTolerance=0.25)
        for pl in _parse_svg_polylines(req.centerlines_svg):
            co.AddPath([(x,y) for x,y in pl], pyclipper.JT_ROUND, pyclipper.ET_OPENROUND)
        out = co.Execute(delta)
        regions = [[(float(x), float(y)) for x,y in path] for path in out]

    if not regions:
        return {"ok": True, "svg": "<svg xmlns='http://www.w3.org/2000/svg'/>", "stats": {"total_spans": 0, "total_len": 0.0}}

    if not HAVE_SHAPELY:
        raise HTTPException(status_code=500, detail="Shapely required for preview. pip install shapely")

    union = unary_union([Polygon(p) for p in regions if len(p)>=3])

    polylines: List[List[Tuple[float,float]]] = []
    if req.mode == "raster":
        angle = float(req.raster_angle_deg or 0.0)
        rot = shp_rotate(union, -angle, origin=(0,0), use_radians=False)
        minx, miny, maxx, maxy = rot.bounds
        tx, ty = -minx + 1.0, -miny + 1.0
        rot = shp_translate(rot, xoff=tx, yoff=ty)
        y = rot.bounds[1]
        while y <= rot.bounds[3]:
            seg = rot.intersection(LineString([(rot.bounds[0]-1, y), (rot.bounds[2]+1, y)]))
            geoms = getattr(seg, "geoms", [seg])
            for g in geoms:
                coords = list(g.coords)
                if len(coords) >= 2:
                    from shapely.affinity import translate, rotate
                    ls = LineString(coords)
                    ls = translate(ls, xoff=-tx, yoff=-ty)
                    ls = rotate(ls, angle, origin=(0,0), use_radians=False)
                    polylines.append(list(ls.coords))
            y += max(0.1, req.flat_stepover_mm)
    else:
        if not HAVE_PYCLIPPER:
            raise HTTPException(status_code=500, detail="pyclipper required for contour infill. pip install pyclipper")
        import pyclipper
        cur = [list(poly.exterior.coords)[:-1] for poly in ([union] if union.geom_type=='Polygon' else union.geoms)]
        while cur:
            for ring in cur:
                polylines.append([(float(x),float(y)) for x,y in ring])
            co = pyclipper.PyclipperOffset(miterLimit=2.0, arcTolerance=0.25)
            for ring in cur:
                co.AddPath([(x,y) for x,y in ring], pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            nxt = co.Execute(-max(0.1, req.flat_stepover_mm))
            cur = [[(float(x), float(y)) for x,y in path] for path in nxt]

    svg = _polylines_to_svg(polylines)
    stats = {"total_spans": len(polylines), "total_len": _estimate_len(polylines)}
    return {"ok": True, "svg": svg, "stats": stats}
