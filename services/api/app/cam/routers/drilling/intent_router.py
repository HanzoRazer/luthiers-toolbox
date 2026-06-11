"""
Drilling Intent Router

CamIntentV1-based endpoint for peck-drilling operations.
Part of the CAM Intent First-Endpoint Migration (Dev Order 8I), following 8G/8H.

Canonical path for Drilling through the unified CamIntentV1 contract. The legacy
drilling endpoints remain live under Feature Parity Migration Policy.

Endpoint: POST /api/cam/drilling/intent-gcode

LANE: OPERATION - Uses normalize_cam_intent_v1, runs feasibility, persists RMOS
artifact, returns provenance hashes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List

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
    validate_and_persist,
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
    total_depth_mm: float = Field(..., description="Sum of hole depths")
    estimated_time_seconds: float = Field(..., description="Estimated drilling time")
    risk_level: str = Field(..., description="Feasibility risk level")


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
    Generate peck-drilling G-code from CamIntentV1.

    LANE: OPERATION - Normalizes intent, validates design, runs feasibility,
    generates toolpath, persists RMOS artifact.

    Flow: normalize -> validate mode -> validate design -> adapt -> feasibility ->
    block-if-infeasible -> generate -> persist -> respond.
    """
    now = datetime.now(timezone.utc).isoformat()  # noqa: F841 — kept for future audit fields
    request_hash = sha256_of_obj(intent.model_dump())
    tool_id = intent.tool_id or "drill:intent"

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
            detail={"error": "INVALID_DESIGN", "message": str(e)},
        )

    # Step 4: Adapt intent -> holes + DrillConfig
    try:
        holes, config = drilling_params_from_intent(normalized)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "ADAPTER_ERROR", "message": str(e)},
        )

    # Step 5: Feasibility check
    feasibility = compute_drilling_feasibility(
        hole_depth_mm=design.hole_depth_mm,
        hole_diameter_mm=design.hole_diameter_mm,
        peck_drilling=design.peck_drilling,
        peck_depth_mm=design.peck_depth_mm,
        hole_count=len(holes),
        feed_rate_mm_min=config.feed_rate,
        spindle_rpm=config.spindle_rpm,
        safe_z_mm=config.safe_z_mm,
        retract_z_mm=config.retract_z_mm,
    )
    feas_hash = hash_feasibility_result(feasibility)

    # Step 6: Block if infeasible
    if not feasibility.feasible:
        run_id = create_run_id()
        validate_and_persist(
            run_id=run_id,
            mode="drilling_intent",
            tool_id=tool_id,
            status="BLOCKED",
            request_summary={"event_type": "drilling_intent_gcode_blocked"},
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
                "message": "Drilling G-code generation blocked by feasibility check.",
                "run_id": run_id,
                "feasibility": feasibility.to_dict(),
            },
        )

    # Step 7: Generate toolpath
    try:
        result = PeckDrill(holes=holes, config=config).generate()
        gcode = result.gcode
        if not gcode:
            raise ValueError("Generated G-code is empty")
    except Exception as e:
        logger.error("Drilling toolpath generation failed: %s", e, exc_info=True)
        run_id = create_run_id()
        validate_and_persist(
            run_id=run_id,
            mode="drilling_intent",
            tool_id=tool_id,
            status="ERROR",
            request_summary={"event_type": "drilling_intent_gcode_execution"},
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
        mode="drilling_intent",
        tool_id=tool_id,
        status="OK",
        request_summary={"event_type": "drilling_intent_gcode_execution"},
        feasibility=feasibility.to_dict(),
        feasibility_sha256=feas_hash,
        risk_level=feasibility.risk_level,
        gcode_sha256=gcode_hash,
    )

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
            risk_level=feasibility.risk_level,
        ),
    )
