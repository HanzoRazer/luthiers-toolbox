"""Smoke tests for DXF Preflight Validator endpoints."""

import pytest
import base64
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# Sample CurveLab points for testing (simple square)
SQUARE_POINTS = [
    {"x": 0.0, "y": 0.0},
    {"x": 100.0, "y": 0.0},
    {"x": 100.0, "y": 100.0},
    {"x": 0.0, "y": 100.0},
    {"x": 0.0, "y": 0.0}  # Closed
]

# Open curve (not closed)
OPEN_CURVE_POINTS = [
    {"x": 0.0, "y": 0.0},
    {"x": 50.0, "y": 100.0},
    {"x": 100.0, "y": 0.0}
]

# Points with duplicates
DUPLICATE_POINTS = [
    {"x": 0.0, "y": 0.0},
    {"x": 0.0, "y": 0.0},  # Duplicate
    {"x": 100.0, "y": 0.0},
    {"x": 100.0, "y": 100.0},
    {"x": 0.0, "y": 0.0}
]

# Minimal valid DXF R12 file (base64 encoded)
# This is a minimal DXF with one line entity
MINIMAL_DXF_CONTENT = """0
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
0
10
0.0
20
0.0
11
100.0
21
100.0
0
ENDSEC
0
EOF
"""

MINIMAL_DXF_BASE64 = base64.b64encode(MINIMAL_DXF_CONTENT.encode('utf-8')).decode('utf-8')


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_curve_report_endpoint_exists(client):
    """POST /dxf/preflight/curve_report endpoint exists."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS
    })
    assert response.status_code != 404


def test_validate_endpoint_exists(client):
    """POST /dxf/preflight/validate endpoint exists."""
    # This needs a file upload, so we'll check it returns something other than 404
    response = client.post("/api/dxf/preflight/validate")
    # Should be 422 (missing file) not 404
    assert response.status_code != 404


def test_validate_base64_endpoint_exists(client):
    """POST /dxf/preflight/validate_base64 endpoint exists."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf"
    })
    assert response.status_code != 404


def test_auto_fix_endpoint_exists(client):
    """POST /dxf/preflight/auto_fix endpoint exists."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": []
    })
    assert response.status_code != 404


# =============================================================================
# Curve Report Endpoint
# =============================================================================

def test_curve_report_returns_200(client):
    """POST /dxf/preflight/curve_report returns 200."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS
    })
    assert response.status_code == 200


def test_curve_report_has_required_fields(client):
    """Curve report response has required fields."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS
    })
    data = response.json()

    assert "units" in data
    assert "tolerance_mm" in data
    assert "issues" in data
    assert "errors_count" in data
    assert "warnings_count" in data
    assert "info_count" in data
    assert "polyline" in data
    assert "cam_ready" in data
    assert "recommended_actions" in data


def test_curve_report_closed_curve(client):
    """Closed curve is CAM-ready."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "tolerance_mm": 0.1
    })
    data = response.json()

    assert data["polyline"]["closed"] is True
    assert data["errors_count"] == 0


def test_curve_report_open_curve(client):
    """Open curve generates warning."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": OPEN_CURVE_POINTS,
        "tolerance_mm": 0.1
    })
    data = response.json()

    assert data["polyline"]["closed"] is False
    # Should have warning about open polyline
    assert data["warnings_count"] >= 1


def test_curve_report_duplicate_points(client):
    """Duplicate points generate warning."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": DUPLICATE_POINTS,
        "tolerance_mm": 0.1
    })
    data = response.json()

    assert data["polyline"]["duplicate_count"] >= 1
    # Should have warning about duplicates
    warnings = [i["message"] for i in data["issues"] if i["severity"] == "warning"]
    assert any("duplicate" in w.lower() for w in warnings)


def test_curve_report_polyline_metrics(client):
    """Polyline metrics are calculated correctly."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "units": "mm"
    })
    data = response.json()

    polyline = data["polyline"]
    assert polyline["point_count"] == 5
    assert polyline["length"] > 0
    assert polyline["length_units"] == "mm"
    assert "bounding_box" in polyline


def test_curve_report_bounding_box(client):
    """Bounding box is calculated."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS
    })
    data = response.json()

    bbox = data["polyline"]["bounding_box"]
    assert "minx" in bbox or "min_x" in bbox or len(bbox) > 0


def test_curve_report_units_mm(client):
    """Curve report accepts mm units."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "units": "mm"
    })
    data = response.json()

    assert data["units"] == "mm"


def test_curve_report_units_inch(client):
    """Curve report accepts inch units."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "units": "inch"
    })
    data = response.json()

    assert data["units"] == "inch"


def test_curve_report_tolerance_param(client):
    """Curve report uses tolerance parameter."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "tolerance_mm": 0.05
    })
    data = response.json()

    assert data["tolerance_mm"] == 0.05


def test_curve_report_layer_name(client):
    """Curve report accepts custom layer name."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "layer": "CONTOUR"
    })
    assert response.status_code == 200


def test_curve_report_invalid_layer_name(client):
    """Curve report warns about invalid layer names."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "layer": "Layer With Spaces!"
    })
    data = response.json()

    # Should have a warning about layer name
    layer_issues = [i for i in data["issues"] if i["category"] == "layers"]
    assert len(layer_issues) >= 1


def test_curve_report_recommended_actions(client):
    """Curve report has recommended actions."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS
    })
    data = response.json()

    assert isinstance(data["recommended_actions"], list)
    assert len(data["recommended_actions"]) >= 1


def test_curve_report_requires_points(client):
    """Curve report requires points field."""
    response = client.post("/api/dxf/preflight/curve_report", json={})
    assert response.status_code == 422


def test_curve_report_minimum_points(client):
    """Curve report requires at least 2 points."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": [{"x": 0, "y": 0}]
    })
    assert response.status_code == 400


def test_curve_report_biarc_entities(client):
    """Curve report accepts biarc entities."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "biarc_entities": [
            {"type": "arc", "radius": 5.0},
            {"type": "line"}
        ]
    })
    data = response.json()

    # Should have biarc metrics
    assert "biarc" in data


def test_curve_report_tolerance_out_of_range(client):
    """Curve report warns about tolerance out of range."""
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": SQUARE_POINTS,
        "tolerance_mm": 10.0  # Too large
    })
    data = response.json()

    # Should have warning about tolerance
    tolerance_warnings = [i for i in data["issues"] if "tolerance" in i["message"].lower()]
    assert len(tolerance_warnings) >= 1


# =============================================================================
# Validate Base64 Endpoint
# =============================================================================

def test_validate_base64_returns_200(client):
    """POST /dxf/preflight/validate_base64 returns 200."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf"
    })
    assert response.status_code == 200


def test_validate_base64_has_report_fields(client):
    """Validate base64 response has report fields."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf"
    })
    data = response.json()

    assert "filename" in data
    assert "dxf_version" in data
    assert "issues" in data
    assert "geometry" in data
    assert "layers" in data
    assert "cam_ready" in data


def test_validate_base64_filename_preserved(client):
    """Validate base64 preserves filename."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "my_design.dxf"
    })
    data = response.json()

    assert data["filename"] == "my_design.dxf"


def test_validate_base64_geometry_summary(client):
    """Validate base64 returns geometry summary."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf"
    })
    data = response.json()

    geometry = data["geometry"]
    assert "lines" in geometry
    assert "arcs" in geometry
    assert "circles" in geometry
    assert "polylines" in geometry
    assert "total" in geometry


def test_validate_base64_invalid_base64(client):
    """Validate base64 rejects invalid base64."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "dxf_base64": "not-valid-base64!!!",
        "filename": "test.dxf"
    })
    assert response.status_code == 400


def test_validate_base64_requires_dxf(client):
    """Validate base64 requires dxf_base64 field."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "filename": "test.dxf"
    })
    assert response.status_code == 422


def test_validate_base64_default_filename(client):
    """Validate base64 uses default filename."""
    response = client.post("/api/dxf/preflight/validate_base64", json={
        "dxf_base64": MINIMAL_DXF_BASE64
    })
    data = response.json()

    # Default is "uploaded.dxf"
    assert data["filename"] == "uploaded.dxf"


# =============================================================================
# Validate File Upload Endpoint
# =============================================================================

def test_validate_requires_file(client):
    """POST /dxf/preflight/validate requires file upload."""
    response = client.post("/api/dxf/preflight/validate")
    assert response.status_code == 422


def test_validate_rejects_non_dxf(client):
    """Validate rejects non-DXF files."""
    response = client.post(
        "/api/dxf/preflight/validate",
        files={"file": ("test.txt", b"not a dxf file", "text/plain")}
    )
    assert response.status_code == 400


def test_validate_accepts_dxf_file(client):
    """Validate accepts DXF file upload."""
    dxf_content = MINIMAL_DXF_CONTENT.encode('utf-8')
    response = client.post(
        "/api/dxf/preflight/validate",
        files={"file": ("test.dxf", dxf_content, "application/dxf")}
    )
    assert response.status_code == 200


def test_validate_file_returns_report(client):
    """Validate file returns validation report."""
    dxf_content = MINIMAL_DXF_CONTENT.encode('utf-8')
    response = client.post(
        "/api/dxf/preflight/validate",
        files={"file": ("geometry.dxf", dxf_content, "application/dxf")}
    )
    data = response.json()

    assert "filename" in data
    assert "dxf_version" in data
    assert "issues" in data
    assert "geometry" in data
    assert "cam_ready" in data


# =============================================================================
# Auto-Fix Endpoint
# =============================================================================

def test_auto_fix_returns_200(client):
    """POST /dxf/preflight/auto_fix returns 200."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": []
    })
    assert response.status_code == 200


def test_auto_fix_has_response_fields(client):
    """Auto-fix response has required fields."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": []
    })
    data = response.json()

    assert "fixed_dxf_base64" in data
    assert "fixes_applied" in data
    assert "validation_report" in data


def test_auto_fix_returns_base64(client):
    """Auto-fix returns valid base64."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": []
    })
    data = response.json()

    # Should be valid base64
    try:
        decoded = base64.b64decode(data["fixed_dxf_base64"])
        assert len(decoded) > 0
    except Exception:
        pytest.fail("fixed_dxf_base64 is not valid base64")


def test_auto_fix_convert_to_r12(client):
    """Auto-fix can convert to R12."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": ["convert_to_r12"]
    })
    data = response.json()

    assert "R12" in " ".join(data["fixes_applied"])


def test_auto_fix_close_polylines(client):
    """Auto-fix can close open polylines."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": ["close_open_polylines"]
    })
    assert response.status_code == 200


def test_auto_fix_set_units_mm(client):
    """Auto-fix can set units to mm."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": ["set_units_mm"]
    })
    data = response.json()

    # set_units_mm only works without convert_to_r12
    assert response.status_code == 200


def test_auto_fix_invalid_base64(client):
    """Auto-fix rejects invalid base64."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": "not-valid-base64!!!",
        "filename": "test.dxf",
        "fixes": []
    })
    assert response.status_code == 400


def test_auto_fix_requires_fixes_list(client):
    """Auto-fix requires fixes list."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf"
    })
    assert response.status_code == 422


def test_auto_fix_validation_report_included(client):
    """Auto-fix includes new validation report."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": []
    })
    data = response.json()

    report = data["validation_report"]
    assert "dxf_version" in report
    assert "geometry" in report
    assert "cam_ready" in report


def test_auto_fix_multiple_fixes(client):
    """Auto-fix can apply multiple fixes."""
    response = client.post("/api/dxf/preflight/auto_fix", json={
        "dxf_base64": MINIMAL_DXF_BASE64,
        "filename": "test.dxf",
        "fixes": ["close_open_polylines", "convert_to_r12"]
    })
    assert response.status_code == 200


# =============================================================================
# Edge Cases
# =============================================================================

def test_curve_report_very_small_geometry(client):
    """Curve report handles very small geometry."""
    tiny_points = [
        {"x": 0.0, "y": 0.0},
        {"x": 0.001, "y": 0.0},
        {"x": 0.001, "y": 0.001},
        {"x": 0.0, "y": 0.0}
    ]
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": tiny_points,
        "units": "mm"
    })
    data = response.json()

    # Should have info about small geometry
    info_issues = [i for i in data["issues"] if i["severity"] == "info"]
    assert len(info_issues) >= 1


def test_curve_report_very_large_geometry(client):
    """Curve report handles very large geometry."""
    large_points = [
        {"x": 0.0, "y": 0.0},
        {"x": 10000.0, "y": 0.0},
        {"x": 10000.0, "y": 10000.0},
        {"x": 0.0, "y": 0.0}
    ]
    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": large_points,
        "units": "mm"
    })
    data = response.json()

    # Should have info about large geometry
    info_issues = [i for i in data["issues"] if i["severity"] == "info"]
    assert len(info_issues) >= 1


def test_curve_report_many_points(client):
    """Curve report handles many points."""
    # Generate 100 points in a circle
    import math
    many_points = []
    for i in range(100):
        angle = 2 * math.pi * i / 100
        many_points.append({
            "x": 50.0 + 50.0 * math.cos(angle),
            "y": 50.0 + 50.0 * math.sin(angle)
        })
    many_points.append(many_points[0])  # Close

    response = client.post("/api/dxf/preflight/curve_report", json={
        "points": many_points
    })
    assert response.status_code == 200

    data = response.json()
    assert data["polyline"]["point_count"] == 101
