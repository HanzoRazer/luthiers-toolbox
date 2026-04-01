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
    w.add_polyline2d("BODY_OUTLINE", SQUARE, closed=closed)
    return w


# =============================================================================
# test_sentinel_extents_preserved
# =============================================================================

def test_sentinel_extents_preserved():
    """EXTMIN/EXTMAX must remain at sentinel values — never recomputed.

    Fusion 360 chokes when EXTMIN/EXTMAX are set to non-sentinel values
    on AC1015 files.
    """
    w = _make_writer_with_square()
    doc = w.doc

    extmin = doc.header.get("$EXTMIN", None)
    extmax = doc.header.get("$EXTMAX", None)

    # ezdxf AC1015 default sentinel is (1e20, 1e20, 1e20) / (-1e20, …)
    # We just verify the writer hasn't overwritten them with real bounds.
    if extmin is not None:
        # Should NOT match actual geometry bounds (0, 0) — (100, 100)
        assert extmin[0] != 0.0 or extmin[1] != 0.0, (
            "EXTMIN was recomputed from geometry — must stay sentinel"
        )


# =============================================================================
# test_coordinate_precision_3dp
# =============================================================================

def test_coordinate_precision_3dp():
    """All coordinates must be rounded to 3 decimal places."""
    w = DxfWriter(layers=[LayerDef("TEST", 1)])
    # Feed coords with excessive precision
    w.add_polyline2d("TEST", [(1.23456789, 2.98765432)])

    raw = w.to_bytes().decode("utf-8")
    # The rounded values should appear; the raw values should not
    assert "1.235" in raw or "1.234" in raw  # rounded to 3dp
    assert "1.23456789" not in raw


# =============================================================================
# test_body_outline_closed
# =============================================================================

def test_body_outline_closed():
    """A closed polyline must form a closed loop when reloaded."""
    w = _make_writer_with_square(closed=True)
    raw = w.to_bytes()

    doc = ezdxf.read(io.StringIO(raw.decode("utf-8")))
    msp = doc.modelspace()

    polylines = [e for e in msp if e.dxftype() == "POLYLINE"]
    assert len(polylines) == 1
    assert polylines[0].is_closed is True


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
        w.add_polyline2d("NONEXISTENT", [(0, 0), (1, 1)])


# =============================================================================
# test_save_and_reload
# =============================================================================

def test_save_and_reload(tmp_path):
    """Round-trip: save to disk, reload, verify version and units."""
    w = _make_writer_with_square()
    out = tmp_path / "test_output.dxf"
    w.saveas(str(out))

    doc = ezdxf.readfile(str(out))

    # AC1015 format
    assert doc.dxfversion == "AC1015"

    # Units
    assert doc.header.get("$INSUNITS") == 4       # mm
    assert doc.header.get("$MEASUREMENT") == 1     # metric

    # Layer exists
    layer_names = [ly.dxf.name for ly in doc.layers if ly.dxf.name != "0"]
    assert "BODY_OUTLINE" in layer_names

    # Geometry present
    entities = list(doc.modelspace())
    assert len(entities) > 0
