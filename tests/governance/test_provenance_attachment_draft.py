"""
Test Provenance Attachment Draft — Constitutional Invariant Validation
=======================================================================

Cross-Repo Governance Normalization 1A (2026-05-24)

These tests validate that ProvenanceAttachmentDraft maintains
constitutional invariants:
    - export_authorized is ALWAYS False (structural field, not an export gate)
    - is_exportable() (status == RATIFIED) is the canonical export gate, and is
      intentionally decoupled from export_authorized — the two-notion contract
      documented on ProvenanceAttachmentDraft. A RATIFIED attachment therefore
      has is_exportable() True while export_authorized stays False.
    - IBG drafts default to BLOCKED status
    - Drafts cannot be ratified by this code path
    - Serialization round-trip works correctly
"""

import pytest
from datetime import datetime, timezone

from services.api.app.governance.provenance_attachment import (
    ProvenanceAttachmentDraft,
    ProvenanceAttachmentStatus,
    NON_EXPORTABLE_STATUSES,
    IBG_DEFAULT_STATUS,
    create_ibg_provenance_draft,
    ProvenanceRatificationNotAuthorizedError,
)


class TestProvenanceAttachmentInvariants:
    """Test constitutional invariants for provenance attachments."""

    def test_export_authorized_always_false(self):
        """Draft attachments cannot authorize export."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
        )
        assert draft.export_authorized is False

    def test_export_authorized_cannot_be_set_true(self):
        """Attempting to set export_authorized=True must raise error."""
        with pytest.raises(ValueError, match="cannot authorize export"):
            ProvenanceAttachmentDraft(
                attachment_id="test-001",
                source_artifact_id="/path/to/source.dxf",
                export_authorized=True,
            )

    def test_is_exportable_false_for_non_ratified_statuses(self):
        """Draft/pending/blocked attachments are not exportable."""
        for status in NON_EXPORTABLE_STATUSES:
            draft = ProvenanceAttachmentDraft(
                attachment_id=f"test-{status.value}",
                source_artifact_id="/path/to/source.dxf",
                status=status,
            )
            assert draft.is_exportable() is False

    def test_ratified_status_is_exportable_for_r2_wrapper(self):
        """R2 allows RATIFIED attachments while export_authorized remains False.

        Contract lock for the intentional two-notion divergence: is_exportable()
        gates on status, export_authorized is a separate always-False field. This
        fails loudly if a future refactor tries to "reconcile" them by making
        is_exportable() read export_authorized (would flip True->False) or by
        forcing is_exportable() back to always-False.
        """
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
            status=ProvenanceAttachmentStatus.RATIFIED,
        )
        assert draft.export_authorized is False
        assert draft.is_exportable() is True

    def test_draft_status_is_default(self):
        """Default status should be DRAFT."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
        )
        assert draft.status == ProvenanceAttachmentStatus.DRAFT

    def test_non_exportable_statuses(self):
        """Verify non-exportable status set."""
        expected = {
            ProvenanceAttachmentStatus.DRAFT,
            ProvenanceAttachmentStatus.PENDING_RATIFICATION,
            ProvenanceAttachmentStatus.BLOCKED,
        }
        assert NON_EXPORTABLE_STATUSES == expected


class TestIBGProvenanceDraft:
    """Test IBG-specific provenance draft behavior."""

    def test_ibg_default_status_is_blocked(self):
        """IBG drafts must default to BLOCKED status."""
        assert IBG_DEFAULT_STATUS == ProvenanceAttachmentStatus.BLOCKED

    def test_create_ibg_draft_is_blocked(self):
        """create_ibg_provenance_draft returns BLOCKED draft."""
        draft = create_ibg_provenance_draft(
            attachment_id="ibg-001",
            source_artifact_id="/path/to/blueprint.dxf",
        )
        assert draft.status == ProvenanceAttachmentStatus.BLOCKED
        assert draft.is_blocked() is True
        assert "R1 ratification" in draft.blocking_reason

    def test_ibg_draft_has_ratification_requirements(self):
        """IBG drafts must list ratification requirements."""
        draft = create_ibg_provenance_draft(
            attachment_id="ibg-001",
            source_artifact_id="/path/to/blueprint.dxf",
        )
        assert len(draft.ratification_requirements) > 0
        assert any("R1" in req for req in draft.ratification_requirements)

    def test_ibg_draft_authority_state(self):
        """IBG drafts should have advisory_candidate authority state."""
        draft = create_ibg_provenance_draft(
            attachment_id="ibg-001",
            source_artifact_id="/path/to/blueprint.dxf",
        )
        assert draft.authority_state == "advisory_candidate"

    def test_ibg_draft_epistemic_status(self):
        """IBG drafts should have predicted epistemic status."""
        draft = create_ibg_provenance_draft(
            attachment_id="ibg-001",
            source_artifact_id="/path/to/blueprint.dxf",
        )
        assert draft.epistemic_status == "predicted"

    def test_ibg_draft_cannot_be_submitted(self):
        """Blocked IBG drafts cannot be submitted for ratification."""
        draft = create_ibg_provenance_draft(
            attachment_id="ibg-001",
            source_artifact_id="/path/to/blueprint.dxf",
        )
        assert draft.can_submit_for_ratification() is False


class TestDraftSubmission:
    """Test draft submission for ratification."""

    def test_draft_can_be_submitted(self):
        """Regular drafts can be submitted for ratification."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
        )
        assert draft.can_submit_for_ratification() is True

    def test_submit_changes_status(self):
        """Submitting draft changes status to PENDING_RATIFICATION."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
        )
        draft.submit_for_ratification(requirements=["test requirement"])

        assert draft.status == ProvenanceAttachmentStatus.PENDING_RATIFICATION
        assert draft.is_pending_ratification() is True
        assert "test requirement" in draft.ratification_requirements

    def test_blocked_draft_cannot_be_submitted(self):
        """Blocked drafts cannot be submitted."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
        )
        draft.block("Blocked for testing")

        assert draft.can_submit_for_ratification() is False

        with pytest.raises(ValueError, match="Cannot submit draft"):
            draft.submit_for_ratification()

    def test_already_ratified_cannot_be_resubmitted(self):
        """Already ratified drafts cannot be resubmitted."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
            status=ProvenanceAttachmentStatus.RATIFIED,
        )
        assert draft.can_submit_for_ratification() is False

    def test_missing_source_cannot_be_submitted(self):
        """Drafts without source_artifact_id cannot be submitted."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="",  # Empty source
        )
        assert draft.can_submit_for_ratification() is False


class TestDraftBlocking:
    """Test draft blocking behavior."""

    def test_block_sets_status(self):
        """Blocking draft sets BLOCKED status."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
        )
        draft.block("Test blocking reason")

        assert draft.status == ProvenanceAttachmentStatus.BLOCKED
        assert draft.is_blocked() is True
        assert draft.blocking_reason == "Test blocking reason"

    def test_block_updates_timestamp(self):
        """Blocking draft updates timestamp."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
        )
        original_updated = draft.updated_at
        draft.block("Test blocking")

        assert draft.updated_at >= original_updated


class TestSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields."""
        draft = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
            derivation_chain=["parent-001", "grandparent-001"],
            transformation_stage="topology_reconstruction",
            transformation_method="reconstruct_contour",
            authority_state="advisory_candidate",
            epistemic_status="predicted",
        )

        data = draft.to_dict()

        assert data["attachment_id"] == "test-001"
        assert data["source_artifact_id"] == "/path/to/source.dxf"
        assert data["derivation_chain"] == ["parent-001", "grandparent-001"]
        assert data["transformation_stage"] == "topology_reconstruction"
        assert data["status"] == "draft"
        assert data["export_authorized"] is False

    def test_round_trip_serialization(self):
        """Draft should survive round-trip serialization."""
        original = ProvenanceAttachmentDraft(
            attachment_id="test-001",
            source_artifact_id="/path/to/source.dxf",
            derivation_chain=["parent-001"],
            transformation_stage="gap_closure",
            authority_state="semantic_interpretation",
            epistemic_status="estimated",
            status=ProvenanceAttachmentStatus.PENDING_RATIFICATION,
            ratification_requirements=["requirement 1", "requirement 2"],
            metadata={"test_key": "test_value"},
        )

        data = original.to_dict()
        restored = ProvenanceAttachmentDraft.from_dict(data)

        assert restored.attachment_id == original.attachment_id
        assert restored.source_artifact_id == original.source_artifact_id
        assert restored.derivation_chain == original.derivation_chain
        assert restored.transformation_stage == original.transformation_stage
        assert restored.authority_state == original.authority_state
        assert restored.epistemic_status == original.epistemic_status
        assert restored.status == original.status
        assert restored.ratification_requirements == original.ratification_requirements
        assert restored.export_authorized is False
