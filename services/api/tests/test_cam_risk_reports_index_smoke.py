"""Smoke tests for CAM risk reports endpoint (proxied to cam_risk_router)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_risk_reports_returns_list(client):
    """GET /api/cam/risk/reports returns reports list."""
    response = client.get("/api/cam/risk/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_risk_reports_respects_limit(client):
    """GET /api/cam/risk/reports respects limit parameter."""
    response = client.get("/api/cam/risk/reports?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_risk_reports_accepts_preset_filter(client):
    """GET /api/cam/risk/reports accepts preset filter."""
    response = client.get("/api/cam/risk/reports?preset=GRBL")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_risk_reports_accepts_lane_filter(client):
    """GET /api/cam/risk/reports accepts lane filter."""
    response = client.get("/api/cam/risk/reports?lane=roughing")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_risk_jobs_recent_returns_list(client):
    """GET /api/cam/jobs/recent returns list."""
    response = client.get("/api/cam/jobs/recent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
