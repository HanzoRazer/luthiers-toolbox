"""Smoke tests for CAM probe setup sheet endpoint (proxied to setup_router)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_probe_setup_sheet_corner_outside_returns_svg(client):
    """POST /api/cam/probe/svg_setup_sheet returns SVG for corner_outside pattern."""
    response = client.post(
        "/api/cam/probe/svg_setup_sheet",
        json={
            "pattern": "corner_outside",
            "estimated_diameter": 50.0
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    content = response.text
    assert "<svg" in content
    assert "</svg>" in content


def test_probe_setup_sheet_boss_circular_returns_svg(client):
    """POST /api/cam/probe/svg_setup_sheet returns SVG for boss_circular pattern."""
    response = client.post(
        "/api/cam/probe/svg_setup_sheet",
        json={
            "pattern": "boss_circular",
            "estimated_diameter": 75.0
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    content = response.text
    assert "<svg" in content


def test_probe_setup_sheet_surface_z_returns_svg(client):
    """POST /api/cam/probe/svg_setup_sheet returns SVG for surface_z pattern."""
    response = client.post(
        "/api/cam/probe/svg_setup_sheet",
        json={
            "pattern": "surface_z"
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    content = response.text
    assert "<svg" in content


def test_probe_setup_sheet_invalid_pattern_returns_422(client):
    """POST /api/cam/probe/svg_setup_sheet returns 422 for invalid pattern."""
    response = client.post(
        "/api/cam/probe/svg_setup_sheet",
        json={
            "pattern": "nonexistent_pattern",
            "estimated_diameter": 50.0
        }
    )
    # Invalid pattern rejected by Pydantic schema validation
    assert response.status_code == 422
