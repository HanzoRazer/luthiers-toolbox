"""Smoke tests for CAM what-if optimization endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.cam.routers.utility.optimization_router import (
    DEFAULT_WHATIF_MAX_GRID_CELLS,
    DEFAULT_WHATIF_MAX_WORK_UNITS,
    OptIn,
    WHATIF_MAX_GRID_CELLS_ENV,
    WHATIF_MAX_WORK_UNITS_ENV,
)


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


def test_what_if_rejects_oversized_grid(client):
    """POST /api/cam/opt/what_if returns 400 when total grid cells exceed cap.

    Guards the O(grid[0]*grid[1]*len(moves)) cost without rejecting cheap
    rectangular grids only because one axis is greater than 12.
    """
    response = client.post(
        "/api/cam/opt/what_if",
        json={
            "moves": [{"type": "rapid", "x": 0, "y": 0, "z": 5}],
            "machine_profile_id": "GRBL_3018_Default",
            "grid": [20, 20],
        },
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "grid" in detail
    assert "maximum" in detail


def test_what_if_allows_rectangular_grid_under_total_cap(client):
    """A non-square grid is valid when total cells stay within the cap."""
    response = client.post(
        "/api/cam/opt/what_if",
        json={
            "moves": [{"type": "rapid", "x": 0, "y": 0, "z": 5}],
            "machine_profile_id": "GRBL_3018_Default",
            "grid": [16, 4],
        },
    )
    assert response.status_code == 200


def test_what_if_rejects_grid_workload_above_configured_cap(client, monkeypatch):
    """The guard considers cells*moves, not just grid shape."""
    monkeypatch.setenv(WHATIF_MAX_WORK_UNITS_ENV, "10")
    response = client.post(
        "/api/cam/opt/what_if",
        json={
            "moves": [{"type": "rapid", "x": 0, "y": 0, "z": 5}],
            "machine_profile_id": "GRBL_3018_Default",
            "grid": [4, 4],
        },
    )
    assert response.status_code == 400
    assert "move-cells" in response.json()["detail"].lower()


def test_what_if_rejects_malformed_grid_shape(client):
    """Malformed grid shape stays an explicit 400 with a user-facing message."""
    response = client.post(
        "/api/cam/opt/what_if",
        json={
            "moves": [{"type": "rapid", "x": 0, "y": 0, "z": 5}],
            "machine_profile_id": "GRBL_3018_Default",
            "grid": [6],
        },
    )
    assert response.status_code == 400
    assert "exactly two" in response.json()["detail"].lower()


def test_what_if_grid_limits_are_visible_in_request_schema():
    """Generated request schema exposes the workload guard and override knobs."""
    schema = OptIn.model_json_schema()
    grid_schema = schema["properties"]["grid"]
    description = grid_schema["description"]
    assert str(DEFAULT_WHATIF_MAX_GRID_CELLS) in description
    assert str(DEFAULT_WHATIF_MAX_WORK_UNITS) in description
    assert WHATIF_MAX_GRID_CELLS_ENV in description
    assert WHATIF_MAX_WORK_UNITS_ENV in description


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
