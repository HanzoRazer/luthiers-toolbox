"""Smoke tests for CAM risk reports index endpoint (proxied to cam_risk_router)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_risk_reports_index_returns_reports_array(client):
    """GET /api/cam/risk/reports_index returns reports array."""
    response = client.get("/api/cam/risk/reports_index")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert "total" in data
    assert isinstance(data["reports"], list)
    assert isinstance(data["total"], int)


def test_risk_reports_index_total_matches_length(client):
    """GET /api/cam/risk/reports_index total matches reports length."""
    response = client.get("/api/cam/risk/reports_index")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(data["reports"])


def test_risk_reports_index_respects_limit(client):
    """GET /api/cam/risk/reports_index respects limit parameter."""
    response = client.get("/api/cam/risk/reports_index?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["reports"]) <= 5


def test_risk_reports_index_accepts_preset_filter(client):
    """GET /api/cam/risk/reports_index accepts preset filter."""
    response = client.get("/api/cam/risk/reports_index?preset=GRBL")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    # All reports should match preset filter if any exist
    for report in data["reports"]:
        assert report.get("preset") == "GRBL"


def test_risk_reports_index_accepts_lane_filter(client):
    """GET /api/cam/risk/reports_index accepts lane filter."""
    response = client.get("/api/cam/risk/reports_index?lane=roughing")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
