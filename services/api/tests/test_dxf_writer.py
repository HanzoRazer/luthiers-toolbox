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
# test_extents_derived_from_geometry
# =============================================================================

def _header_extents(raw: bytes):
    doc = ezdxf.read(io.StringIO(raw.decode("utf-8")))
    return doc.header.get("$EXTMIN"), doc.header.get("$EXTMAX")


def test_extents_derived_from_geometry():
    """$EXTMIN/$EXTMAX must equal the real geometry bounds, not the sentinel.

    Replaces test_sentinel_extents_preserved (added 8f342189, 2026-04-01),
    which asserted the opposite on the unsourced premise that "Fusion 360
    chokes when EXTMIN/EXTMAX are set to non-sentinel values on AC1015".
    CLAUDE.md corrected that rule as a conflation in 49577046 (2026-06-09);
    the inverted sentinel is what breaks CAD viewer zoom-to-fit (blank canvas,
    2aaff13f). ezdxf never recomputes extents on its own - the layout attrs
    must be set, which is what _finalize_extents() does.
    """
    w = _make_writer_with_square()
    extmin, extmax = _header_extents(w.to_bytes())

    assert extmin is not None and extmax is not None
    assert abs(extmin[0]) < 1e19 and abs(extmax[0]) < 1e19, (
        "inverted 1e+20 sentinel written - breaks zoom-to-fit"
    )
    assert (round(extmin[0], 3), round(extmin[1], 3)) == (0.0, 0.0)
    assert (round(extmax[0], 3), round(extmax[1], 3)) == (100.0, 100.0)
    assert extmax[0] > extmin[0] and extmax[1] > extmin[1]


def test_extents_finalized_for_saveas(tmp_path):
    """saveas() must finalize extents too, not just to_bytes()."""
    w = _make_writer_with_square()
    out = tmp_path / "square.dxf"
    w.saveas(str(out))

    doc = ezdxf.readfile(str(out))
    extmin, extmax = doc.header.get("$EXTMIN"), doc.header.get("$EXTMAX")
    assert abs(extmax[0]) < 1e19
    assert (round(extmax[0], 3), round(extmax[1], 3)) == (100.0, 100.0)


def test_empty_document_serializes_without_error():
    """An empty modelspace must still serialize.

    Regression witness for #146 (reverted by #148): its _finalize_extents()
    raised TypeError on the CI ezdxf because bbox.extents() returns a
    different empty-sentinel across releases, and because it threw inside
    to_bytes() it broke DXF serialization repo-wide. requirements.txt pins
    only ezdxf>=1.1.0, so this must hold on any release.
    """
    w = DxfWriter(layers=[LayerDef("EMPTY", 7)])
    raw = w.to_bytes()  # must not raise
    assert b"SECTION" in raw

    extmin, extmax = _header_extents(raw)
    if extmin is not None:
        assert all(abs(v) != float("inf") for v in extmin[:2]), (
            "empty document must not write inf extents"
        )


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
