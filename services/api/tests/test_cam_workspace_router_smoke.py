"""Smoke tests for CAM Workspace router (Neck Pipeline Wizard)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# =============================================================================
# GET endpoints
# =============================================================================

def test_neck_operations_endpoint_exists(client):
    """GET /api/cam-workspace/neck/operations returns non-404."""
    resp = client.get("/api/cam-workspace/neck/operations")
    assert resp.status_code != 404


def test_neck_operations_returns_list(client):
    """GET /api/cam-workspace/neck/operations returns operations list."""
    resp = client.get("/api/cam-workspace/neck/operations")
    assert resp.status_code == 200
    data = resp.json()
    assert "operations" in data
    assert isinstance(data["operations"], list)


def test_status_endpoint_exists(client):
    """GET /api/cam-workspace/status returns non-404."""
    resp = client.get("/api/cam-workspace/status")
    assert resp.status_code != 404


def test_status_returns_availability(client):
    """GET /api/cam-workspace/status returns availability info."""
    resp = client.get("/api/cam-workspace/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "available" in data


def test_machines_endpoint_exists(client):
    """GET /api/cam-workspace/machines returns non-404."""
    resp = client.get("/api/cam-workspace/machines")
    assert resp.status_code != 404


def test_machines_returns_list(client):
    """GET /api/cam-workspace/machines returns machines list."""
    resp = client.get("/api/cam-workspace/machines")
    assert resp.status_code == 200
    data = resp.json()
    assert "machines" in data


# =============================================================================
# POST /neck/evaluate — uses defaults for all fields
# =============================================================================

def test_evaluate_endpoint_exists(client):
    """POST /api/cam-workspace/neck/evaluate returns non-404."""
    resp = client.post("/api/cam-workspace/neck/evaluate", json={})
    assert resp.status_code != 404


def test_evaluate_returns_result(client):
    """POST /api/cam-workspace/neck/evaluate returns gate checks."""
    resp = client.post("/api/cam-workspace/neck/evaluate", json={})
    # May be 200 (pipeline available) or 503 (pipeline unavailable)
    assert resp.status_code in (200, 503)


# =============================================================================
# POST /neck/generate/{op} — single op generation
# =============================================================================

def test_generate_single_op_endpoint_exists(client):
    """POST /api/cam-workspace/neck/generate/truss_rod returns non-404."""
    resp = client.post("/api/cam-workspace/neck/generate/truss_rod", json={})
    assert resp.status_code != 404


def test_generate_single_op_result(client):
    """POST /api/cam-workspace/neck/generate/truss_rod returns gcode or 503."""
    resp = client.post("/api/cam-workspace/neck/generate/truss_rod", json={})
    assert resp.status_code in (200, 503)


# =============================================================================
# POST /neck/generate-full — full pipeline
# =============================================================================

def test_generate_full_endpoint_exists(client):
    """POST /api/cam-workspace/neck/generate-full returns non-404."""
    resp = client.post("/api/cam-workspace/neck/generate-full", json={})
    assert resp.status_code != 404


def test_generate_full_result(client):
    """POST /api/cam-workspace/neck/generate-full returns gcode or 503."""
    resp = client.post("/api/cam-workspace/neck/generate-full", json={})
    assert resp.status_code in (200, 503)
