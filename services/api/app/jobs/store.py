"""
Job Store
=========

Abstraction for job storage with pluggable backends.

Backends:
- InMemoryJobStore: Development/testing (default)
- RedisJobStore: Production multi-worker deployment

Selection via environment variable:
    BLUEPRINT_JOB_STORE=memory  (default)
    BLUEPRINT_JOB_STORE=redis   (requires REDIS_URL)

Author: Production Shop
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from threading import Lock
from typing import Iterator, Optional
from uuid import uuid4

from .models import BlueprintJob, JobStatus

logger = logging.getLogger(__name__)

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


# Default stale job threshold
DEFAULT_STALE_MINUTES = 15


class JobStore:
    """
    Abstract interface for job storage.

    Implementations can be in-memory (prototype) or Redis (production).
    """

    def create(self, *, filename: str) -> BlueprintJob:
        """Create a new job in QUEUED status."""
        raise NotImplementedError

    def get(self, job_id: str) -> Optional[BlueprintJob]:
        """Get a job by ID, or None if not found."""
        raise NotImplementedError

    def update(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        stage: Optional[str] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
        debug: Optional[dict] = None,
    ) -> Optional[BlueprintJob]:
        """Update job fields. Returns updated job or None if not found."""
        raise NotImplementedError

    def delete(self, job_id: str) -> None:
        """Delete a job by ID."""
        raise NotImplementedError

    def iter_all(self) -> Iterator[BlueprintJob]:
        """Iterate over all jobs. Used for recovery/cleanup."""
        raise NotImplementedError

    def mark_stale_processing_jobs_failed(self, max_age_minutes: int = DEFAULT_STALE_MINUTES) -> int:
        """
        Mark old PROCESSING jobs as FAILED.

        Used to recover from worker restarts where jobs were left in processing state.

        Args:
            max_age_minutes: Jobs processing longer than this are considered stale

        Returns:
            Number of jobs marked as failed
        """
        now = datetime.utcnow()
        threshold = timedelta(minutes=max_age_minutes)
        count = 0

        for job in self.iter_all():
            if job.status != JobStatus.PROCESSING:
                continue

            # Check started_at if available, fall back to created_at
            check_time = job.started_at or job.created_at
            if now - check_time > threshold:
                self.update(
                    job.job_id,
                    status=JobStatus.FAILED,
                    stage="failed",
                    progress=100,
                    error=f"Job exceeded maximum runtime ({max_age_minutes} minutes) or worker restarted.",
                )
                logger.warning(
                    f"STALE_JOB_RECOVERED | job_id={job.job_id} "
                    f"filename={job.filename} started_at={check_time}"
                )
                count += 1

        return count


class InMemoryJobStore(JobStore):
    """
    In-memory job store for development/testing.

    NOT suitable for production multi-worker deployments.
    Jobs expire after TTL to prevent memory leaks.
    """

    def __init__(self, ttl_hours: int = 24):
        self._jobs: dict[str, BlueprintJob] = {}
        self._lock = Lock()
        self._ttl = timedelta(hours=ttl_hours)

    def create(self, *, filename: str) -> BlueprintJob:
        now = datetime.utcnow()
        job = BlueprintJob(
            job_id=str(uuid4()),
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
            filename=filename,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[BlueprintJob]:
        self._cleanup_expired()
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        stage: Optional[str] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
        debug: Optional[dict] = None,
    ) -> Optional[BlueprintJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            # Set started_at when transitioning to PROCESSING
            if status == JobStatus.PROCESSING and job.started_at is None:
                job.started_at = datetime.utcnow()

            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
            if stage is not None:
                job.stage = stage
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if debug is not None:
                job.debug = debug

            job.updated_at = datetime.utcnow()
            return job

    def delete(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)

    def iter_all(self) -> Iterator[BlueprintJob]:
        """Iterate over all jobs."""
        self._cleanup_expired()
        with self._lock:
            # Return copies to avoid mutation during iteration
            for job in list(self._jobs.values()):
                yield job

    def _cleanup_expired(self) -> None:
        """Remove jobs older than TTL."""
        now = datetime.utcnow()
        with self._lock:
            expired = [
                job_id
                for job_id, job in self._jobs.items()
                if now - job.created_at > self._ttl
            ]
            for job_id in expired:
                del self._jobs[job_id]


class RedisJobStore(JobStore):
    """
    Redis-backed job store for production multi-worker deployments.

    Each job is stored as a JSON blob with automatic TTL expiration.
    Key format: blueprint_job:{job_id}

    Requires: pip install redis
    """

    def __init__(
        self,
        client: "redis.Redis",
        ttl_hours: int = 24,
        key_prefix: str = "blueprint_job",
    ):
        self._client = client
        self._ttl_seconds = ttl_hours * 3600
        self._key_prefix = key_prefix

    def _key(self, job_id: str) -> str:
        return f"{self._key_prefix}:{job_id}"

    def _pattern(self) -> str:
        return f"{self._key_prefix}:*"

    def create(self, *, filename: str) -> BlueprintJob:
        now = datetime.utcnow()
        job = BlueprintJob(
            job_id=str(uuid4()),
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
            filename=filename,
        )
        self._write(job)
        logger.debug(f"REDIS_JOB_CREATE | job_id={job.job_id}")
        return job

    def get(self, job_id: str) -> Optional[BlueprintJob]:
        raw = self._client.get(self._key(job_id))
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(raw)
        return BlueprintJob.from_dict(data)

    def update(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        stage: Optional[str] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
        debug: Optional[dict] = None,
    ) -> Optional[BlueprintJob]:
        job = self.get(job_id)
        if not job:
            return None

        # Set started_at when transitioning to PROCESSING
        if status == JobStatus.PROCESSING and job.started_at is None:
            job.started_at = datetime.utcnow()

        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if stage is not None:
            job.stage = stage
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        if debug is not None:
            job.debug = debug

        job.updated_at = datetime.utcnow()
        self._write(job)  # Refreshes TTL
        return job

    def delete(self, job_id: str) -> None:
        self._client.delete(self._key(job_id))
        logger.debug(f"REDIS_JOB_DELETE | job_id={job_id}")

    def iter_all(self) -> Iterator[BlueprintJob]:
        """Iterate over all jobs using SCAN (non-blocking)."""
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=self._pattern(), count=100)
            for key in keys:
                raw = self._client.get(key)
                if raw:
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    try:
                        data = json.loads(raw)
                        yield BlueprintJob.from_dict(data)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse job from {key}: {e}")
            if cursor == 0:
                break

    def _write(self, job: BlueprintJob) -> None:
        """Write job to Redis with TTL."""
        self._client.setex(
            self._key(job.job_id),
            self._ttl_seconds,
            json.dumps(job.to_dict()),
        )


def build_job_store() -> JobStore:
    """
    Factory function to create the appropriate job store backend.

    Environment variables:
        BLUEPRINT_JOB_STORE: "memory" (default) or "redis"
        REDIS_URL: Redis connection URL (required if backend is "redis")

    Returns:
        JobStore instance (InMemoryJobStore or RedisJobStore)
    """
    backend = os.getenv("BLUEPRINT_JOB_STORE", "memory").lower()

    if backend == "redis":
        if not REDIS_AVAILABLE:
            logger.error("BLUEPRINT_JOB_STORE=redis but redis package not installed. Falling back to memory.")
            return InMemoryJobStore()

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.error("BLUEPRINT_JOB_STORE=redis but REDIS_URL not set. Falling back to memory.")
            return InMemoryJobStore()

        try:
            client = redis.Redis.from_url(redis_url, decode_responses=False)
            client.ping()
            logger.info(f"Job store initialized with Redis backend")
            return RedisJobStore(client)
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Falling back to memory.")
            return InMemoryJobStore()

    # Default: in-memory
    logger.info("Job store initialized with in-memory backend")
    return InMemoryJobStore()


def recover_stale_jobs_on_startup(max_age_minutes: int = DEFAULT_STALE_MINUTES) -> int:
    """
    Recover stale jobs at application startup.

    Call this from main.py or a startup event handler.

    Args:
        max_age_minutes: Jobs processing longer than this are considered stale

    Returns:
        Number of jobs recovered
    """
    count = job_store.mark_stale_processing_jobs_failed(max_age_minutes)
    if count > 0:
        logger.info(f"STARTUP_RECOVERY | Marked {count} stale job(s) as failed")
    return count


# Singleton store instance - backend chosen at import time
job_store = build_job_store()
