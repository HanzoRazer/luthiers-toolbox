"""Smoke tests for CAM feeds/speeds optimization endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_feeds_speeds_with_preset(client):
    """POST /api/cam/opt/feeds-speeds returns calculated parameters."""
    response = client.post(
        "/api/cam/opt/feeds-speeds",
        json={
            "tool_id": "upcut_1_4",
            "material": "hardwood",
            "strategy": "roughing"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "feed_xy" in data
    assert "rpm" in data
    assert "stepdown_mm" in data
    assert "chipload_mm" in data
    assert "heat_rating" in data
    assert "notes" in data


def test_feeds_speeds_fallback_to_geometry(client):
    """POST /api/cam/opt/feeds-speeds falls back to geometry-based calculation."""
    response = client.post(
        "/api/cam/opt/feeds-speeds",
        json={
            "tool_id": "custom_tool",
            "material": "unknown_wood",
            "strategy": "roughing",
            "flutes": 3,
            "diameter_mm": 8.0,
            "stickout_mm": 30.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Calculated from tool geometry" in data["notes"]
    assert data["feed_xy"] > 0
    assert data["rpm"] > 0


def test_feeds_speeds_finishing_strategy(client):
    """POST /api/cam/opt/feeds-speeds supports finishing strategy."""
    response = client.post(
        "/api/cam/opt/feeds-speeds",
        json={
            "tool_id": "ballnose_1_8",
            "material": "softwood",
            "strategy": "finishing"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "finishing"
    assert data["feed_xy"] > 0
