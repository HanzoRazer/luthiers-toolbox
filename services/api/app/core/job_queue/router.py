"""
Job Queue REST API Router
=========================

Endpoints for submitting, monitoring, and managing async jobs.

Endpoints:
    POST /api/jobs         - Submit a new job
    GET  /api/jobs         - List jobs (with filters)
    GET  /api/jobs/{id}    - Get job status
    POST /api/jobs/{id}/cancel  - Cancel a job
    POST /api/jobs/{id}/retry   - Retry a failed job
    GET  /api/jobs/stats   - Queue statistics
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .queue import JobQueue, JobStatus, get_job_queue
from .schemas import (
    JobCancelRequest,
    JobListItem,
    JobListResponse,
    JobPriority,
    JobProgress,
    JobRetryRequest,
    JobState,
    JobStatsResponse,
    JobStatusResponse,
    JobSubmitRequest,
    JobSubmitResponse,
)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


def _job_to_status_response(job: JobStatus) -> JobStatusResponse:
    """Convert JobStatus to API response."""
    progress = None
    if job.state == JobState.RUNNING:
        progress = JobProgress(
            percent=job.progress_percent,
            message=job.progress_message,
        )

    return JobStatusResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        state=job.state,
        priority=job.priority,
        progress=progress,
        params=job.params,
        result=job.result,
        error=job.error,
        error_details=job.error_details,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        duration_seconds=job.duration_seconds,
        tags=job.tags,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
    )


def _job_to_list_item(job: JobStatus) -> JobListItem:
    """Convert JobStatus to list item."""
    return JobListItem(
        job_id=job.job_id,
        job_type=job.job_type,
        state=job.state,
        priority=job.priority,
        progress_percent=job.progress_percent,
        created_at=job.created_at,
        started_at=job.started_at,
        tags=job.tags,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/health")
async def job_queue_health() -> dict:
    """
    Job queue health check.

    Returns queue status and worker information.
    """
    queue = get_job_queue()
    stats = await queue.get_stats()

    return {
        "ok": True,
        "queue_size": stats["pending"],
        "running": stats["running"],
        "workers_active": stats["workers_active"],
    }


@router.post("", response_model=JobSubmitResponse)
async def submit_job(request: JobSubmitRequest) -> JobSubmitResponse:
    """
    Submit a new job to the queue.

    The job will be processed asynchronously by a background worker.
    Use the returned job_id to check status.

    Example:
        POST /api/jobs
        {
            "job_type": "cam_generation",
            "params": {"dxf_id": "abc123"},
            "priority": "high"
        }
    """
    queue = get_job_queue()

    job_id = await queue.submit(
        job_type=request.job_type,
        params=request.params,
        priority=request.priority,
        timeout_seconds=request.timeout_seconds,
        callback_url=request.callback_url,
        idempotency_key=request.idempotency_key,
        tags=request.tags,
    )

    job = await queue.get_status(job_id)
    if not job:
        raise HTTPException(status_code=500, detail="Job creation failed")

    return JobSubmitResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        state=job.state,
        created_at=job.created_at,
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    state: Optional[JobState] = Query(default=None, description="Filter by state"),
    job_type: Optional[str] = Query(default=None, description="Filter by job type"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
) -> JobListResponse:
    """
    List jobs with optional filtering.

    Example:
        GET /api/jobs?state=running&page=1&page_size=20
    """
    queue = get_job_queue()

    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    offset = (page - 1) * page_size

    jobs = await queue.list_jobs(
        state=state,
        job_type=job_type,
        tags=tag_list,
        limit=page_size + 1,  # Fetch one extra to check has_more
        offset=offset,
    )

    has_more = len(jobs) > page_size
    if has_more:
        jobs = jobs[:page_size]

    return JobListResponse(
        jobs=[_job_to_list_item(j) for j in jobs],
        total=len(jobs),  # Approximate; full count would need separate query
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/stats", response_model=JobStatsResponse)
async def get_queue_stats() -> JobStatsResponse:
    """
    Get queue statistics.

    Returns counts of pending, running, and recent jobs,
    plus average wait and processing times.
    """
    queue = get_job_queue()
    stats = await queue.get_stats()
    return JobStatsResponse(**stats)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get status of a specific job.

    Returns full job details including progress, result, or error.
    """
    queue = get_job_queue()
    job = await queue.get_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return _job_to_status_response(job)


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    request: Optional[JobCancelRequest] = None,
) -> JobStatusResponse:
    """
    Cancel a pending or running job.

    Only jobs in pending or running state can be cancelled.
    """
    queue = get_job_queue()

    reason = request.reason if request else None
    success = await queue.cancel(job_id, reason)

    if not success:
        job = await queue.get_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in state: {job.state.value}",
        )

    job = await queue.get_status(job_id)
    return _job_to_status_response(job)


@router.post("/{job_id}/retry", response_model=JobSubmitResponse)
async def retry_job(
    job_id: str,
    request: Optional[JobRetryRequest] = None,
) -> JobSubmitResponse:
    """
    Retry a failed job.

    Creates a new job with the same parameters (or overridden params).
    Only failed jobs can be retried.
    """
    queue = get_job_queue()

    reset_params = request.reset_params if request else None
    new_job_id = await queue.retry(job_id, reset_params)

    if not new_job_id:
        job = await queue.get_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry job in state: {job.state.value}",
        )

    job = await queue.get_status(new_job_id)
    return JobSubmitResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        state=job.state,
        created_at=job.created_at,
    )
