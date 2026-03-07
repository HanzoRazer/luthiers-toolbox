"""Smoke tests for CAM drilling endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_drilling_gcode_g81(client):
    """POST /api/cam/drilling/gcode generates G81 drilling cycles."""
    response = client.post(
        "/api/cam/drilling/gcode",
        json={
            "holes": [
                {"x": 10.0, "y": 20.0, "z": -5.0, "feed": 100.0},
                {"x": 30.0, "y": 40.0, "z": -5.0, "feed": 100.0}
            ],
            "cycle": "G81",
            "safe_z": 5.0,
            "r_clear": 2.0
        }
    )
    assert response.status_code == 200
    gcode = response.text
    assert "G81" in gcode
    assert "X10.000" in gcode
    assert "Y20.000" in gcode
    assert "Z-5.000" in gcode
    assert "G80" in gcode  # Modal cancel


def test_drilling_gcode_g83_peck(client):
    """POST /api/cam/drilling/gcode generates G83 peck drilling cycles."""
    response = client.post(
        "/api/cam/drilling/gcode",
        json={
            "holes": [
                {"x": 15.0, "y": 25.0, "z": -10.0, "feed": 80.0}
            ],
            "cycle": "G83",
            "peck_q": 2.0,
            "safe_z": 5.0,
            "r_clear": 3.0
        }
    )
    assert response.status_code == 200
    gcode = response.text
    assert "G83" in gcode
    assert "Q2.000" in gcode  # Peck depth
    assert "X15.000" in gcode
    assert "G80" in gcode


def test_drilling_info(client):
    """GET /api/cam/drilling/info returns operation metadata."""
    response = client.get("/api/cam/drilling/info")
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "drilling"
    assert "cycles" in data
    assert "G81" in data["cycles"]
    assert "G83" in data["cycles"]
