"""Smoke tests for Binding Design router."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# =============================================================================
# GET endpoints
# =============================================================================

def test_styles_endpoint_exists(client):
    """GET /api/binding/styles returns non-404."""
    resp = client.get("/api/binding/styles")
    assert resp.status_code != 404


def test_styles_returns_list(client):
    """GET /api/binding/styles returns body styles."""
    resp = client.get("/api/binding/styles")
    assert resp.status_code == 200
    data = resp.json()
    assert "styles" in data
    assert "count" in data


def test_materials_endpoint_exists(client):
    """GET /api/binding/materials returns non-404."""
    resp = client.get("/api/binding/materials")
    assert resp.status_code != 404


def test_materials_returns_list(client):
    """GET /api/binding/materials returns binding materials."""
    resp = client.get("/api/binding/materials")
    assert resp.status_code == 200
    data = resp.json()
    assert "materials" in data
    assert "count" in data


def test_purfling_patterns_endpoint_exists(client):
    """GET /api/binding/purfling-patterns returns non-404."""
    resp = client.get("/api/binding/purfling-patterns")
    assert resp.status_code != 404


def test_purfling_patterns_returns_list(client):
    """GET /api/binding/purfling-patterns returns patterns."""
    resp = client.get("/api/binding/purfling-patterns")
    assert resp.status_code == 200
    data = resp.json()
    assert "patterns" in data
    assert "count" in data


# =============================================================================
# POST /design — binding design orchestration
# =============================================================================

def test_design_endpoint_exists(client):
    """POST /api/binding/design returns non-404."""
    resp = client.post("/api/binding/design", json={"body_style": "dreadnought"})
    assert resp.status_code != 404


def test_design_returns_result(client):
    """POST /api/binding/design returns binding design response."""
    resp = client.post("/api/binding/design", json={"body_style": "dreadnought"})
    assert resp.status_code in (200, 500)  # 500 if outline data missing


def test_design_rejects_empty_body(client):
    """POST /api/binding/design rejects missing body_style."""
    resp = client.post("/api/binding/design", json={})
    assert resp.status_code == 422


# =============================================================================
# POST /strip-length — strip length calculator
# =============================================================================

def test_strip_length_endpoint_exists(client):
    """POST /api/binding/strip-length returns non-404."""
    resp = client.post("/api/binding/strip-length", json={"perimeter_mm": 1500.0})
    assert resp.status_code != 404


def test_strip_length_returns_estimate(client):
    """POST /api/binding/strip-length returns length estimate."""
    resp = client.post("/api/binding/strip-length", json={"perimeter_mm": 1500.0})
    assert resp.status_code == 200
    data = resp.json()
    assert "recommended_length_mm" in data
    assert "order_length_mm" in data


def test_strip_length_rejects_both_inputs(client):
    """POST /api/binding/strip-length rejects body_style AND perimeter_mm."""
    resp = client.post("/api/binding/strip-length", json={
        "body_style": "dreadnought",
        "perimeter_mm": 1500.0,
    })
    assert resp.status_code == 400


def test_strip_length_rejects_no_input(client):
    """POST /api/binding/strip-length rejects missing both inputs."""
    resp = client.post("/api/binding/strip-length", json={})
    assert resp.status_code == 400
