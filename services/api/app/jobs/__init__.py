"""
Jobs module for async blueprint processing.

Storage backend selection via environment:
    BLUEPRINT_JOB_STORE=memory  (default)
    BLUEPRINT_JOB_STORE=redis   (requires REDIS_URL)

Stale job recovery:
    Call recover_stale_jobs_on_startup() at app startup to mark
    abandoned PROCESSING jobs as FAILED.
"""

from .models import BlueprintJob, JobStatus
from .store import (
    JobStore,
    InMemoryJobStore,
    RedisJobStore,
    build_job_store,
    job_store,
    recover_stale_jobs_on_startup,
    REDIS_AVAILABLE,
    DEFAULT_STALE_MINUTES,
)

__all__ = [
    "BlueprintJob",
    "JobStatus",
    "JobStore",
    "InMemoryJobStore",
    "RedisJobStore",
    "build_job_store",
    "job_store",
    "recover_stale_jobs_on_startup",
    "REDIS_AVAILABLE",
    "DEFAULT_STALE_MINUTES",
]
