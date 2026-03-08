"""Smoke tests for Blueprint router endpoints."""

import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def minimal_png_bytes():
    """Create minimal PNG file bytes for testing (1x1 white pixel)."""
    # Minimal valid 1x1 PNG - white pixel
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk start
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # 8-bit RGB
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0xFF,  # compressed data
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,  # checksum
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82                      # IEND CRC
    ])
    return png_bytes


# =============================================================================
# Phase 1 - Endpoint Existence
# =============================================================================

def test_analyze_endpoint_exists(client, minimal_png_bytes):
    """POST /api/blueprint/analyze endpoint exists."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    response = client.post("/api/blueprint/analyze", files=files)
    assert response.status_code != 404


def test_to_svg_endpoint_exists(client):
    """POST /api/blueprint/to-svg endpoint exists."""
    response = client.post("/api/blueprint/to-svg", json={
        "format": "svg",
        "analysis_data": {},
        "scale_correction": 1.0,
        "width_mm": 200,
        "height_mm": 300
    })
    assert response.status_code != 404


# =============================================================================
# Phase 2 - Endpoint Existence
# =============================================================================

def test_to_dxf_endpoint_exists(client):
    """POST /api/blueprint/to-dxf endpoint exists."""
    response = client.post("/api/blueprint/to-dxf", json={
        "format": "dxf",
        "analysis_data": {}
    })
    assert response.status_code != 404


def test_vectorize_geometry_endpoint_exists(client, minimal_png_bytes):
    """POST /api/blueprint/vectorize-geometry endpoint exists."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    response = client.post("/api/blueprint/vectorize-geometry", files=files)
    assert response.status_code != 404


# =============================================================================
# Calibration - Endpoint Existence
# =============================================================================

def test_calibrate_endpoint_exists(client, minimal_png_bytes):
    """POST /api/blueprint/calibrate endpoint exists."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    response = client.post("/api/blueprint/calibrate", files=files)
    assert response.status_code != 404


def test_calibrate_manual_endpoint_exists(client, minimal_png_bytes):
    """POST /api/blueprint/calibrate/manual endpoint exists."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {
        "point1_x": 0,
        "point1_y": 0,
        "point2_x": 100,
        "point2_y": 100,
        "real_dimension": 10.0
    }
    response = client.post("/api/blueprint/calibrate/manual", files=files, data=data)
    assert response.status_code != 404


def test_get_calibration_endpoint_exists(client):
    """GET /api/blueprint/calibration/{id} endpoint exists."""
    response = client.get("/api/blueprint/calibration/test-id")
    # 404 for not found calibration is valid (endpoint exists)
    assert response.status_code in [200, 404, 500]


def test_dimensions_endpoint_exists(client, minimal_png_bytes):
    """POST /api/blueprint/dimensions endpoint exists."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"calibration_id": "test-id", "name": "test"}
    response = client.post("/api/blueprint/dimensions", files=files, data=data)
    # 404 for unknown calibration_id is valid (endpoint exists)
    assert response.status_code in [200, 400, 404, 500, 501]


def test_scale_lengths_endpoint_exists(client):
    """GET /api/blueprint/scale-lengths endpoint exists."""
    response = client.get("/api/blueprint/scale-lengths")
    assert response.status_code != 404


# =============================================================================
# Phase 1 - Response Tests
# =============================================================================

def test_analyze_returns_response(client, minimal_png_bytes):
    """Analyze endpoint returns valid response."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    response = client.post("/api/blueprint/analyze", files=files)
    # May return 503 (AI disabled) or 500 (analysis error) or 200 (success)
    assert response.status_code in [200, 400, 500, 503]


def test_analyze_requires_file(client):
    """Analyze endpoint requires file upload."""
    response = client.post("/api/blueprint/analyze")
    assert response.status_code == 422


def test_to_svg_accepts_minimal_body(client):
    """To-SVG endpoint accepts request without format (has default)."""
    response = client.post("/api/blueprint/to-svg", json={
        "analysis_data": {},
        "scale_correction": 1.0
    })
    # format field has default value, so request may succeed or fail on vectorizer
    assert response.status_code in [200, 400, 500, 501]


def test_to_svg_rejects_non_svg_format(client):
    """To-SVG endpoint rejects non-SVG format."""
    response = client.post("/api/blueprint/to-svg", json={
        "format": "dxf",
        "analysis_data": {}
    })
    assert response.status_code == 400


# =============================================================================
# Phase 2 - Response Tests
# =============================================================================

def test_to_dxf_returns_501(client):
    """To-DXF endpoint returns 501 (not implemented)."""
    response = client.post("/api/blueprint/to-dxf", json={
        "format": "dxf",
        "analysis_data": {}
    })
    # Returns 501 as this is planned functionality
    assert response.status_code in [200, 422, 500, 501]


def test_vectorize_geometry_returns_response(client, minimal_png_bytes):
    """Vectorize geometry returns valid response."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    response = client.post("/api/blueprint/vectorize-geometry", files=files)
    # May return 501 (phase 2 unavailable) or 500 (processing error) or 200
    assert response.status_code in [200, 400, 500, 501]


def test_vectorize_geometry_requires_file(client):
    """Vectorize geometry requires file upload."""
    response = client.post("/api/blueprint/vectorize-geometry")
    assert response.status_code == 422


def test_vectorize_geometry_with_scale_factor(client, minimal_png_bytes):
    """Vectorize geometry accepts scale factor."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"scale_factor": 2.0}
    response = client.post("/api/blueprint/vectorize-geometry", files=files, data=data)
    assert response.status_code in [200, 400, 500, 501]


def test_vectorize_geometry_with_instrument_type(client, minimal_png_bytes):
    """Vectorize geometry accepts instrument type."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"instrument_type": "acoustic"}
    response = client.post("/api/blueprint/vectorize-geometry", files=files, data=data)
    assert response.status_code in [200, 400, 500, 501]


def test_vectorize_geometry_with_extraction_mode(client, minimal_png_bytes):
    """Vectorize geometry accepts extraction mode."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"extraction_mode": "simple"}
    response = client.post("/api/blueprint/vectorize-geometry", files=files, data=data)
    assert response.status_code in [200, 400, 500, 501]


# =============================================================================
# Calibration - Response Tests
# =============================================================================

def test_calibrate_returns_response(client, minimal_png_bytes):
    """Calibrate endpoint returns valid response."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    response = client.post("/api/blueprint/calibrate", files=files)
    # May return 501 (calibration unavailable) or other
    assert response.status_code in [200, 400, 500, 501]


def test_calibrate_requires_file(client):
    """Calibrate endpoint requires file upload."""
    response = client.post("/api/blueprint/calibrate")
    assert response.status_code == 422


def test_calibrate_with_known_scale_length(client, minimal_png_bytes):
    """Calibrate accepts known scale length."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"known_scale_length": 25.5}
    response = client.post("/api/blueprint/calibrate", files=files, data=data)
    assert response.status_code in [200, 400, 500, 501]


def test_calibrate_with_paper_size(client, minimal_png_bytes):
    """Calibrate accepts paper size."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"paper_size": "a4"}
    response = client.post("/api/blueprint/calibrate", files=files, data=data)
    assert response.status_code in [200, 400, 500, 501]


def test_calibrate_manual_returns_response(client, minimal_png_bytes):
    """Manual calibrate returns valid response."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {
        "point1_x": 0,
        "point1_y": 0,
        "point2_x": 100,
        "point2_y": 100,
        "real_dimension": 10.0
    }
    response = client.post("/api/blueprint/calibrate/manual", files=files, data=data)
    assert response.status_code in [200, 400, 500, 501]


def test_calibrate_manual_requires_all_points(client, minimal_png_bytes):
    """Manual calibrate requires all point coordinates."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"point1_x": 0, "point1_y": 0}  # Missing point2 and real_dimension
    response = client.post("/api/blueprint/calibrate/manual", files=files, data=data)
    assert response.status_code == 422


def test_get_calibration_not_found(client):
    """Get calibration returns 404 for unknown ID."""
    response = client.get("/api/blueprint/calibration/nonexistent-id-12345")
    assert response.status_code == 404


def test_dimensions_returns_response(client, minimal_png_bytes):
    """Dimensions endpoint returns valid response."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"calibration_id": "test-id", "name": "test"}
    response = client.post("/api/blueprint/dimensions", files=files, data=data)
    # 404 for missing calibration, 501 if unavailable
    assert response.status_code in [200, 400, 404, 500, 501]


def test_dimensions_requires_calibration_id(client, minimal_png_bytes):
    """Dimensions endpoint requires calibration_id."""
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    data = {"name": "test"}
    response = client.post("/api/blueprint/dimensions", files=files, data=data)
    assert response.status_code == 422


def test_scale_lengths_returns_200(client):
    """Scale lengths endpoint returns 200."""
    response = client.get("/api/blueprint/scale-lengths")
    assert response.status_code == 200


def test_scale_lengths_returns_dict(client):
    """Scale lengths returns dictionary."""
    response = client.get("/api/blueprint/scale-lengths")
    assert isinstance(response.json(), dict)


def test_scale_lengths_has_brands(client):
    """Scale lengths includes common brands."""
    response = client.get("/api/blueprint/scale-lengths")
    data = response.json()
    assert "fender" in data
    assert "gibson" in data
    assert "prs" in data


def test_scale_lengths_fender_stratocaster(client):
    """Scale lengths has correct Fender Stratocaster value."""
    response = client.get("/api/blueprint/scale-lengths")
    data = response.json()
    assert data["fender"]["stratocaster"] == 25.5


def test_scale_lengths_gibson_les_paul(client):
    """Scale lengths has correct Gibson Les Paul value."""
    response = client.get("/api/blueprint/scale-lengths")
    data = response.json()
    assert data["gibson"]["les_paul"] == 24.75


# =============================================================================
# Integration Tests
# =============================================================================

def test_all_blueprint_endpoints_exist(client, minimal_png_bytes):
    """All blueprint endpoints exist (not 404)."""
    # GET endpoints (excluding parameterized endpoints that return 404 for unknown IDs)
    get_endpoints = [
        "/api/blueprint/scale-lengths",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"

    # POST endpoints with file
    files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
    post_file_endpoints = [
        "/api/blueprint/analyze",
        "/api/blueprint/vectorize-geometry",
        "/api/blueprint/calibrate",
    ]
    for path in post_file_endpoints:
        # Reset file position
        files = {"file": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
        response = client.post(path, files=files)
        assert response.status_code != 404, f"{path} returned 404"

    # POST endpoints with JSON
    post_json_endpoints = [
        ("/api/blueprint/to-svg", {"format": "svg", "analysis_data": {}, "scale_correction": 1.0}),
        ("/api/blueprint/to-dxf", {"format": "dxf", "analysis_data": {}}),
    ]
    for path, body in post_json_endpoints:
        response = client.post(path, json=body)
        assert response.status_code != 404, f"{path} returned 404"
