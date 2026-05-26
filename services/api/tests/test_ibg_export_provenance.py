"""Tests for IBG export provenance bridge (DO 80 Phase D)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.governance import create_source_provenance
from app.governance.provenance_attachment import ProvenanceAttachmentStatus
from app.governance.ibg_export_provenance import attachment_from_body_evidence_candidate


def _candidate_stub():
    provenance = create_source_provenance(
        object_id="cand-1",
        object_type="BodyEvidenceCandidate",
        source_artifact="/uploads/test.dxf",
    )
    return SimpleNamespace(
        candidate_id="cand-1",
        provenance=provenance,
        confidence=SimpleNamespace(
            confidence_type=SimpleNamespace(value="predicted"),
        ),
        authority=SimpleNamespace(
            current_state=SimpleNamespace(value="sandbox_experimental"),
        ),
        metadata={},
    )


def test_attachment_from_candidate_uses_provenance_fields():
    draft = attachment_from_body_evidence_candidate(
        _candidate_stub(),
        export_intent="outline_to_dxf",
        ibg_run_id="run-abc",
    )
    assert draft.source_artifact_id == "/uploads/test.dxf"
    assert draft.status == ProvenanceAttachmentStatus.BLOCKED
    assert draft.is_exportable() is False
    assert draft.metadata["candidate_id"] == "cand-1"
    assert draft.metadata["ibg_run_id"] == "run-abc"


def test_governed_save_fail_closed_with_blocked_draft(tmp_path):
    from unittest.mock import MagicMock

    from app.governance.provenance_attachment import create_ibg_provenance_draft
    from app.util.ibg_dxf_export_lifecycle import (
        IbgDxfExportBlockedError,
        governed_ibg_writer_saveas,
    )

    draft = create_ibg_provenance_draft(
        attachment_id="t-1",
        source_artifact_id="in.dxf",
        transformation_method="outline_to_dxf",
    )
    writer = MagicMock()

    with pytest.raises(IbgDxfExportBlockedError):
        governed_ibg_writer_saveas(
            writer,
            str(tmp_path / "out.dxf"),
            attachment=draft,
            source_module="test.module",
        )
    writer.saveas.assert_not_called()
