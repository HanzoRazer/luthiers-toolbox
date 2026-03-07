"""Smoke tests for CAM what-if optimization endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_what_if_requires_moves(client):
    """POST /api/cam/opt/what_if returns 400 without moves."""
    response = client.post(
        "/api/cam/opt/what_if",
        json={
            "machine_profile_id": "GRBL_3018_Default",
            "z_total": -3.0,
            "stepdown": 1.0,
            "safe_z": 5.0
        }
    )
    assert response.status_code == 400
    assert "moves" in response.json()["detail"].lower()


def test_what_if_with_moves(client):
    """POST /api/cam/opt/what_if returns optimization results with moves."""
    # Minimal set of moves for testing
    moves = [
        {"type": "rapid", "x": 0, "y": 0, "z": 5},
        {"type": "cut", "x": 10, "y": 0, "z": -1, "feed": 1000},
        {"type": "cut", "x": 10, "y": 10, "z": -1, "feed": 1000},
        {"type": "cut", "x": 0, "y": 10, "z": -1, "feed": 1000},
        {"type": "cut", "x": 0, "y": 0, "z": -1, "feed": 1000},
    ]

    response = client.post(
        "/api/cam/opt/what_if",
        json={
            "moves": moves,
            "machine_profile_id": "GRBL_3018_Default",
            "z_total": -3.0,
            "stepdown": 1.0,
            "safe_z": 5.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "baseline" in data
    assert "opt" in data


def test_what_if_invalid_profile(client):
    """POST /api/cam/opt/what_if returns 404 for invalid profile."""
    response = client.post(
        "/api/cam/opt/what_if",
        json={
            "moves": [{"type": "rapid", "x": 0, "y": 0, "z": 5}],
            "machine_profile_id": "nonexistent_profile",
            "z_total": -3.0,
            "stepdown": 1.0,
            "safe_z": 5.0
        }
    )
    assert response.status_code == 404
    assert "profile" in response.json()["detail"].lower()
