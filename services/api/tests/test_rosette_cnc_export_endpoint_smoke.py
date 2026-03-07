"""Smoke tests for rosette CNC export endpoint (proxied to real CNC wiring)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_rosette_export_cnc_endpoint_exists(client):
    """POST /api/rmos/rosette/export-cnc endpoint exists."""
    response = client.post("/api/rmos/rosette/export-cnc", json={})
    assert response.status_code != 404


# =============================================================================
# Valid Export Cases
# =============================================================================

def test_rosette_export_cnc_returns_ok(client):
    """POST /api/rmos/rosette/export-cnc returns ok=True with valid input."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {
            "ring_id": 1,
            "radius_mm": 50.0,
            "width_mm": 5.0,
            "tile_length_mm": 10.0,
            "kerf_mm": 0.3,
        },
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


def test_rosette_export_cnc_returns_gcode(client):
    """POST /api/rmos/rosette/export-cnc returns G-code string."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {
            "ring_id": 1,
            "radius_mm": 50.0,
            "width_mm": 5.0,
            "tile_length_mm": 10.0,
            "kerf_mm": 0.3,
        },
    })
    data = response.json()
    assert "gcode" in data
    assert data["gcode"] is not None
    assert isinstance(data["gcode"], str)
    # Should contain G-code markers
    assert "G21" in data["gcode"]  # mm mode
    assert "G90" in data["gcode"]  # absolute mode


def test_rosette_export_cnc_returns_job_id(client):
    """POST /api/rmos/rosette/export-cnc returns job_id."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {
            "ring_id": 1,
            "radius_mm": 50.0,
            "width_mm": 5.0,
            "tile_length_mm": 10.0,
            "kerf_mm": 0.3,
        },
    })
    data = response.json()
    assert "job_id" in data
    assert data["job_id"] is not None
    assert data["job_id"].startswith("JOB-ROSETTE-")


def test_rosette_export_cnc_returns_segment_count(client):
    """POST /api/rmos/rosette/export-cnc returns segment_count."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {
            "ring_id": 1,
            "radius_mm": 50.0,
            "width_mm": 5.0,
            "tile_length_mm": 10.0,
            "kerf_mm": 0.3,
        },
    })
    data = response.json()
    assert "segment_count" in data
    assert isinstance(data["segment_count"], int)
    assert data["segment_count"] > 0


def test_rosette_export_cnc_returns_safety_decision(client):
    """POST /api/rmos/rosette/export-cnc returns safety decision."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {
            "ring_id": 1,
            "radius_mm": 50.0,
            "width_mm": 5.0,
            "tile_length_mm": 10.0,
            "kerf_mm": 0.3,
        },
    })
    data = response.json()
    assert "safety" in data
    safety = data["safety"]
    assert "decision" in safety
    assert "risk_level" in safety


def test_rosette_export_cnc_returns_estimated_runtime(client):
    """POST /api/rmos/rosette/export-cnc returns estimated runtime."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {
            "ring_id": 1,
            "radius_mm": 50.0,
            "width_mm": 5.0,
            "tile_length_mm": 10.0,
            "kerf_mm": 0.3,
        },
    })
    data = response.json()
    assert "estimated_runtime_sec" in data
    assert isinstance(data["estimated_runtime_sec"], (int, float))
    assert data["estimated_runtime_sec"] > 0


# =============================================================================
# Material Options
# =============================================================================

def test_rosette_export_cnc_accepts_material_hardwood(client):
    """POST /api/rmos/rosette/export-cnc accepts material=hardwood."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {"ring_id": 1, "radius_mm": 50.0, "width_mm": 5.0, "tile_length_mm": 10.0, "kerf_mm": 0.3},
        "material": "hardwood",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


def test_rosette_export_cnc_accepts_material_softwood(client):
    """POST /api/rmos/rosette/export-cnc accepts material=softwood."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {"ring_id": 1, "radius_mm": 50.0, "width_mm": 5.0, "tile_length_mm": 10.0, "kerf_mm": 0.3},
        "material": "softwood",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


# =============================================================================
# Machine Profile Options
# =============================================================================

def test_rosette_export_cnc_accepts_grbl_profile(client):
    """POST /api/rmos/rosette/export-cnc accepts machine_profile=grbl."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {"ring_id": 1, "radius_mm": 50.0, "width_mm": 5.0, "tile_length_mm": 10.0, "kerf_mm": 0.3},
        "machine_profile": "grbl",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    # GRBL profile should have comments with semicolons
    assert "; mm" in data["gcode"] or "G21" in data["gcode"]


def test_rosette_export_cnc_accepts_fanuc_profile(client):
    """POST /api/rmos/rosette/export-cnc accepts machine_profile=fanuc."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {"ring_id": 1, "radius_mm": 50.0, "width_mm": 5.0, "tile_length_mm": 10.0, "kerf_mm": 0.3},
        "machine_profile": "fanuc",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    # FANUC profile should not have semicolon comments
    assert "G21" in data["gcode"]


# =============================================================================
# Custom Parameters
# =============================================================================

def test_rosette_export_cnc_accepts_spindle_rpm(client):
    """POST /api/rmos/rosette/export-cnc accepts spindle_rpm."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {"ring_id": 1, "radius_mm": 50.0, "width_mm": 5.0, "tile_length_mm": 10.0, "kerf_mm": 0.3},
        "spindle_rpm": 18000,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "S18000" in data["gcode"]


def test_rosette_export_cnc_accepts_jig_alignment(client):
    """POST /api/rmos/rosette/export-cnc accepts jig alignment parameters."""
    response = client.post("/api/rmos/rosette/export-cnc", json={
        "ring": {"ring_id": 1, "radius_mm": 50.0, "width_mm": 5.0, "tile_length_mm": 10.0, "kerf_mm": 0.3},
        "origin_x_mm": 10.0,
        "origin_y_mm": 20.0,
        "rotation_deg": 45.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


# =============================================================================
# Default Behavior
# =============================================================================

def test_rosette_export_cnc_empty_payload_uses_defaults(client):
    """POST /api/rmos/rosette/export-cnc with empty payload uses defaults."""
    response = client.post("/api/rmos/rosette/export-cnc", json={})
    assert response.status_code == 200
    data = response.json()
    # Should still work with defaults
    assert data["ok"] is True
    assert data["gcode"] is not None
