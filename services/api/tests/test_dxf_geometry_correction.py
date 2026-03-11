"""
DXF Geometry Correction Pipeline Tests
========================================

Tests for SG-GAP-01, SG-GAP-02 resolution.
"""

import pytest
import tempfile
import os
import ezdxf


@pytest.fixture
def offset_dxf_bytes():
    """Create a DXF that is off-center and wrong size."""
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # Rectangle at offset position (not centered on X=0)
    # Bounds: X: 100 to 200, Y: 50 to 150
    # Center: X=150, Y=100
    # Width: 100, Height: 100
    msp.add_lwpolyline(
        [(100, 50), (200, 50), (200, 150), (100, 150)],
        close=True,
        dxfattribs={"layer": "BODY"},
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def smart_guitar_like_dxf_bytes():
    """Create a DXF similar to Smart Guitar (wrong aspect ratio)."""
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # Similar to Smart Guitar issue: wide and short
    # Actual: 386.68 x 344.20
    # Spec: 368.3 x 444.5
    import math

    # Create a guitar-ish shape offset from center
    points = []
    for i in range(36):
        angle = i * (2 * math.pi / 36)
        x = 190 + 193 * math.cos(angle)  # Width ~386, center at X=190
        y = 172 + 172 * math.sin(angle)  # Height ~344
        points.append((x, y))

    msp.add_lwpolyline(points, close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


# =============================================================================
# Geometry Analysis Tests
# =============================================================================


def test_analyze_geometry_bounds(offset_dxf_bytes):
    """Analysis correctly measures bounds and center."""
    from app.routers.blueprint_cam.dxf_geometry_correction import analyze_dxf_geometry

    analysis = analyze_dxf_geometry(offset_dxf_bytes)

    assert analysis.actual_width_mm == pytest.approx(100, abs=0.1)
    assert analysis.actual_length_mm == pytest.approx(100, abs=0.1)
    assert analysis.geometric_center_x == pytest.approx(150, abs=0.1)
    assert analysis.geometric_center_y == pytest.approx(100, abs=0.1)
    assert analysis.centerline_offset_mm == pytest.approx(150, abs=0.1)


def test_analyze_geometry_entity_count(offset_dxf_bytes):
    """Analysis counts entities correctly."""
    from app.routers.blueprint_cam.dxf_geometry_correction import analyze_dxf_geometry

    analysis = analyze_dxf_geometry(offset_dxf_bytes)

    assert analysis.entity_count == 1
    assert analysis.total_points == 4


# =============================================================================
# Centerline Correction Tests
# =============================================================================


def test_center_on_x(offset_dxf_bytes):
    """Correction centers geometry on X=0."""
    from app.routers.blueprint_cam.dxf_geometry_correction import (
        correct_dxf_geometry,
        analyze_dxf_geometry,
    )

    result = correct_dxf_geometry(
        dxf_bytes=offset_dxf_bytes,
        center_on_x=True,
        center_on_y=False,
    )

    assert result.success
    assert result.corrected_analysis.geometric_center_x == pytest.approx(0, abs=0.1)
    # Y should not change
    assert result.corrected_analysis.geometric_center_y == pytest.approx(100, abs=0.1)


def test_center_on_both_axes(offset_dxf_bytes):
    """Correction centers geometry on both axes."""
    from app.routers.blueprint_cam.dxf_geometry_correction import correct_dxf_geometry

    result = correct_dxf_geometry(
        dxf_bytes=offset_dxf_bytes,
        center_on_x=True,
        center_on_y=True,
    )

    assert result.success
    assert result.corrected_analysis.geometric_center_x == pytest.approx(0, abs=0.1)
    assert result.corrected_analysis.geometric_center_y == pytest.approx(0, abs=0.1)


# =============================================================================
# Dimension Scaling Tests
# =============================================================================


def test_scale_to_spec_uniform(offset_dxf_bytes):
    """Uniform scaling scales both axes equally."""
    from app.routers.blueprint_cam.dxf_geometry_correction import correct_dxf_geometry

    # Original is 100x100, scale to 200x200
    result = correct_dxf_geometry(
        dxf_bytes=offset_dxf_bytes,
        spec_width_mm=200,
        spec_length_mm=200,
        uniform_scale=True,
        tolerance_pct=1.0,
    )

    assert result.success
    assert result.scale_applied[0] == pytest.approx(2.0, abs=0.01)
    assert result.scale_applied[1] == pytest.approx(2.0, abs=0.01)
    assert result.corrected_analysis.actual_width_mm == pytest.approx(200, abs=1)
    assert result.corrected_analysis.actual_length_mm == pytest.approx(200, abs=1)


def test_scale_to_spec_non_uniform(offset_dxf_bytes):
    """Non-uniform scaling can match different dimensions."""
    from app.routers.blueprint_cam.dxf_geometry_correction import correct_dxf_geometry

    # Original is 100x100, scale to 200x300 (different aspect ratio)
    result = correct_dxf_geometry(
        dxf_bytes=offset_dxf_bytes,
        spec_width_mm=200,
        spec_length_mm=300,
        uniform_scale=False,
        tolerance_pct=1.0,
    )

    assert result.success
    assert result.scale_applied[0] == pytest.approx(2.0, abs=0.01)
    assert result.scale_applied[1] == pytest.approx(3.0, abs=0.01)
    assert result.corrected_analysis.actual_width_mm == pytest.approx(200, abs=1)
    assert result.corrected_analysis.actual_length_mm == pytest.approx(300, abs=1)


def test_skip_scaling_within_tolerance(offset_dxf_bytes):
    """Scaling skipped when deviation is within tolerance."""
    from app.routers.blueprint_cam.dxf_geometry_correction import correct_dxf_geometry

    # Original is 100x100, spec is 101x101 (1% deviation)
    result = correct_dxf_geometry(
        dxf_bytes=offset_dxf_bytes,
        spec_width_mm=101,
        spec_length_mm=101,
        tolerance_pct=5.0,  # 5% tolerance
    )

    assert result.success
    # Scale should be 1.0 (no scaling)
    assert result.scale_applied[0] == pytest.approx(1.0, abs=0.01)
    assert result.scale_applied[1] == pytest.approx(1.0, abs=0.01)


# =============================================================================
# Smart Guitar-like Tests (SG-GAP-01, SG-GAP-02)
# =============================================================================


def test_smart_guitar_dimension_correction(smart_guitar_like_dxf_bytes):
    """Smart Guitar-like DXF can be corrected to spec dimensions."""
    from app.routers.blueprint_cam.dxf_geometry_correction import (
        correct_dxf_geometry,
        validate_correction,
    )

    # Smart Guitar spec dimensions
    SPEC_WIDTH = 368.3
    SPEC_LENGTH = 444.5

    result = correct_dxf_geometry(
        dxf_bytes=smart_guitar_like_dxf_bytes,
        spec_width_mm=SPEC_WIDTH,
        spec_length_mm=SPEC_LENGTH,
        center_on_x=True,
        uniform_scale=False,  # Allow different X/Y scales
    )

    assert result.success

    # Should match spec dimensions
    assert result.corrected_analysis.actual_width_mm == pytest.approx(SPEC_WIDTH, abs=1)
    assert result.corrected_analysis.actual_length_mm == pytest.approx(SPEC_LENGTH, abs=1)

    # Should be centered on X=0
    assert result.corrected_analysis.centerline_offset_mm == pytest.approx(0, abs=0.5)

    # Should pass validation
    passed, issues = validate_correction(result)
    assert passed, f"Validation failed: {issues}"


def test_smart_guitar_centerline_correction(smart_guitar_like_dxf_bytes):
    """Smart Guitar-like DXF centerline is corrected to X=0."""
    from app.routers.blueprint_cam.dxf_geometry_correction import (
        analyze_dxf_geometry,
        correct_dxf_geometry,
    )

    # Verify original is offset
    original = analyze_dxf_geometry(smart_guitar_like_dxf_bytes)
    assert original.centerline_offset_mm > 100  # Significantly off-center

    # Correct
    result = correct_dxf_geometry(
        dxf_bytes=smart_guitar_like_dxf_bytes,
        center_on_x=True,
    )

    assert result.success
    assert result.corrected_analysis.centerline_offset_mm == pytest.approx(0, abs=0.5)


# =============================================================================
# Validation Tests
# =============================================================================


def test_validation_passes_within_tolerance(offset_dxf_bytes):
    """Validation passes when within tolerance."""
    from app.routers.blueprint_cam.dxf_geometry_correction import (
        correct_dxf_geometry,
        validate_correction,
    )

    result = correct_dxf_geometry(
        dxf_bytes=offset_dxf_bytes,
        spec_width_mm=100,
        spec_length_mm=100,
        center_on_x=True,
    )

    passed, issues = validate_correction(result, max_deviation_pct=1.0, max_centerline_offset_mm=0.5)
    assert passed
    assert len(issues) == 0


def test_validation_fails_outside_tolerance(offset_dxf_bytes):
    """Validation fails when outside tolerance."""
    from app.routers.blueprint_cam.dxf_geometry_correction import (
        correct_dxf_geometry,
        validate_correction,
    )

    # Scale to different size than spec
    result = correct_dxf_geometry(
        dxf_bytes=offset_dxf_bytes,
        spec_width_mm=200,  # But we're not actually scaling
        spec_length_mm=200,
        tolerance_pct=100.0,  # Very high tolerance so no scaling applied
    )

    # Now validate with tight tolerance
    passed, issues = validate_correction(result, max_deviation_pct=1.0)
    assert not passed
    assert len(issues) > 0


# =============================================================================
# API Endpoint Tests
# =============================================================================


def test_geometry_correction_info_endpoint():
    """GET /cam/blueprint/geometry-correction/info returns module info."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/cam/blueprint/geometry-correction/info")

    assert response.status_code == 200
    data = response.json()
    assert "SG-GAP-01" in data["resolves"]
    assert "SG-GAP-02" in data["resolves"]


def test_analyze_endpoint(offset_dxf_bytes):
    """POST /cam/blueprint/geometry-correction/analyze returns analysis."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(offset_dxf_bytes), "application/dxf")}
    data = {"spec_width_mm": "100", "spec_length_mm": "100"}

    response = client.post(
        "/api/cam/blueprint/geometry-correction/analyze",
        files=files,
        data=data,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["actual_width_mm"] == pytest.approx(100, abs=1)
    assert result["centerline_offset_mm"] == pytest.approx(150, abs=1)


def test_correct_endpoint(offset_dxf_bytes):
    """POST /cam/blueprint/geometry-correction/correct returns correction result."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(offset_dxf_bytes), "application/dxf")}
    data = {
        "spec_width_mm": "200",
        "spec_length_mm": "200",
        "center_on_x": "true",
        "uniform_scale": "true",
    }

    response = client.post(
        "/api/cam/blueprint/geometry-correction/correct",
        files=files,
        data=data,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["corrected_width_mm"] == pytest.approx(200, abs=1)
    assert result["corrected_centerline_offset_mm"] == pytest.approx(0, abs=1)
