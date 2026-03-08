"""Smoke tests for Music Temperament endpoints."""

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

def test_systems_endpoint_exists(client):
    """GET /api/music/temperament/systems endpoint exists."""
    response = client.get("/api/music/temperament/systems")
    assert response.status_code != 404


def test_keys_endpoint_exists(client):
    """GET /api/music/temperament/keys endpoint exists."""
    response = client.get("/api/music/temperament/keys")
    assert response.status_code != 404


def test_tunings_endpoint_exists(client):
    """GET /api/music/temperament/tunings endpoint exists."""
    response = client.get("/api/music/temperament/tunings")
    assert response.status_code != 404


def test_compare_endpoint_exists(client):
    """POST /api/music/temperament/compare endpoint exists."""
    response = client.post("/api/music/temperament/compare", json={})
    assert response.status_code != 404


def test_compare_all_endpoint_exists(client):
    """GET /api/music/temperament/compare-all endpoint exists."""
    response = client.get("/api/music/temperament/compare-all")
    assert response.status_code != 404


def test_equal_temperament_endpoint_exists(client):
    """GET /api/music/temperament/equal-temperament endpoint exists."""
    response = client.get("/api/music/temperament/equal-temperament")
    assert response.status_code != 404


def test_resolve_endpoint_exists(client):
    """GET /api/music/temperament/resolve endpoint exists."""
    response = client.get("/api/music/temperament/resolve")
    assert response.status_code != 404


def test_tables_endpoint_exists(client):
    """GET /api/music/temperament/tables endpoint exists."""
    response = client.get("/api/music/temperament/tables")
    assert response.status_code != 404


# =============================================================================
# Systems Endpoint
# =============================================================================

def test_systems_returns_200(client):
    """GET /api/music/temperament/systems returns 200."""
    response = client.get("/api/music/temperament/systems")
    assert response.status_code == 200


def test_systems_returns_list(client):
    """GET /api/music/temperament/systems returns a list."""
    response = client.get("/api/music/temperament/systems")
    data = response.json()
    assert isinstance(data, list)


def test_systems_has_known_systems(client):
    """Systems list includes expected temperament systems."""
    response = client.get("/api/music/temperament/systems")
    data = response.json()
    system_ids = [s.get("id") for s in data]
    # Should have at least just_major and pythagorean
    assert "just_major" in system_ids or "JUST_MAJOR" in system_ids
    assert len(data) >= 3


def test_system_has_required_fields(client):
    """System objects have required fields."""
    response = client.get("/api/music/temperament/systems")
    data = response.json()

    assert len(data) > 0
    system = data[0]

    assert "id" in system
    assert "name" in system
    assert "description" in system


# =============================================================================
# Keys Endpoint
# =============================================================================

def test_keys_returns_200(client):
    """GET /api/music/temperament/keys returns 200."""
    response = client.get("/api/music/temperament/keys")
    assert response.status_code == 200


def test_keys_has_keys_list(client):
    """Keys response has keys list."""
    response = client.get("/api/music/temperament/keys")
    data = response.json()

    assert "keys" in data
    assert isinstance(data["keys"], list)


def test_keys_includes_standard_notes(client):
    """Keys list includes standard note names."""
    response = client.get("/api/music/temperament/keys")
    data = response.json()
    keys = data["keys"]

    # Should include basic notes
    assert "C" in keys
    assert "E" in keys
    assert "A" in keys


# =============================================================================
# Tunings Endpoint
# =============================================================================

def test_tunings_returns_200(client):
    """GET /api/music/temperament/tunings returns 200."""
    response = client.get("/api/music/temperament/tunings")
    assert response.status_code == 200


def test_tunings_has_standard_tuning(client):
    """Tunings response includes standard guitar tuning."""
    response = client.get("/api/music/temperament/tunings")
    data = response.json()

    assert "standard" in data
    assert "name" in data["standard"]
    assert "semitones" in data["standard"]


def test_tunings_has_drop_d(client):
    """Tunings response includes Drop D tuning."""
    response = client.get("/api/music/temperament/tunings")
    data = response.json()

    assert "drop_d" in data


def test_tunings_semitones_are_lists(client):
    """Tuning semitones are lists of integers."""
    response = client.get("/api/music/temperament/tunings")
    data = response.json()

    standard = data["standard"]
    assert isinstance(standard["semitones"], list)
    assert all(isinstance(s, int) for s in standard["semitones"])


# =============================================================================
# Compare Endpoint
# =============================================================================

def test_compare_returns_200(client):
    """POST /api/music/temperament/compare returns 200."""
    response = client.post("/api/music/temperament/compare", json={
        "scale_length_mm": 648.0,
        "fret_count": 22,
        "temperament": "just_major"
    })
    assert response.status_code == 200


def test_compare_with_defaults(client):
    """POST /api/music/temperament/compare works with defaults."""
    response = client.post("/api/music/temperament/compare", json={})
    assert response.status_code == 200


def test_compare_has_positions(client):
    """Compare response has positions list."""
    response = client.post("/api/music/temperament/compare", json={})
    data = response.json()

    assert "positions" in data
    assert isinstance(data["positions"], list)


def test_compare_has_summary(client):
    """Compare response has summary."""
    response = client.post("/api/music/temperament/compare", json={})
    data = response.json()

    assert "summary" in data


def test_compare_position_has_fields(client):
    """Position objects have required fields."""
    response = client.post("/api/music/temperament/compare", json={})
    data = response.json()

    assert len(data["positions"]) > 0
    pos = data["positions"][0]

    assert "fret_number" in pos
    assert "equal_pos_mm" in pos
    assert "alt_pos_mm" in pos
    assert "deviation_cents" in pos


# =============================================================================
# Compare All Endpoint
# =============================================================================

def test_compare_all_returns_200(client):
    """GET /api/music/temperament/compare-all returns 200."""
    response = client.get("/api/music/temperament/compare-all")
    assert response.status_code == 200


def test_compare_all_has_systems(client):
    """Compare all response has systems dict."""
    response = client.get("/api/music/temperament/compare-all")
    data = response.json()

    assert "systems" in data
    assert isinstance(data["systems"], dict)


def test_compare_all_accepts_params(client):
    """Compare all accepts query parameters."""
    response = client.get("/api/music/temperament/compare-all?scale_length_mm=628.65&fret_count=22")
    assert response.status_code == 200


# =============================================================================
# Equal Temperament Endpoint
# =============================================================================

def test_equal_temperament_returns_200(client):
    """GET /api/music/temperament/equal-temperament returns 200."""
    response = client.get("/api/music/temperament/equal-temperament")
    assert response.status_code == 200


def test_equal_temperament_has_positions(client):
    """Equal temperament response has positions list."""
    response = client.get("/api/music/temperament/equal-temperament")
    data = response.json()

    assert "positions" in data
    assert isinstance(data["positions"], list)


def test_equal_temperament_position_has_fields(client):
    """Equal temperament positions have required fields."""
    response = client.get("/api/music/temperament/equal-temperament")
    data = response.json()

    assert len(data["positions"]) > 0
    pos = data["positions"][0]

    assert "fret_number" in pos
    assert "position_mm" in pos


def test_equal_temperament_accepts_params(client):
    """Equal temperament accepts query parameters."""
    response = client.get("/api/music/temperament/equal-temperament?scale_length_mm=628.65&fret_count=24")
    assert response.status_code == 200

    data = response.json()
    assert data["scale_length_mm"] == 628.65
    assert data["fret_count"] == 24


# =============================================================================
# Resolve Endpoint
# =============================================================================

def test_resolve_returns_200(client):
    """GET /api/music/temperament/resolve returns 200."""
    response = client.get("/api/music/temperament/resolve")
    assert response.status_code == 200


def test_resolve_has_resolved(client):
    """Resolve response has resolved dict."""
    response = client.get("/api/music/temperament/resolve")
    data = response.json()

    assert "resolved" in data


def test_resolve_accepts_instrument_type(client):
    """Resolve accepts instrument_type parameter."""
    response = client.get("/api/music/temperament/resolve?instrument_type=bass")
    assert response.status_code == 200

    data = response.json()
    assert data["resolved"]["instrument_type"] == "bass"


def test_resolve_accepts_model_id(client):
    """Resolve accepts model_id parameter."""
    response = client.get("/api/music/temperament/resolve?model_id=les_paul")
    assert response.status_code == 200


# =============================================================================
# Tables Endpoint
# =============================================================================

def test_tables_returns_200(client):
    """GET /api/music/temperament/tables returns 200."""
    response = client.get("/api/music/temperament/tables")
    assert response.status_code == 200


def test_tables_has_tables(client):
    """Tables response has tables dict."""
    response = client.get("/api/music/temperament/tables")
    data = response.json()

    assert "tables" in data


def test_tables_has_equal_temperament(client):
    """Tables includes equal temperament table."""
    response = client.get("/api/music/temperament/tables")
    data = response.json()

    assert "equal_temperament" in data["tables"]
    assert isinstance(data["tables"]["equal_temperament"], list)


def test_tables_accepts_params(client):
    """Tables accepts query parameters."""
    response = client.get("/api/music/temperament/tables?scale_length_mm=648.0&fret_count=22")
    assert response.status_code == 200

    data = response.json()
    assert data["scale_length_mm"] == 648.0
    assert data["fret_count"] == 22
