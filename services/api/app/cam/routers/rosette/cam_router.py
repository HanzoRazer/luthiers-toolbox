"""
Rosette CAM Router

LANE: OPERATION
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: A (Planning) - generates toolpaths from geometry

Toolpath planning, G-code generation, and job management for rosette designs.

Extracted from: routers/art_studio_rosette_router.py (lines 679-807)

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- rosette_toolpath_plan (OK/ERROR) - from /plan-toolpath
- rosette_toolpath_blocked (BLOCKED) - from /plan-toolpath when safety policy blocks
- rosette_gcode_post (OK/ERROR) - from /post-gcode
- rosette_gcode_blocked (BLOCKED) - from /post-gcode when safety policy blocks

Endpoints:
    POST /plan-toolpath     - Generate toolpath moves from rosette geometry
    POST /post-gcode        - Convert toolpath moves to G-code
    POST /jobs              - Create CAM job for pipeline handoff
    GET  /jobs/{job_id}     - Retrieve CAM job details
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import CAM bridge and job store
from ....services.rosette_cam_bridge import (
    plan_rosette_toolpath,
    postprocess_toolpath_grbl,
    RosetteGeometry,
    CamParams,
)
from ....services.art_jobs_store import create_art_job, get_art_job

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


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class RosetteToolpathPlanRequest(BaseModel):
    """Request to generate toolpath for a rosette design."""
    center_x: float = Field(0.0, description="Center X coordinate")
    center_y: float = Field(0.0, description="Center Y coordinate")
    inner_radius: float = Field(..., gt=0, description="Inner radius (mm)")
    outer_radius: float = Field(..., gt=0, description="Outer radius (mm)")
    units: str = Field("mm", description="Units (mm or inch)")

    tool_d: float = Field(..., gt=0, description="Tool diameter (mm)")
    stepover: float = Field(0.45, ge=0.1, le=0.9, description="Stepover as fraction (0.1-0.9)")
    stepdown: float = Field(1.5, gt=0, description="Stepdown per pass (mm)")
    feed_xy: float = Field(1200, gt=0, description="XY feed rate (mm/min)")
    feed_z: float = Field(400, gt=0, description="Z plunge rate (mm/min)")
    safe_z: float = Field(5, gt=0, description="Safe retract Z (mm)")
    cut_depth: float = Field(3.0, gt=0, description="Total cut depth (mm)")
    circle_segments: int = Field(64, ge=16, le=256, description="Circle approximation segments")

    # Feasibility context (Phase 2)
    tool_id: Optional[str] = Field(default="rosette:default", description="Tool identifier for feasibility lookup")
    material_id: Optional[str] = Field(default=None, description="Material identifier for feasibility assessment")


class RosetteToolpathPlanResponse(BaseModel):
    """Response with planned toolpath moves and stats."""
    moves: List[Dict[str, Any]] = Field(..., description="Neutral toolpath moves")
    stats: Dict[str, Any] = Field(..., description="Toolpath statistics")
    run_id: Optional[str] = Field(None, description="Run artifact ID for audit trail")
    hashes: Optional[Dict[str, str]] = Field(None, description="SHA256 hashes for provenance")


class RosettePostGcodeRequest(BaseModel):
    """Request to generate G-code from toolpath moves."""
    moves: List[Dict[str, Any]] = Field(..., description="Toolpath moves to convert")
    units: str = Field("mm", description="Units (mm or inch)")
    spindle_rpm: int = Field(18000, ge=0, description="Spindle RPM")

    # Feasibility context (Phase 2)
    tool_id: Optional[str] = Field(default="rosette:default", description="Tool identifier for feasibility lookup")
    material_id: Optional[str] = Field(default=None, description="Material identifier for feasibility assessment")


class RosettePostGcodeResponse(BaseModel):
    """Response with generated G-code and stats."""
    gcode: str = Field(..., description="Generated G-code text")
    stats: Dict[str, Any] = Field(..., description="G-code statistics")
    run_id: Optional[str] = Field(None, description="Run artifact ID for audit trail")
    hashes: Optional[Dict[str, str]] = Field(None, description="SHA256 hashes for provenance")


class RosetteCamJobCreateRequest(BaseModel):
    """Request to create a CAM job for pipeline handoff."""
    job_id: str = Field(..., description="Unique job ID")
    post_preset: str = Field("grbl", description="Post-processor preset (grbl, mach4, etc.)")
    rings: int = Field(..., gt=0, description="Number of radial passes")
    z_passes: int = Field(..., gt=0, description="Number of Z passes")
    length_mm: float = Field(..., gt=0, description="Total toolpath length (mm)")
    gcode_lines: int = Field(..., gt=0, description="Number of G-code lines")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RosetteCamJobIdResponse(BaseModel):
    """Response with created job ID."""
    job_id: str
    message: str


class RosetteCamJobResponse(BaseModel):
    """Response with full job details."""
    id: str
    job_type: str
    created_at: str
    post_preset: str
    rings: int
    z_passes: int
    length_mm: float
    gcode_lines: int
    meta: Dict[str, Any]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/plan-toolpath", response_model=RosetteToolpathPlanResponse)
def plan_rosette_cam_toolpath(body: RosetteToolpathPlanRequest) -> Dict[str, Any]:
    """
    Generate toolpath moves for a rosette design.

    LANE: OPERATION - Creates rosette_toolpath_plan or rosette_toolpath_blocked artifact

    Flow:
    1. Recompute feasibility server-side (NEVER trust client)
    2. Block if RED/UNKNOWN (HTTP 409)
    3. Generate toolpath if safe
    4. Persist run artifact for audit trail
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(body.model_dump())
    tool_id = body.tool_id or "rosette:default"

    # Phase 2: Server-side feasibility enforcement
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req={
            "tool_id": tool_id,
            "material_id": body.material_id,
            "outer_diameter_mm": body.outer_radius * 2,
            "inner_diameter_mm": body.inner_radius * 2,
            "depth_mm": body.cut_depth,
            "feed_rate_mm_min": body.feed_xy,
        },
        context="rosette_toolpath",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    # Block if policy requires (BLOCKED artifact)
    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="rosette",
            event_type="rosette_toolpath_blocked",
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
                "message": "Rosette toolpath planning blocked by server-side safety policy.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    try:
        geom = RosetteGeometry(
            center_x=body.center_x,
            center_y=body.center_y,
            inner_radius=body.inner_radius,
            outer_radius=body.outer_radius,
            units=body.units,
        )

        params = CamParams(
            tool_d=body.tool_d,
            stepover=body.stepover,
            stepdown=body.stepdown,
            feed_xy=body.feed_xy,
            feed_z=body.feed_z,
            safe_z=body.safe_z,
            cut_depth=body.cut_depth,
        )

        moves, stats = plan_rosette_toolpath(geom, params, circle_segments=body.circle_segments)

        # Hash outputs for provenance
        moves_hash = sha256_of_obj(moves)
        stats_hash = sha256_of_obj(stats)

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="rosette",
            event_type="rosette_toolpath_plan",
            status="OK",
            feasibility=feasibility,
            request_hash=request_hash,
            toolpaths_hash=moves_hash,
        )
        persist_run(artifact)

        return {
            "moves": moves,
            "stats": stats,
            "_run_id": run_id,
            "_hashes": {
                "request_sha256": request_hash,
                "feasibility_sha256": feas_hash,
                "moves_sha256": moves_hash,
                "stats_sha256": stats_hash,
            },
        }

    except HTTPException:
        raise  # WP-1: pass through HTTPException (e.g. 409 SAFETY_BLOCKED)
    except Exception as e:
        # Create ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="rosette",
            event_type="rosette_toolpath_plan",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "TOOLPATH_PLAN_ERROR",
                "run_id": run_id,
                "message": f"Toolpath planning failed: {str(e)}",
            },
        )


@router.post("/post-gcode", response_model=RosettePostGcodeResponse)
def post_rosette_gcode(body: RosettePostGcodeRequest) -> Dict[str, Any]:
    """
    Generate G-code from toolpath moves.

    LANE: OPERATION - Creates rosette_gcode_post or rosette_gcode_blocked artifact

    Flow:
    1. Recompute feasibility server-side (NEVER trust client)
    2. Block if RED/UNKNOWN (HTTP 409)
    3. Generate G-code if safe
    4. Persist run artifact for audit trail
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(body.model_dump())
    tool_id = body.tool_id or "rosette:default"

    # Phase 2: Server-side feasibility enforcement
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req={
            "tool_id": tool_id,
            "material_id": body.material_id,
            "rpm": body.spindle_rpm,
        },
        context="rosette_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    # Block if policy requires (BLOCKED artifact)
    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="rosette",
            event_type="rosette_gcode_blocked",
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
                "message": "Rosette G-code generation blocked by server-side safety policy.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    try:
        gcode, stats = postprocess_toolpath_grbl(
            body.moves,
            units=body.units,
            spindle_rpm=body.spindle_rpm,
        )

        # Hash outputs for provenance
        gcode_hash = sha256_of_text(gcode)
        stats_hash = sha256_of_obj(stats)

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="rosette",
            event_type="rosette_gcode_post",
            status="OK",
            feasibility=feasibility,
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        return {
            "gcode": gcode,
            "stats": stats,
            "_run_id": run_id,
            "_hashes": {
                "request_sha256": request_hash,
                "feasibility_sha256": feas_hash,
                "gcode_sha256": gcode_hash,
                "stats_sha256": stats_hash,
            },
        }

    except HTTPException:
        raise  # WP-1: pass through HTTPException (e.g. 409 SAFETY_BLOCKED)
    except Exception as e:
        # Create ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="rosette",
            event_type="rosette_gcode_post",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "GCODE_POST_ERROR",
                "run_id": run_id,
                "message": f"G-code post-processing failed: {str(e)}",
            },
        )


@router.post("/jobs", response_model=RosetteCamJobIdResponse)
def create_rosette_cam_job(body: RosetteCamJobCreateRequest) -> RosetteCamJobIdResponse:
    """
    Create a CAM job for pipeline handoff.

    Stores job metadata for later retrieval by PipelineLab.
    Job ID should be unique across all jobs.

    Returns job_id + success message.
    """
    try:
        create_art_job(
            job_id=body.job_id,
            job_type="rosette_cam",
            post_preset=body.post_preset,
            rings=body.rings,
            z_passes=body.z_passes,
            length_mm=body.length_mm,
            gcode_lines=body.gcode_lines,
            meta=body.meta,
        )

        return RosetteCamJobIdResponse(
            job_id=body.job_id,
            message=f"CAM job '{body.job_id}' created successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Job creation failed: {str(e)}")


@router.get("/jobs/{job_id}", response_model=RosetteCamJobResponse)
def get_rosette_cam_job(job_id: str) -> RosetteCamJobResponse:
    """
    Retrieve a CAM job by ID.

    Used by PipelineLab to load job details for pipeline execution.

    Returns full job details including metadata.
    """
    try:
        job = get_art_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        return RosetteCamJobResponse(
            id=job.id,
            job_type=job.job_type,
            created_at=job.created_at,
            post_preset=job.post_preset,
            rings=job.rings,
            z_passes=job.z_passes,
            length_mm=job.length_mm,
            gcode_lines=job.gcode_lines,
            meta=job.meta,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job retrieval failed: {str(e)}")
