"""Smoke tests for Art Studio Bracing endpoints."""

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

def test_preview_endpoint_exists(client):
    """POST /api/art-studio/bracing/preview endpoint exists."""
    response = client.post("/api/art-studio/bracing/preview", json={})
    assert response.status_code != 404


def test_batch_endpoint_exists(client):
    """POST /api/art-studio/bracing/batch endpoint exists."""
    response = client.post("/api/art-studio/bracing/batch", json={"braces": []})
    assert response.status_code != 404


def test_presets_endpoint_exists(client):
    """GET /api/art-studio/bracing/presets endpoint exists."""
    response = client.get("/api/art-studio/bracing/presets")
    assert response.status_code != 404


def test_export_dxf_endpoint_exists(client):
    """POST /api/art-studio/bracing/export-dxf endpoint exists."""
    response = client.post("/api/art-studio/bracing/export-dxf", json={
        "braces": [{"width_mm": 12, "height_mm": 8, "length_mm": 300}]
    })
    assert response.status_code != 404


def test_dxf_versions_endpoint_exists(client):
    """GET /api/art-studio/bracing/dxf-versions endpoint exists."""
    response = client.get("/api/art-studio/bracing/dxf-versions")
    assert response.status_code != 404


# =============================================================================
# Preview Endpoint
# =============================================================================

def test_preview_returns_200(client):
    """POST /api/art-studio/bracing/preview returns 200."""
    response = client.post("/api/art-studio/bracing/preview", json={
        "profile_type": "parabolic",
        "width_mm": 12.0,
        "height_mm": 8.0,
        "length_mm": 300.0,
        "density_kg_m3": 420.0
    })
    assert response.status_code == 200


def test_preview_with_defaults(client):
    """POST /api/art-studio/bracing/preview works with defaults."""
    response = client.post("/api/art-studio/bracing/preview", json={})
    assert response.status_code == 200


def test_preview_has_section(client):
    """Preview response has section data."""
    response = client.post("/api/art-studio/bracing/preview", json={})
    data = response.json()

    assert "section" in data
    assert "mass_grams" in data
    assert "stiffness_estimate" in data


def test_preview_section_has_fields(client):
    """Preview section has required fields."""
    response = client.post("/api/art-studio/bracing/preview", json={})
    data = response.json()

    section = data["section"]
    assert "profile_type" in section
    assert "width_mm" in section
    assert "height_mm" in section
    assert "area_mm2" in section


def test_preview_mass_is_numeric(client):
    """Preview mass_grams is numeric."""
    response = client.post("/api/art-studio/bracing/preview", json={})
    data = response.json()

    assert isinstance(data["mass_grams"], (int, float))
    assert data["mass_grams"] > 0


def test_preview_stiffness_is_numeric(client):
    """Preview stiffness_estimate is numeric."""
    response = client.post("/api/art-studio/bracing/preview", json={})
    data = response.json()

    assert isinstance(data["stiffness_estimate"], (int, float))
    assert data["stiffness_estimate"] > 0


def test_preview_different_profiles(client):
    """Preview works with different profile types."""
    profiles = ["rectangular", "triangular", "parabolic", "scalloped"]

    for profile in profiles:
        response = client.post("/api/art-studio/bracing/preview", json={
            "profile_type": profile
        })
        assert response.status_code == 200, f"Failed for profile: {profile}"
        data = response.json()
        assert data["section"]["profile_type"] == profile


# =============================================================================
# Batch Endpoint
# =============================================================================

def test_batch_returns_200(client):
    """POST /api/art-studio/bracing/batch returns 200."""
    response = client.post("/api/art-studio/bracing/batch", json={
        "name": "Test Set",
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 280},
            {"width_mm": 12, "height_mm": 8, "length_mm": 280}
        ]
    })
    assert response.status_code == 200


def test_batch_has_required_fields(client):
    """Batch response has required fields."""
    response = client.post("/api/art-studio/bracing/batch", json={
        "name": "X-Brace Test",
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 280}
        ]
    })
    data = response.json()

    assert "name" in data
    assert "braces" in data
    assert "totals" in data


def test_batch_returns_name(client):
    """Batch response preserves name."""
    response = client.post("/api/art-studio/bracing/batch", json={
        "name": "My Custom Bracing",
        "braces": [{"width_mm": 10, "height_mm": 6, "length_mm": 200}]
    })
    data = response.json()
    assert data["name"] == "My Custom Bracing"


def test_batch_braces_count_matches(client):
    """Batch response has same number of braces as input."""
    response = client.post("/api/art-studio/bracing/batch", json={
        "name": "Three Braces",
        "braces": [
            {"width_mm": 8, "height_mm": 5, "length_mm": 200},
            {"width_mm": 8, "height_mm": 5, "length_mm": 220},
            {"width_mm": 8, "height_mm": 5, "length_mm": 240}
        ]
    })
    data = response.json()
    assert len(data["braces"]) == 3


def test_batch_totals_has_mass(client):
    """Batch totals include total mass."""
    response = client.post("/api/art-studio/bracing/batch", json={
        "name": "Totals Test",
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 300}
        ]
    })
    data = response.json()

    assert "total_mass_grams" in data["totals"]
    assert isinstance(data["totals"]["total_mass_grams"], (int, float))


# =============================================================================
# Presets Endpoint
# =============================================================================

def test_presets_returns_200(client):
    """GET /api/art-studio/bracing/presets returns 200."""
    response = client.get("/api/art-studio/bracing/presets")
    assert response.status_code == 200


def test_presets_returns_list(client):
    """GET /api/art-studio/bracing/presets returns a list."""
    response = client.get("/api/art-studio/bracing/presets")
    data = response.json()
    assert isinstance(data, list)


def test_presets_has_items(client):
    """Presets list has at least one item."""
    response = client.get("/api/art-studio/bracing/presets")
    data = response.json()
    assert len(data) >= 1


def test_preset_has_required_fields(client):
    """Preset objects have required fields."""
    response = client.get("/api/art-studio/bracing/presets")
    data = response.json()

    preset = data[0]
    assert "id" in preset
    assert "name" in preset
    assert "description" in preset
    assert "braces" in preset


def test_preset_braces_are_list(client):
    """Preset braces field is a list."""
    response = client.get("/api/art-studio/bracing/presets")
    data = response.json()

    preset = data[0]
    assert isinstance(preset["braces"], list)
    assert len(preset["braces"]) > 0


def test_presets_includes_x_brace(client):
    """Presets include X-brace configuration."""
    response = client.get("/api/art-studio/bracing/presets")
    data = response.json()

    preset_ids = [p["id"] for p in data]
    assert "x-brace-standard" in preset_ids


# =============================================================================
# DXF Export Endpoint
# =============================================================================

def test_export_dxf_returns_200(client):
    """POST /api/art-studio/bracing/export-dxf returns 200."""
    response = client.post("/api/art-studio/bracing/export-dxf", json={
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 280, "x_mm": 0, "y_mm": 0}
        ]
    })
    assert response.status_code == 200


def test_export_dxf_returns_file(client):
    """DXF export returns file content."""
    response = client.post("/api/art-studio/bracing/export-dxf", json={
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 280}
        ]
    })

    # Check content type
    content_type = response.headers.get("content-type", "")
    assert "dxf" in content_type or "octet-stream" in content_type


def test_export_dxf_has_content(client):
    """DXF export returns non-empty content."""
    response = client.post("/api/art-studio/bracing/export-dxf", json={
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 280}
        ]
    })

    assert len(response.content) > 0


def test_export_dxf_with_soundhole(client):
    """DXF export works with soundhole reference."""
    response = client.post("/api/art-studio/bracing/export-dxf", json={
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 280}
        ],
        "soundhole_diameter_mm": 100.0,
        "soundhole_x_mm": 0,
        "soundhole_y_mm": 50
    })
    assert response.status_code == 200


def test_export_dxf_multiple_braces(client):
    """DXF export works with multiple braces."""
    response = client.post("/api/art-studio/bracing/export-dxf", json={
        "braces": [
            {"width_mm": 12, "height_mm": 8, "length_mm": 280, "angle_deg": 45},
            {"width_mm": 12, "height_mm": 8, "length_mm": 280, "angle_deg": -45}
        ]
    })
    assert response.status_code == 200


def test_export_dxf_version_r12(client):
    """DXF export works with R12 version."""
    response = client.post("/api/art-studio/bracing/export-dxf", json={
        "braces": [{"width_mm": 12, "height_mm": 8, "length_mm": 280}],
        "dxf_version": "R12"
    })
    assert response.status_code == 200


# =============================================================================
# DXF Versions Endpoint
# =============================================================================

def test_dxf_versions_returns_200(client):
    """GET /api/art-studio/bracing/dxf-versions returns 200."""
    response = client.get("/api/art-studio/bracing/dxf-versions")
    assert response.status_code == 200


def test_dxf_versions_has_default(client):
    """DXF versions response has default version."""
    response = client.get("/api/art-studio/bracing/dxf-versions")
    data = response.json()

    assert "default" in data
    assert data["default"] == "R12"


def test_dxf_versions_has_list(client):
    """DXF versions response has versions list."""
    response = client.get("/api/art-studio/bracing/dxf-versions")
    data = response.json()

    assert "versions" in data
    assert isinstance(data["versions"], list)
    assert len(data["versions"]) > 0


def test_dxf_version_has_fields(client):
    """DXF version objects have required fields."""
    response = client.get("/api/art-studio/bracing/dxf-versions")
    data = response.json()

    version = data["versions"][0]
    assert "version" in version
    assert "ac_code" in version
    assert "supports_lwpolyline" in version


def test_dxf_versions_includes_r12(client):
    """DXF versions include R12."""
    response = client.get("/api/art-studio/bracing/dxf-versions")
    data = response.json()

    version_names = [v["version"] for v in data["versions"]]
    assert "R12" in version_names


def test_dxf_r12_no_lwpolyline(client):
    """R12 does not support LWPOLYLINE."""
    response = client.get("/api/art-studio/bracing/dxf-versions")
    data = response.json()

    r12 = next((v for v in data["versions"] if v["version"] == "R12"), None)
    assert r12 is not None
    assert r12["supports_lwpolyline"] is False
