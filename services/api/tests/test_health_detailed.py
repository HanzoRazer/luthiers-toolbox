"""Tests for /api/health/detailed endpoint (Phase 6 Observability)."""

import pytest
from fastapi.testclient import TestClient


def test_health_detailed_returns_ok_status(client: TestClient):
    """Test that /api/health/detailed returns expected structure."""
    response = client.get("/api/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0
    assert "version" in data
    assert "features" in data
    assert "loaded" in data["features"]
    assert "loaded_count" in data["features"]
    assert "failed" in data["features"]
    assert "failed_count" in data["features"]


def test_health_detailed_uptime_increases(client: TestClient):
    """Test that uptime increases between calls."""
    import time

    response1 = client.get("/api/health/detailed")
    uptime1 = response1.json()["uptime_seconds"]

    time.sleep(0.1)  # Wait a bit

    response2 = client.get("/api/health/detailed")
    uptime2 = response2.json()["uptime_seconds"]

    assert uptime2 >= uptime1


def test_health_detailed_has_version(client: TestClient):
    """Test that version field is present."""
    response = client.get("/api/health/detailed")
    data = response.json()

    # Version should be a non-empty string
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


def test_features_endpoint_returns_structure(client: TestClient):
    """Test that /api/features returns expected structure."""
    response = client.get("/api/features")
    assert response.status_code == 200

    data = response.json()
    assert "loaded" in data
    assert "loaded_count" in data
    assert "failed" in data
    assert "failed_count" in data
    assert "total_routes" in data
    assert isinstance(data["loaded"], dict)
    assert isinstance(data["failed"], dict)
    assert isinstance(data["total_routes"], int)
