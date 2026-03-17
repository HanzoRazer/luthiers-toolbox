"""
Job Queue Core — orchestrator: composes storage and execution.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .schemas import JobPriority, JobState
from .queue_storage import JobStatus, QueueStorage
from .queue_execution import (
    _HANDLER_REGISTRY,
    get_handler,
    register_handler,
    _worker_loop,
)

logger = logging.getLogger(__name__)


class JobQueue:
    """
    Async job queue with in-memory storage and background processing.
    Delegates storage to QueueStorage and execution to queue_execution.
    """

    def __init__(self, max_history: int = 1000) -> None:
        self._storage = QueueStorage(max_history=max_history)
        self._pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._workers: List[asyncio.Task] = []
        self._shutdown = False

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
        """Submit a job to the queue. Returns job_id."""
        if idempotency_key:
            existing_id = self._storage.get_job_id_by_idempotency_key(idempotency_key)
            if existing_id:
                logger.info(f"Idempotent job {idempotency_key} -> {existing_id}")
                return existing_id

        resolved_handler: Optional[str] = handler or _HANDLER_REGISTRY.get(job_type)
        if not resolved_handler:
            logger.warning(f"No handler registered for job type: {job_type}")

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
        await self._storage.add_job(job, idempotency_key=idempotency_key)

        priority_value = {"critical": 0, "high": 1, "normal": 2, "low": 3}[priority.value]
        await self._pending_queue.put((priority_value, job.created_at.timestamp(), job_id))

        logger.info(f"Job submitted: {job_id} ({job_type}) priority={priority.value}")
        return job_id

    async def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status by ID."""
        return await self._storage.get_job(job_id)

    async def cancel(self, job_id: str, reason: Optional[str] = None) -> bool:
        """Cancel a pending or running job. Returns True if cancelled."""
        job = await self._storage.get_job(job_id)
        if not job or job.state in (JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED):
            return False
        await self._storage.update_job(
            job_id,
            state=JobState.CANCELLED,
            completed_at=datetime.utcnow(),
            error=reason or "Cancelled by user",
        )
        logger.info(f"Job cancelled: {job_id}")
        return True

    async def retry(
        self,
        job_id: str,
        reset_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Retry a failed job. Returns new job_id or None."""
        job = await self._storage.get_job(job_id)
        if not job or job.state != JobState.FAILED:
            return None
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
        return await self._storage.list_jobs(state, job_type, tags, limit, offset)

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = await self._storage.get_stats()
        stats["workers_active"] = len([w for w in self._workers if not w.done()])
        stats["workers_idle"] = 0
        return stats

    async def update_progress(
        self,
        job_id: str,
        percent: int,
        message: Optional[str] = None,
    ) -> bool:
        """Update job progress. Returns True if updated."""
        job = await self._storage.get_job(job_id)
        if not job or job.state != JobState.RUNNING:
            return False
        await self._storage.update_job(
            job_id,
            progress_percent=min(100, max(0, percent)),
            progress_message=message,
        )
        return True

    async def start_workers(self, num_workers: int = 2) -> None:
        """Start background worker tasks."""
        self._shutdown = False
        for i in range(num_workers):
            worker = asyncio.create_task(_worker_loop(self, f"worker-{i}"))
            self._workers.append(worker)
        logger.info(f"Started {num_workers} job queue workers")

    async def stop_workers(self, timeout: float = 30.0) -> None:
        """Stop all workers gracefully."""
        self._shutdown = True
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

    async def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove old completed/failed jobs. Returns count removed."""
        return await self._storage.cleanup_old_jobs(max_age_hours)


_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get singleton job queue instance."""
    global _queue
    if _queue is None:
        _queue = JobQueue()
    return _queue
