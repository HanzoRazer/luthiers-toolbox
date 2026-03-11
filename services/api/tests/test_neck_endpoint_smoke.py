"""Smoke tests for Neck Generator endpoints."""

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

def test_generate_endpoint_exists(client):
    """POST /api/neck/generate endpoint exists."""
    response = client.post("/api/neck/generate", json={})
    assert response.status_code != 404


def test_export_dxf_endpoint_exists(client):
    """POST /api/neck/export_dxf endpoint exists."""
    response = client.post("/api/neck/export_dxf", json={})
    assert response.status_code != 404


def test_presets_endpoint_exists(client):
    """GET /api/neck/presets endpoint exists."""
    response = client.get("/api/neck/presets")
    assert response.status_code != 404


def test_stratocaster_generate_endpoint_exists(client):
    """POST /api/neck/generate/stratocaster endpoint exists."""
    response = client.post("/api/neck/generate/stratocaster", json={})
    assert response.status_code != 404


def test_stratocaster_presets_endpoint_exists(client):
    """GET /api/neck/stratocaster/presets endpoint exists."""
    response = client.get("/api/neck/stratocaster/presets")
    assert response.status_code != 404


# =============================================================================
# Generate Les Paul Neck
# =============================================================================

def test_generate_returns_200(client):
    """POST /api/neck/generate returns 200."""
    response = client.post("/api/neck/generate", json={})
    assert response.status_code == 200


def test_generate_with_defaults(client):
    """Generate returns geometry with default parameters."""
    response = client.post("/api/neck/generate", json={})
    data = response.json()

    assert "profile_points" in data
    assert "fret_positions" in data
    assert "headstock_points" in data
    assert "tuner_holes" in data
    assert "centerline" in data


def test_generate_has_fretboard(client):
    """Generate includes fretboard when requested."""
    response = client.post("/api/neck/generate", json={
        "include_fretboard": True
    })
    data = response.json()

    assert "fretboard_points" in data
    assert data["fretboard_points"] is not None


def test_generate_has_scale_length(client):
    """Generate returns scale length."""
    response = client.post("/api/neck/generate", json={
        "scale_length": 24.75
    })
    data = response.json()

    assert "scale_length" in data
    assert data["scale_length"] == 24.75


def test_generate_has_units(client):
    """Generate returns units."""
    response = client.post("/api/neck/generate", json={})
    data = response.json()

    assert "units" in data
    assert data["units"] in ["mm", "in"]


def test_generate_fret_count(client):
    """Generate returns correct number of fret positions."""
    response = client.post("/api/neck/generate", json={
        "num_frets": 22
    })
    data = response.json()

    assert len(data["fret_positions"]) == 22


def test_generate_custom_fret_count(client):
    """Generate accepts custom fret count."""
    response = client.post("/api/neck/generate", json={
        "num_frets": 24
    })
    data = response.json()

    assert len(data["fret_positions"]) == 24


def test_generate_mm_units(client):
    """Generate can output in millimeters."""
    response = client.post("/api/neck/generate", json={
        "units": "mm"
    })
    data = response.json()

    assert data["units"] == "mm"
    # MM values should be roughly 25x larger than inches
    assert data["scale_length"] > 600  # 24.75" ~= 628mm


def test_generate_tuner_holes_count(client):
    """Generate returns 6 tuner holes for Les Paul."""
    response = client.post("/api/neck/generate", json={})
    data = response.json()

    assert len(data["tuner_holes"]) == 6


def test_generate_profile_is_closed(client):
    """Profile points form closed loop."""
    response = client.post("/api/neck/generate", json={})
    data = response.json()

    profile = data["profile_points"]
    # First and last points should be the same
    assert profile[0]["x"] == profile[-1]["x"]
    assert profile[0]["y"] == profile[-1]["y"]


def test_generate_point_structure(client):
    """Points have x and y coordinates."""
    response = client.post("/api/neck/generate", json={})
    data = response.json()

    for point in data["profile_points"]:
        assert "x" in point
        assert "y" in point
        assert isinstance(point["x"], (int, float))
        assert isinstance(point["y"], (int, float))


# =============================================================================
# Export DXF
# =============================================================================

def test_export_dxf_returns_200(client):
    """POST /api/neck/export_dxf returns 200."""
    response = client.post("/api/neck/export_dxf", json={})
    assert response.status_code == 200


def test_export_dxf_returns_file(client):
    """DXF export returns file content."""
    response = client.post("/api/neck/export_dxf", json={})

    content_type = response.headers.get("content-type", "")
    assert "dxf" in content_type or "octet-stream" in content_type


def test_export_dxf_has_content(client):
    """DXF export returns non-empty content."""
    response = client.post("/api/neck/export_dxf", json={})

    assert len(response.content) > 0


def test_export_dxf_has_disposition(client):
    """DXF export has content-disposition header."""
    response = client.post("/api/neck/export_dxf", json={})

    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert ".dxf" in disposition


def test_export_dxf_filename_has_scale(client):
    """DXF filename includes scale length."""
    response = client.post("/api/neck/export_dxf", json={
        "scale_length": 24.75
    })

    disposition = response.headers.get("content-disposition", "")
    assert "24.75" in disposition


def test_export_dxf_mm_units(client):
    """DXF export works with mm units."""
    response = client.post("/api/neck/export_dxf", json={
        "units": "mm"
    })
    assert response.status_code == 200


# =============================================================================
# Les Paul Presets
# =============================================================================

def test_presets_returns_200(client):
    """GET /api/neck/presets returns 200."""
    response = client.get("/api/neck/presets")
    assert response.status_code == 200


def test_presets_has_list(client):
    """Presets response has presets list."""
    response = client.get("/api/neck/presets")
    data = response.json()

    assert "presets" in data
    assert isinstance(data["presets"], list)


def test_presets_has_items(client):
    """Presets list has at least one item."""
    response = client.get("/api/neck/presets")
    data = response.json()

    assert len(data["presets"]) >= 1


def test_preset_has_required_fields(client):
    """Preset objects have required fields."""
    response = client.get("/api/neck/presets")
    data = response.json()

    preset = data["presets"][0]
    assert "name" in preset
    assert "scale_length" in preset
    assert "nut_width" in preset


def test_presets_includes_les_paul_standard(client):
    """Presets include Les Paul Standard."""
    response = client.get("/api/neck/presets")
    data = response.json()

    names = [p["name"] for p in data["presets"]]
    assert any("Les Paul" in name for name in names)


# =============================================================================
# Generate Stratocaster Neck
# =============================================================================

def test_strat_generate_returns_200(client):
    """POST /api/neck/generate/stratocaster returns 200."""
    response = client.post("/api/neck/generate/stratocaster", json={})
    assert response.status_code == 200


def test_strat_generate_with_variant(client):
    """Stratocaster generation accepts variant."""
    response = client.post("/api/neck/generate/stratocaster", json={
        "variant": "vintage"
    })
    assert response.status_code == 200

    response = client.post("/api/neck/generate/stratocaster", json={
        "variant": "modern"
    })
    assert response.status_code == 200


def test_strat_generate_has_geometry(client):
    """Stratocaster returns geometry."""
    response = client.post("/api/neck/generate/stratocaster", json={})
    data = response.json()

    assert "profile_points" in data
    assert "fret_positions" in data
    assert "headstock_points" in data
    assert "tuner_holes" in data


def test_strat_generate_6_inline_tuners(client):
    """Stratocaster has 6 inline tuners."""
    response = client.post("/api/neck/generate/stratocaster", json={})
    data = response.json()

    assert len(data["tuner_holes"]) == 6


def test_strat_generate_fender_scale(client):
    """Stratocaster has 25.5\" scale."""
    response = client.post("/api/neck/generate/stratocaster", json={
        "units": "in"
    })
    data = response.json()

    # Default Strat scale is 25.5"
    assert abs(data["scale_length"] - 25.5) < 0.01


def test_strat_generate_custom_frets(client):
    """Stratocaster accepts custom fret count."""
    response = client.post("/api/neck/generate/stratocaster", json={
        "num_frets": 24
    })
    data = response.json()

    assert len(data["fret_positions"]) == 24


def test_strat_generate_mm_units(client):
    """Stratocaster can output in millimeters."""
    response = client.post("/api/neck/generate/stratocaster", json={
        "units": "mm"
    })
    data = response.json()

    assert data["units"] == "mm"
    # 25.5" ~= 647.7mm
    assert data["scale_length"] > 640


# =============================================================================
# Stratocaster Presets
# =============================================================================

def test_strat_presets_returns_200(client):
    """GET /api/neck/stratocaster/presets returns 200."""
    response = client.get("/api/neck/stratocaster/presets")
    assert response.status_code == 200


def test_strat_presets_has_list(client):
    """Stratocaster presets has presets list."""
    response = client.get("/api/neck/stratocaster/presets")
    data = response.json()

    assert "presets" in data
    assert isinstance(data["presets"], list)


def test_strat_presets_has_items(client):
    """Stratocaster presets list has items."""
    response = client.get("/api/neck/stratocaster/presets")
    data = response.json()

    assert len(data["presets"]) >= 1


def test_strat_preset_has_required_fields(client):
    """Stratocaster preset has required fields."""
    response = client.get("/api/neck/stratocaster/presets")
    data = response.json()

    preset = data["presets"][0]
    assert "name" in preset
    assert "variant" in preset
    assert "scale_length" in preset


def test_strat_presets_includes_vintage(client):
    """Stratocaster presets include vintage variant."""
    response = client.get("/api/neck/stratocaster/presets")
    data = response.json()

    variants = [p.get("variant") for p in data["presets"]]
    assert "vintage" in variants


def test_strat_presets_includes_modern(client):
    """Stratocaster presets include modern variant."""
    response = client.get("/api/neck/stratocaster/presets")
    data = response.json()

    variants = [p.get("variant") for p in data["presets"]]
    assert "modern" in variants


def test_strat_preset_has_description(client):
    """Stratocaster presets have description."""
    response = client.get("/api/neck/stratocaster/presets")
    data = response.json()

    preset = data["presets"][0]
    assert "description" in preset
