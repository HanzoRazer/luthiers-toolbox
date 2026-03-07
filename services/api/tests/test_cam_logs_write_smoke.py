"""Smoke tests for CAM logs write endpoint (proxied to logs_router)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_logs_write_returns_run_id(client):
    """POST /api/cam/logs/write returns run_id on success."""
    response = client.post(
        "/api/cam/logs/write",
        json={
            "run": {
                "machine_id": "GRBL_3018_Default",
                "material_id": "maple_hard",
                "tool_d": 6.0,
                "stepover": 0.4,
                "stepdown": 1.0,
            },
            "segments": [
                {"idx": 0, "code": "G0", "x": 0, "y": 0},
                {"idx": 1, "code": "G1", "x": 10, "y": 0, "len_mm": 10.0, "feed_f": 1000},
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data.get("status") == "ok"


def test_logs_write_minimal_run(client):
    """POST /api/cam/logs/write works with minimal required fields."""
    response = client.post(
        "/api/cam/logs/write",
        json={
            "run": {
                "machine_id": "test_machine",
                "material_id": "test_material",
                "tool_d": 3.0,
                "stepover": 0.5,
                "stepdown": 0.5,
            },
            "segments": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data


def test_logs_write_validation_error(client):
    """POST /api/cam/logs/write returns 422 for missing required fields."""
    response = client.post(
        "/api/cam/logs/write",
        json={
            "run": {
                "machine_id": "test",
                # Missing required fields: material_id, tool_d, stepover, stepdown
            },
            "segments": []
        }
    )
    assert response.status_code == 422


def test_logs_write_with_full_segment_details(client):
    """POST /api/cam/logs/write handles full segment details."""
    response = client.post(
        "/api/cam/logs/write",
        json={
            "run": {
                "job_name": "test_job",
                "machine_id": "GRBL_3018_Default",
                "material_id": "walnut",
                "tool_d": 6.35,
                "stepover": 0.4,
                "stepdown": 2.0,
                "post_id": "GRBL",
                "feed_xy": 1500,
                "rpm": 18000,
                "est_time_s": 120.5,
            },
            "segments": [
                {"idx": 0, "code": "G0", "x": 0, "y": 0, "limit": "none"},
                {"idx": 1, "code": "G1", "x": 50, "y": 0, "len_mm": 50.0, "limit": "feed_cap", "feed_f": 1500},
                {"idx": 2, "code": "G2", "x": 50, "y": 50, "len_mm": 78.5, "limit": "accel", "radius_mm": 50.0},
                {"idx": 3, "code": "G1", "x": 0, "y": 50, "len_mm": 50.0, "limit": "jerk", "trochoid": True},
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "run_id" in data
