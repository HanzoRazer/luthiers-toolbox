"""Closed-contour detection for the DXF asset gate.

R12 files from dxf_compat emit LINE chains, not LWPOLYLINE. The asset
validator must accept those loops or every R12 catalog DXF fails CI.
"""
from __future__ import annotations

import importlib.util
import io
import tempfile
from pathlib import Path

import ezdxf
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_asset_validator():
    import sys

    path = REPO_ROOT / "scripts" / "validate_dxf_assets.py"
    spec = importlib.util.spec_from_file_location("validate_dxf_assets", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator():
    return _load_asset_validator()


def _write_dxf(doc) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".dxf", delete=False)
    tmp.close()
    path = Path(tmp.name)
    doc.saveas(str(path))
    return path


def test_count_closed_line_loops_square(validator):
    segs = [
        ((0.0, 0.0), (10.0, 0.0)),
        ((10.0, 0.0), (10.0, 10.0)),
        ((10.0, 10.0), (0.0, 10.0)),
        ((0.0, 10.0), (0.0, 0.0)),
    ]
    assert validator.count_closed_line_loops(segs) == 1


def test_count_closed_line_loops_open_chain(validator):
    segs = [
        ((0.0, 0.0), (10.0, 0.0)),
        ((10.0, 0.0), (10.0, 10.0)),
        ((10.0, 10.0), (0.0, 10.0)),
    ]
    assert validator.count_closed_line_loops(segs) == 0


def test_r12_line_square_passes_asset_gate(validator):
    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0))
    msp.add_line((100, 0), (100, 60))
    msp.add_line((100, 60), (0, 60))
    msp.add_line((0, 60), (0, 0))
    path = _write_dxf(doc)
    try:
        result = validator.validate_dxf_file(path)
    finally:
        path.unlink(missing_ok=True)
    assert result.closed_polylines >= 1
    assert result.passed, [i.message for i in result.issues]


def test_open_lines_warn_but_pass_when_geometry_exists(validator):
    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0))
    msp.add_line((100, 0), (100, 60))
    path = _write_dxf(doc)
    try:
        result = validator.validate_dxf_file(path)
    finally:
        path.unlink(missing_ok=True)
    assert result.passed
    assert any(i.severity == "WARNING" for i in result.issues)


def test_empty_dxf_fails_asset_gate(validator):
    doc = ezdxf.new("R12")
    path = _write_dxf(doc)
    try:
        result = validator.validate_dxf_file(path)
    finally:
        path.unlink(missing_ok=True)
    assert not result.passed


def test_ac1024_closed_lwpolyline_is_allowed(validator):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 60), (0, 60)], close=True)
    path = _write_dxf(doc)
    try:
        result = validator.validate_dxf_file(path)
    finally:
        path.unlink(missing_ok=True)
    assert result.dxf_version == "AC1024"
    assert result.passed


def test_closed_lwpolyline_still_counts(validator):
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 60), (0, 60)], close=True)
    path = _write_dxf(doc)
    try:
        result = validator.validate_dxf_file(path)
    finally:
        path.unlink(missing_ok=True)
    assert result.passed
    assert result.closed_polylines >= 1


def test_dxf_advanced_validation_does_not_import_dxf_compat_at_module_level():
    """CI DXF gate installs ezdxf+shapely only. A module-level dxf_compat
    import pulls app.util.__init__ → fastapi and kills the job.
    """
    import ast

    src = (REPO_ROOT / "services" / "api" / "app" / "cam" / "dxf_advanced_validation.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("dxf_compat"):
            pytest.fail(
                "app.util.dxf_compat must not be imported at module level "
                "(fastapi is not installed in dxf_validation_gate.yml)"
            )


def test_check_dxf_files_accepts_r12_polyline(tmp_path):
    """Catalog gate must accept R12 POLYLINE bodies (not only LWPOLYLINE)."""
    from app.ci.check_dxf_files import validate_dxf_file

    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    # R12 POLYLINE via vertices
    msp.add_polyline2d([(0, 0), (100, 0), (100, 60), (0, 60)], close=True)
    path = tmp_path / "body.dxf"
    doc.saveas(str(path))
    result = validate_dxf_file(path)
    assert result["passed"], result["errors"]


def test_check_dxf_files_open_lwpolyline_is_advisory(tmp_path):
    from app.ci.check_dxf_files import validate_dxf_file

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 60)], close=False)
    path = tmp_path / "open.dxf"
    doc.saveas(str(path))
    result = validate_dxf_file(path)
    assert result["passed"], result["errors"]
    assert result["warnings"]
    """Importing TopologyValidator must not require fastapi."""
    from app.cam.dxf_advanced_validation import TopologyValidator

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)
    buf = io.StringIO()
    doc.write(buf)
    report = TopologyValidator(buf.getvalue().encode("utf-8"), "square.dxf").check_self_intersections()
    assert report.entities_checked >= 1
