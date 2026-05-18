"""
IBG Constitutional Integration Smoke Test

DEV ORDER 1D-HARDEN: Integration and failure-mode tests

Tests cover:
- Full intake flow: BodyEvidenceCandidate → IBGIntakeGate → decision
- Failure modes: missing provenance, low topology integrity, review_required
- Bypass resistance: machine code cannot elevate authority
"""

import pytest

from app.governance import (
    AuthorityState,
    ReviewDecision,
    ConfidenceType,
    create_heuristic_confidence,
    create_default_review_enforcement,
    ReviewBypassAttemptError,
    ForbiddenTransitionError,
)

from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    BodyEvidence,
    EvidenceSource,
)

from app.instrument_geometry.body.ibg.body_evidence_candidate import (
    BodyEvidenceCandidate,
    create_candidate_from_evidence,
    CandidateNotApprovedError,
)

from app.instrument_geometry.body.ibg.ibg_intake_gate import (
    IBGIntakeGate,
    IBGIntakeRejectionError,
    IntakeRejectionReason,
    create_default_intake_gate,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_evidence():
    """Create minimal body evidence."""
    return BodyEvidence(
        outline_points=[(0, 0), (350, 0), (350, 450), (0, 450)],
        source_type=EvidenceSource.VECTORIZER_DXF,
    )


@pytest.fixture
def candidate_advisory(sample_evidence):
    """Create candidate in ADVISORY_CANDIDATE state (default from factory)."""
    return create_candidate_from_evidence(
        evidence=sample_evidence,
        source_artifact="/blueprints/test_guitar.dxf",
        extraction_method="body_isolation_stage",
        confidence_value=0.75,
    )


@pytest.fixture
def candidate_approved(sample_evidence):
    """Create candidate that has been human-approved."""
    candidate = create_candidate_from_evidence(
        evidence=sample_evidence,
        source_artifact="/blueprints/test_guitar.dxf",
        extraction_method="body_isolation_stage",
        confidence_value=0.85,
    )
    candidate.record_review(
        "human:reviewer_integration_test",
        ReviewDecision.APPROVE,
        "Integration test approval",
    )
    return candidate


# =============================================================================
# Integration Smoke Test
# =============================================================================

class TestIntegrationSmokeTest:
    """
    Full flow: BodyEvidenceCandidate → IBGIntakeGate → decision

    This is the primary smoke test for 1D-HARDEN.
    """

    def test_advisory_candidate_is_blocked(self, candidate_advisory):
        """Advisory candidates cannot pass the gate."""
        gate = create_default_intake_gate()
        result = gate.validate(candidate_advisory)

        assert result.is_valid is False
        assert IntakeRejectionReason.AUTHORITY_INSUFFICIENT in result.rejections
        assert candidate_advisory.approved_for_ibg_memory is False

    def test_approved_candidate_passes_gate(self, candidate_approved):
        """Human-approved candidates pass the gate."""
        gate = create_default_intake_gate()
        result = gate.validate(candidate_approved)

        assert result.is_valid is True
        assert len(result.rejections) == 0
        assert candidate_approved.approved_for_ibg_memory is True

    def test_validate_or_raise_blocks_advisory(self, candidate_advisory):
        """validate_or_raise raises for advisory candidates."""
        gate = create_default_intake_gate()

        with pytest.raises(IBGIntakeRejectionError) as exc_info:
            gate.validate_or_raise(candidate_advisory)

        assert exc_info.value.reason == IntakeRejectionReason.AUTHORITY_INSUFFICIENT

    def test_validate_or_raise_passes_approved(self, candidate_approved):
        """validate_or_raise succeeds for approved candidates."""
        gate = create_default_intake_gate()
        result = gate.validate_or_raise(candidate_approved)

        assert result.is_valid is True

    def test_require_approval_blocks_advisory(self, candidate_advisory):
        """require_approval raises for advisory candidates."""
        with pytest.raises(CandidateNotApprovedError) as exc_info:
            candidate_advisory.require_approval("populate IBG memory")

        assert "advisory_candidate" in str(exc_info.value)

    def test_require_approval_passes_approved(self, candidate_approved):
        """require_approval succeeds for approved candidates."""
        # Should not raise
        candidate_approved.require_approval("populate IBG memory")


# =============================================================================
# Failure Mode Tests
# =============================================================================

class TestFailureModes:
    """
    Tests for specific failure scenarios.

    Each test verifies the gate catches the failure mode correctly.
    """

    def test_missing_provenance_blocked(self, sample_evidence):
        """Candidates without provenance are blocked."""
        candidate = BodyEvidenceCandidate(
            candidate_id="no_prov_test",
            evidence=sample_evidence,
            provenance=None,  # No provenance
        )

        gate = create_default_intake_gate()
        result = gate.validate(candidate)

        assert result.is_valid is False
        assert IntakeRejectionReason.PROVENANCE_MISSING in result.rejections

    def test_low_topology_integrity_blocked(self, candidate_approved):
        """Candidates with degraded topology are blocked."""
        # Degrade topology below threshold
        candidate_approved.provenance.record_topology_degradation(
            0.3,  # Below 0.5 default threshold
            "Severe gap closure applied"
        )

        gate = create_default_intake_gate()
        result = gate.validate(candidate_approved)

        assert result.is_valid is False
        assert IntakeRejectionReason.TOPOLOGY_INTEGRITY_DEGRADED in result.rejections
        assert any("gap closure" in w.lower() for w in result.warnings)

    def test_review_required_never_cleared_by_machine(self, candidate_advisory):
        """Machine code cannot clear review_required."""
        assert candidate_advisory.review_required is True

        # Attempt machine bypass
        with pytest.raises(ReviewBypassAttemptError):
            candidate_advisory.review.set_review_required(
                False,
                "system:machine_bypass_attempt",
                "Trying to skip review"
            )

        # review_required unchanged
        assert candidate_advisory.review_required is True
        assert candidate_advisory.review.bypass_attempt_count == 1

    def test_multiple_bypass_attempts_accumulate(self, candidate_advisory):
        """Bypass attempts are tracked cumulatively."""
        for i in range(3):
            try:
                candidate_advisory.review.set_review_required(
                    False,
                    f"system:bot_{i}",
                    "bypass attempt"
                )
            except ReviewBypassAttemptError:
                pass

        assert candidate_advisory.review.bypass_attempt_count == 3

        gate = create_default_intake_gate()
        result = gate.validate(candidate_advisory)

        assert IntakeRejectionReason.REVIEW_BYPASS_DETECTED in result.rejections

    def test_rejected_candidate_stays_blocked(self, candidate_advisory):
        """Rejected candidates cannot be resurrected."""
        # Human rejects
        candidate_advisory.record_review(
            "human:reviewer_reject",
            ReviewDecision.REJECT,
            "Does not match reference"
        )

        gate = create_default_intake_gate()
        result = gate.validate(candidate_advisory)

        assert result.is_valid is False
        assert IntakeRejectionReason.CANDIDATE_REJECTED in result.rejections


# =============================================================================
# Authority Escalation Protection
# =============================================================================

class TestAuthorityEscalationProtection:
    """
    Tests that machine code cannot silently elevate authority.
    """

    def test_cannot_jump_advisory_to_canonical(self, candidate_advisory):
        """Cannot transition from advisory to canonical directly."""
        with pytest.raises(ForbiddenTransitionError):
            candidate_advisory.authority.transition(
                AuthorityState.CANONICAL_GEOMETRY,
                "system:malicious_escalation",
                "Attempting forbidden transition"
            )

        assert candidate_advisory.authority_state == AuthorityState.ADVISORY_CANDIDATE

    def test_cannot_jump_sandbox_to_approved(self, sample_evidence):
        """Cannot transition from sandbox to approved_for_generation."""
        candidate = BodyEvidenceCandidate(
            candidate_id="sandbox_test",
            evidence=sample_evidence,
        )

        assert candidate.authority_state == AuthorityState.SANDBOX_EXPERIMENTAL

        with pytest.raises(ForbiddenTransitionError):
            candidate.authority.transition(
                AuthorityState.APPROVED_FOR_GENERATION,
                "system:skip_review",
                "Bypassing human review"
            )

        assert candidate.authority_state == AuthorityState.SANDBOX_EXPERIMENTAL

    def test_machine_approve_blocked(self, candidate_advisory):
        """Machine code cannot issue APPROVE decision."""
        with pytest.raises(ReviewBypassAttemptError):
            candidate_advisory.review.record_review(
                "system:auto_approver",
                ReviewDecision.APPROVE,
                "Auto-approved"
            )

        assert candidate_advisory.review.review_completed is False
        assert candidate_advisory.approved_for_ibg_memory is False


# =============================================================================
# Provenance Chain Integrity
# =============================================================================

class TestProvenanceChainIntegrity:
    """
    Tests for provenance chain preservation.
    """

    def test_provenance_tracks_source(self, candidate_advisory):
        """Provenance tracks original source artifact."""
        assert candidate_advisory.provenance is not None
        assert candidate_advisory.provenance.source_artifact == "/blueprints/test_guitar.dxf"

    def test_provenance_records_transformation(self, candidate_advisory):
        """Provenance records extraction transformation."""
        history = candidate_advisory.provenance.transformation_history
        assert len(history) >= 2  # SOURCE_INTAKE + BODY_ISOLATION

        methods = [t.method for t in history]
        assert "body_isolation_stage" in methods

    def test_approval_recorded_in_provenance(self, candidate_approved):
        """Human approval is recorded in provenance."""
        history = candidate_approved.provenance.transformation_history

        approval_records = [
            t for t in history
            if "approved" in t.method.lower() or "review" in t.params.get("reason", "").lower()
        ]

        assert len(approval_records) >= 1


# =============================================================================
# Gate Configuration
# =============================================================================

class TestGateConfiguration:
    """
    Tests for gate configuration options.
    """

    def test_default_gate_topology_threshold(self, candidate_approved):
        """Default gate uses 0.5 topology threshold."""
        # Just above threshold
        candidate_approved.provenance.record_topology_degradation(0.55, "Minor")

        gate = create_default_intake_gate()
        result = gate.validate(candidate_approved)
        assert result.is_valid is True

        # Just below threshold
        candidate_approved.provenance.record_topology_degradation(0.45, "More")
        result = gate.validate(candidate_approved)
        assert result.is_valid is False

    def test_gate_result_includes_all_checks(self, candidate_approved):
        """Gate result includes all gate check results."""
        gate = create_default_intake_gate()
        result = gate.validate(candidate_approved)

        expected_gates = [
            "authority",
            "provenance_presence",
            "provenance_completeness",
            "review_status",
            "confidence",
            "bypass_detection",
            "topology_integrity",
            "rejection_status",
        ]

        for gate_name in expected_gates:
            assert gate_name in result.gate_results
