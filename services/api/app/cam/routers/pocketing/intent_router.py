"""
Pocketing Intent Router

CamIntentV1-based endpoint for adaptive pocket-clearing (Dev Order 8J), following
8G/8H/8I. Wraps the L.1 adaptive core (plan_adaptive_l1 / to_toolpath).

Endpoint: POST /api/cam/pocketing/intent-gcode

LANE: OPERATION - normalize_cam_intent_v1, feasibility, RMOS artifact, provenance.

Reconstructed from preserved bytecode. Feasibility (shapely) and the L.1 core are
imported behind availability guards (the original hit a Python 3.14 shapely/numpy
issue; both import cleanly in this environment).
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1
from app.rmos.cam.normalize_intent import (
    normalize_cam_intent_v1,
    CamIntentIssue,
    CamIntentValidationError,
)
from app.cam.pocketing import validate_pocket_design, pocket_params_from_intent

try:
    from app.cam.pocketing.feasibility import (
        compute_pocket_feasibility,
        hash_feasibility_result,
    )
    HAS_FEASIBILITY = True
except ImportError:  # pragma: no cover - shapely/numpy unavailable
    HAS_FEASIBILITY = False

try:
    from app.cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath
    HAS_L1_CORE = True
except ImportError:  # pragma: no cover - pyclipper unavailable
    HAS_L1_CORE = False

from app.rmos.runs_v2 import (
    validate_and_persist,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class PocketingIntentIssue(BaseModel):
    """Normalization issue from CamIntentV1 processing."""

    code: str
    message: str
    path: str = ""


class PocketingIntentMetadata(BaseModel):
    """Metadata from pocketing generation."""

    pocket_area_mm2: float = Field(..., description="Pocket area in mm^2")
    island_count: int = Field(..., description="Number of islands")
    stepover_percent: float = Field(..., description="Stepover percentage")
    estimated_time_seconds: float = Field(..., description="Estimated machining time")


class PocketingIntentResponse(BaseModel):
    """Response from Pocketing intent endpoint."""

    gcode: str = Field(..., description="Generated G-code")
    issues: List[PocketingIntentIssue] = Field(
        default_factory=list,
        description="Normalization issues (soft warnings)",
    )
    run_id: str = Field(..., description="RMOS run artifact ID")
    hashes: Dict[str, str] = Field(default_factory=dict, description="SHA256 hashes for provenance")
    metadata: PocketingIntentMetadata = Field(..., description="Pocketing generation metadata")


def _issues_to_response(issues: List[CamIntentIssue]) -> List[PocketingIntentIssue]:
    """Convert internal issues to response format."""
    return [PocketingIntentIssue(code=i.code, message=i.message, path=i.path) for i in issues]


def _moves_to_gcode(moves: List[Dict[str, Any]]) -> List[str]:
    """Convert an L.1 move list to G-code lines."""
    lines: List[str] = []
    for m in moves:
        seg = m.get("code", "G1")
        if "x" in m:
            seg += f" X{m['x']:.3f}"
        if "y" in m:
            seg += f" Y{m['y']:.3f}"
        if "z" in m:
            seg += f" Z{m['z']:.3f}"
        if "f" in m:
            seg += f" F{m['f']:.0f}"
        lines.append(seg)
    return lines


def _estimate_time(
    path_pts: List,
    feed_xy: float,
    pocket_depth: float,
    stepdown: float,
    plunge_rate: float,
) -> float:
    """Estimate machining time in seconds."""
    if not path_pts:
        return 0.0
    xy = 0.0
    for i in range(1, len(path_pts)):
        xy += math.hypot(path_pts[i][0] - path_pts[i - 1][0], path_pts[i][1] - path_pts[i - 1][1])
    passes = max(1, math.ceil(pocket_depth / stepdown)) if stepdown > 0 else 1
    cut_time = (xy / feed_xy) * 60 * passes if feed_xy > 0 else 0.0
    plunge_time = (pocket_depth / plunge_rate) * 60 if plunge_rate > 0 else 0.0
    return round(cut_time + plunge_time, 1)


@router.post("/intent-gcode", response_model=PocketingIntentResponse)
async def generate_pocketing_intent_gcode(intent: CamIntentV1) -> PocketingIntentResponse:
    """
    Generate adaptive pocket-clearing G-code from CamIntentV1.

    Flow: dependency guards -> normalize -> validate mode -> validate design ->
    adapt -> feasibility -> block-if-infeasible -> L.1 plan + per-pass toolpath ->
    persist -> respond.
    """
    if not HAS_FEASIBILITY:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DEPENDENCY_UNAVAILABLE",
                "message": "Pocketing feasibility requires shapely which is not available (Python 3.14 numpy issue)",
            },
        )
    if not HAS_L1_CORE:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DEPENDENCY_UNAVAILABLE",
                "message": "Pocketing requires L.1 adaptive core which is not available",
            },
        )

    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(intent.model_dump())
    tool_id = intent.tool_id or "pocketing:intent"

    # Step 1: Normalize
    try:
        normalized, issues = normalize_cam_intent_v1(intent, strict=False)
    except CamIntentValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "NORMALIZATION_ERROR",
                "message": str(e),
                "issues": [{"code": i.code, "message": i.message, "path": i.path} for i in e.issues],
            },
        )

    # Step 2: Mode
    if normalized.mode != CamModeV1.ROUTER_3AXIS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_MODE",
                "message": f"Pocketing requires mode=router_3axis, got {normalized.mode.value}",
                "expected": "router_3axis",
                "actual": normalized.mode.value,
            },
        )

    # Step 3: Validate design
    try:
        design = validate_pocket_design(normalized.design)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"error": "INVALID_DESIGN", "message": str(e)})

    # Step 4: Adapt
    try:
        adaptation = pocket_params_from_intent(normalized)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"error": "ADAPTER_ERROR", "message": str(e)})

    boundary = adaptation.loops[0]
    islands = adaptation.loops[1:]

    # Step 5: Feasibility
    feasibility = compute_pocket_feasibility(
        boundary=boundary,
        islands=islands,
        pocket_depth_mm=adaptation.pocket_depth_mm,
        tool_diameter_mm=adaptation.tool_d,
        stepover_percent=design.stepover_percent,
        feed_rate_mm_min=adaptation.feed_xy,
        plunge_rate_mm_min=adaptation.plunge_rate,
        safe_z_mm=adaptation.safe_z,
        retract_z_mm=adaptation.retract_z,
        stepdown_mm=adaptation.stepdown,
        finish_allowance_mm=adaptation.finish_allowance_mm,
    )
    feas_hash = hash_feasibility_result(feasibility)

    # Step 6: Block if infeasible
    if not feasibility.feasible:
        run_id = create_run_id()
        validate_and_persist(
            run_id=run_id,
            mode="pocketing_intent",
            tool_id=tool_id,
            status="BLOCKED",
            request_summary={"event_type": "pocketing_intent_gcode_blocked"},
            feasibility=feasibility.to_dict(),
            feasibility_sha256=feas_hash,
            risk_level=feasibility.risk_level,
            block_reason=f"Blocked by feasibility check: {', '.join(feasibility.issues)}",
            meta={"notes": f"Feasibility issues: {', '.join(feasibility.issues)}"},
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "FEASIBILITY_BLOCKED",
                "message": "Pocketing G-code generation blocked by feasibility check.",
                "run_id": run_id,
                "feasibility": feasibility.to_dict(),
            },
        )

    # Step 7: Plan + generate
    try:
        path = plan_adaptive_l1(
            adaptation.loops,
            adaptation.tool_d,
            adaptation.stepover,
            adaptation.stepdown,
            adaptation.margin,
            adaptation.strategy,
            adaptation.smoothing_radius,
        )
        if not path:
            raise ValueError("L.1 returned empty toolpath")

        depth = adaptation.pocket_depth_mm
        stepdown = adaptation.stepdown
        num_passes = max(1, math.ceil(depth / stepdown)) if stepdown > 0 else 1

        lines: List[str] = [
            "(Pocketing Operation - L.1 Adaptive Core)",
            f"(Pocket depth: {depth}mm in {num_passes} passes)",
            f"(Tool: {adaptation.tool_d}mm, Stepover: {adaptation.stepover * 100:.0f}%)",
            f"(Islands: {len(islands)})",
            "G90 (Absolute positioning)",
            "G21 (Units: mm)",
            "M3 S18000 (Spindle on)",
            "G4 P2 (Dwell for spindle)",
            f"G0 Z{adaptation.safe_z:.3f} (Safe height)",
        ]
        for p in range(1, num_passes + 1):
            z = -min(p * stepdown, depth)
            lines.append(f"(--- Pass {p}: Z = {z:.3f} ---)")
            moves = to_toolpath(path, adaptation.feed_xy, z, adaptation.safe_z)
            lines.extend(_moves_to_gcode(moves))
        lines.append("M5 (Spindle off)")
        lines.append("M30 (Program end)")
        gcode = "\n".join(lines)

        if not gcode.strip():
            raise ValueError("Generated G-code is empty")
    except ValueError as e:
        logger.error("L.1 toolpath generation failed: %s", e, exc_info=True)
        run_id = create_run_id()
        validate_and_persist(
            run_id=run_id,
            mode="pocketing_intent",
            tool_id=tool_id,
            status="ERROR",
            request_summary={"event_type": "pocketing_intent_gcode_execution"},
            feasibility=feasibility.to_dict(),
            feasibility_sha256=feas_hash,
            risk_level=feasibility.risk_level,
            meta={"errors": [f"{type(e).__name__}: {str(e)}"]},
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "TOOLPATH_GENERATION_ERROR",
                "run_id": run_id,
                "message": f"L.1 toolpath generation failed: {str(e)}",
            },
        )

    # Step 8: Persist
    gcode_hash = sha256_of_text(gcode)
    run_id = create_run_id()
    validate_and_persist(
        run_id=run_id,
        mode="pocketing_intent",
        tool_id=tool_id,
        status="OK",
        request_summary={"event_type": "pocketing_intent_gcode_execution"},
        feasibility=feasibility.to_dict(),
        feasibility_sha256=feas_hash,
        risk_level=feasibility.risk_level,
        gcode_sha256=gcode_hash,
    )

    # Step 9: Respond
    return PocketingIntentResponse(
        gcode=gcode,
        issues=_issues_to_response(issues),
        run_id=run_id,
        hashes={
            "request_sha256": request_hash,
            "feasibility_sha256": feas_hash,
            "gcode_sha256": gcode_hash,
        },
        metadata=PocketingIntentMetadata(
            pocket_area_mm2=feasibility.summary.get("pocket_area_mm2", 0.0),
            island_count=len(islands),
            stepover_percent=design.stepover_percent,
            estimated_time_seconds=_estimate_time(
                path, adaptation.feed_xy, depth, stepdown, adaptation.plunge_rate
            ),
        ),
    )
