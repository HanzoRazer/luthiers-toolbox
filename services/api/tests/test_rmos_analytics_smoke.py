"""Smoke tests for RMOS Analytics endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_analytics_summary(client):
    """GET /api/rmos/analytics/summary returns valid response."""
    response = client.get("/api/rmos/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "by_status" in data
    assert "by_risk_level" in data


def test_analytics_lane_analytics(client):
    """GET /api/rmos/analytics/lane-analytics returns valid response."""
    response = client.get("/api/rmos/analytics/lane-analytics")
    assert response.status_code == 200
    data = response.json()
    assert "lanes" in data
    assert "total_runs" in data
    assert isinstance(data["lanes"], list)


def test_analytics_risk_timeline(client):
    """GET /api/rmos/analytics/risk-timeline returns valid response."""
    response = client.get("/api/rmos/analytics/risk-timeline")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)


def test_analytics_trends(client):
    """GET /api/rmos/analytics/trends returns valid response."""
    response = client.get("/api/rmos/analytics/trends")
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert "period_days" in data


def test_analytics_export(client):
    """GET /api/rmos/analytics/export returns valid response."""
    response = client.get("/api/rmos/analytics/export")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "lanes" in data
    assert "trends" in data
