"""
CAM Roughing Router

LANE: OPERATION (for /gcode endpoint)
LANE: UTILITY (for /info endpoint)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: B (Deterministic) - generates G-code from explicit parameters

Simple rectangular roughing G-code generator with post-processor support.

Migrated from: routers/cam_roughing_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

GOVERNANCE INVARIANTS:
1. /gcode endpoint creates a run artifact (OK or ERROR)
2. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- roughing_gcode_execution (OK/ERROR) - from /gcode

Endpoints:
    POST /gcode    - Generate rectangular roughing G-code (OPERATION)
    GET  /info     - Get operation information (UTILITY)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

# Import post injection utilities (already in codebase from Phase 2)
try:
    from ....util.post_injection_helpers import build_post_context_v2, wrap_with_post_v2
    HAS_POST_HELPERS = True
except ImportError:
    HAS_POST_HELPERS = False

# Import run artifact persistence (OPERATION lane requirement)
from ....rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

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

    LANE: OPERATION - Creates roughing_gcode_execution artifact.

    Pattern: Move to origin, plunge, mill rectangular boundary, retract.
    Suitable for basic pocket roughing or face milling.
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump())

    try:
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
            f"G0 Z{_f(req.safe_z)}"  # Retract
        ]

        body = "\n".join(lines) + "\n"

        # Hash G-code for provenance
        gcode_hash = sha256_of_text(body)

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="roughing_gcode",
            workflow_mode="roughing",
            event_type="roughing_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        # Create response
        resp = Response(content=body, media_type="text/plain; charset=utf-8")
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash

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

    except Exception as e:
        # Create ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="roughing_gcode",
            workflow_mode="roughing",
            event_type="roughing_gcode_execution",
            status="ERROR",
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=500,
            detail={
                "error": "ROUGHING_GCODE_ERROR",
                "run_id": run_id,
                "message": str(e),
            },
        )


@router.get("/info")
def roughing_info() -> Dict[str, Any]:
    """
    Get roughing operation information.

    LANE: UTILITY - Info only, no artifacts.
    """
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
