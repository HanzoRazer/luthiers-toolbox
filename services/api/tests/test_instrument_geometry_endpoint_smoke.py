"""Smoke tests for Instrument Geometry and Bridge Presets endpoints."""

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

def test_bridge_location_endpoint_exists(client):
    """POST /api/instrument/geometry/bridge endpoint exists."""
    response = client.post("/api/instrument/geometry/bridge", json={
        "scale_length_mm": 648.0
    })
    assert response.status_code != 404


def test_radius_profile_endpoint_exists(client):
    """POST /api/instrument/geometry/radius-profile endpoint exists."""
    response = client.post("/api/instrument/geometry/radius-profile", json={
        "fret_count": 22,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    assert response.status_code != 404


def test_radius_at_position_endpoint_exists(client):
    """POST /api/instrument/geometry/radius-at-position endpoint exists."""
    response = client.post("/api/instrument/geometry/radius-at-position", json={
        "position_mm": 100.0,
        "fretboard_length_mm": 400.0,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    assert response.status_code != 404


def test_standard_guitar_endpoint_exists(client):
    """POST /api/instrument/geometry/standard-guitar endpoint exists."""
    response = client.post("/api/instrument/geometry/standard-guitar", json={
        "preset": "fender_25.5"
    })
    assert response.status_code != 404


def test_presets_endpoint_exists(client):
    """GET /api/instrument/geometry/presets endpoint exists."""
    response = client.get("/api/instrument/geometry/presets")
    assert response.status_code != 404


def test_bridge_presets_endpoint_exists(client):
    """GET /api/cam/bridge/presets endpoint exists."""
    response = client.get("/api/cam/bridge/presets")
    assert response.status_code != 404


# =============================================================================
# Bridge Location Endpoint
# =============================================================================

def test_bridge_location_returns_200(client):
    """POST /api/instrument/geometry/bridge returns 200."""
    response = client.post("/api/instrument/geometry/bridge", json={
        "scale_length_mm": 648.0
    })
    assert response.status_code == 200


def test_bridge_location_has_fields(client):
    """Bridge location response has required fields."""
    response = client.post("/api/instrument/geometry/bridge", json={
        "scale_length_mm": 648.0
    })
    data = response.json()

    assert "scale_length_mm" in data
    assert "bridge_location_mm" in data
    assert "compensation_mm" in data
    assert "notes" in data


def test_bridge_location_basic_calculation(client):
    """Bridge location equals scale length when no compensation."""
    response = client.post("/api/instrument/geometry/bridge", json={
        "scale_length_mm": 648.0
    })
    data = response.json()

    assert data["scale_length_mm"] == 648.0
    assert data["bridge_location_mm"] == 648.0
    assert data["compensation_mm"] == 0.0


def test_bridge_location_with_manual_compensation(client):
    """Bridge location accepts manual compensation."""
    response = client.post("/api/instrument/geometry/bridge", json={
        "scale_length_mm": 648.0,
        "saddle_compensation_mm": 2.5
    })
    data = response.json()

    assert data["compensation_mm"] == 2.5
    assert data["bridge_location_mm"] == 650.5


def test_bridge_location_with_automatic_compensation(client):
    """Bridge location calculates automatic compensation."""
    response = client.post("/api/instrument/geometry/bridge", json={
        "scale_length_mm": 648.0,
        "string_gauge_mm": 0.46,
        "action_height_mm": 2.0
    })
    data = response.json()

    assert data["compensation_mm"] != 0.0
    assert "Calculated" in data["notes"]


# =============================================================================
# Radius Profile Endpoint
# =============================================================================

def test_radius_profile_returns_200(client):
    """POST /api/instrument/geometry/radius-profile returns 200."""
    response = client.post("/api/instrument/geometry/radius-profile", json={
        "fret_count": 22,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    assert response.status_code == 200


def test_radius_profile_has_radii(client):
    """Radius profile response has radii list."""
    response = client.post("/api/instrument/geometry/radius-profile", json={
        "fret_count": 22,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    data = response.json()

    assert "radii_mm" in data
    assert isinstance(data["radii_mm"], list)
    assert len(data["radii_mm"]) == 22


def test_radius_profile_is_compound(client):
    """Radius profile detects compound radius."""
    response = client.post("/api/instrument/geometry/radius-profile", json={
        "fret_count": 22,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    data = response.json()

    assert data["is_compound"] is True


def test_radius_profile_single_radius(client):
    """Radius profile with equal radii is not compound."""
    response = client.post("/api/instrument/geometry/radius-profile", json={
        "fret_count": 22,
        "base_radius_mm": 254.0,
        "end_radius_mm": 254.0
    })
    data = response.json()

    assert data["is_compound"] is False


def test_radius_profile_values_are_numeric(client):
    """Radius values are numeric."""
    response = client.post("/api/instrument/geometry/radius-profile", json={
        "fret_count": 12,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    data = response.json()

    for r in data["radii_mm"]:
        assert isinstance(r, (int, float))


# =============================================================================
# Radius at Position Endpoint
# =============================================================================

def test_radius_at_position_returns_200(client):
    """POST /api/instrument/geometry/radius-at-position returns 200."""
    response = client.post("/api/instrument/geometry/radius-at-position", json={
        "position_mm": 200.0,
        "fretboard_length_mm": 400.0,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    assert response.status_code == 200


def test_radius_at_position_has_fields(client):
    """Radius at position response has required fields."""
    response = client.post("/api/instrument/geometry/radius-at-position", json={
        "position_mm": 200.0,
        "fretboard_length_mm": 400.0,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    data = response.json()

    assert "position_mm" in data
    assert "radius_mm" in data


def test_radius_at_position_interpolates(client):
    """Radius at midpoint is between base and end."""
    response = client.post("/api/instrument/geometry/radius-at-position", json={
        "position_mm": 200.0,
        "fretboard_length_mm": 400.0,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    data = response.json()

    # Midpoint should be average
    expected = (184.0 + 305.0) / 2
    assert abs(data["radius_mm"] - expected) < 0.1


def test_radius_at_nut_position(client):
    """Radius at position 0 equals base radius."""
    response = client.post("/api/instrument/geometry/radius-at-position", json={
        "position_mm": 0.0,
        "fretboard_length_mm": 400.0,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    data = response.json()

    assert data["radius_mm"] == 184.0


# =============================================================================
# Standard Guitar Endpoint
# =============================================================================

def test_standard_guitar_returns_200(client):
    """POST /api/instrument/geometry/standard-guitar returns 200."""
    response = client.post("/api/instrument/geometry/standard-guitar", json={
        "preset": "fender_25.5"
    })
    assert response.status_code == 200


def test_standard_guitar_has_fields(client):
    """Standard guitar response has required fields."""
    response = client.post("/api/instrument/geometry/standard-guitar", json={
        "preset": "fender_25.5"
    })
    data = response.json()

    assert "preset" in data
    assert "scale_length_mm" in data
    assert "fret_count" in data
    assert "nut_width_mm" in data
    assert "frets_mm" in data
    assert "bridge_location_mm" in data


def test_standard_guitar_fender(client):
    """Standard guitar Fender preset has correct scale length."""
    response = client.post("/api/instrument/geometry/standard-guitar", json={
        "preset": "fender_25.5"
    })
    data = response.json()

    assert data["scale_length_mm"] == 647.7


def test_standard_guitar_gibson(client):
    """Standard guitar Gibson preset has correct scale length."""
    response = client.post("/api/instrument/geometry/standard-guitar", json={
        "preset": "gibson_24.75"
    })
    data = response.json()

    assert data["scale_length_mm"] == 628.65


def test_standard_guitar_custom_frets(client):
    """Standard guitar accepts custom fret count."""
    response = client.post("/api/instrument/geometry/standard-guitar", json={
        "preset": "fender_25.5",
        "fret_count": 24
    })
    data = response.json()

    assert data["fret_count"] == 24
    assert len(data["frets_mm"]) == 24


def test_standard_guitar_unknown_preset(client):
    """Standard guitar rejects unknown preset."""
    response = client.post("/api/instrument/geometry/standard-guitar", json={
        "preset": "unknown_guitar_xyz"
    })
    assert response.status_code == 400


# =============================================================================
# Geometry Presets Endpoint
# =============================================================================

def test_presets_returns_200(client):
    """GET /api/instrument/geometry/presets returns 200."""
    response = client.get("/api/instrument/geometry/presets")
    assert response.status_code == 200


def test_presets_has_list(client):
    """Presets response has presets list."""
    response = client.get("/api/instrument/geometry/presets")
    data = response.json()

    assert "presets" in data
    assert isinstance(data["presets"], list)


def test_presets_has_details(client):
    """Presets response has details dict."""
    response = client.get("/api/instrument/geometry/presets")
    data = response.json()

    assert "details" in data
    assert isinstance(data["details"], dict)


def test_presets_includes_common_guitars(client):
    """Presets include common guitar types."""
    response = client.get("/api/instrument/geometry/presets")
    data = response.json()

    presets = data["presets"]
    assert "fender_25.5" in presets
    assert "gibson_24.75" in presets


# =============================================================================
# Bridge Presets Endpoint (CAM)
# =============================================================================

def test_bridge_presets_returns_200(client):
    """GET /api/cam/bridge/presets returns 200."""
    response = client.get("/api/cam/bridge/presets")
    assert response.status_code == 200


def test_bridge_presets_has_families(client):
    """Bridge presets has families list."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    assert "families" in data
    assert isinstance(data["families"], list)
    assert len(data["families"]) > 0


def test_bridge_presets_has_gauges(client):
    """Bridge presets has gauges list."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    assert "gauges" in data
    assert isinstance(data["gauges"], list)


def test_bridge_presets_has_actions(client):
    """Bridge presets has actions list."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    assert "actions" in data
    assert isinstance(data["actions"], list)


def test_bridge_family_has_fields(client):
    """Bridge family preset has required fields."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "id" in family
    assert "label" in family
    assert "scaleLength" in family
    assert "stringSpread" in family
    assert "compTreble" in family
    assert "compBass" in family


def test_bridge_presets_includes_les_paul(client):
    """Bridge presets include Les Paul."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family_ids = [f["id"] for f in data["families"]]
    assert "les_paul" in family_ids


def test_bridge_presets_includes_strat(client):
    """Bridge presets include Strat/Tele."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family_ids = [f["id"] for f in data["families"]]
    assert "strat_tele" in family_ids


def test_bridge_gauge_has_adjustments(client):
    """Bridge gauge preset has adjustment fields."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    gauge = data["gauges"][0]
    assert "id" in gauge
    assert "label" in gauge
    # Should have treble/bass adjust or legacy compAdjust
    assert "trebleAdjust" in gauge or "compAdjust" in gauge
