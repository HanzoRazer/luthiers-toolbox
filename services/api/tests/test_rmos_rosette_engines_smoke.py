"""Smoke tests for RMOS rosette engine endpoints (proxied to cam.rosette)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Segment Ring Endpoint
# =============================================================================

def test_segment_ring_returns_ok(client):
    """POST /api/rmos/rosette/segment-ring returns ok=True."""
    response = client.post("/api/rmos/rosette/segment-ring", json={
        "ring_id": 1,
        "radius_mm": 50.0,
        "width_mm": 5.0,
        "tile_length_mm": 10.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "segments" in data
    assert isinstance(data["segments"], list)


def test_segment_ring_respects_tile_count(client):
    """POST /api/rmos/rosette/segment-ring respects tile_count override."""
    response = client.post("/api/rmos/rosette/segment-ring", json={
        "ring_id": 1,
        "radius_mm": 50.0,
        "width_mm": 5.0,
        "tile_length_mm": 10.0,
        "tile_count": 12,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["tile_count"] == 12
    assert len(data["segments"]) == 12


def test_segment_ring_returns_segmentation_id(client):
    """POST /api/rmos/rosette/segment-ring returns segmentation_id."""
    response = client.post("/api/rmos/rosette/segment-ring", json={
        "ring_id": 5,
        "radius_mm": 30.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert "segmentation_id" in data
    assert "ring_5" in data["segmentation_id"]


# =============================================================================
# Generate Slices Endpoint
# =============================================================================

def test_generate_slices_returns_ok(client):
    """POST /api/rmos/rosette/generate-slices returns ok=True."""
    response = client.post("/api/rmos/rosette/generate-slices", json={
        "ring_id": 1,
        "radius_mm": 50.0,
        "width_mm": 5.0,
        "tile_length_mm": 10.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "slices" in data
    assert isinstance(data["slices"], list)


def test_generate_slices_returns_batch_id(client):
    """POST /api/rmos/rosette/generate-slices returns batch_id."""
    response = client.post("/api/rmos/rosette/generate-slices", json={
        "ring_id": 3,
        "radius_mm": 40.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert "ring_3" in data["batch_id"]


def test_generate_slices_slice_count_matches_tile_count(client):
    """POST /api/rmos/rosette/generate-slices slice count matches tile count."""
    response = client.post("/api/rmos/rosette/generate-slices", json={
        "ring_id": 1,
        "tile_count": 6,
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["slices"]) == 6


# =============================================================================
# Preview Endpoint
# =============================================================================

def test_preview_returns_ok(client):
    """POST /api/rmos/rosette/preview returns ok=True."""
    response = client.post("/api/rmos/rosette/preview", json={
        "pattern_id": "test_pattern",
        "rings": [
            {"ring_id": 0, "radius_mm": 30.0, "width_mm": 3.0},
            {"ring_id": 1, "radius_mm": 40.0, "width_mm": 4.0},
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "preview" in data


def test_preview_returns_pattern_id(client):
    """POST /api/rmos/rosette/preview returns pattern_id."""
    response = client.post("/api/rmos/rosette/preview", json={
        "pattern_id": "my_rosette_v1",
        "rings": [{"ring_id": 0, "radius_mm": 50.0}]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["pattern_id"] == "my_rosette_v1"


def test_preview_handles_single_ring_shorthand(client):
    """POST /api/rmos/rosette/preview handles single ring without rings array."""
    response = client.post("/api/rmos/rosette/preview", json={
        "ring_id": 0,
        "radius_mm": 45.0,
        "width_mm": 5.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["rings"]) == 1


def test_preview_returns_ring_summaries(client):
    """POST /api/rmos/rosette/preview returns ring summaries in preview."""
    response = client.post("/api/rmos/rosette/preview", json={
        "rings": [
            {"ring_id": 0, "radius_mm": 25.0},
            {"ring_id": 1, "radius_mm": 35.0},
        ]
    })
    assert response.status_code == 200
    data = response.json()
    preview = data["preview"]
    assert "rings" in preview
    assert len(preview["rings"]) == 2
