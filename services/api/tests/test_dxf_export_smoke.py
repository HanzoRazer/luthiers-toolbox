"""Smoke tests for headstock DXF export endpoints (BCAMCNC 2030A)."""

import pytest
from fastapi.testclient import TestClient

SIMPLE_SVG_PATH = "M 10 10 L 190 10 L 190 310 L 10 310 Z"


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint existence — POST /api/export/headstock-dxf
# =============================================================================

def test_headstock_dxf_endpoint_exists(client):
    """POST /api/export/headstock-dxf returns non-404."""
    resp = client.post("/api/export/headstock-dxf", json={"outline_path": SIMPLE_SVG_PATH})
    assert resp.status_code != 404


def test_headstock_dxf_returns_file(client):
    """POST /api/export/headstock-dxf returns a DXF file response."""
    resp = client.post("/api/export/headstock-dxf", json={"outline_path": SIMPLE_SVG_PATH})
    assert resp.status_code == 200
    assert "application" in resp.headers.get("content-type", "")


# =============================================================================
# Endpoint existence — POST /api/export/headstock-dxf/preview
# =============================================================================

def test_headstock_preview_endpoint_exists(client):
    """POST /api/export/headstock-dxf/preview returns non-404."""
    resp = client.post("/api/export/headstock-dxf/preview", json={"outline_path": SIMPLE_SVG_PATH})
    assert resp.status_code != 404


def test_headstock_preview_returns_json(client):
    """POST /api/export/headstock-dxf/preview returns JSON with points."""
    resp = client.post("/api/export/headstock-dxf/preview", json={"outline_path": SIMPLE_SVG_PATH})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


# =============================================================================
# Endpoint existence — POST /api/export/headstock-dxf/cost
# =============================================================================

def test_headstock_cost_endpoint_exists(client):
    """POST /api/export/headstock-dxf/cost returns non-404."""
    resp = client.post("/api/export/headstock-dxf/cost", json={"outline_path": SIMPLE_SVG_PATH})
    assert resp.status_code != 404


def test_headstock_cost_returns_pricing(client):
    """POST /api/export/headstock-dxf/cost returns pricing fields."""
    resp = client.post("/api/export/headstock-dxf/cost", json={"outline_path": SIMPLE_SVG_PATH})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_cost_usd" in data
    assert "species" in data


# =============================================================================
# Validation — missing required field
# =============================================================================

def test_headstock_dxf_rejects_empty_body(client):
    """POST /api/export/headstock-dxf rejects missing outline_path."""
    resp = client.post("/api/export/headstock-dxf", json={})
    assert resp.status_code == 422
