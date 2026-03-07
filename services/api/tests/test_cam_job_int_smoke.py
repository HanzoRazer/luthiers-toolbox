"""Smoke tests for CAM job intelligence endpoints (proxied to job_int_log service)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_job_int_log_list_returns_items_array(client):
    """GET /api/cam/job-int/log returns items array."""
    response = client.get("/api/cam/job-int/log")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)


def test_job_int_log_list_with_limit(client):
    """GET /api/cam/job-int/log respects limit parameter."""
    response = client.get("/api/cam/job-int/log?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) <= 5


def test_job_int_log_list_with_machine_filter(client):
    """GET /api/cam/job-int/log accepts machine_id filter."""
    response = client.get("/api/cam/job-int/log?machine_id=GRBL_3018")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # All items should match filter if any exist
    for item in data["items"]:
        assert item.get("machine_id") == "GRBL_3018"


def test_job_int_log_get_nonexistent_returns_404(client):
    """GET /api/cam/job-int/log/{run_id} returns 404 for nonexistent."""
    response = client.get("/api/cam/job-int/log/NONEXISTENT_RUN_ID_XYZ")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_job_int_favorites_update_nonexistent_returns_404(client):
    """POST /api/cam/job-int/favorites/{run_id} returns 404 for nonexistent."""
    response = client.post(
        "/api/cam/job-int/favorites/NONEXISTENT_RUN_ID_XYZ",
        json={"favorite": True}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_job_int_favorites_requires_body(client):
    """POST /api/cam/job-int/favorites/{run_id} requires favorite field."""
    response = client.post(
        "/api/cam/job-int/favorites/test_run_id",
        json={}
    )
    assert response.status_code == 422
