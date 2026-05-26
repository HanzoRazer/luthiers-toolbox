"""
DO 79 / R2: IBG DXF export — provenance-aware save boundary tests.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.governance.provenance_attachment import (
    ProvenanceAttachmentStatus,
    create_ibg_provenance_draft,
)
from app.util.dxf_lifecycle_guard import DxfLifecycleContext
from app.util.ibg_dxf_export_lifecycle import (
    IbgDxfExportBlockedError,
    assert_ibg_dxf_export_allowed,
    governed_ibg_writer_saveas,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
IBG_SOURCES = {
    "body_contour_solver": REPO_ROOT
    / "services/api/app/instrument_geometry/body/ibg/body_contour_solver.py",
    "arc_reconstructor": REPO_ROOT
    / "services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py",
}


def _ratified_attachment():
    draft = create_ibg_provenance_draft(
        attachment_id="test-ratified-1",
        source_artifact_id="test-artifact.dxf",
        transformation_method="outline_to_dxf",
    )
    draft.status = ProvenanceAttachmentStatus.RATIFIED
    return draft


def _count_governed_ibg_save_sites(source: str) -> tuple[int, int]:
    governed = source.count("governed_ibg_writer_saveas(")
    bare = sum(
        1
        for line in source.splitlines()
        if "writer.saveas(" in line and "governed_ibg_writer_saveas" not in line
    )
    return governed, bare


@pytest.mark.parametrize(
    "key,min_governed",
    [
        ("body_contour_solver", 2),
        ("arc_reconstructor", 3),
    ],
)
def test_ibg_source_uses_governed_save_only(key, min_governed):
    source = IBG_SOURCES[key].read_text(encoding="utf-8")
    governed, bare = _count_governed_ibg_save_sites(source)
    assert governed >= min_governed
    assert bare == 0, f"{key}: bare writer.saveas must use governed_ibg_writer_saveas"


def test_blocked_draft_rejects_export():
    draft = create_ibg_provenance_draft(
        attachment_id="blocked-1",
        source_artifact_id="in.dxf",
        transformation_method="chains_to_dxf",
    )
    with pytest.raises(IbgDxfExportBlockedError):
        assert_ibg_dxf_export_allowed(draft, source_module="test.module")


def test_missing_attachment_rejects_export():
    with pytest.raises(IbgDxfExportBlockedError):
        assert_ibg_dxf_export_allowed(None, source_module="test.module")


def test_ratified_attachment_builds_compat_context():
    ctx = assert_ibg_dxf_export_allowed(
        _ratified_attachment(),
        source_module="app.instrument_geometry.body.ibg.body_contour_solver",
    )
    assert ctx.lifecycle_status == "COMPAT_ONLY"
    assert ctx.provenance_status == "YES"
    assert ctx.export_type == "dxf-create-save"


def test_governed_save_invokes_guard_for_ratified_attachment(tmp_path):
    recorded: list[DxfLifecycleContext] = []

    def _record(ctx: DxfLifecycleContext) -> None:
        recorded.append(ctx)

    writer = MagicMock()
    out = tmp_path / "out.dxf"

    with patch(
        "app.util.ibg_dxf_export_lifecycle.assert_dxf_lifecycle_context",
        side_effect=_record,
    ):
        governed_ibg_writer_saveas(
            writer,
            str(out),
            attachment=_ratified_attachment(),
            source_module="app.instrument_geometry.body.ibg.body_contour_solver",
        )

    writer.saveas.assert_called_once_with(str(out))
    assert len(recorded) == 1
    assert recorded[0].lifecycle_status == "COMPAT_ONLY"
