"""
Phase 3A-2: instrument geometry runtime services — DXF lifecycle guards at save boundary.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.util.dxf_lifecycle_guard import DxfLifecycleContext

REPO_ROOT = Path(__file__).resolve().parents[3]
GEOMETRY_SOURCES = {
    "smart_guitar": REPO_ROOT
    / "services/api/app/instrument_geometry/body/smart_guitar_dxf.py",
    "spiral": REPO_ROOT
    / "services/api/app/instrument_geometry/soundhole/spiral_geometry.py",
    "bezier": REPO_ROOT / "services/api/app/generators/bezier_body.py",
}


def _count_guard_before_saveas(source: str) -> tuple[int, int, int]:
    lines = source.splitlines()
    guard_idxs = [
        i for i, line in enumerate(lines) if "assert_dxf_lifecycle_context" in line
    ]
    save_idxs = [i for i, line in enumerate(lines) if ".saveas(" in line]
    paired = sum(1 for save_i in save_idxs if any(g < save_i for g in guard_idxs))
    return paired, len(save_idxs), len(guard_idxs)


@pytest.mark.parametrize(
    "key,min_save_sites",
    [
        ("smart_guitar", 1),
        ("spiral", 1),
        ("bezier", 1),
    ],
)
def test_geometry_source_has_guard_before_each_saveas(key, min_save_sites):
    source = GEOMETRY_SOURCES[key].read_text(encoding="utf-8")
    paired, save_count, guard_count = _count_guard_before_saveas(source)
    assert save_count >= min_save_sites
    assert guard_count >= min_save_sites
    assert paired >= min_save_sites, f"{key}: guard must precede each saveas"


def test_smart_guitar_generator_invokes_guard_at_save(tmp_path):
    pytest.importorskip("ezdxf")
    import_path = "app.instrument_geometry.body.smart_guitar_dxf"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(import_path, fromlist=["generate_smart_guitar_dxf"])
    with patch(f"{import_path}.assert_dxf_lifecycle_context", side_effect=_record):
        out = mod.generate_smart_guitar_dxf(
            tmp_path / "smart_guitar.dxf",
            include_body_outline=False,
            include_voids=False,
            include_wiring_channels=False,
        )

    assert out.exists()
    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].export_type == "dxf-create-save"
    assert recorded[0].dxf_version == "R2010"
    assert recorded[0].lifecycle_status == "COMPAT_ONLY"
    assert recorded[0].runtime_callable == "runtime_service"
    assert recorded[0].provenance_status == "NO"


def test_spiral_generator_invokes_guard_at_save(tmp_path):
    import_path = "app.instrument_geometry.soundhole.spiral_geometry"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(
        import_path,
        fromlist=["generate_dxf", "default_carlos_jumbo_spec"],
    )
    with patch(f"{import_path}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.generate_dxf(mod.default_carlos_jumbo_spec(), str(tmp_path / "spiral.dxf"))

    assert (tmp_path / "spiral.dxf").exists()
    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].dxf_version == "R12"
    assert recorded[0].provenance_status == "NO"


def test_bezier_body_invokes_guard_at_save(tmp_path):
    import_path = "app.generators.bezier_body"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    mod = __import__(
        import_path,
        fromlist=["BezierBodyGenerator", "BezierBodyParams"],
    )
    generator = mod.BezierBodyGenerator(mod.BezierBodyParams.dreadnought())
    with patch(f"{import_path}.assert_dxf_lifecycle_context", side_effect=_record):
        out = generator.to_dxf(tmp_path / "body.dxf")

    assert out.exists()
    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].dxf_version == "R12"
    assert recorded[0].provenance_status == "NO"
