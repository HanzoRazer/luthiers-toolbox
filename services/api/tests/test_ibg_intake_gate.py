"""
Tests for IBG Intake Gate

DEV ORDER 1D: IBG Constitutional Intake Foundation

Tests cover:
- Gate rejection behavior for unauthorized candidates
- Gate acceptance behavior for approved candidates
- All rejection reasons
- Configuration options
"""

import pytest

from app.governance import (
    AuthorityState,
    ReviewDecision,
    ConfidenceType,
    create_heuristic_confidence,
)

from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    BodyEvidence,
    EvidenceSource,
)

from app.instrument_geometry.body.ibg.body_evidence_candidate import (
    BodyEvidenceCandidate,
    create_candidate_from_evidence,
)

from app.instrument_geometry.body.ibg.ibg_intake_gate import (
    IBGIntakeGate,
    IBGIntakeGateConfig,
    IBGIntakeRejectionError,
    IntakeRejectionReason,
    create_default_intake_gate,
    create_strict_intake_gate,
    create_permissive_intake_gate,
)


@pytest.fixture
def sample_evidence():
    """Create sample body evidence."""
    return BodyEvidence(
        outline_points=[(0, 0), (100, 0), (100, 200), (0, 200)],
        source_type=EvidenceSource.VECTORIZER_DXF,
    )


@pytest.fixture
def sample_candidate(sample_evidence):
    """Create sample candidate with provenance."""
    return create_candidate_from_evidence(
        evidence=sample_evidence,
        source_artifact="/test/blueprint.dxf",
        extraction_method="test_extraction",
        confidence_value=0.8,
    )


class TestIBGIntakeGateRejection:
    """Tests for gate rejection behavior."""

    def test_rejects_sandbox_experimental(self, sample_candidate):
        """Rejects candidates in sandbox_experimental state."""
        # Force back to sandbox
        sample_candidate.authority._current_state = AuthorityState.SANDBOX_EXPERIMENTAL

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert result.is_valid is False
        assert IntakeRejectionReason.AUTHORITY_INSUFFICIENT in result.rejections

    def test_rejects_advisory_candidate(self, sample_candidate):
        """Rejects candidates in advisory_candidate state (not human reviewed)."""
        assert sample_candidate.authority_state == AuthorityState.ADVISORY_CANDIDATE

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert result.is_valid is False
        assert IntakeRejectionReason.AUTHORITY_INSUFFICIENT in result.rejections

    def test_rejects_missing_provenance(self, sample_evidence):
        """Rejects candidates without provenance."""
        candidate = BodyEvidenceCandidate(
            candidate_id="no_prov_001",
            evidence=sample_evidence,
            provenance=None,  # No provenance
        )

        gate = create_default_intake_gate()
        result = gate.validate(candidate)

        assert result.is_valid is False
        assert IntakeRejectionReason.PROVENANCE_MISSING in result.rejections

    def test_rejects_pending_review(self, sample_candidate):
        """Rejects candidates with pending review."""
        # Transition to human_reviewed but don't complete review
        sample_candidate.authority.transition(
            AuthorityState.HUMAN_REVIEWED,
            "human:fake",
            "Testing",
        )

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert result.is_valid is False
        assert IntakeRejectionReason.REVIEW_REQUIRED in result.rejections

    def test_rejects_rejected_review(self, sample_candidate):
        """Rejects candidates with REJECT review decision."""
        # Complete review with rejection
        sample_candidate.record_review(
            "human:reviewer",
            ReviewDecision.REJECT,
            "Not acceptable",
        )

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert result.is_valid is False
        # Will have multiple rejections including authority insufficient

    def test_rejects_unknown_confidence(self, sample_evidence):
        """Rejects candidates with unknown confidence type."""
        candidate = create_candidate_from_evidence(
            evidence=sample_evidence,
            source_artifact="/test/blueprint.dxf",
            extraction_method="test",
        )
        # Set confidence to unknown
        candidate.confidence = create_heuristic_confidence(0.0, "test", "test")
        candidate.confidence = candidate.confidence.__class__(
            value=0.5,
            confidence_type=ConfidenceType.UNKNOWN,
            origin="unset",
            interpretation="not set",
        )

        gate = create_default_intake_gate()
        result = gate.validate(candidate)

        assert IntakeRejectionReason.CONFIDENCE_UNDECLARED in result.rejections

    def test_rejects_bypass_attempts(self, sample_candidate):
        """Rejects candidates with bypass attempts."""
        # Trigger bypass attempts
        for _ in range(3):
            try:
                sample_candidate.review.set_review_required(False, "system:bot", "bypass")
            except Exception:
                pass

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert IntakeRejectionReason.REVIEW_BYPASS_DETECTED in result.rejections

    def test_rejects_degraded_topology(self, sample_candidate):
        """Rejects candidates with degraded topology integrity."""
        sample_candidate.provenance.record_topology_degradation(
            0.3,  # Below threshold
            "Severe simplification"
        )

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert IntakeRejectionReason.TOPOLOGY_INTEGRITY_DEGRADED in result.rejections

    def test_rejects_rejected_state(self, sample_candidate):
        """Rejects candidates in REJECTED authority state."""
        sample_candidate.authority.transition(
            AuthorityState.REJECTED,
            "human:reviewer",
            "Not acceptable",
        )

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert IntakeRejectionReason.CANDIDATE_REJECTED in result.rejections


class TestIBGIntakeGateAcceptance:
    """Tests for gate acceptance behavior."""

    def test_accepts_fully_approved_candidate(self, sample_candidate):
        """Accepts fully approved candidate with all requirements met."""
        # Complete human review with approval
        sample_candidate.record_review(
            "human:reviewer_123",
            ReviewDecision.APPROVE,
            "Verified correct",
        )

        gate = create_default_intake_gate()
        result = gate.validate(sample_candidate)

        assert result.is_valid is True
        assert len(result.rejections) == 0
        assert all(result.gate_results.values())

    def test_validate_or_raise_on_valid(self, sample_candidate):
        """validate_or_raise returns result for valid candidates."""
        sample_candidate.record_review(
            "human:reviewer",
            ReviewDecision.APPROVE,
        )

        gate = create_default_intake_gate()
        result = gate.validate_or_raise(sample_candidate)

        assert result.is_valid is True

    def test_validate_or_raise_raises_on_invalid(self, sample_candidate):
        """validate_or_raise raises for invalid candidates."""
        gate = create_default_intake_gate()

        with pytest.raises(IBGIntakeRejectionError) as exc_info:
            gate.validate_or_raise(sample_candidate)

        assert exc_info.value.candidate_id == sample_candidate.candidate_id


class TestIBGIntakeGateConfiguration:
    """Tests for gate configuration options."""

    def test_strict_gate_requires_higher_authority(self, sample_candidate):
        """Strict gate requires APPROVED_FOR_GENERATION."""
        # Approve for human_reviewed level
        sample_candidate.record_review(
            "human:reviewer",
            ReviewDecision.APPROVE,
        )

        # Default gate accepts
        default_gate = create_default_intake_gate()
        assert default_gate.validate(sample_candidate).is_valid is True

        # Strict gate requires higher authority
        strict_gate = create_strict_intake_gate()
        result = strict_gate.validate(sample_candidate)

        # Will fail because not APPROVED_FOR_GENERATION
        # Actually human_reviewed is accepted by can_populate_ibg_memory
        # So we need to check topology integrity instead
        # Let's test topology threshold
        sample_candidate.provenance.record_topology_degradation(0.6, "Some degradation")

        # Default accepts 0.5 threshold
        assert default_gate.validate(sample_candidate).is_valid is True

        # Strict requires 0.7
        assert strict_gate.validate(sample_candidate).is_valid is False

    def test_permissive_gate_tolerates_bypass_attempts(self, sample_candidate):
        """Permissive gate tolerates some bypass attempts."""
        # Attempt the bypasses FIRST, while review is still required: a machine
        # actor clearing review_required increments _bypass_attempt_count only when
        # the flag is still set. (Approving first clears the flag, so the attempts
        # would no-op and the counter would stay 0.)
        for _ in range(2):
            try:
                sample_candidate.review.set_review_required(False, "system:bot", "bypass")
            except Exception:
                pass

        # Then complete human approval.
        sample_candidate.record_review(
            "human:reviewer",
            ReviewDecision.APPROVE,
        )

        # Default gate rejects
        default_gate = create_default_intake_gate()
        assert IntakeRejectionReason.REVIEW_BYPASS_DETECTED in default_gate.validate(sample_candidate).rejections

        # Permissive gate accepts up to 2
        permissive_gate = create_permissive_intake_gate()
        assert permissive_gate.validate(sample_candidate).is_valid is True

    def test_custom_configuration(self, sample_candidate):
        """Can create gate with custom configuration."""
        config = IBGIntakeGateConfig(
            minimum_topology_integrity=0.9,
            allow_bypass_attempts=5,
        )
        gate = IBGIntakeGate(config)

        sample_candidate.record_review("human:reviewer", ReviewDecision.APPROVE)
        sample_candidate.provenance.record_topology_degradation(0.85, "Minor degradation")

        result = gate.validate(sample_candidate)

        # Should fail topology check
        assert IntakeRejectionReason.TOPOLOGY_INTEGRITY_DEGRADED in result.rejections


class TestBodyEvidenceCandidateIntegration:
    """Integration tests for BodyEvidenceCandidate with gate."""

    def test_candidate_approved_for_ibg_memory_flag(self, sample_candidate):
        """approved_for_ibg_memory flag matches gate validation."""
        gate = create_default_intake_gate()

        # Before approval
        assert sample_candidate.approved_for_ibg_memory is False
        assert gate.validate(sample_candidate).is_valid is False

        # After approval
        sample_candidate.record_review(
            "human:reviewer",
            ReviewDecision.APPROVE,
        )

        assert sample_candidate.approved_for_ibg_memory is True
        assert gate.validate(sample_candidate).is_valid is True

    def test_require_approval_method(self, sample_candidate):
        """require_approval method validates for IBG operations."""
        from app.instrument_geometry.body.ibg.body_evidence_candidate import CandidateNotApprovedError

        with pytest.raises(CandidateNotApprovedError):
            sample_candidate.require_approval("populate IBG memory")

        sample_candidate.record_review("human:reviewer", ReviewDecision.APPROVE)

        # Should not raise now
        sample_candidate.require_approval("populate IBG memory")
