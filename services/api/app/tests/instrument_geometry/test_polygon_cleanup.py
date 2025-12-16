"""
Polygon cleanup utility tests.

Target: instrument_geometry/tests/test_polygon_cleanup.py
"""
from app.instrument_geometry.queries.polygon_cleanup import clean_ring


def test_cleanup_removes_closing_duplicate_and_consecutive_dups():
    pts = [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 0.0),  # dup
        (1.0, 1.0),
        (0.0, 1.0),
        (0.0, 0.0),  # closing dup
    ]
    out, meta = clean_ring(pts, tol_mm=1e-9)
    
    assert len(out) == 4
    assert meta["removed_duplicates"] >= 2


def test_cleanup_removes_collinear_point():
    pts = [
        (0.0, 0.0),
        (1.0, 0.0),
        (2.0, 0.0),  # collinear mid chain
        (2.0, 1.0),
        (0.0, 1.0),
    ]
    out, meta = clean_ring(pts, collinear_eps=1e-12)
    
    assert len(out) == 4
    assert meta["removed_collinear"] >= 1
