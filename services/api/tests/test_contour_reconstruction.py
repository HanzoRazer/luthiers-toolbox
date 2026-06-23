"""
Contour Reconstruction Pipeline Tests
======================================

Tests for VINE-09 resolution: reconstructing closed contours from LINE/ARC entities.
"""

import pytest
import tempfile
import os
import math
import ezdxf


@pytest.fixture
def line_square_dxf_bytes():
    """Create a DXF with 4 LINE entities forming a square (should become 1 closed contour)."""
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # Square from 4 LINE entities (clockwise)
    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((100, 0), (100, 100), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((100, 100), (0, 100), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((0, 100), (0, 0), dxfattribs={"layer": "CONTOUR"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def arc_circle_dxf_bytes():
    """Create a DXF with 4 ARC entities forming a circle (should become 1 closed contour)."""
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # Circle from 4 quarter-arc entities
    center = (50, 50)
    radius = 40
    msp.add_arc(center, radius, start_angle=0, end_angle=90, dxfattribs={"layer": "CONTOUR"})
    msp.add_arc(center, radius, start_angle=90, end_angle=180, dxfattribs={"layer": "CONTOUR"})
    msp.add_arc(center, radius, start_angle=180, end_angle=270, dxfattribs={"layer": "CONTOUR"})
    msp.add_arc(center, radius, start_angle=270, end_angle=360, dxfattribs={"layer": "CONTOUR"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def mixed_entities_dxf_bytes():
    """Create a DXF with mixed LINE/ARC entities forming a rounded rectangle."""
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # Rounded rectangle: 4 lines + 4 corner arcs
    # Bottom line
    msp.add_line((20, 0), (80, 0), dxfattribs={"layer": "CONTOUR"})
    # Bottom-right arc
    msp.add_arc((80, 20), 20, start_angle=270, end_angle=360, dxfattribs={"layer": "CONTOUR"})
    # Right line
    msp.add_line((100, 20), (100, 80), dxfattribs={"layer": "CONTOUR"})
    # Top-right arc
    msp.add_arc((80, 80), 20, start_angle=0, end_angle=90, dxfattribs={"layer": "CONTOUR"})
    # Top line
    msp.add_line((80, 100), (20, 100), dxfattribs={"layer": "CONTOUR"})
    # Top-left arc
    msp.add_arc((20, 80), 20, start_angle=90, end_angle=180, dxfattribs={"layer": "CONTOUR"})
    # Left line
    msp.add_line((0, 80), (0, 20), dxfattribs={"layer": "CONTOUR"})
    # Bottom-left arc
    msp.add_arc((20, 20), 20, start_angle=180, end_angle=270, dxfattribs={"layer": "CONTOUR"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def two_contours_dxf_bytes():
    """Create a DXF with two separate contours (squares at different positions)."""
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # First square at (0, 0)
    msp.add_line((0, 0), (50, 0), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((50, 0), (50, 50), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((50, 50), (0, 50), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((0, 50), (0, 0), dxfattribs={"layer": "CONTOUR"})

    # Second square at (100, 0) - separate from first
    msp.add_line((100, 0), (150, 0), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((150, 0), (150, 50), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((150, 50), (100, 50), dxfattribs={"layer": "CONTOUR"})
    msp.add_line((100, 50), (100, 0), dxfattribs={"layer": "CONTOUR"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def bracing_like_dxf_bytes():
    """Create a DXF mimicking bracing pattern with multiple contours on named layers."""
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # TOP_BRACING layer - X-brace pattern (2 contours)
    # First brace (narrow rectangle)
    msp.add_line((0, 0), (200, 0), dxfattribs={"layer": "TOP_BRACING"})
    msp.add_line((200, 0), (200, 10), dxfattribs={"layer": "TOP_BRACING"})
    msp.add_line((200, 10), (0, 10), dxfattribs={"layer": "TOP_BRACING"})
    msp.add_line((0, 10), (0, 0), dxfattribs={"layer": "TOP_BRACING"})

    # Second brace (perpendicular)
    msp.add_line((95, -100), (105, -100), dxfattribs={"layer": "TOP_BRACING"})
    msp.add_line((105, -100), (105, 100), dxfattribs={"layer": "TOP_BRACING"})
    msp.add_line((105, 100), (95, 100), dxfattribs={"layer": "TOP_BRACING"})
    msp.add_line((95, 100), (95, -100), dxfattribs={"layer": "TOP_BRACING"})

    # BACK_BRACING layer - single brace
    msp.add_line((0, 200), (150, 200), dxfattribs={"layer": "BACK_BRACING"})
    msp.add_line((150, 200), (150, 210), dxfattribs={"layer": "BACK_BRACING"})
    msp.add_line((150, 210), (0, 210), dxfattribs={"layer": "BACK_BRACING"})
    msp.add_line((0, 210), (0, 200), dxfattribs={"layer": "BACK_BRACING"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


# =============================================================================
# Basic Reconstruction Tests
# =============================================================================


def test_reconstruct_line_square(line_square_dxf_bytes):
    """4 LINE entities forming a square -> 1 closed contour."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    assert result.total_entities == 4
    assert result.entities_used == 4
    assert result.entities_orphaned == 0
    assert result.contours_found == 1
    assert result.closed_contours == 1
    assert result.open_chains == 0

    # The contour should have 4 points (square corners)
    assert len(result.contours) == 1
    assert result.contours[0].is_closed is True
    assert len(result.contours[0].points) == 4


def test_reconstruct_arc_circle(arc_circle_dxf_bytes):
    """4 ARC entities forming a circle -> 1 closed contour."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(arc_circle_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    assert result.total_entities == 4
    assert result.entities_used == 4
    assert result.closed_contours == 1

    # ARC segments are converted to polyline points
    assert len(result.contours) == 1
    assert result.contours[0].is_closed is True
    # Each arc becomes 17 points (16 segments + 1), minus duplicates at joins
    assert len(result.contours[0].points) > 4


def test_reconstruct_mixed_entities(mixed_entities_dxf_bytes):
    """Mixed LINE/ARC entities forming rounded rectangle -> 1 closed contour."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(mixed_entities_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    assert result.total_entities == 8  # 4 lines + 4 arcs
    assert result.entities_used == 8
    assert result.closed_contours == 1
    assert result.contours[0].is_closed is True


def test_reconstruct_two_separate_contours(two_contours_dxf_bytes):
    """Two separate squares -> 2 closed contours."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(two_contours_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    assert result.total_entities == 8  # 4 + 4 lines
    assert result.contours_found == 2
    assert result.closed_contours == 2
    assert all(c.is_closed for c in result.contours)


# =============================================================================
# Bracing-specific Tests
# =============================================================================


def test_reconstruct_bracing_dxf(bracing_like_dxf_bytes):
    """Bracing DXF with multiple layers -> contours per layer."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_bracing_dxf

    result = reconstruct_bracing_dxf(bracing_like_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    # 12 total entities (8 in TOP_BRACING + 4 in BACK_BRACING)
    assert result.total_entities == 12
    assert result.entities_used == 12
    # 3 contours total (2 in TOP_BRACING + 1 in BACK_BRACING)
    assert result.contours_found == 3
    assert result.closed_contours == 3


def test_reconstruct_single_layer(bracing_like_dxf_bytes):
    """Reconstruct only from a specific layer."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(
        bracing_like_dxf_bytes,
        layer_name="TOP_BRACING",
        tolerance_mm=0.5,
    )

    assert result.success is True
    assert result.total_entities == 8  # Only TOP_BRACING entities
    assert result.contours_found == 2
    assert result.closed_contours == 2


# =============================================================================
# Tolerance Tests
# =============================================================================


def test_tolerance_too_small_leaves_orphans():
    """Tiny tolerance leaves entities un-chained."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # Square with 1mm gaps (entities don't quite meet)
    msp.add_line((0, 0), (99, 0))
    msp.add_line((100, 0), (100, 100))  # 1mm gap
    msp.add_line((100, 100), (0, 100))
    msp.add_line((0, 100), (0, 0))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    # With 0.1mm tolerance, the 1mm gap won't be bridged
    result = reconstruct_contours(dxf_bytes, tolerance_mm=0.1)

    assert result.success is True
    assert result.closed_contours < 1  # Not fully closed
    assert "entities could not be chained" in str(result.warnings) or result.open_chains > 0


def test_tolerance_large_bridges_gaps():
    """Larger tolerance bridges small gaps."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    # Square with 1mm gaps
    msp.add_line((0, 0), (99, 0))
    msp.add_line((100, 0), (100, 100))  # 1mm gap
    msp.add_line((100, 100), (0, 100))
    msp.add_line((0, 100), (0, 0))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    # With 2mm tolerance, the 1mm gap is bridged
    result = reconstruct_contours(dxf_bytes, tolerance_mm=2.0)

    assert result.success is True
    # Should form a closed chain (even if not geometrically perfect)
    assert result.entities_used == 4


# =============================================================================
# Output Verification Tests
# =============================================================================


def _load_output(dxf_bytes):
    """Write output bytes to a temp file and return (doc, msp)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf", mode="wb") as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name
    try:
        doc = ezdxf.readfile(tmp_path)
        return doc, list(doc.modelspace())
    finally:
        os.unlink(tmp_path)


# -----------------------------------------------------------------------------
# DXF version-selection convergence (2026-06-22): default output must be
# R12-safe (AC1009, LINE chains, no LWPOLYLINE); R2000 (AC1015, LWPOLYLINE) is
# an explicit opt-in. Witness the byte/file structure directly, not rendering.
# -----------------------------------------------------------------------------


def test_default_output_is_r12_ac1009(line_square_dxf_bytes):
    """Default reconstruction output is R12 (AC1009) at the byte level."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    assert len(result.dxf_bytes) > 0
    # Byte-level witness: the header DXF version code is AC1009 (R12).
    assert b"AC1009" in result.dxf_bytes
    assert b"AC1015" not in result.dxf_bytes


def test_default_output_has_no_lwpolyline(line_square_dxf_bytes):
    """Default (R12) output must NOT emit LWPOLYLINE (R12 does not support it)."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)

    # Byte-level witness.
    assert b"LWPOLYLINE" not in result.dxf_bytes
    # Structural witness via ezdxf.
    _doc, entities = _load_output(result.dxf_bytes)
    assert not [e for e in entities if e.dxftype() == "LWPOLYLINE"]


def test_default_output_preserves_contour_as_closed_line_chain(line_square_dxf_bytes):
    """Default output represents the closed contour as a closed LINE chain.

    The deliberate R12-legal representation is LINE segments (the repo's
    R12 LINE-only convention via dxf_compat.add_polyline). A closed 4-side
    square -> 4 LINE entities whose chain returns to the start point.
    """
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)

    _doc, entities = _load_output(result.dxf_bytes)
    lines = [e for e in entities if e.dxftype() == "LINE"]
    # Closed 100x100 square reconstructed as 4 closing LINE segments.
    assert len(lines) == 4

    # Witness closure: the chain of endpoints returns to its origin.
    starts = [(round(e.dxf.start.x, 3), round(e.dxf.start.y, 3)) for e in lines]
    ends = [(round(e.dxf.end.x, 3), round(e.dxf.end.y, 3)) for e in lines]
    # Every start point is also an end point of some segment (a closed loop).
    assert set(starts) == set(ends)


def test_explicit_r2000_output_is_ac1015_with_lwpolyline(line_square_dxf_bytes):
    """Explicit R2000 opt-in emits AC1015 and may use LWPOLYLINE."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5, dxf_version="R2000")

    assert result.success is True
    assert b"AC1015" in result.dxf_bytes
    _doc, entities = _load_output(result.dxf_bytes)
    polylines = [e for e in entities if e.dxftype() == "LWPOLYLINE"]
    assert len(polylines) == 1
    assert polylines[0].closed is True


def test_arc_contour_default_r12_produces_closed_line_chain(arc_circle_dxf_bytes):
    """Arc-based contours (non-trivial geometry) produce closed LINE chains in R12.

    This tests the full pipeline: ARC discretization via _arc_to_points() -> point
    chain -> dxf_compat.add_polyline -> closed LINE segments. Ensures curved
    contours work correctly, not just 4-segment squares.
    """
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(arc_circle_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    # Byte-level witness: R12 (AC1009), no LWPOLYLINE.
    assert b"AC1009" in result.dxf_bytes
    assert b"LWPOLYLINE" not in result.dxf_bytes

    # Structural witness: closed LINE chain.
    _doc, entities = _load_output(result.dxf_bytes)
    lines = [e for e in entities if e.dxftype() == "LINE"]

    # Arc circle discretized: 4 arcs * 16 segments = 64 LINE segments (approx).
    # May vary slightly due to duplicate-point merging at arc joins.
    assert len(lines) >= 60  # Conservative lower bound

    # Witness closure: every start is some segment's end (closed loop).
    starts = {(round(e.dxf.start.x, 2), round(e.dxf.start.y, 2)) for e in lines}
    ends = {(round(e.dxf.end.x, 2), round(e.dxf.end.y, 2)) for e in lines}
    assert starts == ends


def test_bracing_default_output_is_r12_no_lwpolyline(bracing_like_dxf_bytes):
    """Bracing reconstruction is R12-safe by default, symmetric with contours."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_bracing_dxf

    result = reconstruct_bracing_dxf(bracing_like_dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    assert b"AC1009" in result.dxf_bytes
    assert b"AC1015" not in result.dxf_bytes
    assert b"LWPOLYLINE" not in result.dxf_bytes


def test_bracing_explicit_r2000_is_ac1015(bracing_like_dxf_bytes):
    """Bracing explicit R2000 opt-in emits AC1015."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_bracing_dxf

    result = reconstruct_bracing_dxf(bracing_like_dxf_bytes, tolerance_mm=0.5, dxf_version="R2000")

    assert result.success is True
    assert b"AC1015" in result.dxf_bytes


def test_output_layer_default_0_does_not_crash(line_square_dxf_bytes):
    """output_layer='0' (a default layer) must not crash with DXFTableEntryError.

    Defensive layer creation: skip add if layer already exists. Covers edge case
    where user passes a pre-existing layer name like '0' or 'Defpoints'.
    """
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    # Should not raise DXFTableEntryError: LAYER '0' already exists!
    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5, output_layer="0")

    assert result.success is True
    assert result.closed_contours == 1


def test_governed_saveas_records_actual_emitted_version(line_square_dxf_bytes):
    """governed_doc_saveas must receive the ACTUAL emitted version, not a stale
    hardcoded AC1015. Witnesses the lifecycle dxf_version for both defaults."""
    from unittest.mock import patch
    from app.routers.blueprint_cam import contour_reconstruction as mod

    LIFECYCLE = "app.util.blueprint_dxf_export_lifecycle.assert_dxf_lifecycle_context"

    recorded = []
    with patch(LIFECYCLE, side_effect=lambda ctx: recorded.append(ctx)):
        mod.reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)
        mod.reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5, dxf_version="R2000")

    assert [c.dxf_version for c in recorded] == ["AC1009", "AC1015"]


def test_output_preserves_geometry_bounds(line_square_dxf_bytes):
    """Output geometry bounds match input geometry bounds."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)

    # Original was 100x100 square at origin
    contour = result.contours[0]
    bounds = contour.bounds  # (min_x, min_y, max_x, max_y)

    assert bounds[0] == pytest.approx(0, abs=0.1)
    assert bounds[1] == pytest.approx(0, abs=0.1)
    assert bounds[2] == pytest.approx(100, abs=0.1)
    assert bounds[3] == pytest.approx(100, abs=0.1)


def test_perimeter_calculation(line_square_dxf_bytes):
    """Perimeter is calculated correctly."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    result = reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)

    # 100x100 square has perimeter of 400
    assert result.contours[0].perimeter_mm == pytest.approx(400, abs=1)


# =============================================================================
# Edge Cases
# =============================================================================


def test_empty_dxf():
    """Empty DXF returns success with no contours."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    doc = ezdxf.new("R2000")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    result = reconstruct_contours(dxf_bytes, tolerance_mm=0.5)

    assert result.success is True
    assert result.total_entities == 0
    assert result.contours_found == 0


def test_no_bracing_layers():
    """DXF without bracing layers returns success with warning."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_bracing_dxf

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 100), dxfattribs={"layer": "OTHER_LAYER"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    result = reconstruct_bracing_dxf(dxf_bytes)

    assert result.success is True
    assert "No bracing layers found" in str(result.warnings)


def test_single_line_entity():
    """Single LINE entity becomes an open chain."""
    from app.routers.blueprint_cam.contour_reconstruction import reconstruct_contours

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 100))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    result = reconstruct_contours(dxf_bytes, tolerance_mm=0.5, min_points=2)

    assert result.success is True
    assert result.total_entities == 1
    assert result.contours_found == 1
    assert result.open_chains == 1
    assert result.closed_contours == 0


# =============================================================================
# API Endpoint Tests
# =============================================================================


def test_contour_reconstruction_info_endpoint():
    """GET /cam/blueprint/contour-reconstruction/info returns module info."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/cam/blueprint/contour-reconstruction/info")

    assert response.status_code == 200
    data = response.json()
    assert "VINE-09" in data["resolves"]
    assert "LINE" in data["supported_entity_types"]
    assert "ARC" in data["supported_entity_types"]


def test_reconstruct_endpoint(line_square_dxf_bytes):
    """POST /cam/blueprint/contour-reconstruction/reconstruct processes DXF."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(line_square_dxf_bytes), "application/dxf")}
    data = {"tolerance_mm": "0.5", "min_points": "3"}

    response = client.post(
        "/api/cam/blueprint/contour-reconstruction/reconstruct",
        files=files,
        data=data,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["total_entities"] == 4
    assert result["closed_contours"] == 1


def test_reconstruct_bracing_endpoint(bracing_like_dxf_bytes):
    """POST /cam/blueprint/contour-reconstruction/reconstruct-bracing processes bracing DXF."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("bracing.dxf", io.BytesIO(bracing_like_dxf_bytes), "application/dxf")}
    data = {"tolerance_mm": "0.5"}

    response = client.post(
        "/api/cam/blueprint/contour-reconstruction/reconstruct-bracing",
        files=files,
        data=data,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["contours_found"] == 3  # 2 TOP_BRACING + 1 BACK_BRACING


# =============================================================================
# Router path: same version behavior as the library function
# =============================================================================


def test_reconstruct_download_default_is_r12(line_square_dxf_bytes):
    """Router download path defaults to R12 (AC1009, no LWPOLYLINE) — same as lib."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(line_square_dxf_bytes), "application/dxf")}
    response = client.post(
        "/api/cam/blueprint/contour-reconstruction/reconstruct-download",
        files=files,
        data={"tolerance_mm": "0.5"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/dxf"
    assert b"AC1009" in response.content
    assert b"AC1015" not in response.content
    assert b"LWPOLYLINE" not in response.content


def test_reconstruct_download_explicit_r2000(line_square_dxf_bytes):
    """Router download path honors explicit R2000 opt-in (AC1015) — same as lib."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(line_square_dxf_bytes), "application/dxf")}
    response = client.post(
        "/api/cam/blueprint/contour-reconstruction/reconstruct-download",
        files=files,
        data={"tolerance_mm": "0.5", "dxf_version": "R2000"},
    )

    assert response.status_code == 200
    assert b"AC1015" in response.content


def test_reconstruct_return_dxf_default_is_r12(line_square_dxf_bytes):
    """return_dxf=True on /reconstruct defaults to R12 bytes."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(line_square_dxf_bytes), "application/dxf")}
    response = client.post(
        "/api/cam/blueprint/contour-reconstruction/reconstruct",
        files=files,
        data={"tolerance_mm": "0.5", "return_dxf": "true"},
    )

    assert response.status_code == 200
    assert b"AC1009" in response.content
    assert b"LWPOLYLINE" not in response.content


def test_reconstruct_rejects_invalid_dxf_version(line_square_dxf_bytes):
    """Unsupported dxf_version is rejected with 400 (not silently coerced)."""
    from fastapi.testclient import TestClient
    from app.main import app
    import io

    client = TestClient(app)
    files = {"file": ("test.dxf", io.BytesIO(line_square_dxf_bytes), "application/dxf")}
    response = client.post(
        "/api/cam/blueprint/contour-reconstruction/reconstruct-download",
        files=files,
        data={"tolerance_mm": "0.5", "dxf_version": "R2010"},
    )

    assert response.status_code == 400
