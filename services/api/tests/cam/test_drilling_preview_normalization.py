"""
Test Drilling Preview Normalization (Dev Order 5E)

Verifies that the drilling preview endpoint returns governed preview
standard fields with proper gate evaluation.

Reference: CAM_PREVIEW_CONTRACT_STANDARD.md
Canonical pattern: nut_slot_cam.py, fret_slots_router.py (5C/5D)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# --- Test Data ---

VALID_HOLES = [
    {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 8.0},
    {"x_mm": 30.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 8.0},
    {"x_mm": 50.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 8.0},
]

OVERLAPPING_HOLES = [
    {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 10.0, "depth_mm": 15.0},
    {"x_mm": 15.0, "y_mm": 10.0, "diameter_mm": 10.0, "depth_mm": 15.0},  # Overlaps with first
]

NEAR_TOUCHING_HOLES = [
    {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 5.0, "depth_mm": 15.0},
    {"x_mm": 15.5, "y_mm": 10.0, "diameter_mm": 5.0, "depth_mm": 15.0},  # Gap = 0.5mm
]


class TestGovernedPreviewFields:
    """Verify governed preview standard fields are present."""

    def test_response_has_operation_field(self):
        """operation field identifies the preview type."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        assert resp.status_code == 200
        data = resp.json()
        assert data["operation"] == "drilling_preview"

    def test_response_has_status_field(self):
        """status field is always 'preview'."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert data["status"] == "preview"

    def test_response_has_gate_field(self):
        """gate field indicates preview safety."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert "gate" in data
        assert data["gate"] in ["green", "yellow", "red"]

    def test_response_has_units_field(self):
        """units field is always 'mm'."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert data["units"] == "mm"

    def test_response_has_coordinate_system(self):
        """coordinate_system provides spatial reference metadata."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        cs = data["coordinate_system"]
        assert cs["units"] == "mm"
        assert "origin" in cs
        assert "x_axis" in cs
        assert "y_axis" in cs
        assert "z_axis" in cs
        assert cs["z_zero"] == "top_of_stock"

    def test_response_has_canonical_toolpath(self):
        """canonical_toolpath wraps hole data."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        ct = data["canonical_toolpath"]
        assert "holes" in ct
        assert ct["hole_count"] == len(VALID_HOLES)

    def test_response_has_preview_geometry(self):
        """preview_geometry provides frontend-friendly format."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        pg = data["preview_geometry"]
        assert "holes" in pg
        for hole in pg["holes"]:
            assert "x" in hole
            assert "y" in hole
            assert "diameter_mm" in hole
            assert "radius_mm" in hole

    def test_response_has_warnings_list(self):
        """warnings is a list of warning message strings."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert "warnings" in data
        assert isinstance(data["warnings"], list)

    def test_response_has_errors_list(self):
        """errors is a list of error message strings."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert "errors" in data
        assert isinstance(data["errors"], list)

    def test_response_has_issues_list(self):
        """issues contains structured CamIssue objects."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_response_has_statistics(self):
        """statistics provides drilling metrics."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        stats = data["statistics"]
        assert "operation_count" in stats
        assert "move_count" in stats
        assert "hole_count" in stats

    def test_response_has_metadata(self):
        """metadata provides generator provenance."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        meta = data["metadata"]
        assert meta["generator_id"] == "drilling_preview"
        assert meta["preview_only"] is True
        assert meta["machine_ready"] is False
        assert meta["operation_category"] == "drilling"
        assert "generated_at" in meta


class TestGateSemantics:
    """Verify gate evaluation logic."""

    def test_gate_green_for_valid_holes(self):
        """Valid, well-spaced holes return green gate."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert data["gate"] == "green"
        assert len(data["errors"]) == 0

    def test_gate_red_for_overlapping_holes(self):
        """Overlapping holes return red gate."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": OVERLAPPING_HOLES})
        data = resp.json()
        assert data["gate"] == "red"
        assert any("overlap" in e.lower() for e in data["errors"])

    def test_gate_yellow_for_near_touching_holes(self):
        """Near-touching holes return yellow gate."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": NEAR_TOUCHING_HOLES})
        data = resp.json()
        assert data["gate"] == "yellow"
        assert any("close" in w.lower() or "near" in w.lower() for w in data["warnings"])

    def test_gate_red_for_depth_exceeds_stock(self):
        """Depth exceeding stock thickness returns red gate."""
        holes = [{"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 30.0}]
        resp = client.post("/api/cam/drilling/preview", json={
            "holes": holes,
            "stock_thickness_mm": 25.0,
        })
        data = resp.json()
        assert data["gate"] == "red"
        assert any("depth" in e.lower() and "stock" in e.lower() for e in data["errors"])

    def test_gate_red_for_out_of_bounds(self):
        """Hole extending past stock edge returns red gate."""
        holes = [{"x_mm": 2.0, "y_mm": 10.0, "diameter_mm": 6.0, "depth_mm": 10.0}]  # radius=3, extends past x=0
        resp = client.post("/api/cam/drilling/preview", json={
            "holes": holes,
            "stock_width_mm": 50.0,
            "stock_height_mm": 50.0,
        })
        data = resp.json()
        assert data["gate"] == "red"
        assert any("out" in e.lower() or "edge" in e.lower() or "extends" in e.lower() for e in data["errors"])

    def test_gate_yellow_for_near_edge(self):
        """Hole near stock edge returns yellow gate."""
        holes = [{"x_mm": 4.0, "y_mm": 25.0, "diameter_mm": 3.0, "depth_mm": 8.0}]  # Edge at x=2.5, within min_edge_distance
        resp = client.post("/api/cam/drilling/preview", json={
            "holes": holes,
            "stock_width_mm": 50.0,
            "stock_height_mm": 50.0,
            "min_edge_distance_mm": 3.0,
        })
        data = resp.json()
        # Hole edge is at x=2.5mm, which is within min_edge_distance of 3.0mm from x=0
        assert data["gate"] == "yellow"
        assert any("edge" in w.lower() for w in data["warnings"])

    def test_gate_yellow_for_deep_hole(self):
        """Deep hole (depth > 3x diameter) returns yellow gate."""
        holes = [{"x_mm": 25.0, "y_mm": 25.0, "diameter_mm": 3.0, "depth_mm": 15.0}]  # ratio = 5
        resp = client.post("/api/cam/drilling/preview", json={
            "holes": holes,
            "stock_width_mm": 50.0,
            "stock_height_mm": 50.0,
            "stock_thickness_mm": 20.0,
        })
        data = resp.json()
        assert data["gate"] == "yellow"
        assert any("deep" in w.lower() or "ratio" in w.lower() for w in data["warnings"])

    def test_gate_yellow_for_small_diameter(self):
        """Small diameter (< 1mm) returns yellow gate."""
        holes = [{"x_mm": 25.0, "y_mm": 25.0, "diameter_mm": 0.5, "depth_mm": 1.0}]
        resp = client.post("/api/cam/drilling/preview", json={"holes": holes})
        data = resp.json()
        assert data["gate"] == "yellow"
        assert any("small" in w.lower() or "specialty" in w.lower() for w in data["warnings"])


class TestStatisticsNormalization:
    """Verify statistics include required core fields."""

    def test_statistics_has_operation_count(self):
        """operation_count equals hole count."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert data["statistics"]["operation_count"] == len(VALID_HOLES)

    def test_statistics_has_move_count(self):
        """move_count is present."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        assert "move_count" in data["statistics"]
        assert data["statistics"]["move_count"] > 0

    def test_statistics_has_warning_count(self):
        """warning_count matches warnings list."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": NEAR_TOUCHING_HOLES})
        data = resp.json()
        assert data["statistics"]["warning_count"] == len(data["warnings"])

    def test_statistics_has_error_count(self):
        """error_count matches errors list."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": OVERLAPPING_HOLES})
        data = resp.json()
        assert data["statistics"]["error_count"] == len(data["errors"])

    def test_statistics_has_drilling_specific_fields(self):
        """Drilling-specific statistics are present."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        stats = data["statistics"]
        assert "hole_count" in stats
        assert "min_diameter_mm" in stats
        assert "max_diameter_mm" in stats
        assert "min_depth_mm" in stats
        assert "max_depth_mm" in stats
        assert "total_depth_mm" in stats

    def test_statistics_has_spacing(self):
        """Hole spacing statistics are present."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        stats = data["statistics"]
        assert "min_hole_spacing_mm" in stats
        assert "max_hole_spacing_mm" in stats

    def test_statistics_has_bounds(self):
        """Bounding box is present."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        bounds = data["statistics"]["bounds"]
        assert "x_min" in bounds
        assert "x_max" in bounds
        assert "y_min" in bounds
        assert "y_max" in bounds


class TestIssuesStructure:
    """Verify issues array has correct structure."""

    def test_issues_have_code_field(self):
        """Each issue has a code field."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": OVERLAPPING_HOLES})
        data = resp.json()
        for issue in data["issues"]:
            assert "code" in issue

    def test_issues_have_severity_field(self):
        """Each issue has severity in green/yellow/red."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": OVERLAPPING_HOLES})
        data = resp.json()
        for issue in data["issues"]:
            assert "severity" in issue
            assert issue["severity"] in ["green", "yellow", "red"]

    def test_issues_have_message_field(self):
        """Each issue has a message field."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": OVERLAPPING_HOLES})
        data = resp.json()
        for issue in data["issues"]:
            assert "message" in issue


class TestPreviewGeometry:
    """Verify preview geometry format."""

    def test_preview_geometry_holes_format(self):
        """Holes in preview_geometry have frontend-friendly format."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        data = resp.json()
        holes = data["preview_geometry"]["holes"]
        assert len(holes) == len(VALID_HOLES)
        for hole in holes:
            assert "x" in hole
            assert "y" in hole
            assert "diameter_mm" in hole
            assert "radius_mm" in hole

    def test_preview_geometry_includes_stock_bounds(self):
        """Stock bounds included when provided."""
        resp = client.post("/api/cam/drilling/preview", json={
            "holes": VALID_HOLES,
            "stock_width_mm": 100.0,
            "stock_height_mm": 50.0,
            "stock_thickness_mm": 20.0,
        })
        data = resp.json()
        bounds = data["preview_geometry"]["stock_bounds"]
        assert bounds["width_mm"] == 100.0
        assert bounds["height_mm"] == 50.0
        assert bounds["thickness_mm"] == 20.0


class TestInputValidation:
    """Verify input validation."""

    def test_requires_at_least_one_hole(self):
        """Request with empty holes array is rejected."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": []})
        assert resp.status_code == 422  # Validation error

    def test_requires_positive_diameter(self):
        """Hole with zero or negative diameter is rejected."""
        resp = client.post("/api/cam/drilling/preview", json={
            "holes": [{"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 0, "depth_mm": 10.0}]
        })
        assert resp.status_code == 422

    def test_requires_positive_depth(self):
        """Hole with zero or negative depth is rejected."""
        resp = client.post("/api/cam/drilling/preview", json={
            "holes": [{"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 0}]
        })
        assert resp.status_code == 422


class TestNoRmosPersistence:
    """Verify no RMOS artifacts are created (preview only)."""

    def test_response_has_no_run_id(self):
        """Response does not include run_id header."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        assert "X-Run-ID" not in resp.headers

    def test_response_has_no_gcode_hash(self):
        """Response does not include G-code hash header."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        assert "X-GCode-SHA256" not in resp.headers

    def test_response_is_json_not_gcode(self):
        """Response is JSON, not G-code text."""
        resp = client.post("/api/cam/drilling/preview", json={"holes": VALID_HOLES})
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert "canonical_toolpath" not in str(data.get("canonical_toolpath", "")).lower() or "G81" not in str(data)


class TestHoleLabels:
    """Verify hole labels are preserved."""

    def test_labels_preserved_in_response(self):
        """Hole labels are included in response."""
        holes = [
            {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 15.0, "label": "string_1"},
            {"x_mm": 30.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 15.0, "label": "string_2"},
        ]
        resp = client.post("/api/cam/drilling/preview", json={"holes": holes})
        data = resp.json()
        ct_holes = data["canonical_toolpath"]["holes"]
        assert ct_holes[0]["label"] == "string_1"
        assert ct_holes[1]["label"] == "string_2"

    def test_labels_used_in_error_messages(self):
        """Hole labels appear in error messages."""
        holes = [
            {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 10.0, "depth_mm": 15.0, "label": "hole_A"},
            {"x_mm": 15.0, "y_mm": 10.0, "diameter_mm": 10.0, "depth_mm": 15.0, "label": "hole_B"},
        ]
        resp = client.post("/api/cam/drilling/preview", json={"holes": holes})
        data = resp.json()
        assert any("hole_A" in e and "hole_B" in e for e in data["errors"])
