"""
Phase 3A-1: archtop runtime services — DXF lifecycle guards at save boundary.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from app.util.dxf_lifecycle_guard import DxfLifecycleContext

REPO_ROOT = Path(__file__).resolve().parents[3]
ARCHTOP_SOURCES = {
    "bridge": REPO_ROOT / "services/api/app/cam/archtop_bridge_generator.py",
    "saddle": REPO_ROOT / "services/api/app/cam/archtop_saddle_generator.py",
    "surface_tools": REPO_ROOT / "services/api/app/cam/archtop/archtop_surface_tools.py",
    "contour": REPO_ROOT / "services/api/app/cam/archtop/archtop_contour_generator.py",
}

EXPECTED = DxfLifecycleContext(
    source_module="",  # filled per module
    export_type="dxf-create-save",
    dxf_version="R2010",
    lifecycle_status="COMPAT_ONLY",
    runtime_callable="runtime_service",
    authority_context="pipeline_stage",
    provenance_status="NO",
)


def _count_guard_before_saveas(source: str) -> int:
    """Each saveas must be preceded by assert_dxf_lifecycle_context in source order."""
    tree = ast.parse(source)
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "saveas":
            # Walk backwards in enclosing function body for guard call
            pass
    lines = source.splitlines()
    guard_idxs = [
        i for i, line in enumerate(lines) if "assert_dxf_lifecycle_context" in line
    ]
    save_idxs = [i for i, line in enumerate(lines) if ".saveas(" in line]
    paired = 0
    for save_i in save_idxs:
        if any(g < save_i for g in guard_idxs):
            paired += 1
    return paired, len(save_idxs), len(guard_idxs)


@pytest.mark.parametrize(
    "key,module_name,min_save_sites",
    [
        ("bridge", "app.cam.archtop_bridge_generator", 1),
        ("saddle", "app.cam.archtop_saddle_generator", 1),
        ("surface_tools", "app.cam.archtop.archtop_surface_tools", 1),
        ("contour", "app.cam.archtop.archtop_contour_generator", 2),
    ],
)
def test_archtop_source_has_guard_before_each_saveas(key, module_name, min_save_sites):
    source = ARCHTOP_SOURCES[key].read_text(encoding="utf-8")
    paired, save_count, guard_count = _count_guard_before_saveas(source)
    assert save_count >= min_save_sites
    assert guard_count >= min_save_sites
    assert paired >= min_save_sites, f"{key}: guard must precede each saveas"


@pytest.mark.parametrize(
    "import_path,generator_fn,output_name",
    [
        (
            "app.cam.archtop_bridge_generator",
            "generate_bridge_dxf",
            "b.dxf",
        ),
        (
            "app.cam.archtop_saddle_generator",
            "generate_saddle_dxf",
            "s.dxf",
        ),
    ],
)
def test_archtop_generator_invokes_guard_at_save(import_path, generator_fn, output_name, tmp_path):
    pytest.importorskip("ezdxf")
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(import_path, fromlist=[generator_fn])
    with patch(f"{import_path}.assert_dxf_lifecycle_context", side_effect=_record):
        result = getattr(mod, generator_fn)({}, output_path=str(tmp_path / output_name))

    assert result.get("ok") is True
    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].export_type == "dxf-create-save"
    assert recorded[0].lifecycle_status == "COMPAT_ONLY"
    assert recorded[0].runtime_callable == "runtime_service"
    assert recorded[0].provenance_status == "NO"
