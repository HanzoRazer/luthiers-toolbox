"""Smoke tests for CAM fret slots preview endpoint (proxied to fret_slots_cam calculator)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_fret_slots_preview_returns_slots(client):
    """POST /api/cam/fret_slots/preview returns slots array."""
    response = client.post(
        "/api/cam/fret_slots/preview",
        json={
            "model_id": "strat_25_5",
            "fret_count": 22,
            "slot_width_mm": 0.58,
            "slot_depth_mm": 3.0,
            "bit_diameter_mm": 0.58,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "slots" in data
    assert "messages" in data
    assert "fret_count" in data
    assert isinstance(data["slots"], list)


def test_fret_slots_preview_default_fret_count(client):
    """POST /api/cam/fret_slots/preview uses default fret_count if not specified."""
    response = client.post(
        "/api/cam/fret_slots/preview",
        json={
            "model_id": "test_model",
            "slot_width_mm": 0.58,
            "slot_depth_mm": 3.0,
            "bit_diameter_mm": 0.58,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fret_count"] == 22  # default


def test_fret_slots_preview_generates_correct_slot_count(client):
    """POST /api/cam/fret_slots/preview generates correct number of slots."""
    response = client.post(
        "/api/cam/fret_slots/preview",
        json={
            "model_id": "test_model",
            "fret_count": 12,
            "slot_width_mm": 0.58,
            "slot_depth_mm": 3.0,
            "bit_diameter_mm": 0.58,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["slots"]) == 12


def test_fret_slots_preview_includes_statistics(client):
    """POST /api/cam/fret_slots/preview includes statistics."""
    response = client.post(
        "/api/cam/fret_slots/preview",
        json={
            "model_id": "test_model",
            "fret_count": 22,
            "slot_width_mm": 0.58,
            "slot_depth_mm": 3.0,
            "bit_diameter_mm": 0.58,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "statistics" in data
    if data["statistics"]:
        assert "slot_count" in data["statistics"]
        assert "total_cutting_length_mm" in data["statistics"]


def test_fret_slots_preview_bit_too_large_warning(client):
    """POST /api/cam/fret_slots/preview warns when bit is too large."""
    response = client.post(
        "/api/cam/fret_slots/preview",
        json={
            "model_id": "test_model",
            "fret_count": 22,
            "slot_width_mm": 0.58,
            "slot_depth_mm": 3.0,
            "bit_diameter_mm": 2.0,  # Much larger than slot width
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should have a warning about bit being too large
    codes = [m["code"] for m in data["messages"]]
    assert "BIT_TOO_LARGE" in codes


def test_fret_slots_preview_validation_error(client):
    """POST /api/cam/fret_slots/preview returns 422 for invalid input."""
    response = client.post(
        "/api/cam/fret_slots/preview",
        json={
            "model_id": "test_model",
            "fret_count": 100,  # Exceeds max of 36
            "slot_width_mm": 0.58,
            "slot_depth_mm": 3.0,
            "bit_diameter_mm": 0.58,
        }
    )
    assert response.status_code == 422


def test_fret_slots_preview_slot_structure(client):
    """POST /api/cam/fret_slots/preview returns correct slot structure."""
    response = client.post(
        "/api/cam/fret_slots/preview",
        json={
            "model_id": "test_model",
            "fret_count": 5,
            "slot_width_mm": 0.58,
            "slot_depth_mm": 3.0,
            "bit_diameter_mm": 0.58,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["slots"]) == 5

    # Check first slot structure
    slot = data["slots"][0]
    assert "fret" in slot
    assert "positionMm" in slot
    assert "widthMm" in slot
    assert "depthMm" in slot
    assert slot["fret"] == 1
    assert slot["positionMm"] > 0
