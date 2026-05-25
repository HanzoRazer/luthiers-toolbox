"""
Drilling Intent Router

CamIntentV1-based endpoint for Drilling operations.
Part of the CAM Intent First-Endpoint Migration (ADR-003).

This is the canonical path for Drilling operations through the unified
CamIntentV1 contract. The legacy /gcode endpoint remains live under
Feature Parity Migration Policy until this path is proven.

Endpoint: POST /api/cam/drilling/intent-gcode

LANE: OPERATION - Uses normalize_cam_intent_v1, runs feasibility,
persists RMOS artifact, writes audit trail.
"""
from __future__ import annotations

import logging
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
from app.cam.drilling import PeckDrill
from app.cam.drilling.intent_schema import validate_drilling_design
from app.cam.drilling.intent_adapter import drilling_params_from_intent
from app.cam.drilling.feasibility import (
    compute_drilling_feasibility,
    hash_feasibility_result,
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

logger = logging.getLogger(__name__)

router = APIRouter()


class DrillingIntentIssue(BaseModel):
    """Normalization issue from CamIntentV1 processing."""

    code: str
    message: str
    path: str = ""


class DrillingIntentMetadata(BaseModel):
    """Metadata from drilling generation."""

    hole_count: int = Field(..., description="Number of holes drilled")
    total_depth_mm: float = Field(..., description="Sum of all hole depths")
    estimated_time_seconds: float = Field(..., description="Estimated drilling time")


class DrillingIntentResponse(BaseModel):
    """Response from Drilling intent endpoint."""

    gcode: str = Field(..., description="Generated G-code")
    issues: List[DrillingIntentIssue] = Field(
        default_factory=list,
        description="Normalization issues (soft warnings)",
    )
    run_id: str = Field(..., description="RMOS run artifact ID")
    hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="SHA256 hashes for provenance",
    )
    metadata: DrillingIntentMetadata = Field(
        ...,
        description="Drilling generation metadata",
    )


def _issues_to_response(issues: List[CamIntentIssue]) -> List[DrillingIntentIssue]:
    """Convert internal issues to response format."""
    return [
        DrillingIntentIssue(code=i.code, message=i.message, path=i.path)
        for i in issues
    ]


@router.post("/intent-gcode", response_model=DrillingIntentResponse)
async def generate_drilling_intent_gcode(intent: CamIntentV1) -> DrillingIntentResponse:
    """
    Generate Drilling G-code from CamIntentV1.

    LANE: OPERATION - Normalizes intent, validates design, runs feasibility,
    generates toolpath, persists RMOS artifact.

    Flow:
    1. Normalize CamIntentV1 (units conversion, type coercion)
    2. Validate mode == router_3axis
    3. Validate design against DrillingDesignV1 schema
    4. Adapt design+context -> DrillConfig + holes
    5. Run feasibility check
    6. Block if feasibility check fails
    7. Generate drilling G-code
    8. Persist RMOS run artifact
    9. Return JSON with gcode, issues, run_id, hashes, metadata

    Args:
        intent: CamIntentV1 request envelope

    Returns:
        DrillingIntentResponse with gcode, issues, run_id, hashes, metadata

    Raises:
        HTTPException 422: Invalid mode or design
        HTTPException 409: Blocked by feasibility check
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(intent.model_dump())
    tool_id = intent.tool_id or "drilling:intent"

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
                "message": f"Drilling requires mode=router_3axis, got {normalized.mode.value}",
                "expected": "router_3axis",
                "actual": normalized.mode.value,
            },
        )

    # Step 3: Validate design against DrillingDesignV1
    try:
        design = validate_drilling_design(normalized.design)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_DESIGN",
                "message": str(e),
            },
        )

    # Step 4: Adapt intent -> DrillConfig + holes
    try:
        holes, config = drilling_params_from_intent(normalized)
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
    feasibility = compute_drilling_feasibility(
        hole_depth_mm=config.hole_depth_mm,
        hole_diameter_mm=config.drill_diameter_mm,
        peck_depth_mm=config.peck_depth_mm,
        peck_drilling=config.use_canned_cycle,
        feed_rate_mm_min=config.feed_rate,
        spindle_rpm=config.spindle_rpm,
        safe_z_mm=config.safe_z_mm,
        retract_z_mm=config.retract_z_mm,
        hole_count=len(holes),
        dwell_ms=config.dwell_ms,
    )
    feas_hash = hash_feasibility_result(feasibility)

    # Step 6: Block if feasibility check fails
    if not feasibility.feasible:
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            mode="drilling_intent",
            event_type="drilling_intent_gcode_blocked",
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
                "message": "Drilling G-code generation blocked by feasibility check.",
                "run_id": run_id,
                "feasibility": feasibility.to_dict(),
            },
        )

    # Step 7: Generate drilling G-code
    try:
        drill = PeckDrill(holes=holes, config=config)
        result = drill.generate()
        gcode = result.gcode

        if not gcode:
            raise ValueError("Generated G-code is empty")

    except Exception as e:
        logger.error("Drilling G-code generation failed: %s", e, exc_info=True)
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            mode="drilling_intent",
            event_type="drilling_intent_gcode_execution",
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

    # Step 8: Persist RMOS artifact
    gcode_hash = sha256_of_text(gcode)
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id=tool_id,
        mode="drilling_intent",
        event_type="drilling_intent_gcode_execution",
        status="OK",
        feasibility=feasibility.to_dict(),
        decision=RunDecision(risk_level=feasibility.risk_level),
        hashes=Hashes(
            feasibility_sha256=feas_hash,
            gcode_sha256=gcode_hash,
        ),
    )
    persist_run(artifact)

    # Step 9: Return response
    return DrillingIntentResponse(
        gcode=gcode,
        issues=_issues_to_response(issues),
        run_id=run_id,
        hashes={
            "request_sha256": request_hash,
            "feasibility_sha256": feas_hash,
            "gcode_sha256": gcode_hash,
        },
        metadata=DrillingIntentMetadata(
            hole_count=result.hole_count,
            total_depth_mm=result.total_depth_mm,
            estimated_time_seconds=result.estimated_time_seconds,
        ),
    )
