"""
Async Job Queue System
======================

Provides unified background job processing for long-running operations.

Components:
- JobQueue: Core queue management (submit, status, cancel)
- JobWorker: Background worker processing
- job_router: REST API endpoints

Usage:
    from app.core.job_queue import JobQueue, JobStatus

    queue = JobQueue()

    # Submit a job
    job_id = await queue.submit(
        job_type="cam_generation",
        params={"dxf_id": "abc123", "tool_id": "6mm_endmill"},
        handler="app.cam.generate_toolpath",
    )

    # Check status
    status = await queue.get_status(job_id)
    if status.state == "completed":
        result = status.result
"""

from .queue import JobQueue, JobStatus, JobState, get_job_queue
from .schemas import (
    JobSubmitRequest,
    JobSubmitResponse,
    JobStatusResponse,
    JobListResponse,
)

__all__ = [
    "JobQueue",
    "JobStatus",
    "JobState",
    "get_job_queue",
    "JobSubmitRequest",
    "JobSubmitResponse",
    "JobStatusResponse",
    "JobListResponse",
]
