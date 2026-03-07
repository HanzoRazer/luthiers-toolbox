"""Smoke tests for bridge DXF export endpoint (wired to real DXF generator)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def _make_valid_bridge_payload():
    """Create a valid bridge geometry payload matching frontend BridgeModel."""
    return {
        "geometry": {
            "units": "mm",
            "scaleLength": 648.0,
            "stringSpread": 52.0,
            "compTreble": 1.5,
            "compBass": 3.0,
            "slotWidth": 3.0,
            "slotLength": 80.0,
            "angleDeg": 1.2,
            "endpoints": {
                "treble": {"x": 649.5, "y": -26.0},
                "bass": {"x": 651.0, "y": 26.0},
            },
            "slotPolygon": [
                {"x": 647.0, "y": -40.0},
                {"x": 653.0, "y": -40.0},
                {"x": 653.0, "y": 40.0},
                {"x": 647.0, "y": 40.0},
            ],
        },
        "filename": "test_bridge_648mm",
    }


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_bridge_export_dxf_endpoint_exists(client):
    """POST /api/cam/bridge/export_dxf endpoint exists."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    assert response.status_code != 404


# =============================================================================
# Valid Export Cases
# =============================================================================

def test_bridge_export_dxf_returns_200(client):
    """POST /api/cam/bridge/export_dxf returns 200 with valid payload."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    assert response.status_code == 200


def test_bridge_export_dxf_returns_dxf_content_type(client):
    """POST /api/cam/bridge/export_dxf returns application/dxf content type."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    assert "application/dxf" in response.headers.get("content-type", "")


def test_bridge_export_dxf_returns_attachment_header(client):
    """POST /api/cam/bridge/export_dxf returns Content-Disposition attachment header."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "filename=" in disposition


def test_bridge_export_dxf_filename_in_header(client):
    """POST /api/cam/bridge/export_dxf uses provided filename in header."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    disposition = response.headers.get("content-disposition", "")
    assert "test_bridge_648mm" in disposition
    assert ".dxf" in disposition


def test_bridge_export_dxf_contains_section_markers(client):
    """POST /api/cam/bridge/export_dxf returns DXF with SECTION/ENDSEC markers."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    content = response.text
    assert "SECTION" in content
    assert "ENTITIES" in content
    assert "ENDSEC" in content
    assert "EOF" in content


def test_bridge_export_dxf_contains_saddle_layer(client):
    """POST /api/cam/bridge/export_dxf contains SADDLE layer."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    content = response.text
    assert "SADDLE" in content


def test_bridge_export_dxf_contains_slot_layer(client):
    """POST /api/cam/bridge/export_dxf contains SLOT layer."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    content = response.text
    assert "SLOT" in content


def test_bridge_export_dxf_contains_reference_layer(client):
    """POST /api/cam/bridge/export_dxf contains REFERENCE layer."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    content = response.text
    assert "REFERENCE" in content


def test_bridge_export_dxf_contains_line_entities(client):
    """POST /api/cam/bridge/export_dxf contains LINE entities."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    content = response.text
    # LINE entities use group codes 10, 20 (start) and 11, 21 (end)
    assert "LINE" in content
    assert "\n10\n" in content
    assert "\n11\n" in content


def test_bridge_export_dxf_contains_metadata_comment(client):
    """POST /api/cam/bridge/export_dxf contains metadata comment."""
    response = client.post("/api/cam/bridge/export_dxf", json=_make_valid_bridge_payload())
    content = response.text
    # Metadata starts with group code 999
    assert "999" in content
    assert "BRIDGE" in content
    assert "SCALE=648.0" in content


# =============================================================================
# Validation Cases
# =============================================================================

def test_bridge_export_dxf_requires_geometry(client):
    """POST /api/cam/bridge/export_dxf requires geometry field."""
    response = client.post("/api/cam/bridge/export_dxf", json={})
    assert response.status_code == 422


def test_bridge_export_dxf_requires_scale_length(client):
    """POST /api/cam/bridge/export_dxf requires scaleLength in geometry."""
    payload = _make_valid_bridge_payload()
    del payload["geometry"]["scaleLength"]
    response = client.post("/api/cam/bridge/export_dxf", json=payload)
    assert response.status_code == 422


def test_bridge_export_dxf_requires_endpoints(client):
    """POST /api/cam/bridge/export_dxf requires endpoints in geometry."""
    payload = _make_valid_bridge_payload()
    del payload["geometry"]["endpoints"]
    response = client.post("/api/cam/bridge/export_dxf", json=payload)
    assert response.status_code == 422


def test_bridge_export_dxf_requires_slot_polygon(client):
    """POST /api/cam/bridge/export_dxf requires slotPolygon in geometry."""
    payload = _make_valid_bridge_payload()
    del payload["geometry"]["slotPolygon"]
    response = client.post("/api/cam/bridge/export_dxf", json=payload)
    assert response.status_code == 422


# =============================================================================
# Edge Cases
# =============================================================================

def test_bridge_export_dxf_without_filename_uses_default(client):
    """POST /api/cam/bridge/export_dxf uses default filename when not provided."""
    payload = _make_valid_bridge_payload()
    del payload["filename"]
    response = client.post("/api/cam/bridge/export_dxf", json=payload)
    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    assert "filename=" in disposition
    assert ".dxf" in disposition


def test_bridge_export_dxf_sanitizes_filename(client):
    """POST /api/cam/bridge/export_dxf sanitizes special characters in filename."""
    payload = _make_valid_bridge_payload()
    payload["filename"] = "bridge/../../../etc/passwd"
    response = client.post("/api/cam/bridge/export_dxf", json=payload)
    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    # Filename should be sanitized - no path separators (path traversal neutralized)
    filename_part = disposition.replace('attachment; filename="', "").replace('"', "")
    assert "/" not in filename_part
    assert "\\" not in filename_part
    # Should still have .dxf extension
    assert filename_part.endswith(".dxf")


def test_bridge_export_dxf_handles_imperial_units(client):
    """POST /api/cam/bridge/export_dxf accepts imperial units."""
    payload = _make_valid_bridge_payload()
    payload["geometry"]["units"] = "in"
    payload["geometry"]["scaleLength"] = 25.5  # 25.5 inches
    response = client.post("/api/cam/bridge/export_dxf", json=payload)
    assert response.status_code == 200
    content = response.text
    assert "UNITS=in" in content


def test_bridge_export_dxf_empty_slot_polygon_still_works(client):
    """POST /api/cam/bridge/export_dxf handles empty slotPolygon gracefully."""
    payload = _make_valid_bridge_payload()
    payload["geometry"]["slotPolygon"] = []
    response = client.post("/api/cam/bridge/export_dxf", json=payload)
    # Should still succeed, just no SLOT lines
    assert response.status_code == 200
    content = response.text
    assert "SADDLE" in content  # Saddle line should still be there
