"""
Phase 3A-3: layered_dxf_writer — DXF lifecycle guard at save boundary.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.services.layer_builder import ExportPreset, Layer, LayeredEntities, LayeredEntity
from app.util.dxf_lifecycle_guard import DxfLifecycleContext

REPO_ROOT = Path(__file__).resolve().parents[3]
LAYERED_WRITER_SOURCE = REPO_ROOT / "services/api/app/services/layered_dxf_writer.py"
IMPORT_PATH = "app.services.layered_dxf_writer"


def _count_guard_before_saveas(source: str) -> tuple[int, int, int]:
    lines = source.splitlines()
    guard_idxs = [
        i for i, line in enumerate(lines) if "assert_dxf_lifecycle_context" in line
    ]
    save_idxs = [i for i, line in enumerate(lines) if ".saveas(" in line]
    paired = sum(1 for save_i in save_idxs if any(g < save_i for g in guard_idxs))
    return paired, len(save_idxs), len(guard_idxs)


def test_layered_writer_source_has_guard_before_saveas():
    source = LAYERED_WRITER_SOURCE.read_text(encoding="utf-8")
    paired, save_count, guard_count = _count_guard_before_saveas(source)
    assert save_count >= 1
    assert guard_count >= 1
    assert paired >= 1, "guard must precede saveas"


def test_write_layered_dxf_invokes_guard_at_save(tmp_path):
    pytest.importorskip("ezdxf")
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    contour = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)
    entity = LayeredEntity(
        contour=contour,
        layer=Layer.BODY,
        bbox=(0, 0, 10, 10),
        area=100.0,
        is_closed=True,
    )
    entities = LayeredEntities(
        body=[entity],
        image_size=(100, 100),
        mm_per_px=1.0,
    )

    mod = __import__(IMPORT_PATH, fromlist=["write_layered_dxf"])
    out = tmp_path / "layered.dxf"
    with patch(f"{IMPORT_PATH}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.write_layered_dxf(entities, str(out), preset=ExportPreset.GEOMETRY_ONLY)

    assert out.exists()
    assert len(recorded) == 1
    assert recorded[0].source_module == IMPORT_PATH
    assert recorded[0].export_type == "dxf-create-save"
    assert recorded[0].dxf_version == "R12"
    assert recorded[0].lifecycle_status == "COMPAT_ONLY"
    assert recorded[0].runtime_callable == "runtime_service"
    assert recorded[0].provenance_status == "NO"
