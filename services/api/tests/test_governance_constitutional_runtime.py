"""
Tests for Constitutional Runtime Foundation

DEV ORDER 1D: IBG Constitutional Intake Foundation

Tests cover:
- AuthorityState transitions and forbidden transitions
- ProvenanceRecord presence and lineage
- ConfidenceDeclaration semantics
- ReviewEnforcement protection (review_required cannot be machine-cleared)
- IBGIntakeGate rejection behavior
"""

import pytest
from datetime import datetime, timezone

from app.governance import (
    # Authority State
    AuthorityState,
    AuthorityStateContainer,
    AuthorityStateTransition,
    AuthorityTransitionError,
    ForbiddenTransitionError,
    FORBIDDEN_TRANSITIONS,
    compare_authority,
    requires_human_review,
    can_populate_ibg_memory,
    # Provenance
    ProvenanceRecord,
    TransformationStage,
    ProvenanceMissingError,
    create_source_provenance,
    create_derived_provenance,
    # Confidence
    ConfidenceDeclaration,
    ConfidenceType,
    create_statistical_confidence,
    create_heuristic_confidence,
    create_human_confidence,
    create_unknown_confidence,
    aggregate_confidence_min,
    # Review
    ReviewEnforcement,
    ReviewDecision,
    ReviewBypassAttemptError,
    ReviewIncompleteError,
    create_default_review_enforcement,
    create_pre_approved_review_enforcement,
)


# =============================================================================
# Authority State Tests
# =============================================================================

class TestAuthorityState:
    """Tests for AuthorityState enum and transitions."""

    def test_default_state_is_sandbox(self):
        """New containers start in sandbox_experimental."""
        container = AuthorityStateContainer()
        assert container.current_state == AuthorityState.SANDBOX_EXPERIMENTAL

    def test_valid_transition_sandbox_to_advisory(self):
        """Can transition from sandbox to advisory candidate."""
        container = AuthorityStateContainer()
        transition = container.transition(
            AuthorityState.ADVISORY_CANDIDATE,
            "system:test",
            "Test transition"
        )
        assert container.current_state == AuthorityState.ADVISORY_CANDIDATE
        assert transition.from_state == AuthorityState.SANDBOX_EXPERIMENTAL
        assert transition.to_state == AuthorityState.ADVISORY_CANDIDATE

    def test_valid_transition_advisory_to_human_reviewed(self):
        """Can transition from advisory to human_reviewed."""
        container = AuthorityStateContainer(current_state=AuthorityState.ADVISORY_CANDIDATE)
        container.transition(
            AuthorityState.HUMAN_REVIEWED,
            "human:reviewer_123",
            "Approved by human"
        )
        assert container.current_state == AuthorityState.HUMAN_REVIEWED

    def test_forbidden_transition_advisory_to_canonical(self):
        """Cannot transition from advisory_candidate to canonical_geometry."""
        container = AuthorityStateContainer(current_state=AuthorityState.ADVISORY_CANDIDATE)
        with pytest.raises(ForbiddenTransitionError) as exc_info:
            container.transition(
                AuthorityState.CANONICAL_GEOMETRY,
                "system:test",
                "Attempting forbidden transition"
            )
        assert exc_info.value.from_state == AuthorityState.ADVISORY_CANDIDATE
        assert exc_info.value.to_state == AuthorityState.CANONICAL_GEOMETRY

    def test_forbidden_transition_sandbox_to_approved(self):
        """Cannot transition from sandbox directly to approved_for_generation."""
        container = AuthorityStateContainer()
        with pytest.raises(ForbiddenTransitionError):
            container.transition(
                AuthorityState.APPROVED_FOR_GENERATION,
                "system:test",
                "Attempting to skip human review"
            )

    def test_transition_history_recorded(self):
        """Transition history is recorded."""
        container = AuthorityStateContainer()
        container.transition(AuthorityState.ADVISORY_CANDIDATE, "system:test", "First")
        container.transition(AuthorityState.HUMAN_REVIEWED, "human:reviewer", "Approved")

        assert len(container.transition_history) == 2
        assert container.transition_history[0].to_state == AuthorityState.ADVISORY_CANDIDATE
        assert container.transition_history[1].to_state == AuthorityState.HUMAN_REVIEWED

    def test_compare_authority_levels(self):
        """Authority levels can be compared."""
        assert compare_authority(AuthorityState.SANDBOX_EXPERIMENTAL, AuthorityState.CANONICAL_GEOMETRY) == -1
        assert compare_authority(AuthorityState.CANONICAL_GEOMETRY, AuthorityState.SANDBOX_EXPERIMENTAL) == 1
        assert compare_authority(AuthorityState.ADVISORY_CANDIDATE, AuthorityState.ADVISORY_CANDIDATE) == 0

    def test_requires_human_review(self):
        """Advisory and sandbox states require human review."""
        assert requires_human_review(AuthorityState.ADVISORY_CANDIDATE) is True
        assert requires_human_review(AuthorityState.SANDBOX_EXPERIMENTAL) is True
        assert requires_human_review(AuthorityState.HUMAN_REVIEWED) is False

    def test_can_populate_ibg_memory(self):
        """Only human_reviewed and approved can populate IBG memory."""
        assert can_populate_ibg_memory(AuthorityState.SANDBOX_EXPERIMENTAL) is False
        assert can_populate_ibg_memory(AuthorityState.ADVISORY_CANDIDATE) is False
        assert can_populate_ibg_memory(AuthorityState.HUMAN_REVIEWED) is True
        assert can_populate_ibg_memory(AuthorityState.APPROVED_FOR_GENERATION) is True

    def test_all_forbidden_transitions_are_blocked(self):
        """Verify all forbidden transitions in FORBIDDEN_TRANSITIONS are blocked."""
        for from_state, to_state in FORBIDDEN_TRANSITIONS:
            container = AuthorityStateContainer(current_state=from_state)
            with pytest.raises(ForbiddenTransitionError):
                container.transition(to_state, "system:test", "Testing forbidden")


# =============================================================================
# Provenance Record Tests
# =============================================================================

class TestProvenanceRecord:
    """Tests for ProvenanceRecord."""

    def test_create_source_provenance(self):
        """Can create provenance for a source artifact."""
        provenance = create_source_provenance(
            object_id="test_001",
            object_type="TestObject",
            source_artifact="/path/to/source.dxf",
        )
        assert provenance.object_id == "test_001"
        assert provenance.source_artifact == "/path/to/source.dxf"
        assert len(provenance.transformation_history) == 1
        assert provenance.transformation_history[0].stage == TransformationStage.SOURCE_INTAKE

    def test_create_derived_provenance(self):
        """Can create derived provenance preserving lineage."""
        parent = create_source_provenance(
            object_id="parent_001",
            object_type="ParentObject",
            source_artifact="/path/to/source.dxf",
        )

        child = create_derived_provenance(
            object_id="child_001",
            object_type="ChildObject",
            parent_provenance=parent,
            transformation_stage=TransformationStage.BODY_ISOLATION,
            transformation_method="test_isolation",
        )

        assert child.source_artifact == parent.source_artifact
        assert child.derived_from == parent.object_id
        assert parent.object_id in child.derivation_chain

    def test_has_complete_lineage(self):
        """Check lineage completeness."""
        provenance = create_source_provenance(
            object_id="test_001",
            object_type="TestObject",
            source_artifact="/path/to/source.dxf",
        )
        assert provenance.has_complete_lineage() is True

        # Missing source_artifact
        incomplete = ProvenanceRecord(
            object_id="test_002",
            object_type="TestObject",
            source_artifact="",  # Empty
        )
        assert incomplete.has_complete_lineage() is False

    def test_add_transformation(self):
        """Can add transformations to history."""
        provenance = create_source_provenance(
            object_id="test_001",
            object_type="TestObject",
            source_artifact="/path/to/source.dxf",
        )

        provenance.add_transformation(
            stage=TransformationStage.BODY_ISOLATION,
            method="isolate_body",
            params={"threshold": 0.5},
        )

        assert len(provenance.transformation_history) == 2
        assert provenance.transformation_history[1].stage == TransformationStage.BODY_ISOLATION

    def test_topology_degradation_tracking(self):
        """Can track topology degradation."""
        provenance = create_source_provenance(
            object_id="test_001",
            object_type="TestObject",
            source_artifact="/path/to/source.dxf",
        )

        provenance.record_topology_degradation(0.7, "Gap closure applied")
        assert provenance.topology_integrity_score == 0.7
        assert "Gap closure applied" in provenance.topology_degradation_notes

        # Further degradation should take minimum
        provenance.record_topology_degradation(0.5, "Simplification applied")
        assert provenance.topology_integrity_score == 0.5

    def test_provenance_hash_is_deterministic(self):
        """Provenance hash is deterministic for same inputs."""
        prov1 = create_source_provenance("obj_001", "Type", "/path/source.dxf")
        prov2 = create_source_provenance("obj_001", "Type", "/path/source.dxf")

        # Same ID, type, and source should produce same hash
        assert prov1.compute_provenance_hash() == prov2.compute_provenance_hash()


# =============================================================================
# Confidence Declaration Tests
# =============================================================================

class TestConfidenceDeclaration:
    """Tests for ConfidenceDeclaration."""

    def test_confidence_value_range(self):
        """Confidence value must be 0.0-1.0."""
        with pytest.raises(ValueError):
            ConfidenceDeclaration(
                value=1.5,  # Invalid
                confidence_type=ConfidenceType.STATISTICAL,
                origin="test",
                interpretation="test",
            )

        with pytest.raises(ValueError):
            ConfidenceDeclaration(
                value=-0.1,  # Invalid
                confidence_type=ConfidenceType.STATISTICAL,
                origin="test",
                interpretation="test",
            )

    def test_confidence_never_implies_correctness(self):
        """Confidence does not imply correctness."""
        conf = create_statistical_confidence(
            value=0.99,
            origin="test",
            interpretation="test",
        )
        assert conf.implies_correctness() is False

    def test_confidence_never_implies_canonicity(self):
        """Confidence does not imply canonicity."""
        conf = create_statistical_confidence(
            value=0.99,
            origin="test",
            interpretation="test",
        )
        assert conf.implies_canonicity() is False

    def test_confidence_never_implies_review_bypass(self):
        """Confidence does not imply review bypass."""
        conf = create_statistical_confidence(
            value=0.99,
            origin="test",
            interpretation="test",
        )
        assert conf.implies_review_bypass() is False

    def test_confidence_never_implies_ibg_eligibility(self):
        """Confidence does not imply IBG eligibility."""
        conf = create_statistical_confidence(
            value=0.99,
            origin="test",
            interpretation="test",
        )
        assert conf.implies_ibg_eligibility() is False

    def test_human_assessed_confidence(self):
        """Human-assessed confidence is distinguishable."""
        conf = create_human_confidence(
            value=0.8,
            reviewer_id="user_123",
            interpretation="Human assessment",
        )
        assert conf.is_human_assessed() is True
        assert conf.confidence_type == ConfidenceType.HUMAN_ASSESSED

    def test_unknown_confidence(self):
        """Unknown confidence defaults to 0.0."""
        conf = create_unknown_confidence()
        assert conf.value == 0.0
        assert conf.confidence_type == ConfidenceType.UNKNOWN

    def test_aggregate_confidence_min(self):
        """Aggregate takes minimum (conservative)."""
        declarations = [
            create_statistical_confidence(0.9, "test1", "test"),
            create_heuristic_confidence(0.7, "test2", "test"),
            create_statistical_confidence(0.8, "test3", "test"),
        ]
        composite = aggregate_confidence_min(declarations)
        assert composite.final_value == 0.7


# =============================================================================
# Review Enforcement Tests
# =============================================================================

class TestReviewEnforcement:
    """Tests for ReviewEnforcement."""

    def test_default_requires_review(self):
        """Default enforcement requires review."""
        enforcement = create_default_review_enforcement()
        assert enforcement.review_required is True
        assert enforcement.review_completed is False

    def test_machine_cannot_clear_review_required(self):
        """Machine code cannot clear review_required."""
        enforcement = create_default_review_enforcement()

        with pytest.raises(ReviewBypassAttemptError) as exc_info:
            enforcement.set_review_required(
                False,
                "system:test",  # Machine actor
                "Attempting to bypass"
            )

        assert exc_info.value.actor == "system:test"
        assert enforcement.bypass_attempt_count == 1

    def test_human_can_clear_review_required(self):
        """Human can clear review_required."""
        enforcement = create_default_review_enforcement()

        enforcement.set_review_required(
            False,
            "human:reviewer_123",  # Human actor
            "Approved after manual review"
        )

        assert enforcement.review_required is False

    def test_machine_cannot_approve(self):
        """Machine code cannot issue APPROVE decision."""
        enforcement = create_default_review_enforcement()

        with pytest.raises(ReviewBypassAttemptError):
            enforcement.record_review(
                "system:auto_approver",
                ReviewDecision.APPROVE,
            )

        assert enforcement.bypass_attempt_count == 1
        assert enforcement.review_completed is False

    def test_machine_cannot_reject(self):
        """Machine code cannot issue REJECT decision."""
        enforcement = create_default_review_enforcement()

        with pytest.raises(ReviewBypassAttemptError):
            enforcement.record_review(
                "system:auto_rejector",
                ReviewDecision.REJECT,
            )

    def test_machine_can_defer(self):
        """Machine code can issue DEFER decision."""
        enforcement = create_default_review_enforcement()

        enforcement.record_review(
            "system:triage",
            ReviewDecision.DEFER,
            notes="Needs more evidence",
        )

        assert len(enforcement.review_history) == 1
        assert enforcement.review_completed is False  # Defer doesn't complete

    def test_human_approval_completes_review(self):
        """Human approval completes review."""
        enforcement = create_default_review_enforcement()

        enforcement.record_review(
            "human:reviewer_123",
            ReviewDecision.APPROVE,
            notes="Looks good",
        )

        assert enforcement.review_completed is True
        assert enforcement.review_decision == ReviewDecision.APPROVE
        assert enforcement.review_required is False

    def test_require_completed_review(self):
        """Can assert review is completed."""
        enforcement = create_default_review_enforcement()

        with pytest.raises(ReviewIncompleteError):
            enforcement.require_completed_review("populate IBG memory")

        enforcement.record_review(
            "human:reviewer",
            ReviewDecision.APPROVE,
        )

        # Should not raise now
        enforcement.require_completed_review("populate IBG memory")

    def test_require_approval(self):
        """Can assert approval decision."""
        enforcement = create_default_review_enforcement()

        # Complete with REJECT
        enforcement.record_review(
            "human:reviewer",
            ReviewDecision.REJECT,
        )

        with pytest.raises(ReviewIncompleteError):
            enforcement.require_approval("populate IBG memory")

    def test_pre_approved_enforcement(self):
        """Can create pre-approved enforcement for human-reviewed items."""
        enforcement = create_pre_approved_review_enforcement(
            "human:prior_reviewer",
            "Previously reviewed in another system",
        )

        assert enforcement.review_required is False
        assert enforcement.review_completed is True
        assert enforcement.review_decision == ReviewDecision.APPROVE

    def test_pre_approved_requires_human(self):
        """Pre-approval requires human actor."""
        with pytest.raises(ValueError):
            create_pre_approved_review_enforcement(
                "system:fake_human",  # Not a human
                "Fake approval",
            )


# =============================================================================
# Integration Tests
# =============================================================================

class TestConstitutionalIntegration:
    """Integration tests for constitutional runtime foundation."""

    def test_full_intake_flow(self):
        """Test complete flow from creation to approval."""
        # Create source provenance
        provenance = create_source_provenance(
            object_id="test_body",
            object_type="BodyEvidence",
            source_artifact="/blueprints/guitar.dxf",
        )

        # Add transformation
        provenance.add_transformation(
            stage=TransformationStage.BODY_ISOLATION,
            method="body_isolation_stage",
            params={"threshold": 0.5},
        )

        # Create authority container
        authority = AuthorityStateContainer()

        # Transition through states
        authority.transition(
            AuthorityState.ADVISORY_CANDIDATE,
            "system:body_isolation",
            "Extracted body candidate",
        )

        assert authority.current_state == AuthorityState.ADVISORY_CANDIDATE
        assert not can_populate_ibg_memory(authority.current_state)

        # Human reviews and approves
        authority.transition(
            AuthorityState.HUMAN_REVIEWED,
            "human:reviewer_123",
            "Verified body extraction",
        )

        assert can_populate_ibg_memory(authority.current_state)

    def test_bypass_attempt_detection_accumulates(self):
        """Bypass attempts are accumulated across multiple attempts."""
        enforcement = create_default_review_enforcement()

        # Multiple bypass attempts
        for i in range(3):
            with pytest.raises(ReviewBypassAttemptError):
                enforcement.set_review_required(False, f"system:bot_{i}", "bypass")

        assert enforcement.bypass_attempt_count == 3
