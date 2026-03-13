"""
Job Queue Core Implementation
=============================

Async job queue with SQLite persistence and background worker processing.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import logging
import os
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from .schemas import JobPriority, JobState

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


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


# =============================================================================
# Job Handler Registry
# =============================================================================


# Map of job_type -> handler function path
_HANDLER_REGISTRY: Dict[str, str] = {}


def register_handler(job_type: str, handler_path: str) -> None:
    """
    Register a handler for a job type.

    Args:
        job_type: Job type identifier
        handler_path: Full module path to handler function
                     (e.g., "app.cam.handlers.generate_toolpath")

    Example:
        register_handler("cam_generation", "app.cam.handlers.generate_toolpath")
    """
    _HANDLER_REGISTRY[job_type] = handler_path
    logger.info(f"Registered job handler: {job_type} -> {handler_path}")


def get_handler(job_type: str) -> Optional[Callable]:
    """
    Get handler function for a job type.

    Returns:
        Callable handler or None if not registered
    """
    handler_path = _HANDLER_REGISTRY.get(job_type)
    if not handler_path:
        return None

    try:
        module_path, func_name = handler_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load handler {handler_path}: {e}")
        return None


# =============================================================================
# Job Queue
# =============================================================================


class JobQueue:
    """
    Async job queue with in-memory storage and background processing.

    Features:
    - Priority-based scheduling (critical > high > normal > low)
    - Progress tracking
    - Automatic retries on failure
    - Timeout enforcement
    - Idempotency key deduplication
    - Callback webhooks on completion

    Example:
        queue = JobQueue()
        await queue.start_workers(num_workers=2)

        job_id = await queue.submit(
            job_type="cam_generation",
            params={"dxf_id": "abc"},
        )

        status = await queue.get_status(job_id)
    """

    def __init__(self, max_history: int = 1000) -> None:
        """
        Initialize job queue.

        Args:
            max_history: Maximum completed/failed jobs to retain
        """
        self._jobs: Dict[str, JobStatus] = {}
        self._pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._idempotency_cache: Dict[str, str] = {}  # key -> job_id
        self._max_history = max_history
        self._workers: List[asyncio.Task] = []
        self._shutdown = False
        self._lock = asyncio.Lock()

    async def submit(
        self,
        job_type: str,
        params: Optional[Dict[str, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL,
        handler: Optional[str] = None,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        callback_url: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Submit a job to the queue.

        Args:
            job_type: Job type identifier
            params: Job parameters
            priority: Scheduling priority
            handler: Handler function path (uses registry if not provided)
            timeout_seconds: Maximum execution time
            max_retries: Retry attempts on failure
            callback_url: Webhook for completion notification
            idempotency_key: Client key for deduplication
            tags: Tags for filtering

        Returns:
            Job ID

        Raises:
            ValueError: If no handler is registered for job_type
        """
        # Check idempotency
        if idempotency_key:
            async with self._lock:
                if idempotency_key in self._idempotency_cache:
                    existing_id = self._idempotency_cache[idempotency_key]
                    logger.info(f"Idempotent job {idempotency_key} -> {existing_id}")
                    return existing_id

        # Resolve handler
        resolved_handler = handler or _HANDLER_REGISTRY.get(job_type)
        if not resolved_handler:
            # Allow submission without handler (for testing/external processing)
            logger.warning(f"No handler registered for job type: {job_type}")

        # Create job
        job_id = str(uuid.uuid4())
        job = JobStatus(
            job_id=job_id,
            job_type=job_type,
            state=JobState.PENDING,
            priority=priority,
            params=params or {},
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            callback_url=callback_url,
            idempotency_key=idempotency_key,
            tags=tags or [],
            handler=resolved_handler,
        )

        # Store and enqueue
        async with self._lock:
            self._jobs[job_id] = job
            if idempotency_key:
                self._idempotency_cache[idempotency_key] = job_id

        # Priority queue: (priority_value, created_at, job_id)
        # Lower priority value = higher priority
        priority_value = {"critical": 0, "high": 1, "normal": 2, "low": 3}[priority.value]
        await self._pending_queue.put((priority_value, job.created_at.timestamp(), job_id))

        logger.info(f"Job submitted: {job_id} ({job_type}) priority={priority.value}")
        return job_id

    async def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status by ID."""
        return self._jobs.get(job_id)

    async def cancel(self, job_id: str, reason: Optional[str] = None) -> bool:
        """
        Cancel a pending or running job.

        Returns:
            True if cancelled, False if job not found or already completed
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.state in (JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED):
            return False

        job.state = JobState.CANCELLED
        job.completed_at = datetime.utcnow()
        job.error = reason or "Cancelled by user"
        logger.info(f"Job cancelled: {job_id}")
        return True

    async def retry(
        self,
        job_id: str,
        reset_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Retry a failed job.

        Args:
            job_id: Job to retry
            reset_params: Override parameters

        Returns:
            New job ID or None if job not found/not retriable
        """
        job = self._jobs.get(job_id)
        if not job or job.state != JobState.FAILED:
            return None

        # Create new job with same parameters
        params = reset_params if reset_params else job.params.copy()
        return await self.submit(
            job_type=job.job_type,
            params=params,
            priority=job.priority,
            handler=job.handler,
            timeout_seconds=job.timeout_seconds,
            max_retries=job.max_retries,
            callback_url=job.callback_url,
            tags=job.tags,
        )

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

        # Filter
        if state:
            jobs = [j for j in jobs if j.state == state]
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        if tags:
            jobs = [j for j in jobs if any(t in j.tags for t in tags)]

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[offset : offset + limit]

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
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

        # Calculate averages
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
            "workers_active": len([w for w in self._workers if not w.done()]),
            "workers_idle": 0,  # TODO: track idle workers
        }

    async def update_progress(
        self,
        job_id: str,
        percent: int,
        message: Optional[str] = None,
    ) -> bool:
        """
        Update job progress.

        Args:
            job_id: Job ID
            percent: Completion percentage (0-100)
            message: Progress message

        Returns:
            True if updated, False if job not found
        """
        job = self._jobs.get(job_id)
        if not job or job.state != JobState.RUNNING:
            return False

        job.progress_percent = min(100, max(0, percent))
        job.progress_message = message
        return True

    # =========================================================================
    # Worker Management
    # =========================================================================

    async def start_workers(self, num_workers: int = 2) -> None:
        """Start background worker tasks."""
        self._shutdown = False
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)
        logger.info(f"Started {num_workers} job queue workers")

    async def stop_workers(self, timeout: float = 30.0) -> None:
        """Stop all workers gracefully."""
        self._shutdown = True

        # Wait for workers to finish current jobs
        if self._workers:
            done, pending = await asyncio.wait(
                self._workers,
                timeout=timeout,
                return_when=asyncio.ALL_COMPLETED,
            )
            for task in pending:
                task.cancel()

        self._workers.clear()
        logger.info("Job queue workers stopped")

    async def _worker_loop(self, worker_id: str) -> None:
        """Worker loop that processes jobs from the queue."""
        logger.info(f"{worker_id}: Started")

        while not self._shutdown:
            try:
                # Get next job with timeout (allows checking shutdown flag)
                try:
                    priority, created_at, job_id = await asyncio.wait_for(
                        self._pending_queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                job = self._jobs.get(job_id)
                if not job or job.state != JobState.PENDING:
                    continue

                # Process job
                await self._process_job(worker_id, job)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_id}: Unexpected error: {e}")
                await asyncio.sleep(1)

        logger.info(f"{worker_id}: Stopped")

    async def _process_job(self, worker_id: str, job: JobStatus) -> None:
        """Process a single job."""
        logger.info(f"{worker_id}: Processing job {job.job_id} ({job.job_type})")

        # Mark as running
        job.state = JobState.RUNNING
        job.started_at = datetime.utcnow()

        try:
            # Get handler
            handler = get_handler(job.job_type) if job.handler else None
            if not handler and job.handler:
                # Try direct import
                try:
                    module_path, func_name = job.handler.rsplit(".", 1)
                    module = importlib.import_module(module_path)
                    handler = getattr(module, func_name)
                except Exception:
                    pass

            if not handler:
                raise ValueError(f"No handler for job type: {job.job_type}")

            # Execute with timeout
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(
                    handler(job.params, job),
                    timeout=job.timeout_seconds,
                )
            else:
                # Run sync handler in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, handler, job.params, job),
                    timeout=job.timeout_seconds,
                )

            # Success
            job.state = JobState.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result if isinstance(result, dict) else {"result": result}
            job.progress_percent = 100
            logger.info(f"{worker_id}: Job {job.job_id} completed")

        except asyncio.TimeoutError:
            job.state = JobState.FAILED
            job.completed_at = datetime.utcnow()
            job.error = f"Job timed out after {job.timeout_seconds} seconds"
            logger.warning(f"{worker_id}: Job {job.job_id} timed out")

        except Exception as e:
            job.state = JobState.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(e)
            job.error_details = {"traceback": traceback.format_exc()}
            logger.error(f"{worker_id}: Job {job.job_id} failed: {e}")

            # Auto-retry if allowed
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.state = JobState.PENDING
                job.started_at = None
                job.completed_at = None
                job.error = None
                job.error_details = None

                # Re-enqueue with delay
                await asyncio.sleep(2 ** job.retry_count)  # Exponential backoff
                priority_value = {"critical": 0, "high": 1, "normal": 2, "low": 3}[job.priority.value]
                await self._pending_queue.put((priority_value, datetime.utcnow().timestamp(), job.job_id))
                logger.info(f"{worker_id}: Job {job.job_id} requeued (attempt {job.retry_count})")

        # Send webhook callback if configured
        if job.callback_url and job.state in (JobState.COMPLETED, JobState.FAILED):
            await self._send_callback(job)

    async def _send_callback(self, job: JobStatus) -> None:
        """Send webhook callback for completed/failed job."""
        if not job.callback_url:
            return

        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    job.callback_url,
                    json={
                        "job_id": job.job_id,
                        "job_type": job.job_type,
                        "state": job.state.value,
                        "result": job.result,
                        "error": job.error,
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to send callback for job {job.job_id}: {e}")

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove old completed/failed jobs.

        Returns:
            Number of jobs removed
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = []

        for job_id, job in self._jobs.items():
            if job.state in (JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED):
                if job.completed_at and job.completed_at < cutoff:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]
            # Clean idempotency cache
            key_to_remove = None
            for key, val in self._idempotency_cache.items():
                if val == job_id:
                    key_to_remove = key
                    break
            if key_to_remove:
                del self._idempotency_cache[key_to_remove]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")

        return len(to_remove)


# =============================================================================
# Singleton
# =============================================================================

_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get singleton job queue instance."""
    global _queue
    if _queue is None:
        _queue = JobQueue()
    return _queue
