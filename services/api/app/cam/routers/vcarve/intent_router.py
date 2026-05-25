"""
V-Carve Intent Router

CamIntentV1-based endpoint for V-Carve operations.
Part of the CAM Intent First-Endpoint Migration (ADR-003).

This is the canonical path for V-Carve operations through the unified
CamIntentV1 contract. The legacy /gcode endpoint remains live under
Feature Parity Migration Policy until this path is proven.

Endpoint: POST /api/cam/vcarve/intent-gcode

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
from app.cam.vcarve import (
    VCarveToolpath,
    vcarve_params_from_intent,
    validate_vcarve_design,
)
from app.rmos.runs_v2 import (
    RunArtifact,
    RunDecision,
    Hashes,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)
from app.rmos.api.rmos_feasibility_router import compute_feasibility_internal
from app.rmos.policies import SafetyPolicy

logger = logging.getLogger(__name__)

router = APIRouter()


class VCarveIntentIssue(BaseModel):
    """Normalization issue from CamIntentV1 processing."""

    code: str
    message: str
    path: str = ""


class VCarveIntentResponse(BaseModel):
    """Response from V-Carve intent endpoint."""

    gcode: str = Field(..., description="Generated G-code")
    issues: List[VCarveIntentIssue] = Field(
        default_factory=list,
        description="Normalization issues (soft warnings)",
    )
    run_id: str = Field(..., description="RMOS run artifact ID")
    hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="SHA256 hashes for provenance",
    )


def _issues_to_response(issues: List[CamIntentIssue]) -> List[VCarveIntentIssue]:
    """Convert internal issues to response format."""
    return [
        VCarveIntentIssue(code=i.code, message=i.message, path=i.path)
        for i in issues
    ]


@router.post("/intent-gcode", response_model=VCarveIntentResponse)
async def generate_vcarve_intent_gcode(intent: CamIntentV1) -> VCarveIntentResponse:
    """
    Generate V-Carve G-code from CamIntentV1.

    LANE: OPERATION - Normalizes intent, validates design, runs feasibility,
    generates toolpath, persists RMOS artifact.

    Flow:
    1. Normalize CamIntentV1 (units conversion, type coercion)
    2. Validate mode == router_3axis
    3. Validate design against VCarveDesignV1 schema
    4. Adapt design+context → VCarveConfig
    5. Run feasibility check (same as legacy endpoint)
    6. Generate toolpath
    7. Persist RMOS run artifact
    8. Return JSON with gcode, issues, run_id, hashes

    Args:
        intent: CamIntentV1 request envelope

    Returns:
        VCarveIntentResponse with gcode, issues, run_id, hashes

    Raises:
        HTTPException 422: Invalid mode or design
        HTTPException 409: Blocked by safety policy
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(intent.model_dump())
    tool_id = intent.tool_id or "vcarve:intent"

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
                "message": f"V-Carve requires mode=router_3axis, got {normalized.mode.value}",
                "expected": "router_3axis",
                "actual": normalized.mode.value,
            },
        )

    # Step 3: Validate design against VCarveDesignV1
    try:
        validate_vcarve_design(normalized.design)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_DESIGN",
                "message": str(e),
            },
        )

    # Step 4: Adapt intent → VCarveConfig + paths
    try:
        config, ml_paths = vcarve_params_from_intent(normalized)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ADAPTER_ERROR",
                "message": str(e),
            },
        )

    # Step 5: Feasibility check (same as legacy endpoint)
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req={
            "tool_id": tool_id,
            "material_id": normalized.material_id,
            "depth_mm": config.target_depth_mm or config.target_line_width_mm,
            "bit_angle_deg": config.bit_angle_deg,
            "feed_rate_mm_min": config.feed_rate_mm_min or 800.0,
        },
        context="vcarve_intent_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    # Block if safety policy requires
    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            mode="vcarve_intent",
            event_type="vcarve_intent_gcode_blocked",
            status="BLOCKED",
            feasibility=feasibility,
            decision=RunDecision(
                risk_level=risk_level,
                block_reason=f"Blocked by safety policy: {risk_level}",
            ),
            hashes=Hashes(feasibility_sha256=feas_hash),
            notes=f"Blocked by safety policy: {risk_level}",
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "V-Carve G-code generation blocked by safety policy.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    # Step 6: Generate toolpath
    try:
        vcarve = VCarveToolpath(paths=ml_paths, config=config)
        result = vcarve.generate()
        gcode = result.gcode

        if not gcode:
            raise ValueError("Generated G-code is empty")

    except Exception as e:
        logger.error("V-Carve toolpath generation failed: %s", e, exc_info=True)
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            mode="vcarve_intent",
            event_type="vcarve_intent_gcode_execution",
            status="ERROR",
            feasibility=feasibility,
            decision=RunDecision(risk_level=risk_level),
            hashes=Hashes(feasibility_sha256=feas_hash),
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "TOOLPATH_GENERATION_ERROR",
                "run_id": run_id,
                "message": f"Toolpath generation failed: {str(e)}",
            },
        )

    # Step 7: Persist RMOS artifact
    gcode_hash = sha256_of_text(gcode)
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id=tool_id,
        mode="vcarve_intent",
        event_type="vcarve_intent_gcode_execution",
        status="OK",
        feasibility=feasibility,
        decision=RunDecision(risk_level=risk_level),
        hashes=Hashes(
            feasibility_sha256=feas_hash,
            gcode_sha256=gcode_hash,
        ),
    )
    persist_run(artifact)

    # Step 8: Return response
    return VCarveIntentResponse(
        gcode=gcode,
        issues=_issues_to_response(issues),
        run_id=run_id,
        hashes={
            "request_sha256": request_hash,
            "feasibility_sha256": feas_hash,
            "gcode_sha256": gcode_hash,
        },
    )
