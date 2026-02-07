"""
CAM Drill Pattern Router

LANE: OPERATION (for /gcode endpoint)
LANE: UTILITY (for /info endpoint)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: B (Deterministic) - generates G-code from explicit parameters

Generate drilling patterns (grid, circle, line) with modal cycles.

Migrated from: routers/cam_drill_pattern_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- drill_pattern_gcode_execution (OK/ERROR) - from /gcode
- drill_pattern_gcode_blocked (BLOCKED) - from /gcode when safety policy blocks

Endpoints:
    POST /gcode    - Generate pattern drilling G-code (OPERATION)
    GET  /info     - Get pattern info (UTILITY)
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import cos, pi, sin
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

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


class GridSpec(BaseModel):
    cols: int
    rows: int
    dx: float
    dy: float


class CircleSpec(BaseModel):
    count: int
    radius: float
    start_angle_deg: float = 0.0


class LineSpec(BaseModel):
    count: int
    dx: float
    dy: float


class Pattern(BaseModel):
    type: Literal["grid", "circle", "line"]
    origin_x: float = 0.0
    origin_y: float = 0.0
    grid: Optional[GridSpec] = None
    circle: Optional[CircleSpec] = None
    line: Optional[LineSpec] = None


class DrillParams(BaseModel):
    z: float
    feed: float
    cycle: Literal["G81", "G83"] = "G81"
    r_clear: Optional[float] = None
    peck_q: Optional[float] = None
    dwell_p: Optional[float] = None
    safe_z: float = 5.0
    units: str = "mm"
    post: Optional[str] = None
    post_mode: Optional[str] = None
    machine_id: Optional[str] = None
    rpm: Optional[float] = None
    program_no: Optional[str] = None
    work_offset: Optional[str] = None
    tool: Optional[int] = None


def _f(n: float) -> str:
    return f"{n:.3f}"


def _generate_points(p: Pattern) -> List[tuple]:
    pts = []
    ox, oy = p.origin_x, p.origin_y

    if p.type == "grid" and p.grid:
        for r in range(p.grid.rows):
            for c in range(p.grid.cols):
                pts.append((ox + c * p.grid.dx, oy + r * p.grid.dy))
    elif p.type == "circle" and p.circle:
        n = max(1, p.circle.count)
        for i in range(n):
            ang = (p.circle.start_angle_deg / 180.0 * pi) + 2 * pi * i / n
            pts.append((ox + p.circle.radius * cos(ang), oy + p.circle.radius * sin(ang)))
    elif p.type == "line" and p.line:
        for i in range(p.line.count):
            pts.append((ox + i * p.line.dx, oy + i * p.line.dy))

    return pts


@router.post("/gcode", response_class=Response)
def drill_pattern_gcode(pat: Pattern, prm: DrillParams) -> Response:
    """
    Generate drilling G-code from pattern specification.

    LANE: OPERATION - Creates drill_pattern_gcode_execution artifact.
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj({"pattern": pat.model_dump(), "params": prm.model_dump()})

    # --- Server-side feasibility enforcement (ADR-003 / OPERATION lane) ---
    feasibility = compute_feasibility_internal(
        tool_id="drill_pattern_gcode",
        req={"pattern": pat.model_dump(), "params": prm.model_dump()},
        context="drill_pattern_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="drill_pattern_gcode",
            workflow_mode="drill_pattern",
            event_type="drill_pattern_gcode_blocked",
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
                "message": "Drill pattern G-code generation blocked due to unresolved feasibility concerns.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    try:
        points = _generate_points(pat)

        if HAS_POST_HELPERS:
            ctx = build_post_context_v2(
                post=prm.post,
                post_mode=prm.post_mode,
                units=prm.units,
                machine_id=prm.machine_id,
                RPM=prm.rpm,
                PROGRAM_NO=prm.program_no,
                WORK_OFFSET=prm.work_offset,
                TOOL=prm.tool,
                SAFE_Z=prm.safe_z,
            )

        r_clear = _f(prm.r_clear if prm.r_clear is not None else 5.0)

        lines = [
            "G90",
            f"G0 Z{_f(prm.safe_z)}",
        ]

        cyc = prm.cycle.upper()

        for (x, y) in points:
            if cyc == "G81":
                dwell = f" P{_f(prm.dwell_p)}" if prm.dwell_p is not None else ""
                lines.append(f"G81 X{_f(x)} Y{_f(y)} Z{_f(prm.z)} R{r_clear} F{_f(prm.feed)}{dwell}")
            else:
                peck = _f(prm.peck_q if prm.peck_q is not None else 1.0)
                dwell = f" P{_f(prm.dwell_p)}" if prm.dwell_p is not None else ""
                lines.append(f"G83 X{_f(x)} Y{_f(y)} Z{_f(prm.z)} R{r_clear} Q{peck} F{_f(prm.feed)}{dwell}")

        lines.append("G80")
        body = "\n".join(lines) + "\n"

        # Hash G-code for provenance
        gcode_hash = sha256_of_text(body)

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="drill_pattern_gcode",
            workflow_mode="drill_pattern",
            event_type="drill_pattern_gcode_execution",
            status="OK",
            feasibility=feasibility,
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        resp = Response(content=body, media_type="text/plain; charset=utf-8")
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash

        if HAS_POST_HELPERS:
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
            tool_id="drill_pattern_gcode",
            workflow_mode="drill_pattern",
            event_type="drill_pattern_gcode_execution",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=500,
            detail={
                "error": "DRILL_PATTERN_GCODE_ERROR",
                "run_id": run_id,
                "message": str(e),
            },
        )


@router.get("/info")
def pattern_info() -> Dict[str, Any]:
    """
    Get drill pattern information.

    LANE: UTILITY - Info only, no artifacts.
    """
    return {
        "operation": "drill_pattern",
        "description": "Generate drilling patterns (grid, circle, line) with modal cycles",
        "supports_post_processors": HAS_POST_HELPERS,
    }
