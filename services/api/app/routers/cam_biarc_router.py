# services/api/app/routers/cam_biarc_router.py
"""
CAM Bi-Arc Router (N10 CAM Essentials)
Simple contour following from point array with post-processor support.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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

# Import post injection utilities
try:
    from ..util.post_injection_helpers import build_post_context_v2, wrap_with_post_v2
    HAS_POST_HELPERS = True
except ImportError:
    HAS_POST_HELPERS = False

router = APIRouter(prefix="/cam/biarc", tags=["CAM", "N10"])


class Seg(BaseModel):
    """Single point in path"""
    x: float
    y: float


class BiarcReq(BaseModel):
    """Request model for bi-arc contour following"""
    path: List[Seg]  # Array of (x, y) points
    z: float  # Cutting depth
    feed: float  # Feed rate (mm/min)
    safe_z: float = 5.0
    units: str = "mm"
    
    # Post-processor parameters
    post: Optional[str] = None
    post_mode: Optional[str] = None
    machine_id: Optional[str] = None
    rpm: Optional[float] = None
    program_no: Optional[str] = None
    work_offset: Optional[str] = None
    tool: Optional[int] = None


def _f(n: float) -> str:
    """Format float to 3 decimal places"""
    return f"{n:.3f}"


def generate_biarc_program(req: "BiarcReq") -> str:
    """
    Pure generator: returns G-code text for contour following.
    Single source of truth for biarc toolpath - used by both draft and governed endpoints.
    """
    lines = [
        "G90",  # Absolute positioning
        f"G0 Z{_f(req.safe_z)}",  # Rapid to safe height
    ]
    
    if req.path:
        # Rapid to first point
        lines.append(f"G0 X{_f(req.path[0].x)} Y{_f(req.path[0].y)}")
        
        # Plunge to cutting depth
        lines.append(f"G1 Z{_f(req.z)} F{_f(req.feed)}")
        
        # Follow path (linear interpolation)
        for p in req.path[1:]:
            lines.append(f"G1 X{_f(p.x)} Y{_f(p.y)} F{_f(req.feed)}")
    
    return "\n".join(lines) + "\n"


# =============================================================================
# Draft Lane: Fast preview, no RMOS tracking
# =============================================================================

@router.post("/gcode", response_class=Response)
def biarc_gcode(req: BiarcReq) -> Response:
    """
    Generate contour-following G-code from point array (DRAFT lane).
    
    Process:
    1. Rapid to safe height
    2. Rapid to first point (XY)
    3. Plunge to cutting depth
    4. Linear interpolation through all points
    5. Retract to safe height
    
    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /gcode_governed.
    """
    program = generate_biarc_program(req)
    
    # Create response
    resp = Response(content=program, media_type="text/plain; charset=utf-8")
    
    # Apply post-processor wrapping if available
    if HAS_POST_HELPERS:
        ctx = build_post_context_v2(
            post=req.post,
            post_mode=req.post_mode,
            units=req.units,
            machine_id=req.machine_id,
            RPM=req.rpm,
            PROGRAM_NO=req.program_no,
            WORK_OFFSET=req.work_offset,
            TOOL=req.tool,
            SAFE_Z=req.safe_z
        )
        resp = wrap_with_post_v2(resp, ctx)
    
    # Mark as draft lane
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail
# =============================================================================

@router.post("/gcode_governed", response_class=Response)
def biarc_gcode_governed(req: BiarcReq) -> Response:
    """
    Generate contour-following G-code from point array (GOVERNED lane).
    
    Same toolpath as /gcode but with full RMOS artifact persistence:
    - Creates immutable RunArtifact
    - SHA256 hashes request and output
    - Returns run_id for audit trail
    
    Use this endpoint for production/machine execution.
    """
    program = generate_biarc_program(req)
    
    # Create response
    resp = Response(content=program, media_type="text/plain; charset=utf-8")
    
    # Apply post-processor wrapping if available
    if HAS_POST_HELPERS:
        ctx = build_post_context_v2(
            post=req.post,
            post_mode=req.post_mode,
            units=req.units,
            machine_id=req.machine_id,
            RPM=req.rpm,
            PROGRAM_NO=req.program_no,
            WORK_OFFSET=req.work_offset,
            TOOL=req.tool,
            SAFE_Z=req.safe_z
        )
        resp = wrap_with_post_v2(resp, ctx)
        # Get final program text after wrapping for accurate hash
        try:
            program = resp.body.decode("utf-8") if isinstance(resp.body, (bytes, bytearray)) else program
        except Exception:
            pass
    
    # Create RMOS artifact (matches adaptive pocket contract 1:1)
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump(mode="json"))
    gcode_hash = sha256_of_text(program)
    
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="biarc_gcode",
        workflow_mode="biarc",
        event_type="biarc_gcode_execution",
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)
    
    # Add provenance headers
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp


@router.get("/info")
def biarc_info() -> Dict[str, Any]:
    """Get bi-arc operation information"""
    return {
        "operation": "biarc_contour",
        "description": "Simple contour following from point array (linear interpolation)",
        "supports_post_processors": HAS_POST_HELPERS,
        "parameters": {
            "path": "Array of {x, y} points defining contour",
            "z": "Cutting depth (mm)",
            "feed": "Feed rate (mm/min)",
            "safe_z": "Safe retract height (mm)"
        },
        "future_enhancements": [
            "Bi-arc spline fitting for smoother curves",
            "Arc detection from polyline segments",
            "Tolerance-based simplification"
        ]
    }
