"""Smoke tests for the central DXF writer (app.cam.dxf_writer).

Follows the pattern from test_dxf_export_smoke.py — lightweight checks
that the writer enforces Fusion 360 compatibility standards.
"""

import io

import pytest
import ezdxf

from app.cam.dxf_writer import DxfWriter, LayerDef


# =============================================================================
# Helpers
# =============================================================================

SQUARE = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]


def _make_writer_with_square(*, closed: bool = True) -> DxfWriter:
    """Return a DxfWriter with a single closed square on BODY_OUTLINE."""
    w = DxfWriter(layers=[LayerDef("BODY_OUTLINE", 7)])
    w.add_polyline("BODY_OUTLINE", SQUARE, closed=closed)
    return w


# =============================================================================
# test_extents_policy_uses_geometry_not_sentinels
# =============================================================================

def test_extents_policy_uses_geometry_not_sentinels():
    """DXF extents policy is geometry-driven, not sentinel-preserving.

    The canonical writer must not reintroduce the retired 1e+20/-1e+20
    sentinel headers that caused CAD viewer zoom-to-fit failures. The finite
    geometry itself is the positive witness for downstream extent calculation.
    """
    w = _make_writer_with_square()
    raw = w.to_bytes().decode("utf-8")

    assert "1e+20" not in raw
    assert "-1e+20" not in raw
    assert "1E+20" not in raw
    assert "-1E+20" not in raw

    doc = ezdxf.read(io.StringIO(raw))
    points = []
    for entity in doc.modelspace():
        if entity.dxftype() == "LINE":
            points.append((
                round(entity.dxf.start[0], 3),
                round(entity.dxf.start[1], 3),
            ))
            points.append((
                round(entity.dxf.end[0], 3),
                round(entity.dxf.end[1], 3),
            ))

    assert points
    assert min(x for x, _ in points) == 0.0
    assert min(y for _, y in points) == 0.0
    assert max(x for x, _ in points) == 100.0
    assert max(y for _, y in points) == 100.0


# =============================================================================
# test_coordinate_precision_3dp
# =============================================================================

def test_coordinate_precision_3dp():
    """All coordinates must be rounded to 3 decimal places."""
    w = DxfWriter(layers=[LayerDef("TEST", 1)])
    # Feed coords with excessive precision - need 2+ points for a LINE
    w.add_polyline("TEST", [(1.23456789, 2.98765432), (10.0, 10.0)])

    raw = w.to_bytes().decode("utf-8")
    # The raw values should NOT appear (proves rounding happened)
    assert "1.23456789" not in raw
    assert "2.98765432" not in raw

    # Verify via entity inspection (more reliable than text search)
    doc = ezdxf.read(io.StringIO(raw))
    lines = [e for e in doc.modelspace() if e.dxftype() == "LINE"]
    assert len(lines) >= 1
    # First LINE start should be rounded to 3dp
    start = lines[0].dxf.start
    assert start[0] == round(1.23456789, 3)  # 1.235
    assert start[1] == round(2.98765432, 3)  # 2.988


# =============================================================================
# test_body_outline_closed
# =============================================================================

def test_body_outline_closed():
    """A closed shape must form a closed loop when reloaded.

    R12 uses LINE entities (not POLYLINE), so we verify closure by
    checking that the last LINE endpoint connects to the first LINE start.
    """
    w = _make_writer_with_square(closed=True)
    raw = w.to_bytes()

    doc = ezdxf.read(io.StringIO(raw.decode("utf-8")))
    msp = doc.modelspace()

    lines = [e for e in msp if e.dxftype() == "LINE"]
    # 4-point closed square = 4 LINE segments (including closing segment)
    assert len(lines) == 4

    # Verify geometric closure: collect all endpoints
    starts = [(round(e.dxf.start[0], 3), round(e.dxf.start[1], 3)) for e in lines]
    ends = [(round(e.dxf.end[0], 3), round(e.dxf.end[1], 3)) for e in lines]
    # Each start should match some end (closed chain)
    for s in starts:
        assert s in ends, f"Start point {s} has no matching end — not closed"


# =============================================================================
# test_named_layers_only
# =============================================================================

def test_named_layers_only():
    """Geometry must never be placed on layer 0."""
    # Attempting to create geometry on layer 0 must raise
    with pytest.raises(ValueError, match="layer 0"):
        DxfWriter(layers=[LayerDef("0", 7)])

    # Attempting to add geometry to an unregistered layer must raise
    w = DxfWriter(layers=[LayerDef("VALID", 1)])
    with pytest.raises(ValueError, match="not registered"):
        w.add_polyline("NONEXISTENT", [(0, 0), (1, 1)])


# =============================================================================
# test_save_and_reload
# =============================================================================

def test_save_and_reload(tmp_path):
    """Round-trip: save to disk, reload, verify version and units."""
    w = _make_writer_with_square()
    out = tmp_path / "test_output.dxf"
    w.saveas(str(out))

    doc = ezdxf.readfile(str(out))

    # AC1009 format (R12 default for maximum CAM compatibility)
    assert doc.dxfversion == "AC1009"

    # Units - R12 may not support these headers, check gracefully
    insunits = doc.header.get("$INSUNITS", None)
    measurement = doc.header.get("$MEASUREMENT", None)
    if insunits is not None:
        assert insunits == 4  # mm
    if measurement is not None:
        assert measurement == 1  # metric

    # Layer exists
    layer_names = [ly.dxf.name for ly in doc.layers if ly.dxf.name != "0"]
    assert "BODY_OUTLINE" in layer_names

    # Geometry present
    entities = list(doc.modelspace())
    assert len(entities) > 0
