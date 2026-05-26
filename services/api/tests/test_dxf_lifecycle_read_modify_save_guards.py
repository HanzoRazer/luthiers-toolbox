"""
Phase 3A-4: read-modify-save services — DXF lifecycle guards at save boundary.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.util.dxf_lifecycle_guard import DxfLifecycleContext

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    "line_deduplicator": REPO_ROOT / "services/api/app/cam/line_deduplicator.py",
    "text_reinsertion": REPO_ROOT / "services/api/app/services/text_reinsertion.py",
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
        ("line_deduplicator", 1),
        ("text_reinsertion", 1),
    ],
)
def test_read_modify_save_source_has_guard_before_each_saveas(key, min_save_sites):
    source = SOURCES[key].read_text(encoding="utf-8")
    paired, save_count, guard_count = _count_guard_before_saveas(source)
    assert save_count >= min_save_sites
    assert guard_count >= min_save_sites
    assert paired >= min_save_sites, f"{key}: guard must precede each saveas"


def _write_minimal_r12_dxf(path: Path) -> None:
    pytest.importorskip("ezdxf")
    import ezdxf

    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "BODY_OUTLINE"})
    doc.saveas(path)


def test_line_deduplicator_invokes_guard_at_save(tmp_path):
    pytest.importorskip("ezdxf")
    import_path = "app.cam.line_deduplicator"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    inp = tmp_path / "in.dxf"
    out = tmp_path / "out.dxf"
    _write_minimal_r12_dxf(inp)

    mod = __import__(import_path, fromlist=["deduplicate_parallel_lines"])
    with patch(f"{import_path}.assert_dxf_lifecycle_context", side_effect=_record):
        mod.deduplicate_parallel_lines(str(inp), str(out))

    assert out.exists()
    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].export_type == "dxf-read-modify-save"
    assert recorded[0].lifecycle_status == "DIRECT_SAVE_GAP"
    assert recorded[0].runtime_callable == "runtime_service"
    assert recorded[0].provenance_status == "NO"


def test_text_reinsertion_invokes_guard_at_save(tmp_path):
    pytest.importorskip("ezdxf")
    import_path = "app.services.text_reinsertion"
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    dxf_path = tmp_path / "existing.dxf"
    _write_minimal_r12_dxf(dxf_path)

    from app.services.text_reinsertion import ExtractedText

    polygon = [(10.0, 10.0), (50.0, 10.0), (50.0, 20.0), (10.0, 20.0)]
    fake_texts = [
        ExtractedText(
            content="SCALE 1:1",
            confidence=0.95,
            insert_px=(10.0, 20.0),
            height_px=10.0,
            rotation_deg=0.0,
            bbox_polygon=polygon,
        )
    ]
    fake_image = object()

    mod = __import__(import_path, fromlist=["append_text_to_existing_dxf"])
    with patch(f"{import_path}.assert_dxf_lifecycle_context", side_effect=_record):
        with patch(
            f"{import_path}.extract_text_for_reinsertion",
            return_value=fake_texts,
        ):
            count = mod.append_text_to_existing_dxf(
                str(dxf_path),
                fake_image,
                image_height_px=100.0,
                mm_per_px=1.0,
            )

    assert count == 1
    assert len(recorded) == 1
    assert recorded[0].source_module == import_path
    assert recorded[0].export_type == "dxf-read-modify-save"
    assert recorded[0].lifecycle_status == "DIRECT_SAVE_GAP"
    assert recorded[0].provenance_status == "NO"
