"""
Phase 3B: blueprint_cam routers — governed DXF export lifecycle orchestration.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.util.dxf_lifecycle_guard import DxfLifecycleContext

REPO_ROOT = Path(__file__).resolve().parents[3]
BLUEPRINT_CAM_SOURCES = {
    "dxf_preprocessor": REPO_ROOT
    / "services/api/app/routers/blueprint_cam/dxf_preprocessor.py",
    "contour_reconstruction": REPO_ROOT
    / "services/api/app/routers/blueprint_cam/contour_reconstruction.py",
    "dxf_geometry_correction": REPO_ROOT
    / "services/api/app/routers/blueprint_cam/dxf_geometry_correction.py",
}
LIFECYCLE_MODULE = "app.util.blueprint_dxf_export_lifecycle"


def _count_governed_save_sites(source: str) -> tuple[int, int]:
    governed = source.count("governed_doc_saveas(")
    bare_saveas = sum(
        1
        for line in source.splitlines()
        if ".saveas(" in line and "governed_doc_saveas" not in line
    )
    return governed, bare_saveas


@pytest.mark.parametrize(
    "key,min_governed_sites",
    [
        ("dxf_preprocessor", 2),
        ("contour_reconstruction", 2),
        ("dxf_geometry_correction", 1),
    ],
)
def test_blueprint_cam_source_uses_governed_save_only(key, min_governed_sites):
    source = BLUEPRINT_CAM_SOURCES[key].read_text(encoding="utf-8")
    governed, bare = _count_governed_save_sites(source)
    assert governed >= min_governed_sites
    assert bare == 0, f"{key}: direct saveas must route through governed_doc_saveas"


def test_assert_governed_blueprint_dxf_export_context():
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(LIFECYCLE_MODULE, fromlist=["assert_governed_blueprint_dxf_export"])
    with patch(f"{LIFECYCLE_MODULE}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.assert_governed_blueprint_dxf_export(
            source_module="app.routers.blueprint_cam.dxf_preprocessor",
            export_type="dxf-create-save",
            dxf_version="AC1015",
        )

    assert len(recorded) == 1
    ctx = recorded[0]
    assert ctx.lifecycle_status == "LIFECYCLE_GOVERNED"
    assert ctx.runtime_callable == "router_endpoint"
    assert ctx.authority_context == "user_request"
    assert ctx.provenance_status == "NO"


def test_normalize_dxf_format_invokes_governed_lifecycle(ac1024_dxf_bytes):
    import_path = "app.routers.blueprint_cam.dxf_preprocessor"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(import_path, fromlist=["normalize_dxf_format"])
    with patch(f"{LIFECYCLE_MODULE}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.normalize_dxf_format(ac1024_dxf_bytes)

    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].export_type == "dxf-create-save"
    assert recorded[0].lifecycle_status == "LIFECYCLE_GOVERNED"


def test_densify_dxf_invokes_governed_lifecycle(coarse_dxf_bytes):
    import_path = "app.routers.blueprint_cam.dxf_preprocessor"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(import_path, fromlist=["densify_dxf"])
    with patch(f"{LIFECYCLE_MODULE}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.densify_dxf(coarse_dxf_bytes, min_points=200)

    assert len(recorded) == 1
    assert recorded[0].export_type == "dxf-read-modify-save"
    assert recorded[0].lifecycle_status == "LIFECYCLE_GOVERNED"


def test_reconstruct_contours_invokes_governed_lifecycle(line_square_dxf_bytes):
    import_path = "app.routers.blueprint_cam.contour_reconstruction"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(import_path, fromlist=["reconstruct_contours"])
    with patch(f"{LIFECYCLE_MODULE}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.reconstruct_contours(line_square_dxf_bytes, tolerance_mm=0.5)

    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].export_type == "dxf-create-save"
    assert recorded[0].lifecycle_status == "LIFECYCLE_GOVERNED"


def test_correct_dxf_geometry_invokes_governed_lifecycle(offset_dxf_bytes):
    import_path = "app.routers.blueprint_cam.dxf_geometry_correction"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(import_path, fromlist=["correct_dxf_geometry"])
    with patch(f"{LIFECYCLE_MODULE}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.correct_dxf_geometry(
            dxf_bytes=offset_dxf_bytes,
            center_on_x=True,
            center_on_y=False,
        )

    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].export_type == "dxf-read-modify-save"
    assert recorded[0].lifecycle_status == "LIFECYCLE_GOVERNED"


@pytest.fixture
def ac1024_dxf_bytes():
    pytest.importorskip("ezdxf")
    import ezdxf
    import os
    import tempfile

    doc = ezdxf.new("AC1024")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def coarse_dxf_bytes():
    pytest.importorskip("ezdxf")
    import ezdxf
    import math
    import os
    import tempfile

    doc = ezdxf.new("AC1024")
    msp = doc.modelspace()
    points = []
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        points.append((200 * math.cos(angle), 200 * math.sin(angle)))
    msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "BODY_OUTLINE"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def line_square_dxf_bytes():
    pytest.importorskip("ezdxf")
    import ezdxf
    import os
    import tempfile

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
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
def offset_dxf_bytes():
    pytest.importorskip("ezdxf")
    import ezdxf
    import os
    import tempfile

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
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
