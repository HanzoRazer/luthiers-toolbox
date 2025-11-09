
from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import List
from .util.poly_offset_spiral import build_spiral_poly
from .util.g2_emitter import emit_program_xy
router = APIRouter(prefix="/cam/adaptive3", tags=["cam","adaptive-poly","gcode"])
class PolyNCReq(BaseModel):
    polygon: List[List[float]]
    tool_dia: float = 6.0
    stepover: float = 2.4
    target_engage: float = 0.35
    arc_r: float = 2.0
    units: str = "mm"
    z: float = -1.0
    safe_z: float = 5.0
    base_feed: float = 600.0
    min_feed: float = 120.0
    floor_R: float = 3.0
    arc_tol: float = 0.05
    min_R: float = 1.0
    spindle: int = 12000
@router.post("/offset_spiral.nc")
def offset_spiral_nc(req: PolyNCReq):
    poly = [(p[0], p[1]) for p in req.polygon]
    if poly[0] != poly[-1]: poly.append(poly[0])
    pts = build_spiral_poly(poly, req.tool_dia, req.stepover, req.target_engage, req.arc_r)
    nc = emit_program_xy(pts, units=req.units, z=req.z, safe_z=req.safe_z, base_feed=req.base_feed, min_feed=req.min_feed, floor_R=req.floor_R, arc_tol=req.arc_tol, min_R=req.min_R, spindle=req.spindle)
    return Response(content=nc, media_type="text/plain")
