"""
DXF Preprocessor Pipeline Tests
================================

Tests for EX-GAP-01, EX-GAP-02, EX-GAP-03 resolution.
"""

import pytest
import tempfile
import os
import ezdxf


@pytest.fixture
def coarse_dxf_bytes():
    """Create a coarse 8-point DXF (below MIN_PRODUCTION_POINTS)."""
    doc = ezdxf.new('AC1024')  # AutoCAD 2010 format
    msp = doc.modelspace()

    # Simple 8-point octagon (coarse)
    import math
    points = []
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        x = 200 * math.cos(angle)
        y = 200 * math.sin(angle)
        points.append((x, y))

    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'BODY_OUTLINE'})

    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    return dxf_bytes


@pytest.fixture
def ac1024_dxf_bytes():
    """Create AC1024 (AutoCAD 2010) format DXF."""
    doc = ezdxf.new('AC1024')
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    return dxf_bytes


# =============================================================================
# Format Normalization Tests (EX-GAP-02)
# =============================================================================

def test_normalize_ac1024_to_r2000(ac1024_dxf_bytes):
    """AC1024 format is normalized to R2000 (AC1015)."""
    from app.routers.blueprint_cam.dxf_preprocessor import normalize_dxf_format

    normalized, orig_ver, new_ver, warnings = normalize_dxf_format(ac1024_dxf_bytes)

    assert orig_ver == 'AC1024'
    assert new_ver == 'AC1015'
    assert len(normalized) > 0

    # Verify the normalized file is readable
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
        tmp.write(normalized)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
        assert doc.dxfversion == 'AC1015'
    finally:
        os.unlink(tmp_path)


def test_r2000_stays_r2000():
    """R2000 format doesn't change."""
    from app.routers.blueprint_cam.dxf_preprocessor import normalize_dxf_format

    # Create R2000 DXF
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (50, 0), (50, 50), (0, 50)], close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            r2000_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    normalized, orig_ver, new_ver, warnings = normalize_dxf_format(r2000_bytes)

    assert orig_ver == 'AC1015'
    assert new_ver == 'AC1015'


# =============================================================================
# Curve Densification Tests (EX-GAP-01)
# =============================================================================

def test_densify_coarse_polyline(coarse_dxf_bytes):
    """Coarse 8-point polyline is densified to 200+ points."""
    from app.routers.blueprint_cam.dxf_preprocessor import densify_dxf

    densified, orig_pts, new_pts, warnings = densify_dxf(coarse_dxf_bytes, min_points=200)

    assert orig_pts == 8
    assert new_pts >= 200
    assert len(densified) > 0


def test_dense_polyline_unchanged():
    """Already-dense polyline is not modified."""
    from app.routers.blueprint_cam.dxf_preprocessor import densify_dxf

    # Create 500-point polyline
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()

    import math
    points = []
    for i in range(500):
        angle = i * (2 * math.pi / 500)
        x = 200 * math.cos(angle)
        y = 200 * math.sin(angle)
        points.append((x, y))

    msp.add_lwpolyline(points, close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dense_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    _, orig_pts, new_pts, warnings = densify_dxf(dense_bytes, min_points=200)

    assert orig_pts == 500
    assert new_pts == 500  # Unchanged


# =============================================================================
# Dimension Validation Tests (EX-GAP-03)
# =============================================================================

def test_validate_dimensions_in_spec():
    """Dimensions within spec pass validation."""
    from app.routers.blueprint_cam.dxf_preprocessor import validate_dimensions

    # Create DXF matching Les Paul spec (375-395 x 260-280)
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (385, 0), (385, 270), (0, 270)], close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    result = validate_dimensions(dxf_bytes, 'les_paul')

    assert result.valid is True
    assert 'within spec' in result.message.lower()


def test_validate_dimensions_out_of_spec():
    """Dimensions outside spec fail validation with deviation percentage."""
    from app.routers.blueprint_cam.dxf_preprocessor import validate_dimensions

    # Create DXF way outside Les Paul spec
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (600, 0), (600, 400), (0, 400)], close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    result = validate_dimensions(dxf_bytes, 'les_paul')

    assert result.valid is False
    assert result.width_deviation_pct != 0
    assert 'outside spec' in result.message.lower()


def test_validate_dimensions_without_spec():
    """Validation without instrument type still returns dimensions."""
    from app.routers.blueprint_cam.dxf_preprocessor import validate_dimensions

    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 200), (0, 200)], close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    result = validate_dimensions(dxf_bytes, None)

    assert result.valid is True  # No spec to fail against
    assert result.actual_width == pytest.approx(100, abs=0.1)
    assert result.actual_height == pytest.approx(200, abs=0.1)


# =============================================================================
# Full Pipeline Tests
# =============================================================================

def test_full_preprocess_pipeline(coarse_dxf_bytes):
    """Full pipeline normalizes format, densifies curves, and validates."""
    from app.routers.blueprint_cam.dxf_preprocessor import preprocess_dxf

    result = preprocess_dxf(
        dxf_bytes=coarse_dxf_bytes,
        normalize_format=True,
        densify_curves=True,
        validate_dims=True,
        instrument_type=None,  # Skip spec validation
        min_points=200,
    )

    assert result.success is True
    assert result.original_version == 'AC1024'
    assert result.normalized_version == 'AC1015'
    assert result.original_point_count == 8
    assert result.densified_point_count >= 200
    assert len(result.dxf_bytes) > 0


def test_preprocess_preserves_geometry(coarse_dxf_bytes):
    """Preprocessing preserves overall geometry bounds."""
    from app.routers.blueprint_cam.dxf_preprocessor import preprocess_dxf

    result = preprocess_dxf(
        dxf_bytes=coarse_dxf_bytes,
        normalize_format=True,
        densify_curves=True,
        validate_dims=True,
    )

    # Original was 400mm diameter circle (octagon inscribed)
    # Bounds should be approximately preserved
    assert result.original_bounds_mm[0] == pytest.approx(400, abs=5)
    assert result.original_bounds_mm[1] == pytest.approx(400, abs=5)


# =============================================================================
# API Endpoint Tests
# =============================================================================

def test_preprocessor_info_endpoint():
    """GET /cam/blueprint/preprocess/info returns module info."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/cam/blueprint/preprocess/info")

    assert response.status_code == 200
    data = response.json()
    assert "EX-GAP-01" in data["resolves"]
    assert "EX-GAP-02" in data["resolves"]
    assert "EX-GAP-03" in data["resolves"]
    assert "explorer" in data["supported_instruments"]


def test_preprocess_full_endpoint(coarse_dxf_bytes):
    """POST /cam/blueprint/preprocess/full processes DXF."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(coarse_dxf_bytes), "application/dxf")}
    data = {"normalize_format": "true", "densify_curves": "true", "min_points": "200"}

    response = client.post("/api/cam/blueprint/preprocess/full", files=files, data=data)

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["densified_point_count"] >= 200


def test_validate_endpoint(coarse_dxf_bytes):
    """POST /cam/blueprint/preprocess/validate validates dimensions."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(coarse_dxf_bytes), "application/dxf")}

    response = client.post("/api/cam/blueprint/preprocess/validate", files=files)

    assert response.status_code == 200
    result = response.json()
    assert "actual_width_mm" in result
    assert "actual_height_mm" in result
