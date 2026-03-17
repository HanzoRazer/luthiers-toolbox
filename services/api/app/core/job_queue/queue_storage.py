"""
Job Queue Storage — data persistence and job CRUD operations.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .schemas import JobPriority, JobState

logger = logging.getLogger(__name__)


@dataclass
class JobStatus:
    """Complete job status information."""

    job_id: str
    job_type: str
    state: JobState
    priority: JobPriority = JobPriority.NORMAL
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    progress_percent: int = 0
    progress_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    callback_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    handler: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "state": self.state.value,
            "priority": self.priority.value,
            "params": self.params,
            "result": self.result,
            "error": self.error,
            "error_details": self.error_details,
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tags": self.tags,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "callback_url": self.callback_url,
            "idempotency_key": self.idempotency_key,
            "handler": self.handler,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobStatus":
        """Create from dictionary."""
        return cls(
            job_id=data["job_id"],
            job_type=data["job_type"],
            state=JobState(data["state"]),
            priority=JobPriority(data.get("priority", "normal")),
            params=data.get("params", {}),
            result=data.get("result"),
            error=data.get("error"),
            error_details=data.get("error_details"),
            progress_percent=data.get("progress_percent", 0),
            progress_message=data.get("progress_message"),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            tags=data.get("tags", []),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 300),
            callback_url=data.get("callback_url"),
            idempotency_key=data.get("idempotency_key"),
            handler=data.get("handler"),
        )


class QueueStorage:
    """In-memory job storage with CRUD operations."""

    def __init__(self, max_history: int = 1000) -> None:
        self._jobs: Dict[str, JobStatus] = {}
        self._idempotency_cache: Dict[str, str] = {}
        self._max_history = max_history
        self._lock = asyncio.Lock()

    async def add_job(
        self,
        job: JobStatus,
        idempotency_key: Optional[str] = None,
    ) -> str:
        """Store a job. If idempotency_key is set, record it. Returns job_id."""
        async with self._lock:
            self._jobs[job.job_id] = job
            if idempotency_key:
                self._idempotency_cache[idempotency_key] = job.job_id
        return job.job_id

    def get_job_id_by_idempotency_key(self, key: str) -> Optional[str]:
        """Return existing job_id for idempotency key, or None."""
        return self._idempotency_cache.get(key)

    async def get_job(self, job_id: str) -> Optional[JobStatus]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    async def update_job(self, job_id: str, **updates: Any) -> bool:
        """Update job attributes. Returns True if job found and updated."""
        job = self._jobs.get(job_id)
        if not job:
            return False
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        return True

    async def list_jobs(
        self,
        state: Optional[JobState] = None,
        job_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[JobStatus]:
        """List jobs with optional filtering."""
        jobs = list(self._jobs.values())
        if state:
            jobs = [j for j in jobs if j.state == state]
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        if tags:
            jobs = [j for j in jobs if any(t in j.tags for t in tags)]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics (no worker count)."""
        jobs = list(self._jobs.values())
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        pending = [j for j in jobs if j.state == JobState.PENDING]
        running = [j for j in jobs if j.state == JobState.RUNNING]
        completed_recent = [
            j for j in jobs
            if j.state == JobState.COMPLETED and j.completed_at and j.completed_at > hour_ago
        ]
        failed_recent = [
            j for j in jobs
            if j.state == JobState.FAILED and j.completed_at and j.completed_at > hour_ago
        ]
        durations = [j.duration_seconds for j in completed_recent if j.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else None
        wait_times = [
            (j.started_at - j.created_at).total_seconds()
            for j in running + completed_recent + failed_recent
            if j.started_at
        ]
        avg_wait = sum(wait_times) / len(wait_times) if wait_times else None
        return {
            "pending": len(pending),
            "running": len(running),
            "completed_last_hour": len(completed_recent),
            "failed_last_hour": len(failed_recent),
            "avg_wait_seconds": avg_wait,
            "avg_duration_seconds": avg_duration,
        }

    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove old completed/failed/cancelled jobs. Returns count removed."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = []
        async with self._lock:
            for job_id, job in self._jobs.items():
                if job.state in (JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED):
                    if job.completed_at and job.completed_at < cutoff:
                        to_remove.append(job_id)
            for job_id in to_remove:
                del self._jobs[job_id]
                for key, val in list(self._idempotency_cache.items()):
                    if val == job_id:
                        del self._idempotency_cache[key]
                        break
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")
        return len(to_remove)


__all__ = [
    "JobStatus",
    "QueueStorage",
]
