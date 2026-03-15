"""Smoke tests for CAM adaptive2 endpoints (proxied to benchmark_router)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_adaptive2_bench_returns_timing_stats(client):
    """POST /api/cam/bench returns benchmark timing statistics."""
    response = client.post(
        "/api/cam/bench",
        json={
            "width": 100.0,
            "height": 60.0,
            "tool_dia": 6.0,
            "stepover": 2.4,
            "runs": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert "avg_ms" in data
    assert "total_ms" in data
    assert data["runs"] == 5


def test_adaptive2_offset_spiral_returns_svg(client):
    """POST /api/cam/offset_spiral.svg returns SVG content."""
    response = client.post(
        "/api/cam/offset_spiral.svg",
        json={
            "width": 100.0,
            "height": 60.0,
            "tool_dia": 6.0,
            "stepover": 2.4,
            "corner_fillet": 0.5
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    content = response.text
    assert "<svg" in content
    assert "</svg>" in content


def test_adaptive2_trochoid_corners_returns_svg(client):
    """POST /api/cam/trochoid_corners.svg returns SVG content."""
    response = client.post(
        "/api/cam/trochoid_corners.svg",
        json={
            "width": 100.0,
            "height": 60.0,
            "tool_dia": 6.0,
            "loop_pitch": 2.5,
            "amp": 0.4
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    content = response.text
    assert "<svg" in content
    assert "</svg>" in content


def test_adaptive2_bench_validation_errors(client):
    """POST /api/cam/bench returns 422 for invalid params."""
    response = client.post(
        "/api/cam/bench",
        json={
            "width": 100.0,
            "height": 60.0,
            "tool_dia": -1.0,  # Invalid: must be positive
            "stepover": 2.4,
            "runs": 5
        }
    )
    assert response.status_code == 422


def test_adaptive2_offset_spiral_validation_errors(client):
    """POST /api/cam/offset_spiral.svg returns 422 for invalid params."""
    response = client.post(
        "/api/cam/offset_spiral.svg",
        json={
            "width": -10.0,  # Invalid: must be positive
            "height": 60.0,
            "tool_dia": 6.0,
            "stepover": 2.4
        }
    )
    assert response.status_code == 422
