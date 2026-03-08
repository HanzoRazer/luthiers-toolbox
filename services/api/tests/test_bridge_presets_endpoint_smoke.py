"""Smoke tests for Bridge Presets endpoints."""

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

def test_bridge_presets_endpoint_exists(client):
    """GET /api/cam/bridge/presets endpoint exists."""
    response = client.get("/api/cam/bridge/presets")
    assert response.status_code != 404


# =============================================================================
# Bridge Presets Endpoint
# =============================================================================

def test_bridge_presets_returns_200(client):
    """GET /api/cam/bridge/presets returns 200."""
    response = client.get("/api/cam/bridge/presets")
    assert response.status_code == 200


def test_bridge_presets_has_families(client):
    """Response has families list."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    assert "families" in data
    assert isinstance(data["families"], list)


def test_bridge_presets_has_gauges(client):
    """Response has gauges list."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    assert "gauges" in data
    assert isinstance(data["gauges"], list)


def test_bridge_presets_has_actions(client):
    """Response has actions list."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    assert "actions" in data
    assert isinstance(data["actions"], list)


def test_bridge_presets_families_count(client):
    """Response has expected number of family presets."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    # Should have at least les_paul, strat_tele, om, dread, archtop
    assert len(data["families"]) >= 5


def test_bridge_presets_gauges_count(client):
    """Response has expected number of gauge presets."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    # Should have light, medium, heavy
    assert len(data["gauges"]) >= 3


def test_bridge_presets_actions_count(client):
    """Response has expected number of action presets."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    # Should have low, standard, high
    assert len(data["actions"]) >= 3


# =============================================================================
# Family Preset Structure
# =============================================================================

def test_family_has_id(client):
    """Family preset has id field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "id" in family
    assert isinstance(family["id"], str)


def test_family_has_label(client):
    """Family preset has label field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "label" in family
    assert isinstance(family["label"], str)


def test_family_has_scale_length(client):
    """Family preset has scaleLength field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "scaleLength" in family
    assert isinstance(family["scaleLength"], (int, float))


def test_family_has_string_spread(client):
    """Family preset has stringSpread field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "stringSpread" in family
    assert isinstance(family["stringSpread"], (int, float))


def test_family_has_comp_treble(client):
    """Family preset has compTreble field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "compTreble" in family
    assert isinstance(family["compTreble"], (int, float))


def test_family_has_comp_bass(client):
    """Family preset has compBass field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "compBass" in family
    assert isinstance(family["compBass"], (int, float))


def test_family_has_slot_width(client):
    """Family preset has slotWidth field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "slotWidth" in family
    assert isinstance(family["slotWidth"], (int, float))


def test_family_has_slot_length(client):
    """Family preset has slotLength field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    family = data["families"][0]
    assert "slotLength" in family
    assert isinstance(family["slotLength"], (int, float))


# =============================================================================
# Known Family Presets
# =============================================================================

def test_has_les_paul_preset(client):
    """Response includes Les Paul preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [f["id"] for f in data["families"]]
    assert "les_paul" in ids


def test_has_strat_tele_preset(client):
    """Response includes Strat/Tele preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [f["id"] for f in data["families"]]
    assert "strat_tele" in ids


def test_has_om_preset(client):
    """Response includes OM acoustic preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [f["id"] for f in data["families"]]
    assert "om" in ids


def test_has_dread_preset(client):
    """Response includes Dreadnought preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [f["id"] for f in data["families"]]
    assert "dread" in ids


def test_has_archtop_preset(client):
    """Response includes Archtop preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [f["id"] for f in data["families"]]
    assert "archtop" in ids


# =============================================================================
# Gauge Preset Structure
# =============================================================================

def test_gauge_has_id(client):
    """Gauge preset has id field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    gauge = data["gauges"][0]
    assert "id" in gauge
    assert isinstance(gauge["id"], str)


def test_gauge_has_label(client):
    """Gauge preset has label field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    gauge = data["gauges"][0]
    assert "label" in gauge
    assert isinstance(gauge["label"], str)


def test_gauge_has_treble_adjust(client):
    """Gauge preset has trebleAdjust field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    gauge = data["gauges"][0]
    assert "trebleAdjust" in gauge


def test_gauge_has_bass_adjust(client):
    """Gauge preset has bassAdjust field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    gauge = data["gauges"][0]
    assert "bassAdjust" in gauge


# =============================================================================
# Known Gauge Presets
# =============================================================================

def test_has_light_gauge(client):
    """Response includes light gauge preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [g["id"] for g in data["gauges"]]
    assert "light" in ids


def test_has_medium_gauge(client):
    """Response includes medium gauge preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [g["id"] for g in data["gauges"]]
    assert "medium" in ids


def test_has_heavy_gauge(client):
    """Response includes heavy gauge preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [g["id"] for g in data["gauges"]]
    assert "heavy" in ids


# =============================================================================
# Action Preset Structure
# =============================================================================

def test_action_has_id(client):
    """Action preset has id field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    action = data["actions"][0]
    assert "id" in action
    assert isinstance(action["id"], str)


def test_action_has_label(client):
    """Action preset has label field."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    action = data["actions"][0]
    assert "label" in action
    assert isinstance(action["label"], str)


# =============================================================================
# Known Action Presets
# =============================================================================

def test_has_low_action(client):
    """Response includes low action preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [a["id"] for a in data["actions"]]
    assert "low" in ids


def test_has_standard_action(client):
    """Response includes standard action preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [a["id"] for a in data["actions"]]
    assert "standard" in ids


def test_has_high_action(client):
    """Response includes high action preset."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    ids = [a["id"] for a in data["actions"]]
    assert "high" in ids


# =============================================================================
# Value Sanity Checks
# =============================================================================

def test_scale_lengths_realistic(client):
    """Scale lengths are in realistic range (500-700mm)."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    for family in data["families"]:
        scale = family["scaleLength"]
        assert 500 < scale < 700, f"Scale {scale} out of realistic range"


def test_string_spread_realistic(client):
    """String spreads are in realistic range (45-60mm)."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    for family in data["families"]:
        spread = family["stringSpread"]
        assert 45 < spread < 60, f"Spread {spread} out of realistic range"


def test_compensation_values_positive(client):
    """Compensation values are positive."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    for family in data["families"]:
        assert family["compTreble"] > 0
        assert family["compBass"] > 0


def test_bass_compensation_greater_than_treble(client):
    """Bass compensation is typically greater than treble."""
    response = client.get("/api/cam/bridge/presets")
    data = response.json()

    for family in data["families"]:
        assert family["compBass"] >= family["compTreble"], \
            f"Bass comp {family['compBass']} < treble comp {family['compTreble']}"
