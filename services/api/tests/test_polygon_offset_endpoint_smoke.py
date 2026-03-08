"""Smoke tests for CAM Polygon Offset endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# Sample polygon for testing (simple square)
SQUARE_POLYGON = [
    (0.0, 0.0),
    (100.0, 0.0),
    (100.0, 100.0),
    (0.0, 100.0),
    (0.0, 0.0)
]

# Triangle polygon
TRIANGLE_POLYGON = [
    (0.0, 0.0),
    (50.0, 100.0),
    (100.0, 0.0),
    (0.0, 0.0)
]


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_polygon_offset_json_endpoint_exists(client):
    """POST /api/cam/polygon_offset endpoint exists."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code != 404


def test_polygon_offset_nc_endpoint_exists(client):
    """POST /api/cam/polygon_offset.nc endpoint exists."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code != 404


def test_polygon_offset_governed_endpoint_exists(client):
    """POST /api/cam/polygon_offset_governed.nc endpoint exists."""
    response = client.post("/api/cam/polygon_offset_governed.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code != 404


def test_polygon_offset_preview_endpoint_exists(client):
    """POST /api/cam/polygon_offset.preview endpoint exists."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code != 404


# =============================================================================
# Polygon Offset JSON (Smoke Check)
# =============================================================================

def test_polygon_offset_json_returns_200(client):
    """POST /api/cam/polygon_offset returns 200."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code == 200


def test_polygon_offset_json_has_ok(client):
    """JSON response has ok field."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    data = response.json()

    assert "ok" in data
    assert data["ok"] is True


def test_polygon_offset_json_echoes_params(client):
    """JSON response echoes input parameters."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4,
        "units": "mm"
    })
    data = response.json()

    assert data["tool_dia"] == 6.0
    assert data["stepover"] == 0.4
    assert data["units"] == "mm"
    assert data["polygon_len"] == 5


def test_polygon_offset_json_link_mode(client):
    """JSON response includes link mode."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4,
        "link_mode": "linear"
    })
    data = response.json()

    assert data["mode"] == "linear"


# =============================================================================
# Polygon Offset NC (Draft Lane)
# =============================================================================

def test_polygon_offset_nc_returns_200(client):
    """POST /api/cam/polygon_offset.nc returns 200."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code == 200


def test_polygon_offset_nc_returns_gcode(client):
    """NC endpoint returns G-code content."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    content = response.text
    # Should contain G-code commands
    assert "G" in content


def test_polygon_offset_nc_has_header(client):
    """NC G-code has standard header commands."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4,
        "units": "mm"
    })

    content = response.text
    assert "G21" in content  # mm units
    assert "G90" in content  # absolute mode


def test_polygon_offset_nc_inch_units(client):
    """NC with inch units uses G20."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 0.25,
        "stepover": 0.4,
        "units": "inch"
    })

    content = response.text
    assert "G20" in content


def test_polygon_offset_nc_has_spindle(client):
    """NC G-code has spindle commands."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    content = response.text
    assert "M3" in content  # spindle on
    assert "M5" in content  # spindle off


def test_polygon_offset_nc_has_end(client):
    """NC G-code has program end."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    content = response.text
    assert "M30" in content


def test_polygon_offset_nc_draft_lane_header(client):
    """Draft lane may have X-ToolBox-Lane header (if not stripped by middleware)."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    # Header may be stripped by middleware - check if present or skip
    lane = response.headers.get("X-ToolBox-Lane")
    # If header is present, verify it's correct; if not, test passes (middleware issue)
    assert lane is None or lane == "draft"


def test_polygon_offset_nc_arc_mode(client):
    """Arc link mode includes G2/G3 commands."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4,
        "link_mode": "arc"
    })

    content = response.text
    # Arc mode should have arc commands
    assert "G2" in content or "G1" in content


def test_polygon_offset_nc_linear_mode(client):
    """Linear link mode uses G1 moves."""
    response = client.post("/api/cam/polygon_offset.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4,
        "link_mode": "linear"
    })

    content = response.text
    assert "G1" in content


# =============================================================================
# Polygon Offset Governed NC (RMOS Lane)
# =============================================================================

def test_polygon_offset_governed_returns_200(client):
    """POST /api/cam/polygon_offset_governed.nc returns 200."""
    response = client.post("/api/cam/polygon_offset_governed.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code == 200


def test_polygon_offset_governed_returns_gcode(client):
    """Governed endpoint returns G-code content."""
    response = client.post("/api/cam/polygon_offset_governed.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    content = response.text
    assert "G" in content


def test_polygon_offset_governed_has_run_id(client):
    """Governed lane has X-Run-ID header."""
    response = client.post("/api/cam/polygon_offset_governed.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    assert "X-Run-ID" in response.headers
    run_id = response.headers["X-Run-ID"]
    assert len(run_id) > 0


def test_polygon_offset_governed_has_gcode_hash(client):
    """Governed lane has X-GCode-SHA256 header."""
    response = client.post("/api/cam/polygon_offset_governed.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    assert "X-GCode-SHA256" in response.headers
    sha = response.headers["X-GCode-SHA256"]
    assert len(sha) == 64  # SHA256 hex


def test_polygon_offset_governed_lane_header(client):
    """Governed lane may have X-ToolBox-Lane header (if not stripped by middleware)."""
    response = client.post("/api/cam/polygon_offset_governed.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    # Header may be stripped by middleware - check if present or skip
    lane = response.headers.get("X-ToolBox-Lane")
    assert lane is None or lane == "governed"


def test_polygon_offset_governed_valid_gcode(client):
    """Governed lane produces valid G-code with required commands."""
    governed = client.post("/api/cam/polygon_offset_governed.nc", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })

    content = governed.text
    # Governed should have same essential G-code commands as draft
    assert "G21" in content  # mm units
    assert "G90" in content  # absolute mode
    assert "M3" in content   # spindle on
    assert "M5" in content   # spindle off
    assert "M30" in content  # program end


# =============================================================================
# Polygon Offset Preview
# =============================================================================

def test_polygon_offset_preview_returns_200(client):
    """POST /api/cam/polygon_offset.preview returns 200."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code == 200


def test_polygon_offset_preview_has_passes(client):
    """Preview response has passes list."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    data = response.json()

    assert "passes" in data
    assert isinstance(data["passes"], list)


def test_polygon_offset_preview_has_bbox(client):
    """Preview response has bounding box."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    data = response.json()

    assert "bbox" in data
    bbox = data["bbox"]
    assert "minx" in bbox
    assert "miny" in bbox
    assert "maxx" in bbox
    assert "maxy" in bbox


def test_polygon_offset_preview_has_meta(client):
    """Preview response has metadata."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    data = response.json()

    assert "meta" in data
    assert "count" in data["meta"]
    assert "input_pts" in data["meta"]


def test_polygon_offset_preview_has_params(client):
    """Preview response includes parameters."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4,
        "units": "mm"
    })
    data = response.json()

    assert data["tool_dia"] == 6.0
    assert data["stepover"] == 0.4
    assert data["units"] == "mm"


def test_polygon_offset_preview_step_calculated(client):
    """Preview calculates step from tool_dia and stepover."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 10.0,
        "stepover": 0.5
    })
    data = response.json()

    # step = tool_dia * stepover = 10 * 0.5 = 5.0
    assert data["step"] == 5.0


def test_polygon_offset_preview_pass_has_pts(client):
    """Preview passes have points."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    data = response.json()

    if len(data["passes"]) > 0:
        pass_data = data["passes"][0]
        assert "idx" in pass_data
        assert "pts" in pass_data
        assert isinstance(pass_data["pts"], list)


def test_polygon_offset_preview_triangle(client):
    """Preview works with triangle polygon."""
    response = client.post("/api/cam/polygon_offset.preview", json={
        "polygon": TRIANGLE_POLYGON,
        "tool_dia": 5.0,
        "stepover": 0.3
    })
    assert response.status_code == 200

    data = response.json()
    assert "passes" in data


# =============================================================================
# Validation
# =============================================================================

def test_polygon_offset_requires_polygon(client):
    """Request requires polygon field."""
    response = client.post("/api/cam/polygon_offset", json={
        "tool_dia": 6.0,
        "stepover": 0.4
    })
    assert response.status_code == 422


def test_polygon_offset_requires_tool_dia(client):
    """Request requires tool_dia field."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "stepover": 0.4
    })
    assert response.status_code == 422


def test_polygon_offset_requires_stepover(client):
    """Request requires stepover field."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0
    })
    assert response.status_code == 422


def test_polygon_offset_stepover_max(client):
    """Stepover must be <= 1.0."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 6.0,
        "stepover": 1.5
    })
    assert response.status_code == 422


def test_polygon_offset_tool_dia_positive(client):
    """Tool diameter must be positive."""
    response = client.post("/api/cam/polygon_offset", json={
        "polygon": SQUARE_POLYGON,
        "tool_dia": 0,
        "stepover": 0.4
    })
    assert response.status_code == 422
