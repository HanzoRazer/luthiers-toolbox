"""Rosette Jobs Router - CAM job management for pipeline handoff.

LANE: UTILITY
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Provides:
- POST /jobs - Create CAM job for pipeline handoff
- GET /jobs/{job_id} - Retrieve CAM job details

Total: 2 routes for job management.

Note: These endpoints do NOT create RMOS artifacts as they are purely
metadata operations (storing/retrieving job configurations).
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import job store
from ....services.art_jobs_store import create_art_job, get_art_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Rosette", "Jobs"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

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

    except HTTPException:
        raise  # WP-1: pass through
    except (ValueError, TypeError, KeyError, OSError) as e:
        logger.error("Rosette CAM job creation failed: %s", e, exc_info=True)
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
        raise  # WP-1: pass through
    except (ValueError, TypeError, KeyError, OSError) as e:
        logger.error("Rosette CAM job retrieval failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Job retrieval failed: {str(e)}")


__all__ = [
    "router",
    "RosetteCamJobCreateRequest",
    "RosetteCamJobIdResponse",
    "RosetteCamJobResponse",
]
