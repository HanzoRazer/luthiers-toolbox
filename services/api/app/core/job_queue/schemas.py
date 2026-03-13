"""
Job Queue Pydantic Schemas
==========================

Request/response models for job queue API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobState(str, Enum):
    """Job lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Job priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Request Schemas
# =============================================================================


class JobSubmitRequest(BaseModel):
    """Request to submit a new job."""

    job_type: str = Field(
        ...,
        description="Job type identifier (e.g., 'cam_generation', 'dxf_export')",
        examples=["cam_generation", "rosette_batch", "gcode_simulation"],
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Job-specific parameters",
    )
    priority: JobPriority = Field(
        default=JobPriority.NORMAL,
        description="Job priority level",
    )
    callback_url: Optional[str] = Field(
        default=None,
        description="Webhook URL to POST results when complete",
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        description="Client-provided key for deduplication",
    )
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Maximum job execution time in seconds",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for filtering and grouping",
    )


class JobCancelRequest(BaseModel):
    """Request to cancel a job."""

    reason: Optional[str] = Field(
        default=None,
        description="Reason for cancellation",
    )


class JobRetryRequest(BaseModel):
    """Request to retry a failed job."""

    reset_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Override parameters for retry",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class JobSubmitResponse(BaseModel):
    """Response after submitting a job."""

    ok: bool = True
    job_id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Job type")
    state: JobState = Field(default=JobState.PENDING, description="Initial state")
    created_at: datetime = Field(..., description="Job creation timestamp")
    estimated_duration_seconds: Optional[int] = Field(
        default=None,
        description="Estimated time to complete (if available)",
    )


class JobProgress(BaseModel):
    """Job progress information."""

    percent: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Completion percentage",
    )
    message: Optional[str] = Field(
        default=None,
        description="Current operation description",
    )
    step: Optional[int] = Field(default=None, description="Current step number")
    total_steps: Optional[int] = Field(default=None, description="Total steps")


class JobStatusResponse(BaseModel):
    """Job status response."""

    ok: bool = True
    job_id: str
    job_type: str
    state: JobState
    priority: JobPriority = JobPriority.NORMAL
    progress: Optional[JobProgress] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


class JobListItem(BaseModel):
    """Summary of a job for list views."""

    job_id: str
    job_type: str
    state: JobState
    priority: JobPriority
    progress_percent: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class JobListResponse(BaseModel):
    """Response for listing jobs."""

    ok: bool = True
    jobs: List[JobListItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
    has_more: bool = False


class JobStatsResponse(BaseModel):
    """Queue statistics."""

    ok: bool = True
    pending: int = 0
    running: int = 0
    completed_last_hour: int = 0
    failed_last_hour: int = 0
    avg_wait_seconds: Optional[float] = None
    avg_duration_seconds: Optional[float] = None
    workers_active: int = 0
    workers_idle: int = 0
