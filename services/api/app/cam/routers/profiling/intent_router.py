"""
Profile Intent Router

CamIntentV1-based endpoint for Profile operations.
Part of the CAM Intent First-Endpoint Migration (ADR-003).

This is the canonical path for Profile operations through the unified
CamIntentV1 contract. The legacy /gcode endpoint remains live under
Feature Parity Migration Policy until this path is proven.

Endpoint: POST /api/cam/profiling/intent-gcode

LANE: OPERATION - Uses normalize_cam_intent_v1, runs feasibility,
persists RMOS artifact, writes audit trail.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1
from app.rmos.cam.normalize_intent import (
    normalize_cam_intent_v1,
    CamIntentIssue,
    CamIntentValidationError,
)
from app.cam.profiling import (
    ProfileToolpath,
    ProfileConfig,
)
from app.cam.profiling.intent_schema import validate_profile_design
from app.cam.profiling.intent_adapter import profile_params_from_intent
from app.cam.profiling.feasibility import (
    compute_profile_feasibility,
    hash_feasibility_result,
)
from app.rmos.runs_v2 import (
    validate_and_persist,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ProfileIntentIssue(BaseModel):
    """Normalization issue from CamIntentV1 processing."""

    code: str
    message: str
    path: str = ""


class ProfileIntentMetadata(BaseModel):
    """Metadata from profile generation."""

    pass_count: int = Field(..., description="Number of machining passes")
    tab_count: int = Field(..., description="Number of holding tabs")
    total_length_mm: float = Field(..., description="Total toolpath length")
    estimated_time_seconds: float = Field(..., description="Estimated machining time")


class ProfileIntentResponse(BaseModel):
    """Response from Profile intent endpoint."""

    gcode: str = Field(..., description="Generated G-code")
    issues: List[ProfileIntentIssue] = Field(
        default_factory=list,
        description="Normalization issues (soft warnings)",
    )
    run_id: str = Field(..., description="RMOS run artifact ID")
    hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="SHA256 hashes for provenance",
    )
    metadata: ProfileIntentMetadata = Field(
        ...,
        description="Profile generation metadata",
    )


def _issues_to_response(issues: List[CamIntentIssue]) -> List[ProfileIntentIssue]:
    """Convert internal issues to response format."""
    return [
        ProfileIntentIssue(code=i.code, message=i.message, path=i.path)
        for i in issues
    ]


@router.post("/intent-gcode", response_model=ProfileIntentResponse)
async def generate_profile_intent_gcode(intent: CamIntentV1) -> ProfileIntentResponse:
    """
    Generate Profile G-code from CamIntentV1.

    LANE: OPERATION - Normalizes intent, validates design, runs feasibility,
    generates toolpath, persists RMOS artifact.

    Flow:
    1. Normalize CamIntentV1 (units conversion, type coercion)
    2. Validate mode == router_3axis
    3. Validate design against ProfileDesignV1 schema
    4. Adapt design+context → ProfileConfig
    5. Run feasibility check
    6. Block if feasibility check fails
    7. Generate toolpath
    8. Persist RMOS run artifact
    9. Return JSON with gcode, issues, run_id, hashes, metadata

    Args:
        intent: CamIntentV1 request envelope

    Returns:
        ProfileIntentResponse with gcode, issues, run_id, hashes, metadata

    Raises:
        HTTPException 422: Invalid mode or design
        HTTPException 409: Blocked by feasibility check
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(intent.model_dump())
    tool_id = intent.tool_id or "profile:intent"

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
                "message": f"Profile requires mode=router_3axis, got {normalized.mode.value}",
                "expected": "router_3axis",
                "actual": normalized.mode.value,
            },
        )

    # Step 3: Validate design against ProfileDesignV1
    try:
        design = validate_profile_design(normalized.design)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_DESIGN",
                "message": str(e),
            },
        )

    # Step 4: Adapt intent → ProfileConfig + outline
    try:
        outline, config, is_closed = profile_params_from_intent(normalized)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ADAPTER_ERROR",
                "message": str(e),
            },
        )

    # Step 5: Feasibility check
    context = normalized.context or {}
    feasibility = compute_profile_feasibility(
        tool_diameter_mm=config.tool_diameter_mm,
        cut_depth_mm=config.cut_depth_mm,
        stepdown_mm=config.stepdown_mm,
        feed_rate_mm_min=config.feed_rate_xy,
        plunge_rate_mm_min=config.plunge_rate,
        safe_z_mm=config.safe_z_mm,
        retract_z_mm=config.retract_z_mm,
        contour_point_count=len(outline),
        tab_count=config.tab_count,
        tab_height_mm=config.tab_height_mm,
        use_tabs=config.tab_count > 0,
        finishing_pass=config.finishing_pass,
        finishing_allowance_mm=config.finishing_allowance_mm,
    )
    feas_hash = hash_feasibility_result(feasibility)

    # Step 6: Block if feasibility check fails
    if not feasibility.feasible:
        run_id = create_run_id()
        validate_and_persist(
            run_id=run_id,
            mode="profile_intent",
            tool_id=tool_id,
            status="BLOCKED",
            request_summary={"event_type": "profile_intent_gcode_blocked"},
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
                "message": "Profile G-code generation blocked by feasibility check.",
                "run_id": run_id,
                "feasibility": feasibility.to_dict(),
            },
        )

    # Step 7: Generate toolpath
    try:
        profiler = ProfileToolpath(
            outline=outline,
            config=config,
        )
        result = profiler.generate()
        gcode = result.gcode

        if not gcode:
            raise ValueError("Generated G-code is empty")

    except Exception as e:
        logger.error("Profile toolpath generation failed: %s", e, exc_info=True)
        run_id = create_run_id()
        validate_and_persist(
            run_id=run_id,
            mode="profile_intent",
            tool_id=tool_id,
            status="ERROR",
            request_summary={"event_type": "profile_intent_gcode_execution"},
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
                "message": f"Toolpath generation failed: {str(e)}",
            },
        )

    # Step 8: Persist RMOS artifact
    gcode_hash = sha256_of_text(gcode)
    run_id = create_run_id()
    validate_and_persist(
        run_id=run_id,
        mode="profile_intent",
        tool_id=tool_id,
        status="OK",
        request_summary={"event_type": "profile_intent_gcode_execution"},
        feasibility=feasibility.to_dict(),
        feasibility_sha256=feas_hash,
        risk_level=feasibility.risk_level,
        gcode_sha256=gcode_hash,
    )

    # Step 9: Return response
    return ProfileIntentResponse(
        gcode=gcode,
        issues=_issues_to_response(issues),
        run_id=run_id,
        hashes={
            "request_sha256": request_hash,
            "feasibility_sha256": feas_hash,
            "gcode_sha256": gcode_hash,
        },
        metadata=ProfileIntentMetadata(
            pass_count=result.pass_count,
            tab_count=config.tab_count,
            total_length_mm=result.total_length_mm,
            estimated_time_seconds=result.estimated_time_seconds,
        ),
    )
