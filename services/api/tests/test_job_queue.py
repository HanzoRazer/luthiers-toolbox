"""
Job Queue Tests
===============

Unit and integration tests for the async job queue system.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.job_queue import JobQueue, JobStatus, JobState, get_job_queue
from app.core.job_queue.schemas import JobPriority


# =============================================================================
# Unit Tests: JobStatus
# =============================================================================


class TestJobStatus:
    """Tests for JobStatus dataclass."""

    def test_job_status_creation(self):
        """JobStatus can be created with required fields."""
        job = JobStatus(
            job_id="test-123",
            job_type="cam_generation",
            state=JobState.PENDING,
        )
        assert job.job_id == "test-123"
        assert job.job_type == "cam_generation"
        assert job.state == JobState.PENDING
        assert job.priority == JobPriority.NORMAL

    def test_job_status_to_dict(self):
        """JobStatus can be serialized to dictionary."""
        job = JobStatus(
            job_id="test-123",
            job_type="cam_generation",
            state=JobState.PENDING,
            params={"dxf_id": "abc"},
            tags=["test", "ci"],
        )
        data = job.to_dict()

        assert data["job_id"] == "test-123"
        assert data["job_type"] == "cam_generation"
        assert data["state"] == "pending"
        assert data["params"] == {"dxf_id": "abc"}
        assert data["tags"] == ["test", "ci"]

    def test_job_status_from_dict(self):
        """JobStatus can be deserialized from dictionary."""
        data = {
            "job_id": "test-456",
            "job_type": "dxf_export",
            "state": "running",
            "priority": "high",
            "params": {"format": "svg"},
            "created_at": "2026-01-01T00:00:00",
            "tags": [],
        }
        job = JobStatus.from_dict(data)

        assert job.job_id == "test-456"
        assert job.job_type == "dxf_export"
        assert job.state == JobState.RUNNING
        assert job.priority == JobPriority.HIGH

    def test_job_duration_calculation(self):
        """Duration is calculated from started_at and completed_at."""
        job = JobStatus(
            job_id="test-123",
            job_type="test",
            state=JobState.COMPLETED,
            started_at=datetime(2026, 1, 1, 0, 0, 0),
            completed_at=datetime(2026, 1, 1, 0, 0, 30),
        )
        assert job.duration_seconds == 30.0

    def test_job_duration_running(self):
        """Duration is calculated for running jobs."""
        job = JobStatus(
            job_id="test-123",
            job_type="test",
            state=JobState.RUNNING,
            started_at=datetime.utcnow() - timedelta(seconds=10),
        )
        assert job.duration_seconds >= 10.0


# =============================================================================
# Unit Tests: JobQueue
# =============================================================================


class TestJobQueue:
    """Tests for JobQueue class."""

    @pytest.fixture
    def queue(self):
        """Create fresh job queue for each test."""
        return JobQueue()

    @pytest.mark.asyncio
    async def test_submit_job(self, queue):
        """Jobs can be submitted to the queue."""
        job_id = await queue.submit(
            job_type="test_job",
            params={"key": "value"},
        )

        assert job_id is not None
        job = await queue.get_status(job_id)
        assert job is not None
        assert job.state == JobState.PENDING
        assert job.params == {"key": "value"}

    @pytest.mark.asyncio
    async def test_submit_with_priority(self, queue):
        """Jobs can be submitted with different priorities."""
        low_id = await queue.submit(job_type="test", priority=JobPriority.LOW)
        high_id = await queue.submit(job_type="test", priority=JobPriority.HIGH)

        low_job = await queue.get_status(low_id)
        high_job = await queue.get_status(high_id)

        assert low_job.priority == JobPriority.LOW
        assert high_job.priority == JobPriority.HIGH

    @pytest.mark.asyncio
    async def test_submit_with_idempotency(self, queue):
        """Idempotency key prevents duplicate jobs."""
        job_id_1 = await queue.submit(
            job_type="test",
            idempotency_key="unique-key-123",
        )
        job_id_2 = await queue.submit(
            job_type="test",
            idempotency_key="unique-key-123",
        )

        assert job_id_1 == job_id_2  # Same job returned

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, queue):
        """get_status returns None for unknown job."""
        job = await queue.get_status("nonexistent-id")
        assert job is None

    @pytest.mark.asyncio
    async def test_cancel_pending_job(self, queue):
        """Pending jobs can be cancelled."""
        job_id = await queue.submit(job_type="test")

        success = await queue.cancel(job_id, reason="Test cancellation")
        assert success is True

        job = await queue.get_status(job_id)
        assert job.state == JobState.CANCELLED
        assert job.error == "Test cancellation"

    @pytest.mark.asyncio
    async def test_cancel_completed_job_fails(self, queue):
        """Completed jobs cannot be cancelled."""
        job_id = await queue.submit(job_type="test")
        job = await queue.get_status(job_id)
        job.state = JobState.COMPLETED

        success = await queue.cancel(job_id)
        assert success is False

    @pytest.mark.asyncio
    async def test_list_jobs(self, queue):
        """Jobs can be listed with filters."""
        await queue.submit(job_type="type_a", tags=["tag1"])
        await queue.submit(job_type="type_b", tags=["tag2"])
        await queue.submit(job_type="type_a", tags=["tag1"])

        # List all
        all_jobs = await queue.list_jobs()
        assert len(all_jobs) == 3

        # Filter by type
        type_a_jobs = await queue.list_jobs(job_type="type_a")
        assert len(type_a_jobs) == 2

        # Filter by tags
        tag1_jobs = await queue.list_jobs(tags=["tag1"])
        assert len(tag1_jobs) == 2

    @pytest.mark.asyncio
    async def test_get_stats(self, queue):
        """Queue stats are calculated correctly."""
        await queue.submit(job_type="test")
        await queue.submit(job_type="test")

        stats = await queue.get_stats()
        assert stats["pending"] == 2
        assert stats["running"] == 0

    @pytest.mark.asyncio
    async def test_update_progress(self, queue):
        """Progress can be updated for running jobs."""
        job_id = await queue.submit(job_type="test")
        job = await queue.get_status(job_id)
        job.state = JobState.RUNNING

        success = await queue.update_progress(job_id, 50, "Halfway done")
        assert success is True

        job = await queue.get_status(job_id)
        assert job.progress_percent == 50
        assert job.progress_message == "Halfway done"

    @pytest.mark.asyncio
    async def test_retry_failed_job(self, queue):
        """Failed jobs can be retried."""
        job_id = await queue.submit(job_type="test", params={"x": 1})
        job = await queue.get_status(job_id)
        job.state = JobState.FAILED
        job.error = "Test failure"

        new_job_id = await queue.retry(job_id)
        assert new_job_id is not None
        assert new_job_id != job_id

        new_job = await queue.get_status(new_job_id)
        assert new_job.state == JobState.PENDING
        assert new_job.params == {"x": 1}

    @pytest.mark.asyncio
    async def test_retry_non_failed_job_returns_none(self, queue):
        """Only failed jobs can be retried."""
        job_id = await queue.submit(job_type="test")  # Pending

        new_job_id = await queue.retry(job_id)
        assert new_job_id is None

    @pytest.mark.asyncio
    async def test_cleanup_old_jobs(self, queue):
        """Old completed jobs are cleaned up."""
        job_id = await queue.submit(job_type="test")
        job = await queue.get_status(job_id)
        job.state = JobState.COMPLETED
        job.completed_at = datetime.utcnow() - timedelta(hours=48)

        removed = await queue.cleanup_old_jobs(max_age_hours=24)
        assert removed == 1

        job = await queue.get_status(job_id)
        assert job is None


# =============================================================================
# Integration Tests: Router
# =============================================================================


class TestJobQueueRouter:
    """Integration tests for job queue REST endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with full app (includes middleware)."""
        from fastapi.testclient import TestClient
        from app.main import app

        return TestClient(app)

    def test_submit_job_endpoint(self, client):
        """POST /api/jobs creates a new job."""
        response = client.post(
            "/api/jobs",
            json={
                "job_type": "test_job",
                "params": {"key": "value"},
                "priority": "high",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "job_id" in data
        assert data["job_type"] == "test_job"
        assert data["state"] == "pending"

    def test_get_job_status_endpoint(self, client):
        """GET /api/jobs/{id} returns job status."""
        # Create a job first
        create_response = client.post(
            "/api/jobs",
            json={"job_type": "test_job"},
        )
        job_id = create_response.json()["job_id"]

        # Get status
        response = client.get(f"/api/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["state"] == "pending"

    def test_get_job_status_not_found(self, client):
        """GET /api/jobs/{id} returns 404 for unknown job."""
        response = client.get("/api/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_list_jobs_endpoint(self, client):
        """GET /api/jobs lists all jobs."""
        # Create some jobs
        client.post("/api/jobs", json={"job_type": "type_a"})
        client.post("/api/jobs", json={"job_type": "type_b"})

        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["jobs"]) >= 2

    def test_list_jobs_with_filter(self, client):
        """GET /api/jobs with filters."""
        client.post("/api/jobs", json={"job_type": "filter_test"})

        response = client.get("/api/jobs?job_type=filter_test")

        assert response.status_code == 200
        data = response.json()
        assert all(j["job_type"] == "filter_test" for j in data["jobs"])

    def test_cancel_job_endpoint(self, client):
        """POST /api/jobs/{id}/cancel cancels a job."""
        # Create a job
        create_response = client.post(
            "/api/jobs",
            json={"job_type": "test_job"},
        )
        job_id = create_response.json()["job_id"]

        # Cancel it
        response = client.post(
            f"/api/jobs/{job_id}/cancel",
            json={"reason": "Test cancel"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "cancelled"

    def test_queue_stats_endpoint(self, client):
        """GET /api/jobs/stats returns queue statistics."""
        response = client.get("/api/jobs/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "pending" in data
        assert "running" in data

    def test_queue_health_endpoint(self, client):
        """GET /api/jobs/health returns health status."""
        response = client.get("/api/jobs/health")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


# =============================================================================
# Worker Tests
# =============================================================================


class TestJobWorker:
    """Tests for background job processing."""

    @pytest.fixture
    def queue(self):
        """Create fresh job queue."""
        return JobQueue()

    @pytest.mark.asyncio
    async def test_worker_processes_job(self, queue):
        """Worker processes pending jobs."""
        from app.core.job_queue.queue import register_handler

        # Register a simple handler
        results = []

        async def test_handler(params, job):
            results.append(params)
            return {"processed": True}

        with patch.dict(
            "app.core.job_queue.queue_execution._HANDLER_REGISTRY",
            {"test_job": "test.handler"},
        ):
            with patch(
                "app.core.job_queue.queue_execution.get_handler",
                return_value=test_handler,
            ):
                # Submit job
                job_id = await queue.submit(
                    job_type="test_job",
                    params={"value": 42},
                )

                # Start workers
                await queue.start_workers(num_workers=1)

                # Wait for processing
                await asyncio.sleep(0.5)

                # Stop workers
                await queue.stop_workers(timeout=1.0)

                # Check result
                job = await queue.get_status(job_id)
                assert job.state == JobState.COMPLETED
                assert job.result == {"processed": True}
                assert len(results) == 1
                assert results[0] == {"value": 42}

    @pytest.mark.asyncio
    async def test_worker_handles_failure(self, queue):
        """Worker handles job failures gracefully."""

        async def failing_handler(params, job):
            raise ValueError("Intentional failure")

        with patch.dict(
            "app.core.job_queue.queue_execution._HANDLER_REGISTRY",
            {"fail_job": "test.handler"},
        ):
            with patch(
                "app.core.job_queue.queue_execution.get_handler",
                return_value=failing_handler,
            ):
                job_id = await queue.submit(
                    job_type="fail_job",
                    max_retries=0,  # No retries for this test
                )

                await queue.start_workers(num_workers=1)
                await asyncio.sleep(0.5)
                await queue.stop_workers(timeout=1.0)

                job = await queue.get_status(job_id)
                assert job.state == JobState.FAILED
                assert "Intentional failure" in job.error

    @pytest.mark.asyncio
    async def test_worker_respects_priority(self, queue):
        """Higher priority jobs are processed first."""
        processed_order = []

        async def tracking_handler(params, job):
            processed_order.append(params["order"])
            return {"order": params["order"]}

        with patch.dict(
            "app.core.job_queue.queue_execution._HANDLER_REGISTRY",
            {"priority_test": "test.handler"},
        ):
            with patch(
                "app.core.job_queue.queue_execution.get_handler",
                return_value=tracking_handler,
            ):
                # Submit in reverse priority order
                await queue.submit(
                    job_type="priority_test",
                    params={"order": 3},
                    priority=JobPriority.LOW,
                )
                await queue.submit(
                    job_type="priority_test",
                    params={"order": 1},
                    priority=JobPriority.CRITICAL,
                )
                await queue.submit(
                    job_type="priority_test",
                    params={"order": 2},
                    priority=JobPriority.HIGH,
                )

                await queue.start_workers(num_workers=1)
                await asyncio.sleep(1.0)
                await queue.stop_workers(timeout=1.0)

                # Should be processed in priority order
                assert processed_order == [1, 2, 3]
