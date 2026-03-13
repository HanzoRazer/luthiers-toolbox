"""
Jobs API v1

Manufacturing job management:

1. POST /jobs/create - Create a new manufacturing job
2. GET  /jobs/list - List jobs with filters
3. GET  /jobs/{id} - Get job details
4. POST /jobs/{id}/start - Start job execution
5. POST /jobs/{id}/complete - Mark job complete
6. GET  /jobs/{id}/artifacts - Get job artifacts
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class JobCreateRequest(BaseModel):
    """Request to create a manufacturing job."""
    name: str = Field(..., description="Job name/description")
    job_type: str = Field("cnc", description="Job type: cnc, assembly, finishing")
    instrument_type: str = Field("guitar", description="Instrument being built")
    customer_id: Optional[str] = Field(None, description="Customer reference")
    priority: int = Field(2, ge=1, le=5, description="Priority 1-5 (1=highest)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Job-specific parameters")


class JobStartRequest(BaseModel):
    """Request to start job execution."""
    operator_id: str = Field(..., description="Operator starting the job")
    machine_id: str = Field(..., description="Machine being used")
    notes: Optional[str] = Field(None, description="Start notes")


class JobCompleteRequest(BaseModel):
    """Request to complete a job."""
    operator_id: str = Field(..., description="Operator completing the job")
    status: str = Field("success", description="Completion status: success, partial, failed")
    quality_notes: Optional[str] = Field(None, description="Quality observations")
    photos: List[str] = Field(default_factory=list, description="Photo URLs")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/create")
def create_job(req: JobCreateRequest) -> V1Response:
    """
    Create a new manufacturing job.

    Jobs track work from design through completion.
    """
    import hashlib
    from datetime import datetime

    job_id = f"job_{hashlib.sha256(f'{req.name}{datetime.utcnow()}'.encode()).hexdigest()[:12]}"

    return V1Response(
        ok=True,
        data={
            "job_id": job_id,
            "name": req.name,
            "job_type": req.job_type,
            "instrument_type": req.instrument_type,
            "status": "created",
            "priority": req.priority,
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
    )


@router.get("/list")
def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> V1Response:
    """
    List manufacturing jobs with optional filters.

    Filter by status (created, in_progress, completed) or job_type.
    """
    # Mock response showing structure
    jobs = [
        {
            "job_id": "job_abc123",
            "name": "Acoustic Guitar Body #42",
            "status": "in_progress",
            "job_type": "cnc",
            "priority": 2,
            "created_at": "2024-01-15T09:00:00Z",
        },
        {
            "job_id": "job_def456",
            "name": "Neck Carving #18",
            "status": "created",
            "job_type": "cnc",
            "priority": 3,
            "created_at": "2024-01-15T10:00:00Z",
        },
    ]

    # Apply filters if provided
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    if job_type:
        jobs = [j for j in jobs if j["job_type"] == job_type]

    return V1Response(
        ok=True,
        data={
            "jobs": jobs[offset:offset + limit],
            "total": len(jobs),
            "limit": limit,
            "offset": offset,
        },
    )


@router.get("/{job_id}")
def get_job(job_id: str = Path(..., description="Job ID")) -> V1Response:
    """
    Get detailed job information.

    Includes parameters, history, and linked artifacts.
    """
    return V1Response(
        ok=True,
        data={
            "job_id": job_id,
            "name": "Acoustic Guitar Body #42",
            "status": "in_progress",
            "job_type": "cnc",
            "instrument_type": "guitar",
            "priority": 2,
            "parameters": {
                "body_style": "dreadnought",
                "wood_top": "sitka_spruce",
                "wood_back": "indian_rosewood",
            },
            "history": [
                {"event": "created", "timestamp": "2024-01-15T09:00:00Z"},
                {"event": "started", "timestamp": "2024-01-15T14:00:00Z", "operator": "operator_1"},
            ],
            "artifacts": {
                "dxf": f"/api/v1/jobs/{job_id}/artifacts/design.dxf",
                "gcode": f"/api/v1/jobs/{job_id}/artifacts/toolpath.nc",
            },
        },
    )


@router.post("/{job_id}/start")
def start_job(
    job_id: str = Path(..., description="Job ID"),
    req: JobStartRequest = ...,
) -> V1Response:
    """
    Start job execution.

    Records operator, machine, and start time for tracking.
    """
    from datetime import datetime

    return V1Response(
        ok=True,
        data={
            "job_id": job_id,
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "operator_id": req.operator_id,
            "machine_id": req.machine_id,
        },
    )


@router.post("/{job_id}/complete")
def complete_job(
    job_id: str = Path(..., description="Job ID"),
    req: JobCompleteRequest = ...,
) -> V1Response:
    """
    Mark job as complete.

    Records completion status, quality notes, and optional photos.
    """
    from datetime import datetime

    return V1Response(
        ok=True,
        data={
            "job_id": job_id,
            "status": req.status,
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "operator_id": req.operator_id,
            "quality_notes": req.quality_notes,
            "photos_count": len(req.photos),
        },
    )


@router.get("/{job_id}/artifacts")
def list_job_artifacts(job_id: str = Path(..., description="Job ID")) -> V1Response:
    """
    List all artifacts associated with a job.

    Artifacts include DXF files, G-code, photos, and reports.
    """
    artifacts = [
        {
            "type": "dxf",
            "name": "body_outline.dxf",
            "url": f"/api/v1/jobs/{job_id}/artifacts/body_outline.dxf",
            "size_bytes": 45678,
            "created_at": "2024-01-15T09:00:00Z",
        },
        {
            "type": "gcode",
            "name": "roughing.nc",
            "url": f"/api/v1/jobs/{job_id}/artifacts/roughing.nc",
            "size_bytes": 123456,
            "created_at": "2024-01-15T09:05:00Z",
        },
        {
            "type": "gcode",
            "name": "finishing.nc",
            "url": f"/api/v1/jobs/{job_id}/artifacts/finishing.nc",
            "size_bytes": 234567,
            "created_at": "2024-01-15T09:10:00Z",
        },
    ]

    return V1Response(
        ok=True,
        data={
            "job_id": job_id,
            "artifacts": artifacts,
            "total": len(artifacts),
        },
    )
