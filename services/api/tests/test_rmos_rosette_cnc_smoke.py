"""Smoke tests for RMOS rosette CNC endpoints (proxied to art_jobs_store)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_rosette_cnc_history_returns_jobs_array(client):
    """GET /api/rmos/rosette/cnc-history returns jobs array."""
    response = client.get("/api/rmos/rosette/cnc-history")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert isinstance(data["jobs"], list)
    assert isinstance(data["total"], int)


def test_rosette_cnc_history_respects_limit(client):
    """GET /api/rmos/rosette/cnc-history respects limit parameter."""
    response = client.get("/api/rmos/rosette/cnc-history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) <= 5


def test_rosette_cnc_history_accepts_job_type_filter(client):
    """GET /api/rmos/rosette/cnc-history accepts job_type filter."""
    response = client.get("/api/rmos/rosette/cnc-history?job_type=rosette_cam")
    assert response.status_code == 200
    data = response.json()
    # All jobs should match filter if any exist
    for job in data["jobs"]:
        assert job.get("job_type") == "rosette_cam"


def test_rosette_cnc_job_nonexistent_returns_404(client):
    """GET /api/rmos/rosette/cnc-job/{job_id} returns 404 for nonexistent."""
    response = client.get("/api/rmos/rosette/cnc-job/NONEXISTENT_JOB_ID_XYZ")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_rosette_cnc_history_total_matches_length(client):
    """GET /api/rmos/rosette/cnc-history total >= returned jobs length."""
    response = client.get("/api/rmos/rosette/cnc-history?limit=5")
    assert response.status_code == 200
    data = response.json()
    # total should be >= len(jobs) since we might have limited results
    assert data["total"] >= len(data["jobs"])
