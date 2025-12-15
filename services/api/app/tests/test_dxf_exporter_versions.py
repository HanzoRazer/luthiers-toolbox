# services/api/app/tests/test_dxf_exporter_versions.py

"""
DXF version header tests (Wave 2).

Tests that:
- The header advertises the right DXF version
- ENTITIES are present
- The exporter runs without error for each version
"""

from __future__ import annotations

import io

import pytest

from app.toolpath import MLPath
from app.toolpath.dxf_exporter import (
    DXFExportOptions,
    DXFVersion,
    export_mlpaths_to_dxf,
)


def _sample_paths():
    """Create a sample triangle path."""
    return [
        MLPath(
            points=[
                (0.0, 0.0),
                (10.0, 0.0),
                (5.0, 5.0),
                (0.0, 0.0),
            ],
            is_closed=True,
        )
    ]


def test_dxf_exporter_r12_header():
    """Test R12 DXF header has correct version marker."""
    buf = io.StringIO()
    paths = _sample_paths()
    opts = DXFExportOptions(dxf_version=DXFVersion.R12)
    export_mlpaths_to_dxf(paths, buf, options=opts)
    txt = buf.getvalue()

    assert "$ACADVER" in txt
    assert "AC1009" in txt  # R12
    assert "SECTION" in txt
    assert "ENTITIES" in txt
    assert "EOF" in txt


def test_dxf_exporter_r14_header():
    """Test R14 DXF header has correct version marker."""
    buf = io.StringIO()
    paths = _sample_paths()
    opts = DXFExportOptions(dxf_version=DXFVersion.R14)
    export_mlpaths_to_dxf(paths, buf, options=opts)
    txt = buf.getvalue()

    assert "AC1014" in txt  # R14


def test_dxf_exporter_r18_header():
    """Test R18 DXF header has correct version marker."""
    buf = io.StringIO()
    paths = _sample_paths()
    opts = DXFExportOptions(dxf_version=DXFVersion.R18)
    export_mlpaths_to_dxf(paths, buf, options=opts)
    txt = buf.getvalue()

    assert "AC1018" in txt  # R18


def test_dxf_exporter_default_options():
    """Test exporter works with default options."""
    buf = io.StringIO()
    paths = _sample_paths()
    export_mlpaths_to_dxf(paths, buf)
    txt = buf.getvalue()

    # Should default to R12
    assert "AC1009" in txt
    assert "EOF" in txt
