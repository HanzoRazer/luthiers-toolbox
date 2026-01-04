# services/api/app/routers/cam_drill_router.py
"""
CAM Drilling Router (N10 CAM Essentials)
Modal drilling cycles (G81, G83) with post-processor support.
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

router = APIRouter(prefix="/cam/drill", tags=["CAM", "N10"])


class Hole(BaseModel):
    """Single hole definition"""
    x: float
    y: float
    z: float
    feed: float


class DrillReq(BaseModel):
    """Request model for drilling operation"""
    holes: List[Hole]
    r_clear: Optional[float] = None  # Clearance height (R parameter)
    peck_q: Optional[float] = None  # Peck depth for G83 (Q parameter)
    dwell_p: Optional[float] = None  # Dwell time in seconds (P parameter)
    cycle: str = "G81"  # G81 (simple) or G83 (peck)
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


def generate_drill_program(req: "DrillReq") -> str:
    """
    Pure generator: returns G-code text for the requested drilling operation.
    Single source of truth for drilling toolpath - used by both draft and governed endpoints.
    """
    cyc = req.cycle.upper().strip()
    if cyc not in ("G81", "G83"):
        cyc = "G81"  # Default to simple drilling

    # Default clearance height
    r_clear = _f(req.r_clear if req.r_clear is not None else 5.0)

    # Generate G-code
    lines = [
        "G90",  # Absolute positioning
        f"G0 Z{_f(req.safe_z)}",  # Rapid to safe height
    ]

    # Generate cycle for each hole
    for h in req.holes:
        if cyc == "G81":
            # Simple drilling (optional dwell)
            dwell = f" P{_f(req.dwell_p)}" if req.dwell_p is not None else ""
            lines.append(
                f"G81 X{_f(h.x)} Y{_f(h.y)} Z{_f(h.z)} R{r_clear} F{_f(h.feed)}{dwell}"
            )
        else:
            # Peck drilling (G83)
            peck = _f(req.peck_q if req.peck_q is not None else 1.0)
            dwell = f" P{_f(req.dwell_p)}" if req.dwell_p is not None else ""
            lines.append(
                f"G83 X{_f(h.x)} Y{_f(h.y)} Z{_f(h.z)} R{r_clear} Q{peck} F{_f(h.feed)}{dwell}"
            )

    # Cancel cycle
    lines.append("G80")

    return "
".join(lines) + "
"


# =============================================================================
# Draft Lane: Fast preview, no RMOS tracking
# =============================================================================

@router.post("/gcode", response_class=Response)
def drill_gcode(req: DrillReq) -> Response:
    """
    Generate drilling G-code using modal cycles (DRAFT lane).

    Supports:
    - G81: Simple drilling with optional dwell
    - G83: Peck drilling with incremental depth

    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /gcode_governed.
    """
    program = generate_drill_program(req)

    # Create response
    resp = Response(content=program, media_type="text/plain; charset=utf-8")

    # Apply post-processor wrapping
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
            SAFE_Z=req.safe_z,
            DWELL_P=req.dwell_p,
            PECK_Q=req.peck_q,
            R_CLEAR=req.r_clear
        )
        resp = wrap_with_post_v2(resp, ctx)

    # Mark as draft lane
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail
# =============================================================================

@router.post("/gcode_governed", response_class=Response)
def drill_gcode_governed(req: DrillReq) -> Response:
    """
    Generate drilling G-code using modal cycles (GOVERNED lane).

    Same toolpath as /gcode but with full RMOS artifact persistence:
    - Creates immutable RunArtifact
    - SHA256 hashes request and output
    - Returns run_id for audit trail

    Use this endpoint for production/machine execution.
    """
    program = generate_drill_program(req)

    # Create response
    resp = Response(content=program, media_type="text/plain; charset=utf-8")

    # Apply post-processor wrapping
    # Must wrap BEFORE hashing so we hash the final output
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
            SAFE_Z=req.safe_z,
            DWELL_P=req.dwell_p,
            PECK_Q=req.peck_q,
            R_CLEAR=req.r_clear
        )
        resp = wrap_with_post_v2(resp, ctx)
        # Get final program text after wrapping for accurate hash
        try:
            program = resp.body.decode("utf-8") if isinstance(resp.body, (bytes, bytearray)) else program
        except Exception:
            pass  # Fall back to pre-wrap program if body not accessible

    # Create RMOS artifact (matches adaptive pocket contract 1:1)
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump(mode="json"))
    gcode_hash = sha256_of_text(program)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="drill_gcode",
        workflow_mode="drilling",
        event_type="drill_gcode_execution",
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
def drill_info() -> Dict[str, Any]:
    """Get drilling operation information"""
    return {
        "operation": "drilling",
        "description": "Modal drilling cycles (G81 simple, G83 peck drilling)",
        "supports_post_processors": HAS_POST_HELPERS,
        "cycles": {
            "G81": "Simple drilling with optional dwell at bottom",
            "G83": "Peck drilling with incremental depth (chip breaking)"
        },
        "parameters": {
            "holes": "Array of {x, y, z, feed} hole definitions",
            "r_clear": "Clearance height (R parameter, default 5.0mm)",
            "peck_q": "Peck depth for G83 (Q parameter, default 1.0mm)",
            "dwell_p": "Dwell time at hole bottom (P parameter, seconds)",
            "cycle": "G81 or G83",
            "safe_z": "Safe retract height (default 5.0mm)"
        }
    }
