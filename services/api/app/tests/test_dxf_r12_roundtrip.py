# services/api/app/tests/test_dxf_r12_roundtrip.py

"""
DXF R12 roundtrip tests (Wave 2).

Tests that:
- We can write a set of MLPaths to R12 DXF
- We can parse them back and still get roughly the same geometry
"""

from __future__ import annotations

import io

import pytest

from app.toolpath import MLPath
from app.toolpath.dxf_io_legacy import (
    read_dxf_to_mlpaths,
    write_mlpaths_to_dxf_r12,
)


def test_dxf_r12_roundtrip_closed_and_open():
    """Test roundtrip of closed rectangle and open line."""
    # Closed rectangle
    rect = MLPath(
        points=[
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 5.0),
            (0.0, 5.0),
            (0.0, 0.0),
        ],
        is_closed=True,
    )

    # Open path (simple line)
    line = MLPath(points=[(0.0, 0.0), (5.0, 5.0)], is_closed=False)

    mlpaths = [rect, line]

    # Write to DXF
    buf = io.StringIO()
    write_mlpaths_to_dxf_r12(mlpaths, buf)
    dxf_text = buf.getvalue()

    assert "POLYLINE" in dxf_text
    assert "VERTEX" in dxf_text
    assert "LINE" in dxf_text

    # Now parse back
    buf2 = io.StringIO(dxf_text)
    recovered = read_dxf_to_mlpaths(buf2)

    # We expect at least 2 paths (it's okay if the rectangle gets split)
    assert len(recovered) >= 2

    # Flatten out all points to check bounding box similarity
    all_pts_orig = [p for m in mlpaths for p in m.points]
    all_pts_rec = [p for m in recovered for p in m.points]

    assert all_pts_orig, "Original points should not be empty."
    assert all_pts_rec, "Recovered points should not be empty."

    min_x_orig = min(x for x, _ in all_pts_orig)
    max_x_orig = max(x for x, _ in all_pts_orig)
    min_y_orig = min(y for _, y in all_pts_orig)
    max_y_orig = max(y for _, y in all_pts_orig)

    min_x_rec = min(x for x, _ in all_pts_rec)
    max_x_rec = max(x for x, _ in all_pts_rec)
    min_y_rec = min(y for _, y in all_pts_rec)
    max_y_rec = max(y for _, y in all_pts_rec)

    # Very loose tolerance
    assert abs(min_x_orig - min_x_rec) < 1e-3
    assert abs(max_x_orig - max_x_rec) < 1e-3
    assert abs(min_y_orig - min_y_rec) < 1e-3
    assert abs(max_y_orig - max_y_rec) < 1e-3


def test_dxf_write_empty_path():
    """Test that empty paths are handled gracefully."""
    empty_path = MLPath(points=[], is_closed=False)
    buf = io.StringIO()
    write_mlpaths_to_dxf_r12([empty_path], buf)
    # Should not crash, output may be empty
    assert True
