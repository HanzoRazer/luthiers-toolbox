"""
Rosette CAM Router

Toolpath planning, G-code generation, and job management for rosette designs.

Extracted from: routers/art_studio_rosette_router.py (lines 679-807)

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /plan-toolpath     - Generate toolpath moves from rosette geometry
    POST /post-gcode        - Convert toolpath moves to G-code
    POST /jobs              - Create CAM job for pipeline handoff
    GET  /jobs/{job_id}     - Retrieve CAM job details
"""

from __future__ import annotations

from typing import Any, Dict, List

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


class RosetteToolpathPlanResponse(BaseModel):
    """Response with planned toolpath moves and stats."""
    moves: List[Dict[str, Any]] = Field(..., description="Neutral toolpath moves")
    stats: Dict[str, Any] = Field(..., description="Toolpath statistics")


class RosettePostGcodeRequest(BaseModel):
    """Request to generate G-code from toolpath moves."""
    moves: List[Dict[str, Any]] = Field(..., description="Toolpath moves to convert")
    units: str = Field("mm", description="Units (mm or inch)")
    spindle_rpm: int = Field(18000, ge=0, description="Spindle RPM")


class RosettePostGcodeResponse(BaseModel):
    """Response with generated G-code and stats."""
    gcode: str = Field(..., description="Generated G-code text")
    stats: Dict[str, Any] = Field(..., description="G-code statistics")


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
def plan_rosette_cam_toolpath(body: RosetteToolpathPlanRequest) -> RosetteToolpathPlanResponse:
    """
    Generate toolpath moves for a rosette design.

    Uses concentric ring strategy with:
    - Radial passes based on tool diameter + stepover
    - Z passes based on cut depth + stepdown

    Returns neutral move list (code, x, y, z, f) + stats.
    """
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

        return RosetteToolpathPlanResponse(moves=moves, stats=stats)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Toolpath planning failed: {str(e)}")


@router.post("/post-gcode", response_model=RosettePostGcodeResponse)
def post_rosette_gcode(body: RosettePostGcodeRequest) -> RosettePostGcodeResponse:
    """
    Generate G-code from toolpath moves.

    Uses GRBL-compatible post-processor with:
    - Header: G21/G20, G90, G17, M3 spindle on
    - Body: G0/G1 moves with coordinates
    - Footer: M5 spindle off, safe retract, M30

    Returns G-code text + stats (lines, bytes).
    """
    try:
        gcode, stats = postprocess_toolpath_grbl(
            body.moves,
            units=body.units,
            spindle_rpm=body.spindle_rpm,
        )

        return RosettePostGcodeResponse(gcode=gcode, stats=stats)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"G-code post-processing failed: {str(e)}")


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
