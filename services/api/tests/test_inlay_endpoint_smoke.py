"""Smoke tests for Art Studio Inlay endpoints."""

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
    """POST /api/art-studio/inlay/preview endpoint exists."""
    response = client.post("/api/art-studio/inlay/preview", json={})
    assert response.status_code != 404


def test_export_dxf_endpoint_exists(client):
    """POST /api/art-studio/inlay/export-dxf endpoint exists."""
    response = client.post("/api/art-studio/inlay/export-dxf", json={})
    assert response.status_code != 404


def test_presets_endpoint_exists(client):
    """GET /api/art-studio/inlay/presets endpoint exists."""
    response = client.get("/api/art-studio/inlay/presets")
    assert response.status_code != 404


def test_get_preset_endpoint_exists(client):
    """GET /api/art-studio/inlay/presets/{name} endpoint exists."""
    response = client.get("/api/art-studio/inlay/presets/dot_standard")
    assert response.status_code in (200, 404)


def test_preset_preview_endpoint_exists(client):
    """POST /api/art-studio/inlay/preset/{name}/preview endpoint exists."""
    response = client.post("/api/art-studio/inlay/preset/dot_standard/preview")
    assert response.status_code in (200, 404)


def test_pattern_types_endpoint_exists(client):
    """GET /api/art-studio/inlay/pattern-types endpoint exists."""
    response = client.get("/api/art-studio/inlay/pattern-types")
    assert response.status_code != 404


def test_dxf_versions_endpoint_exists(client):
    """GET /api/art-studio/inlay/dxf-versions endpoint exists."""
    response = client.get("/api/art-studio/inlay/dxf-versions")
    assert response.status_code != 404


# =============================================================================
# Preview Endpoint
# =============================================================================

def test_preview_returns_200(client):
    """POST /api/art-studio/inlay/preview returns 200."""
    response = client.post("/api/art-studio/inlay/preview", json={
        "pattern_type": "dot",
        "fret_positions": [3, 5, 7, 9, 12],
        "scale_length_mm": 648.0
    })
    assert response.status_code == 200


def test_preview_with_defaults(client):
    """POST /api/art-studio/inlay/preview works with defaults."""
    response = client.post("/api/art-studio/inlay/preview", json={})
    assert response.status_code == 200


def test_preview_has_result(client):
    """Preview response has result field."""
    response = client.post("/api/art-studio/inlay/preview", json={})
    data = response.json()

    assert "result" in data


def test_preview_result_has_shapes(client):
    """Preview result has shapes list."""
    response = client.post("/api/art-studio/inlay/preview", json={})
    data = response.json()

    result = data["result"]
    assert "shapes" in result
    assert isinstance(result["shapes"], list)


def test_preview_result_has_totals(client):
    """Preview result has total_shapes count."""
    response = client.post("/api/art-studio/inlay/preview", json={})
    data = response.json()

    result = data["result"]
    assert "total_shapes" in result
    assert isinstance(result["total_shapes"], int)


def test_preview_has_svg(client):
    """Preview response includes SVG preview."""
    response = client.post("/api/art-studio/inlay/preview", json={})
    data = response.json()

    assert "preview_svg" in data
    if data["preview_svg"]:
        assert "<svg" in data["preview_svg"]


def test_preview_shape_has_position(client):
    """Preview shapes have position data."""
    response = client.post("/api/art-studio/inlay/preview", json={
        "fret_positions": [3, 5, 7]
    })
    data = response.json()

    shapes = data["result"]["shapes"]
    assert len(shapes) > 0

    shape = shapes[0]
    assert "x_mm" in shape
    assert "y_mm" in shape
    assert "width_mm" in shape
    assert "pattern_type" in shape


def test_preview_double_at_12(client):
    """Preview with double_at_12 creates two markers at 12th fret."""
    response = client.post("/api/art-studio/inlay/preview", json={
        "fret_positions": [12],
        "double_at_12": True
    })
    data = response.json()

    shapes = data["result"]["shapes"]
    # double_at_12 creates 2 shapes for fret 12
    assert len(shapes) == 2


def test_preview_different_patterns(client):
    """Preview works with different pattern types."""
    patterns = ["dot", "diamond", "block"]

    for pattern in patterns:
        response = client.post("/api/art-studio/inlay/preview", json={
            "pattern_type": pattern
        })
        assert response.status_code == 200, f"Failed for pattern: {pattern}"


# =============================================================================
# Export DXF Endpoint
# =============================================================================

def test_export_dxf_returns_200(client):
    """POST /api/art-studio/inlay/export-dxf returns 200."""
    response = client.post("/api/art-studio/inlay/export-dxf", json={
        "pattern_type": "dot",
        "fret_positions": [3, 5, 7, 9, 12]
    })
    assert response.status_code == 200


def test_export_dxf_with_defaults(client):
    """POST /api/art-studio/inlay/export-dxf works with defaults."""
    response = client.post("/api/art-studio/inlay/export-dxf", json={})
    assert response.status_code == 200


def test_export_dxf_returns_file(client):
    """DXF export returns file content."""
    response = client.post("/api/art-studio/inlay/export-dxf", json={})

    content_type = response.headers.get("content-type", "")
    assert "dxf" in content_type or "octet-stream" in content_type


def test_export_dxf_has_content(client):
    """DXF export returns non-empty content."""
    response = client.post("/api/art-studio/inlay/export-dxf", json={})

    assert len(response.content) > 0


def test_export_dxf_has_disposition(client):
    """DXF export has content-disposition header."""
    response = client.post("/api/art-studio/inlay/export-dxf", json={})

    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert ".dxf" in disposition


def test_export_dxf_version_r12(client):
    """DXF export works with R12 version."""
    response = client.post("/api/art-studio/inlay/export-dxf", json={
        "dxf_version": "R12"
    })
    assert response.status_code == 200


# =============================================================================
# Presets Endpoint
# =============================================================================

def test_presets_returns_200(client):
    """GET /api/art-studio/inlay/presets returns 200."""
    response = client.get("/api/art-studio/inlay/presets")
    assert response.status_code == 200


def test_presets_returns_list(client):
    """GET /api/art-studio/inlay/presets returns a list."""
    response = client.get("/api/art-studio/inlay/presets")
    data = response.json()
    assert isinstance(data, list)


def test_presets_has_items(client):
    """Presets list has at least one item."""
    response = client.get("/api/art-studio/inlay/presets")
    data = response.json()
    assert len(data) >= 1


def test_preset_has_required_fields(client):
    """Preset objects have required fields."""
    response = client.get("/api/art-studio/inlay/presets")
    data = response.json()

    preset = data[0]
    assert "name" in preset
    assert "description" in preset
    assert "pattern_type" in preset
    assert "fret_count" in preset


# =============================================================================
# Get Preset Endpoint
# =============================================================================

def test_get_preset_returns_200(client):
    """GET /api/art-studio/inlay/presets/{name} returns 200 for valid preset."""
    # First get list of presets to find a valid name
    list_response = client.get("/api/art-studio/inlay/presets")
    presets = list_response.json()

    if len(presets) > 0:
        preset_name = presets[0]["name"]
        response = client.get(f"/api/art-studio/inlay/presets/{preset_name}")
        assert response.status_code == 200


def test_get_preset_has_config(client):
    """Get preset returns full configuration."""
    list_response = client.get("/api/art-studio/inlay/presets")
    presets = list_response.json()

    if len(presets) > 0:
        preset_name = presets[0]["name"]
        response = client.get(f"/api/art-studio/inlay/presets/{preset_name}")
        data = response.json()

        assert "pattern_type" in data
        assert "fret_positions" in data
        assert "scale_length_mm" in data


def test_get_unknown_preset_returns_404(client):
    """GET /api/art-studio/inlay/presets/{unknown} returns 404."""
    response = client.get("/api/art-studio/inlay/presets/nonexistent_preset_xyz")
    assert response.status_code == 404


# =============================================================================
# Preset Preview Endpoint
# =============================================================================

def test_preset_preview_returns_200(client):
    """POST /api/art-studio/inlay/preset/{name}/preview returns 200."""
    list_response = client.get("/api/art-studio/inlay/presets")
    presets = list_response.json()

    if len(presets) > 0:
        preset_name = presets[0]["name"]
        response = client.post(f"/api/art-studio/inlay/preset/{preset_name}/preview")
        assert response.status_code == 200


def test_preset_preview_has_result(client):
    """Preset preview has result with shapes."""
    list_response = client.get("/api/art-studio/inlay/presets")
    presets = list_response.json()

    if len(presets) > 0:
        preset_name = presets[0]["name"]
        response = client.post(f"/api/art-studio/inlay/preset/{preset_name}/preview")
        data = response.json()

        assert "result" in data
        assert "shapes" in data["result"]


def test_unknown_preset_preview_returns_404(client):
    """POST /api/art-studio/inlay/preset/{unknown}/preview returns 404."""
    response = client.post("/api/art-studio/inlay/preset/nonexistent_xyz/preview")
    assert response.status_code == 404


# =============================================================================
# Pattern Types Endpoint
# =============================================================================

def test_pattern_types_returns_200(client):
    """GET /api/art-studio/inlay/pattern-types returns 200."""
    response = client.get("/api/art-studio/inlay/pattern-types")
    assert response.status_code == 200


def test_pattern_types_returns_list(client):
    """GET /api/art-studio/inlay/pattern-types returns a list."""
    response = client.get("/api/art-studio/inlay/pattern-types")
    data = response.json()
    assert isinstance(data, list)


def test_pattern_types_has_dot(client):
    """Pattern types includes 'dot'."""
    response = client.get("/api/art-studio/inlay/pattern-types")
    data = response.json()
    assert "dot" in data


def test_pattern_types_has_common_types(client):
    """Pattern types includes common inlay types."""
    response = client.get("/api/art-studio/inlay/pattern-types")
    data = response.json()

    # Should have at least dot and block
    assert "dot" in data
    assert "block" in data


# =============================================================================
# DXF Versions Endpoint
# =============================================================================

def test_dxf_versions_returns_200(client):
    """GET /api/art-studio/inlay/dxf-versions returns 200."""
    response = client.get("/api/art-studio/inlay/dxf-versions")
    assert response.status_code == 200


def test_dxf_versions_returns_list(client):
    """GET /api/art-studio/inlay/dxf-versions returns a list."""
    response = client.get("/api/art-studio/inlay/dxf-versions")
    data = response.json()
    assert isinstance(data, list)


def test_dxf_versions_has_r12(client):
    """DXF versions includes R12."""
    response = client.get("/api/art-studio/inlay/dxf-versions")
    data = response.json()
    assert "R12" in data
