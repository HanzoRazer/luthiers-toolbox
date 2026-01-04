
from datetime import datetime, timezone
from typing import List, Tuple

from fastapi import APIRouter, Response
from pydantic import BaseModel

# Import RMOS run artifact persistence (OPERATION lane requirement)
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

from ..util.poly_offset_spiral import build_spiral_poly

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


def _emit_simple_gcode(pts: List[Tuple[float, float]], z: float=-1.0, safe_z: float=5.0, feed: float=600.0) -> str:
    """Simple G-code emitter for N18 spiral paths"""
    lines = []
    lines.append("( N18 Spiral PolyCut - Simple G-code )")
    lines.append("G90 G21")  # Absolute, mm
    lines.append(f"G0 Z{safe_z:.4f}")
    
    if not pts:
        lines.append("M30")
        return "\n".join(lines)
    
    # Rapid to first point
    lines.append(f"G0 X{pts[0][0]:.4f} Y{pts[0][1]:.4f}")
    
    # Plunge
    lines.append(f"G1 Z{z:.4f} F{feed * 0.5:.1f}")
    
    # Cut spiral path
    for pt in pts[1:]:
        lines.append(f"G1 X{pt[0]:.4f} Y{pt[1]:.4f} F{feed:.1f}")
    
    # Retract
    lines.append(f"G0 Z{safe_z:.4f}")
    lines.append("M30")
    lines.append("(END)")
    
    return "\n".join(lines)


def generate_offset_spiral_program(req: PolyNCReq) -> str:
    """
    Pure generator: returns G-code text for the requested offset spiral.
    Single source of truth for adaptive spiral toolpath - used by both draft and governed endpoints.
    """
    poly = [(p[0], p[1]) for p in req.polygon]
    if poly[0] != poly[-1]: 
        poly.append(poly[0])
    
    # Build spiral using N18 core
    margin = req.tool_dia * 0.1  # 10% margin default
    pts = build_spiral_poly(
        poly, 
        req.tool_dia, 
        req.stepover / req.tool_dia,  # Convert to fraction
        margin,
        climb=True,
        corner_radius_min=req.min_R,
        corner_tol_mm=req.arc_tol
    )
    
    # Emit G-code
    return _emit_simple_gcode(
        pts, 
        z=req.z, 
        safe_z=req.safe_z, 
        feed=req.base_feed
    )


# =============================================================================
# Draft Lane: Fast preview, no RMOS tracking
# =============================================================================

@router.post("/offset_spiral.nc")
def offset_spiral_nc(req: PolyNCReq) -> Response:
    """
    Generate offset spiral G-code (DRAFT lane).
    
    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /offset_spiral_governed.nc.
    """
    program = generate_offset_spiral_program(req)
    resp = Response(content=program, media_type="text/plain")
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail
# =============================================================================

@router.post("/offset_spiral_governed.nc")
def offset_spiral_nc_governed(req: PolyNCReq) -> Response:
    """
    Generate offset spiral G-code (GOVERNED lane).
    
    Same toolpath as /offset_spiral.nc but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    program = generate_offset_spiral_program(req)
    
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump(mode="json"))
    gcode_hash = sha256_of_text(program)
    
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="adaptive_offset_spiral",
        workflow_mode="adaptive_spiral",
        event_type="adaptive_spiral_gcode_execution",
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)
    
    resp = Response(content=program, media_type="text/plain")
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp
