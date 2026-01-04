from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

# Import RMOS run artifact persistence (OPERATION lane requirement)
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

from ..cam.polygon_offset_n17 import toolpath_offsets
from ..util.gcode_emit_advanced import emit_xy_with_arcs
from ..util.gcode_emit_basic import emit_xy_polyline_nc

router = APIRouter()

Pt = Tuple[float, float]


class PolyOffsetReq(BaseModel):
    """Request model for polygon offset G-code generation"""
    polygon: List[Tuple[float, float]]
    tool_dia: float = 6.0
    stepover: float = 2.0
    inward: bool = True
    z: float = -1.5
    safe_z: float = 5.0
    units: str = "mm"
    feed: float = 600.0
    feed_arc: Optional[float] = None
    feed_floor: Optional[float] = None
    join_type: str = "round"
    arc_tolerance: float = 0.25
    link_mode: str = "arc"
    link_radius: float = 1.0
    spindle: int = 12000
    post: Optional[str] = None


def generate_polygon_offset_program(req: PolyOffsetReq) -> str:
    """
    Pure generator: returns G-code text for the requested polygon offset toolpath.
    Single source of truth for polygon offset toolpath - used by both draft and governed endpoints.
    
    Returns empty string with error comment if no valid paths generated.
    """
    # Generate offset paths
    paths = toolpath_offsets(
        req.polygon,
        req.tool_dia,
        req.stepover,
        req.inward,
        req.join_type,
        req.arc_tolerance
    )
    
    if not paths:
        return "(Error: No valid offset paths generated)
M30
"
    
    # Generate G-code with selected linking mode
    if req.link_mode == "arc":
        nc = emit_xy_with_arcs(
            paths,
            z=req.z,
            safe_z=req.safe_z,
            units=req.units,
            feed=req.feed,
            feed_arc=req.feed_arc,
            feed_floor=req.feed_floor,
            link_radius=req.link_radius
        )
    else:
        nc = emit_xy_polyline_nc(
            paths,
            z=req.z,
            safe_z=req.safe_z,
            units=req.units,
            feed=req.feed,
            spindle=req.spindle
        )
    
    return nc


# =============================================================================
# Draft Lane: Fast preview, no RMOS tracking
# =============================================================================

@router.post("/polygon_offset.nc", response_class=Response)
def polygon_offset(req: PolyOffsetReq) -> Response:
    """
    Generate G-code for polygon offsetting with multiple passes (DRAFT lane).
    
    Supports:
    - Robust pyclipper offsetting (or fallback miter)
    - Join types: miter, round, bevel
    - Arc linking (G2/G3) or linear linking (G1)
    - Feed management for tight curves
    
    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /polygon_offset_governed.nc.
    """
    program = generate_polygon_offset_program(req)
    
    resp = Response(content=program, media_type="text/plain")
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail
# =============================================================================

@router.post("/polygon_offset_governed.nc", response_class=Response)
def polygon_offset_governed(req: PolyOffsetReq) -> Response:
    """
    Generate G-code for polygon offsetting with multiple passes (GOVERNED lane).
    
    Same toolpath as /polygon_offset.nc but with full RMOS artifact persistence:
    - Creates immutable RunArtifact
    - SHA256 hashes request and output
    - Returns run_id for audit trail
    
    Use this endpoint for production/machine execution.
    """
    program = generate_polygon_offset_program(req)
    
    # Create RMOS artifact (matches adaptive pocket contract 1:1)
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump(mode="json"))
    gcode_hash = sha256_of_text(program)
    
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="polygon_offset_gcode",
        workflow_mode="polygon_offset",
        event_type="polygon_offset_gcode_execution",
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
