"""
CAM Roughing Router

Simple rectangular roughing G-code generator with post-processor support.

Migrated from: routers/cam_roughing_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /gcode    - Generate rectangular roughing G-code
    GET  /info     - Get operation information
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

# Import post injection utilities (already in codebase from Phase 2)
try:
    from ....util.post_injection_helpers import build_post_context_v2, wrap_with_post_v2
    HAS_POST_HELPERS = True
except ImportError:
    HAS_POST_HELPERS = False

router = APIRouter()


class RoughReq(BaseModel):
    """Request model for rectangular roughing operation"""
    width: float
    height: float
    stepdown: float
    stepover: float
    feed: float
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
def roughing_gcode(req: RoughReq) -> Response:
    """
    Generate simple rectangular roughing G-code.

    Pattern: Move to origin, plunge, mill rectangular boundary, retract.
    Suitable for basic pocket roughing or face milling.
    """
    x2, y2 = req.width, req.height

    # Generate G-code body (simple rectangle)
    lines = [
        "G90",  # Absolute positioning
        f"G0 Z{_f(req.safe_z)}",  # Rapid to safe height
        "G0 X0 Y0",  # Rapid to origin
        f"G1 Z{_f(-req.stepdown)} F{_f(req.feed)}",  # Plunge to depth
        f"G1 X{_f(x2)}",  # Cut to far X
        f"G1 Y{_f(y2)}",  # Cut to far Y
        f"G1 X0",  # Cut back to near X
        f"G1 Y0",  # Cut back to origin
        "G0 Z{SAFE_Z}"  # Retract (token will be replaced)
    ]

    body = "\n".join(lines).replace("{SAFE_Z}", _f(req.safe_z)) + "\n"

    # Create response
    resp = Response(content=body, media_type="text/plain; charset=utf-8")

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

    return resp


@router.get("/info")
def roughing_info() -> Dict[str, Any]:
    """Get roughing operation information"""
    return {
        "operation": "roughing",
        "description": "Simple rectangular roughing for pocket clearing or face milling",
        "supports_post_processors": HAS_POST_HELPERS,
        "parameters": {
            "width": "Pocket width (mm)",
            "height": "Pocket height (mm)",
            "stepdown": "Depth per pass (mm)",
            "stepover": "Lateral stepover (mm)",
            "feed": "Feed rate (mm/min)",
            "safe_z": "Safe retract height (mm)"
        },
        "post_params": ["post", "post_mode", "machine_id", "rpm", "program_no", "work_offset", "tool"]
    }
