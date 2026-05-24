"""
Test Authority Metadata — Constitutional Invariant Validation
==============================================================

Cross-Repo Governance Normalization 1A (2026-05-24)

These tests validate that AuthorityMetadata maintains compatibility
layer semantics:
    - Does not grant authority
    - All fields optional or default-safe
    - Serialization round-trip works
    - Factory functions produce correct metadata
"""

import pytest
from datetime import datetime, timezone

from services.api.app.governance.authority_metadata import (
    AuthorityMetadata,
    ReviewState,
    LifecycleState,
    SourceRepo,
    create_luthiers_authority_metadata,
    create_vectorizer_authority_metadata,
    create_ibg_authority_metadata,
)


class TestAuthorityMetadataDefaults:
    """Test default values and safe initialization."""

    def test_all_fields_have_safe_defaults(self):
        """All fields should have safe defaults."""
        metadata = AuthorityMetadata()

        assert metadata.authority_state is None
        assert metadata.epistemic_status is None
        assert metadata.review_state is None
        assert metadata.lifecycle_state is None
        assert metadata.source_repo == SourceRepo.UNKNOWN
        assert metadata.source_subsystem is None
        assert metadata.non_authoritative_reason is None

    def test_default_authority_exclusions(self):
        """Default exclusions should be populated."""
        metadata = AuthorityMetadata()

        required_exclusions = [
            "execution authorization",
            "production deployment",
            "governance bypass",
            "review bypass",
            "lifecycle promotion",
            "cross-repo authority propagation",
        ]

        for exclusion in required_exclusions:
            assert exclusion in metadata.authority_exclusions

    def test_timestamps_are_set(self):
        """Timestamps should be automatically set."""
        metadata = AuthorityMetadata()

        assert metadata.created_at is not None
        assert metadata.updated_at is not None
        assert isinstance(metadata.created_at, datetime)


class TestIsAuthoritative:
    """Test is_authoritative() method."""

    def test_non_authoritative_with_reason(self):
        """Metadata with non_authoritative_reason is not authoritative."""
        metadata = AuthorityMetadata(
            non_authoritative_reason="Test reason",
        )
        assert metadata.is_authoritative() is False

    def test_non_authoritative_sandbox_state(self):
        """Sandbox experimental state is not authoritative."""
        metadata = AuthorityMetadata(
            authority_state="sandbox_experimental",
        )
        assert metadata.is_authoritative() is False

    def test_non_authoritative_advisory_state(self):
        """Advisory candidate state is not authoritative."""
        metadata = AuthorityMetadata(
            authority_state="advisory_candidate",
        )
        assert metadata.is_authoritative() is False

    def test_non_authoritative_rejected_state(self):
        """Rejected state is not authoritative."""
        metadata = AuthorityMetadata(
            authority_state="rejected",
        )
        assert metadata.is_authoritative() is False

    def test_non_authoritative_rd_excluded(self):
        """R&D excluded lifecycle is not authoritative."""
        metadata = AuthorityMetadata(
            lifecycle_state=LifecycleState.R_AND_D_EXCLUDED,
        )
        assert metadata.is_authoritative() is False

    def test_non_authoritative_blocked_provenance(self):
        """Blocked provenance lifecycle is not authoritative."""
        metadata = AuthorityMetadata(
            lifecycle_state=LifecycleState.BLOCKED_PROVENANCE,
        )
        assert metadata.is_authoritative() is False

    def test_authoritative_when_clean(self):
        """Metadata without exclusion markers can be authoritative."""
        metadata = AuthorityMetadata(
            authority_state="approved_for_generation",
            lifecycle_state=LifecycleState.LIFECYCLE_GOVERNED,
        )
        assert metadata.is_authoritative() is True


class TestIsProductionReady:
    """Test is_production_ready() method."""

    def test_production_ready_requires_lifecycle_governed(self):
        """Production ready requires LIFECYCLE_GOVERNED."""
        metadata = AuthorityMetadata(
            authority_state="approved_for_generation",
            review_state=ReviewState.REVIEWED,
            lifecycle_state=LifecycleState.COMPAT_ONLY,  # Not governed
        )
        assert metadata.is_production_ready() is False

    def test_production_ready_requires_approved_authority(self):
        """Production ready requires approved authority state."""
        metadata = AuthorityMetadata(
            authority_state="advisory_candidate",  # Not approved
            review_state=ReviewState.REVIEWED,
            lifecycle_state=LifecycleState.LIFECYCLE_GOVERNED,
        )
        assert metadata.is_production_ready() is False

    def test_production_ready_requires_reviewed(self):
        """Production ready requires REVIEWED review state."""
        metadata = AuthorityMetadata(
            authority_state="approved_for_generation",
            review_state=ReviewState.PENDING_REVIEW,  # Not reviewed
            lifecycle_state=LifecycleState.LIFECYCLE_GOVERNED,
        )
        assert metadata.is_production_ready() is False

    def test_production_ready_when_all_criteria_met(self):
        """Production ready when all criteria are met."""
        metadata = AuthorityMetadata(
            authority_state="approved_for_generation",
            review_state=ReviewState.REVIEWED,
            lifecycle_state=LifecycleState.LIFECYCLE_GOVERNED,
        )
        assert metadata.is_production_ready() is True


class TestRequiresReview:
    """Test requires_review() method."""

    def test_requires_review_when_not_submitted(self):
        """NOT_SUBMITTED requires review."""
        metadata = AuthorityMetadata(
            review_state=ReviewState.NOT_SUBMITTED,
        )
        assert metadata.requires_review() is True

    def test_requires_review_when_pending(self):
        """PENDING_REVIEW requires review."""
        metadata = AuthorityMetadata(
            review_state=ReviewState.PENDING_REVIEW,
        )
        assert metadata.requires_review() is True

    def test_requires_review_when_in_review(self):
        """IN_REVIEW requires review."""
        metadata = AuthorityMetadata(
            review_state=ReviewState.IN_REVIEW,
        )
        assert metadata.requires_review() is True

    def test_requires_review_sandbox_state(self):
        """Sandbox state always requires review."""
        metadata = AuthorityMetadata(
            authority_state="sandbox_experimental",
            review_state=ReviewState.REVIEWED,  # Even if reviewed
        )
        assert metadata.requires_review() is True

    def test_requires_review_advisory_state(self):
        """Advisory state always requires review."""
        metadata = AuthorityMetadata(
            authority_state="advisory_candidate",
            review_state=ReviewState.REVIEWED,
        )
        assert metadata.requires_review() is True

    def test_no_review_needed_when_reviewed_and_approved(self):
        """No review needed when reviewed and approved."""
        metadata = AuthorityMetadata(
            authority_state="approved_for_generation",
            review_state=ReviewState.REVIEWED,
        )
        assert metadata.requires_review() is False


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_luthiers_authority_metadata(self):
        """create_luthiers_authority_metadata sets correct source."""
        metadata = create_luthiers_authority_metadata(
            authority_state="advisory_candidate",
            subsystem="ibg",
        )
        assert metadata.source_repo == SourceRepo.LUTHIERS_TOOLBOX
        assert metadata.source_subsystem == "ibg"
        assert metadata.authority_state == "advisory_candidate"

    def test_create_vectorizer_authority_metadata(self):
        """create_vectorizer_authority_metadata is always non-authoritative."""
        metadata = create_vectorizer_authority_metadata(
            subsystem="research",
        )
        assert metadata.source_repo == SourceRepo.VECTORIZER_SANDBOX
        assert metadata.lifecycle_state == LifecycleState.R_AND_D_EXCLUDED
        assert metadata.non_authoritative_reason is not None
        assert metadata.is_authoritative() is False
        assert "spine integration" in metadata.authority_exclusions

    def test_create_ibg_authority_metadata(self):
        """create_ibg_authority_metadata has blocked provenance."""
        metadata = create_ibg_authority_metadata()

        assert metadata.source_repo == SourceRepo.LUTHIERS_TOOLBOX
        assert metadata.source_subsystem == "ibg"
        assert metadata.lifecycle_state == LifecycleState.BLOCKED_PROVENANCE
        assert "R1 ratification" in metadata.non_authoritative_reason
        assert "DXF export" in metadata.authority_exclusions
        assert metadata.is_authoritative() is False


class TestMetadataMutation:
    """Test metadata mutation methods."""

    def test_mark_non_authoritative(self):
        """mark_non_authoritative sets reason and updates timestamp."""
        metadata = AuthorityMetadata()
        original_updated = metadata.updated_at

        metadata.mark_non_authoritative("Test reason")

        assert metadata.non_authoritative_reason == "Test reason"
        assert metadata.is_authoritative() is False
        assert metadata.updated_at >= original_updated

    def test_add_authority_exclusion(self):
        """add_authority_exclusion adds to list."""
        metadata = AuthorityMetadata()
        original_count = len(metadata.authority_exclusions)

        metadata.add_authority_exclusion("test exclusion")

        assert len(metadata.authority_exclusions) == original_count + 1
        assert "test exclusion" in metadata.authority_exclusions

    def test_add_authority_exclusion_no_duplicates(self):
        """add_authority_exclusion does not add duplicates."""
        metadata = AuthorityMetadata()
        metadata.add_authority_exclusion("execution authorization")  # Already present
        count = len(metadata.authority_exclusions)

        metadata.add_authority_exclusion("execution authorization")

        assert len(metadata.authority_exclusions) == count


class TestSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields."""
        metadata = AuthorityMetadata(
            authority_state="advisory_candidate",
            epistemic_status="predicted",
            review_state=ReviewState.PENDING_REVIEW,
            lifecycle_state=LifecycleState.BLOCKED_PROVENANCE,
            source_repo=SourceRepo.LUTHIERS_TOOLBOX,
            source_subsystem="ibg",
            non_authoritative_reason="Test reason",
        )

        data = metadata.to_dict()

        assert data["authority_state"] == "advisory_candidate"
        assert data["epistemic_status"] == "predicted"
        assert data["review_state"] == "pending_review"
        assert data["lifecycle_state"] == "blocked_provenance"
        assert data["source_repo"] == "luthiers_toolbox"
        assert data["source_subsystem"] == "ibg"
        assert data["non_authoritative_reason"] == "Test reason"

    def test_round_trip_serialization(self):
        """Metadata should survive round-trip serialization."""
        original = AuthorityMetadata(
            authority_state="semantic_interpretation",
            epistemic_status="estimated",
            review_state=ReviewState.IN_REVIEW,
            lifecycle_state=LifecycleState.COMPAT_ONLY,
            source_repo=SourceRepo.TAP_TONE_PI,
            source_subsystem="analyzer",
            non_authoritative_reason=None,
            metadata={"test_key": "test_value"},
        )

        data = original.to_dict()
        restored = AuthorityMetadata.from_dict(data)

        assert restored.authority_state == original.authority_state
        assert restored.epistemic_status == original.epistemic_status
        assert restored.review_state == original.review_state
        assert restored.lifecycle_state == original.lifecycle_state
        assert restored.source_repo == original.source_repo
        assert restored.source_subsystem == original.source_subsystem
        assert restored.metadata == original.metadata

    def test_serialization_with_none_values(self):
        """Serialization should handle None values."""
        metadata = AuthorityMetadata()  # All defaults

        data = metadata.to_dict()
        restored = AuthorityMetadata.from_dict(data)

        assert restored.authority_state is None
        assert restored.review_state is None
        assert restored.lifecycle_state is None
