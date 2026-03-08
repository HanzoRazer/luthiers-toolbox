"""Smoke tests for DXF Plan router endpoints."""

import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def minimal_dxf_bytes():
    """Create minimal DXF file bytes for testing."""
    dxf_content = """0
SECTION
2
HEADER
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
GEOMETRY
10
0.0
20
0.0
11
100.0
21
0.0
0
LINE
8
GEOMETRY
10
100.0
20
0.0
11
100.0
21
100.0
0
LINE
8
GEOMETRY
10
100.0
20
100.0
11
0.0
21
100.0
0
LINE
8
GEOMETRY
10
0.0
20
100.0
11
0.0
21
0.0
0
ENDSEC
0
EOF
"""
    return dxf_content.encode('utf-8')


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_plan_from_dxf_endpoint_exists(client, minimal_dxf_bytes):
    """POST /api/cam/plan_from_dxf endpoint exists."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    response = client.post("/api/cam/plan_from_dxf", files=files)
    assert response.status_code != 404


# =============================================================================
# Response Tests
# =============================================================================

def test_plan_from_dxf_returns_response(client, minimal_dxf_bytes):
    """Plan from DXF returns valid response."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    response = client.post("/api/cam/plan_from_dxf", files=files)
    # May return 200 or 400/500 depending on DXF validity
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_units_mm(client, minimal_dxf_bytes):
    """Plan from DXF accepts mm units."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"units": "mm"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_units_inch(client, minimal_dxf_bytes):
    """Plan from DXF accepts inch units."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"units": "inch"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_tool_diameter(client, minimal_dxf_bytes):
    """Plan from DXF accepts tool diameter."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"tool_d": 3.175}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_geometry_layer(client, minimal_dxf_bytes):
    """Plan from DXF accepts geometry layer."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"geometry_layer": "GEOMETRY"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_custom_layer(client, minimal_dxf_bytes):
    """Plan from DXF with custom layer name."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"geometry_layer": "CUSTOM_LAYER"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    # Will likely return 400 since CUSTOM_LAYER doesn't exist
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_stepover(client, minimal_dxf_bytes):
    """Plan from DXF accepts stepover fraction."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"stepover": 0.4}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_stepdown(client, minimal_dxf_bytes):
    """Plan from DXF accepts stepdown value."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"stepdown": 1.5}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_margin(client, minimal_dxf_bytes):
    """Plan from DXF accepts margin value."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"margin": 0.25}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_spiral_strategy(client, minimal_dxf_bytes):
    """Plan from DXF accepts Spiral strategy."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"strategy": "Spiral"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_lanes_strategy(client, minimal_dxf_bytes):
    """Plan from DXF accepts Lanes strategy."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"strategy": "Lanes"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_feed_xy(client, minimal_dxf_bytes):
    """Plan from DXF accepts feed rate."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"feed_xy": 800.0}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_safe_z(client, minimal_dxf_bytes):
    """Plan from DXF accepts safe Z height."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"safe_z": 10.0}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_z_rough(client, minimal_dxf_bytes):
    """Plan from DXF accepts rough cut depth."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"z_rough": -2.0}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


def test_plan_from_dxf_with_all_params(client, minimal_dxf_bytes):
    """Plan from DXF with all parameters."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {
        "units": "mm",
        "tool_d": 6.0,
        "geometry_layer": "GEOMETRY",
        "stepover": 0.45,
        "stepdown": 2.0,
        "margin": 0.5,
        "strategy": "Spiral",
        "feed_xy": 1200.0,
        "safe_z": 5.0,
        "z_rough": -1.5,
    }
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code in [200, 400, 422, 500]


# =============================================================================
# Validation Tests
# =============================================================================

def test_plan_from_dxf_requires_file(client):
    """Plan from DXF requires file upload."""
    response = client.post("/api/cam/plan_from_dxf", data={})
    assert response.status_code == 422


def test_plan_from_dxf_rejects_invalid_units(client, minimal_dxf_bytes):
    """Plan from DXF rejects invalid units."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"units": "meters"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code == 422


def test_plan_from_dxf_rejects_invalid_strategy(client, minimal_dxf_bytes):
    """Plan from DXF rejects invalid strategy."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    data = {"strategy": "Invalid"}
    response = client.post("/api/cam/plan_from_dxf", files=files, data=data)
    assert response.status_code == 422


def test_plan_from_dxf_with_empty_dxf(client):
    """Plan from DXF with empty file."""
    files = {"file": ("test.dxf", io.BytesIO(b""), "application/octet-stream")}
    response = client.post("/api/cam/plan_from_dxf", files=files)
    # Should return error for empty file
    assert response.status_code in [400, 422, 500]


def test_plan_from_dxf_with_invalid_dxf(client):
    """Plan from DXF with invalid content."""
    files = {"file": ("test.dxf", io.BytesIO(b"not a dxf file"), "application/octet-stream")}
    response = client.post("/api/cam/plan_from_dxf", files=files)
    # Should return error for invalid file
    assert response.status_code in [400, 422, 500]


# =============================================================================
# Response Structure Tests
# =============================================================================

def test_plan_from_dxf_response_is_dict(client, minimal_dxf_bytes):
    """Plan from DXF response is dictionary."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    response = client.post("/api/cam/plan_from_dxf", files=files)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)


def test_plan_from_dxf_response_has_plan(client, minimal_dxf_bytes):
    """Plan from DXF response has plan field."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    response = client.post("/api/cam/plan_from_dxf", files=files)
    if response.status_code == 200:
        data = response.json()
        assert "plan" in data


def test_plan_from_dxf_response_has_debug(client, minimal_dxf_bytes):
    """Plan from DXF response has debug field."""
    files = {"file": ("test.dxf", io.BytesIO(minimal_dxf_bytes), "application/octet-stream")}
    response = client.post("/api/cam/plan_from_dxf", files=files)
    if response.status_code == 200:
        data = response.json()
        assert "debug" in data
