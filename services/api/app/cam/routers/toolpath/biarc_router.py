"""
CAM Bi-Arc Router

LANE: OPERATION (for /gcode endpoint)
LANE: UTILITY (for /info endpoint)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: B (Deterministic) - generates G-code from explicit parameters

Simple contour following from point array with post-processor support.

Migrated from: routers/cam_biarc_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- biarc_gcode_execution (OK/ERROR) - from /gcode
- biarc_gcode_blocked (BLOCKED) - from /gcode when safety policy blocks

Endpoints:
    POST /gcode    - Generate contour-following G-code (OPERATION)
    GET  /info     - Get operation information (UTILITY)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

# Import post injection utilities
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

# Import feasibility functions (Phase 2: server-side enforcement)
from ....rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ....rmos.policies import SafetyPolicy

router = APIRouter()


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


@router.post("/gcode", response_class=Response)
def biarc_gcode(req: BiarcReq) -> Response:
    """
    Generate contour-following G-code from point array.

    LANE: OPERATION - Creates biarc_gcode_execution artifact.

    Process:
    1. Rapid to safe height
    2. Rapid to first point (XY)
    3. Plunge to cutting depth
    4. Linear interpolation through all points
    5. Retract to safe height

    Note: "Bi-arc" name is historical; currently generates linear moves (G1).
    Future enhancement: Fit bi-arc splines for smoother paths.
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump())

    # --- Server-side feasibility enforcement (ADR-003 / OPERATION lane) ---
    feasibility = compute_feasibility_internal(
        tool_id="biarc_gcode",
        req=req,
        context="biarc_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="biarc_gcode",
            workflow_mode="biarc",
            event_type="biarc_gcode_blocked",
            status="BLOCKED",
            feasibility=feasibility,
            request_hash=feas_hash,
            notes=f"Blocked by safety policy: {risk_level}",
        )
        persist_run(artifact)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "Bi-arc G-code generation blocked due to unresolved feasibility concerns.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    try:
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

        body = "\n".join(lines) + "\n"

        # Hash G-code for provenance
        gcode_hash = sha256_of_text(body)

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="biarc_gcode",
            workflow_mode="biarc",
            event_type="biarc_gcode_execution",
            status="OK",
            feasibility=feasibility,
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

    except HTTPException:
        raise  # WP-1: pass through HTTPException (e.g. 409 SAFETY_BLOCKED)
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        # Create ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="biarc_gcode",
            workflow_mode="biarc",
            event_type="biarc_gcode_execution",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=500,
            detail={
                "error": "BIARC_GCODE_ERROR",
                "run_id": run_id,
                "message": str(e),
            },
        )


@router.get("/info")
def biarc_info() -> Dict[str, Any]:
    """
    Get bi-arc operation information.

    LANE: UTILITY - Info only, no artifacts.
    """
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
