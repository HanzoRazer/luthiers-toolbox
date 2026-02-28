"""Saw Lab job queue - persistent queue backed by SQLite joblog store.

Provides FIFO queue semantics for saw operations using the joblog
store for persistence. Jobs move through states: pending -> running -> completed/failed.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from app.stores.sqlite_joblog_store import SQLiteJobLogStore


# Job type constant for saw queue items
JOB_TYPE_SAW_QUEUE = "saw_queue_job"


class SawLabQueue:
    """
    Persistent job queue for saw operations.

    Uses SQLite joblog store for durability. Jobs are tracked by status:
    - pending: Waiting in queue
    - running: Currently being processed
    - completed: Successfully finished
    - failed: Error during processing

    Example:
        queue = SawLabQueue()

        # Add job to queue
        job_id = queue.enqueue({
            "op_type": "slice",
            "blade_id": "thin_kerf_001",
            "material": "maple",
            "gcode": "G1 X100 F50",
        })

        # Get next pending job (marks as running)
        job = queue.dequeue()
        if job:
            # Process job...
            queue.complete(job["id"], results={"cuts": 10})

        # View queue
        pending = queue.snapshot()
    """

    def __init__(self, store: Optional[SQLiteJobLogStore] = None) -> None:
        """
        Initialize queue with joblog store.

        Args:
            store: SQLiteJobLogStore instance (creates one if not provided)
        """
        self._store = store or SQLiteJobLogStore()

    def enqueue(self, item: Dict[str, Any]) -> str:
        """
        Add a job to the queue.

        Args:
            item: Job parameters (op_type, blade_id, material, gcode, etc.)

        Returns:
            Job ID for tracking

        Example:
            job_id = queue.enqueue({
                "op_type": "slice",
                "blade_id": "blade_001",
                "material": "maple",
            })
        """
        job_data = {
            "job_type": JOB_TYPE_SAW_QUEUE,
            "status": "pending",
            "parameters": item,
            "results": {},
        }
        created = self._store.create(job_data)
        return created["id"]

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get the next pending job and mark it as running.

        Returns:
            Job dict if available, None if queue is empty

        Example:
            job = queue.dequeue()
            if job:
                process(job["parameters"])
                queue.complete(job["id"])
        """
        # Get oldest pending job
        pending = self._store.get_by_status("pending", limit=1)
        if not pending:
            return None

        job = pending[0]
        job_id = job["id"]

        # Mark as running
        self._store.update_status(
            job_id,
            status="running",
        )

        # Refresh and return
        return self._store.get_job(job_id)

    def peek(self) -> Optional[Dict[str, Any]]:
        """
        View the next pending job without removing it.

        Returns:
            Next pending job or None if queue is empty
        """
        pending = self._store.get_by_status("pending", limit=1)
        return pending[0] if pending else None

    def complete(
        self,
        job_id: str,
        results: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a job as completed.

        Args:
            job_id: Job ID to complete
            results: Optional results data

        Returns:
            Updated job or None if not found
        """
        return self._store.update_status(
            job_id,
            status="completed",
            end_time=datetime.utcnow().isoformat(),
            results=results,
        )

    def fail(
        self,
        job_id: str,
        error: str,
        results: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a job as failed.

        Args:
            job_id: Job ID that failed
            error: Error message
            results: Optional partial results

        Returns:
            Updated job or None if not found
        """
        result_data = results or {}
        result_data["error"] = error
        return self._store.update_status(
            job_id,
            status="failed",
            end_time=datetime.utcnow().isoformat(),
            results=result_data,
        )

    def requeue(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Move a failed/running job back to pending.

        Args:
            job_id: Job ID to requeue

        Returns:
            Updated job or None if not found
        """
        return self._store.update_status(job_id, status="pending")

    def snapshot(self) -> List[Dict[str, Any]]:
        """
        Get all pending jobs in queue order (oldest first).

        Returns:
            List of pending jobs
        """
        return self._store.get_by_status("pending")

    def running(self) -> List[Dict[str, Any]]:
        """
        Get all currently running jobs.

        Returns:
            List of running jobs
        """
        return self._store.get_by_status("running")

    def history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recently completed/failed jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of completed/failed jobs, newest first
        """
        completed = self._store.get_by_status("completed", limit=limit)
        failed = self._store.get_by_status("failed", limit=limit)

        # Combine and sort by created_at descending
        all_jobs = completed + failed
        all_jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
        return all_jobs[:limit]

    def size(self) -> int:
        """
        Get number of pending jobs.

        Returns:
            Queue size
        """
        return len(self.snapshot())

    def clear_pending(self) -> int:
        """
        Remove all pending jobs from the queue.

        Returns:
            Number of jobs removed
        """
        pending = self.snapshot()
        count = 0
        for job in pending:
            if self._store.delete(job["id"]):
                count += 1
        return count

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job dict or None if not found
        """
        return self._store.get_job(job_id)


# Singleton instance
_queue: Optional[SawLabQueue] = None


def get_saw_lab_queue() -> SawLabQueue:
    """Get singleton queue instance."""
    global _queue
    if _queue is None:
        _queue = SawLabQueue()
    return _queue
