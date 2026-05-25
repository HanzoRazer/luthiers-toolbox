"""
Pocketing Intent Router

CamIntentV1-based endpoint for Pocketing operations.
Part of the CAM Intent First-Endpoint Migration (ADR-003).

This is the canonical path for Pocketing operations through the unified
CamIntentV1 contract. The legacy endpoints remain live under
Feature Parity Migration Policy until this path is proven.

Endpoint: POST /api/cam/pocketing/intent-gcode

LANE: OPERATION - Uses normalize_cam_intent_v1, runs feasibility,
persists RMOS artifact, writes audit trail.
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
from app.cam.pocketing import (
    validate_pocket_design,
    pocket_params_from_intent,
)

# Feasibility requires shapely which may not be available on Python 3.14
HAS_FEASIBILITY = True
try:
    from app.cam.pocketing import (
        compute_pocket_feasibility,
        hash_feasibility_result,
    )
except ImportError:
    HAS_FEASIBILITY = False
    compute_pocket_feasibility = None
    hash_feasibility_result = None

try:
    from app.cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath
    HAS_L1_CORE = True
except ImportError:
    HAS_L1_CORE = False
    plan_adaptive_l1 = None
    to_toolpath = None
from app.rmos.runs_v2 import (
    RunArtifact,
    RunDecision,
    Hashes,
    persist_run,
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

    pocket_area_mm2: float = Field(..., description="Pocket area in mm²")
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
    hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="SHA256 hashes for provenance",
    )
    metadata: PocketingIntentMetadata = Field(
        ...,
        description="Pocketing generation metadata",
    )


def _issues_to_response(issues: List[CamIntentIssue]) -> List[PocketingIntentIssue]:
    """Convert internal issues to response format."""
    return [
        PocketingIntentIssue(code=i.code, message=i.message, path=i.path)
        for i in issues
    ]


def _moves_to_gcode(moves: List[Dict[str, Any]], spindle_rpm: int = 18000) -> str:
    """Convert L.1 move list to G-code string."""
    lines = [
        "(Pocketing Operation - L.1 Adaptive Core)",
        "G90 (Absolute positioning)",
        "G21 (Units: mm)",
        f"M3 S{spindle_rpm} (Spindle on)",
        "G4 P2 (Dwell for spindle)",
        "",
    ]

    for move in moves:
        code = move.get("code", "G1")
        parts = [code]

        if "x" in move:
            parts.append(f"X{move['x']:.3f}")
        if "y" in move:
            parts.append(f"Y{move['y']:.3f}")
        if "z" in move:
            parts.append(f"Z{move['z']:.3f}")
        if "f" in move:
            parts.append(f"F{move['f']:.0f}")

        lines.append(" ".join(parts))

    lines.extend([
        "",
        "M5 (Spindle off)",
        "M30 (Program end)",
    ])

    return "\n".join(lines)


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

    # Calculate path length
    path_length = 0.0
    for i in range(1, len(path_pts)):
        dx = path_pts[i][0] - path_pts[i - 1][0]
        dy = path_pts[i][1] - path_pts[i - 1][1]
        path_length += math.hypot(dx, dy)

    # Number of depth passes
    pass_count = max(1, int(math.ceil(pocket_depth / stepdown)))

    # Time for XY moves (all passes)
    xy_time = (path_length * pass_count / feed_xy) * 60

    # Time for plunges
    plunge_time = (pocket_depth / plunge_rate) * 60

    # Add overhead
    total = (xy_time + plunge_time) * 1.15

    return total


@router.post("/intent-gcode", response_model=PocketingIntentResponse)
async def generate_pocketing_intent_gcode(intent: CamIntentV1) -> PocketingIntentResponse:
    """
    Generate Pocketing G-code from CamIntentV1.

    LANE: OPERATION - Normalizes intent, validates design, runs feasibility,
    generates toolpath, persists RMOS artifact.

    Flow:
    1. Normalize CamIntentV1 (units conversion, type coercion)
    2. Validate mode == router_3axis
    3. Validate design against PocketDesignV1 schema
    4. Adapt design+context -> L.1 parameters
    5. Run feasibility check (including geometric validity)
    6. Block if feasibility check fails
    7. Generate pocket toolpath via L.1
    8. Convert to G-code
    9. Persist RMOS run artifact
    10. Return JSON with gcode, issues, run_id, hashes, metadata

    Args:
        intent: CamIntentV1 request envelope

    Returns:
        PocketingIntentResponse with gcode, issues, run_id, hashes, metadata

    Raises:
        HTTPException 422: Invalid mode or design
        HTTPException 409: Blocked by feasibility check
        HTTPException 503: If required modules (shapely, numpy) are unavailable
    """
    # Check required dependencies
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

    # Step 1: Normalize intent
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

    # Step 2: Validate mode
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

    # Step 3: Validate design against PocketDesignV1
    try:
        design = validate_pocket_design(normalized.design)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_DESIGN",
                "message": str(e),
            },
        )

    # Step 4: Adapt intent -> L.1 parameters
    try:
        adaptation = pocket_params_from_intent(normalized)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ADAPTER_ERROR",
                "message": str(e),
            },
        )

    # Step 5: Feasibility check (includes geometric validity)
    boundary = adaptation.loops[0]
    islands = adaptation.loops[1:] if len(adaptation.loops) > 1 else []

    feasibility = compute_pocket_feasibility(
        boundary=boundary,
        islands=islands,
        pocket_depth_mm=adaptation.pocket_depth_mm,
        tool_diameter_mm=adaptation.tool_d,
        stepover_percent=adaptation.stepover * 100,  # Convert back to percent
        feed_rate_mm_min=adaptation.feed_xy,
        plunge_rate_mm_min=adaptation.plunge_rate,
        safe_z_mm=adaptation.safe_z,
        retract_z_mm=adaptation.retract_z,
        stepdown_mm=adaptation.stepdown,
        finish_allowance_mm=adaptation.finish_allowance_mm,
    )
    feas_hash = hash_feasibility_result(feasibility)

    # Step 6: Block if feasibility check fails
    if not feasibility.feasible:
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            mode="pocketing_intent",
            event_type="pocketing_intent_gcode_blocked",
            status="BLOCKED",
            feasibility=feasibility.to_dict(),
            decision=RunDecision(
                risk_level=feasibility.risk_level,
                block_reason=f"Blocked by feasibility check: {', '.join(feasibility.issues)}",
            ),
            hashes=Hashes(feasibility_sha256=feas_hash),
            notes=f"Feasibility issues: {', '.join(feasibility.issues)}",
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=409,
            detail={
                "error": "FEASIBILITY_BLOCKED",
                "message": "Pocketing G-code generation blocked by feasibility check.",
                "run_id": run_id,
                "feasibility": feasibility.to_dict(),
            },
        )

    # Step 7: Generate pocket toolpath via L.1
    try:
        path_pts = plan_adaptive_l1(
            loops=adaptation.loops,
            tool_d=adaptation.tool_d,
            stepover=adaptation.stepover,
            stepdown=adaptation.stepdown,
            margin=adaptation.margin,
            strategy=adaptation.strategy,
            smoothing_radius=adaptation.smoothing_radius,
        )

        if not path_pts:
            raise ValueError("L.1 returned empty toolpath")

    except Exception as e:
        logger.error("L.1 toolpath generation failed: %s", e, exc_info=True)
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            mode="pocketing_intent",
            event_type="pocketing_intent_gcode_execution",
            status="ERROR",
            feasibility=feasibility.to_dict(),
            decision=RunDecision(risk_level=feasibility.risk_level),
            hashes=Hashes(feasibility_sha256=feas_hash),
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "TOOLPATH_GENERATION_ERROR",
                "run_id": run_id,
                "message": f"L.1 toolpath generation failed: {str(e)}",
            },
        )

    # Step 8: Generate G-code for each depth pass
    try:
        # Calculate depth passes
        pass_count = max(1, int(math.ceil(
            adaptation.pocket_depth_mm / adaptation.stepdown
        )))

        all_gcode_lines = [
            "(Pocketing Operation - L.1 Adaptive Core)",
            f"(Pocket depth: {adaptation.pocket_depth_mm}mm in {pass_count} passes)",
            f"(Tool: {adaptation.tool_d}mm, Stepover: {adaptation.stepover * 100:.0f}%)",
            f"(Islands: {len(islands)})",
            "",
            "G90 (Absolute positioning)",
            "G21 (Units: mm)",
            "M3 S18000 (Spindle on)",
            "G4 P2 (Dwell for spindle)",
            f"G0 Z{adaptation.safe_z:.3f} (Safe height)",
            "",
        ]

        for pass_num in range(1, pass_count + 1):
            z_depth = -min(
                pass_num * adaptation.stepdown,
                adaptation.pocket_depth_mm,
            )

            all_gcode_lines.append(f"(--- Pass {pass_num}: Z = {z_depth:.3f} ---)")

            moves = to_toolpath(
                path_pts=path_pts,
                feed_xy=adaptation.feed_xy,
                z_rough=z_depth,
                safe_z=adaptation.safe_z,
            )

            for move in moves:
                code = move.get("code", "G1")
                parts = [code]
                if "x" in move:
                    parts.append(f"X{move['x']:.3f}")
                if "y" in move:
                    parts.append(f"Y{move['y']:.3f}")
                if "z" in move:
                    parts.append(f"Z{move['z']:.3f}")
                if "f" in move:
                    parts.append(f"F{move['f']:.0f}")
                all_gcode_lines.append(" ".join(parts))

            all_gcode_lines.append("")

        all_gcode_lines.extend([
            f"G0 Z{adaptation.safe_z:.3f} (Safe height)",
            "M5 (Spindle off)",
            "M30 (Program end)",
        ])

        gcode = "\n".join(all_gcode_lines)

        if not gcode:
            raise ValueError("Generated G-code is empty")

    except Exception as e:
        logger.error("G-code generation failed: %s", e, exc_info=True)
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            mode="pocketing_intent",
            event_type="pocketing_intent_gcode_execution",
            status="ERROR",
            feasibility=feasibility.to_dict(),
            decision=RunDecision(risk_level=feasibility.risk_level),
            hashes=Hashes(feasibility_sha256=feas_hash),
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "GCODE_GENERATION_ERROR",
                "run_id": run_id,
                "message": f"G-code generation failed: {str(e)}",
            },
        )

    # Step 9: Persist RMOS artifact
    gcode_hash = sha256_of_text(gcode)
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id=tool_id,
        mode="pocketing_intent",
        event_type="pocketing_intent_gcode_execution",
        status="OK",
        feasibility=feasibility.to_dict(),
        decision=RunDecision(risk_level=feasibility.risk_level),
        hashes=Hashes(
            feasibility_sha256=feas_hash,
            gcode_sha256=gcode_hash,
        ),
    )
    persist_run(artifact)

    # Estimate time
    estimated_time = _estimate_time(
        path_pts=path_pts,
        feed_xy=adaptation.feed_xy,
        pocket_depth=adaptation.pocket_depth_mm,
        stepdown=adaptation.stepdown,
        plunge_rate=adaptation.plunge_rate,
    )

    # Step 10: Return response
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
            stepover_percent=adaptation.stepover * 100,
            estimated_time_seconds=round(estimated_time, 1),
        ),
    )
