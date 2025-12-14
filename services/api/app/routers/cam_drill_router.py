# services/api/app/routers/cam_drill_router.py
"""
CAM Drilling Router (N10 CAM Essentials)
Modal drilling cycles (G81, G83) with post-processor support.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

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


@router.post("/gcode", response_class=Response)
def drill_gcode(req: DrillReq) -> Response:
    """
    Generate drilling G-code using modal cycles.
    
    Supports:
    - G81: Simple drilling with optional dwell
    - G83: Peck drilling with incremental depth
    """
    cyc = req.cycle.upper().strip()
    if cyc not in ("G81", "G83"):
        cyc = "G81"  # Default to simple drilling
    
    # Build post context for token expansion
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
    
    body = "\n".join(lines) + "\n"
    
    # Create response
    resp = Response(content=body, media_type="text/plain; charset=utf-8")
    
    # Apply post-processor wrapping
    if HAS_POST_HELPERS:
        resp = wrap_with_post_v2(resp, ctx)
    
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
