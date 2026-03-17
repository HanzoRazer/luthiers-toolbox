"""
Job Queue Execution — worker loop, status transitions, handler registry, retry, callbacks.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from .queue_storage import JobStatus
from .schemas import JobState

logger = logging.getLogger(__name__)

_HANDLER_REGISTRY: Dict[str, str] = {}


def register_handler(job_type: str, handler_path: str) -> None:
    """
    Register a handler for a job type.

    Args:
        job_type: Job type identifier
        handler_path: Full module path to handler function
                     (e.g., "app.cam.handlers.generate_toolpath")
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


async def _worker_loop(queue: Any, worker_id: str) -> None:
    """Worker loop that processes jobs from the queue."""
    logger.info(f"{worker_id}: Started")
    while not queue._shutdown:
        try:
            try:
                priority, created_at, job_id = await asyncio.wait_for(
                    queue._pending_queue.get(),
                    timeout=1.0,
                )
            except asyncio.TimeoutError:
                continue

            job = await queue._storage.get_job(job_id)
            if not job or job.state != JobState.PENDING:
                continue

            await _process_job(worker_id, job, queue)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"{worker_id}: Unexpected error: {e}")
            await asyncio.sleep(1)

    logger.info(f"{worker_id}: Stopped")


async def _process_job(worker_id: str, job: JobStatus, queue: Any) -> None:
    """Process a single job."""
    logger.info(f"{worker_id}: Processing job {job.job_id} ({job.job_type})")

    await queue._storage.update_job(
        job.job_id,
        state=JobState.RUNNING,
        started_at=datetime.utcnow(),
    )
    job.state = JobState.RUNNING
    job.started_at = datetime.utcnow()

    try:
        handler = get_handler(job.job_type) if job.handler else None
        if not handler and job.handler:
            try:
                module_path, func_name = job.handler.rsplit(".", 1)
                module = importlib.import_module(module_path)
                handler = getattr(module, func_name)
            except Exception:
                pass

        if not handler:
            raise ValueError(f"No handler for job type: {job.job_type}")

        if asyncio.iscoroutinefunction(handler):
            result = await asyncio.wait_for(
                handler(job.params, job),
                timeout=job.timeout_seconds,
            )
        else:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, handler, job.params, job),
                timeout=job.timeout_seconds,
            )

        await queue._storage.update_job(
            job.job_id,
            state=JobState.COMPLETED,
            completed_at=datetime.utcnow(),
            result=result if isinstance(result, dict) else {"result": result},
            progress_percent=100,
        )
        job.state = JobState.COMPLETED
        job.completed_at = datetime.utcnow()
        job.result = result if isinstance(result, dict) else {"result": result}
        job.progress_percent = 100
        logger.info(f"{worker_id}: Job {job.job_id} completed")

    except asyncio.TimeoutError:
        await queue._storage.update_job(
            job.job_id,
            state=JobState.FAILED,
            completed_at=datetime.utcnow(),
            error=f"Job timed out after {job.timeout_seconds} seconds",
        )
        job.state = JobState.FAILED
        job.completed_at = datetime.utcnow()
        job.error = f"Job timed out after {job.timeout_seconds} seconds"
        logger.warning(f"{worker_id}: Job {job.job_id} timed out")

    except Exception as e:
        await queue._storage.update_job(
            job.job_id,
            state=JobState.FAILED,
            completed_at=datetime.utcnow(),
            error=str(e),
            error_details={"traceback": traceback.format_exc()},
        )
        job.state = JobState.FAILED
        job.completed_at = datetime.utcnow()
        job.error = str(e)
        job.error_details = {"traceback": traceback.format_exc()}
        logger.error(f"{worker_id}: Job {job.job_id} failed: {e}")

        if job.retry_count < job.max_retries:
            job.retry_count += 1
            job.state = JobState.PENDING
            job.started_at = None
            job.completed_at = None
            job.error = None
            job.error_details = None
            await queue._storage.update_job(
                job.job_id,
                state=JobState.PENDING,
                started_at=None,
                completed_at=None,
                error=None,
                error_details=None,
                retry_count=job.retry_count,
            )
            await asyncio.sleep(2 ** job.retry_count)
            priority_value = {"critical": 0, "high": 1, "normal": 2, "low": 3}[job.priority.value]
            await queue._pending_queue.put((priority_value, datetime.utcnow().timestamp(), job.job_id))
            logger.info(f"{worker_id}: Job {job.job_id} requeued (attempt {job.retry_count})")

    if job.callback_url and job.state in (JobState.COMPLETED, JobState.FAILED):
        await _send_callback(job)


async def _send_callback(job: JobStatus) -> None:
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


__all__ = [
    "register_handler",
    "get_handler",
    "_worker_loop",
    "_process_job",
    "_send_callback",
    "_HANDLER_REGISTRY",
]
