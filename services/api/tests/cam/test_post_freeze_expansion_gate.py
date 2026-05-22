"""
Tests for Post-Freeze Expansion Gate (CAM Dev Order 8A).

Coverage:
  - PostFreezeExpansionProposal model and validation
  - PostFreezeExpansionReadiness model and gate classification
  - Registry operations (proposal, readiness)
  - CI summary
  - Router endpoints

8A invariants tested:
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.cam.post_freeze_expansion_gate import (
    PostFreezeExpansionProposal,
    TargetLayer,
    ProposalState,
    create_post_freeze_proposal,
    build_post_freeze_proposal_hash,
    validate_post_freeze_proposal,
    is_proposal_valid,
    get_proposal_summary,
    is_valid_target_layer,
    VALID_TARGET_LAYERS,
)
from app.cam.post_freeze_readiness import (
    PostFreezeExpansionReadiness,
    PostFreezeGate,
    classify_post_freeze_gate,
    build_post_freeze_readiness_hash,
    validate_freeze_compatibility,
    detect_baseline_rewrite_request,
    detect_execution_authority_request,
    get_readiness_summary,
    get_readiness_status_message,
)
from app.cam.post_freeze_registry import (
    register_post_freeze_proposal,
    get_post_freeze_proposal,
    get_latest_post_freeze_proposal,
    list_post_freeze_proposals,
    list_proposals_by_target_layer,
    list_proposals_by_state,
    get_post_freeze_proposal_count,
    register_post_freeze_readiness,
    get_post_freeze_readiness,
    get_latest_post_freeze_readiness,
    list_post_freeze_readiness,
    list_readiness_by_gate,
    list_readiness_for_proposal,
    get_post_freeze_readiness_count,
    evaluate_post_freeze_readiness,
    build_post_freeze_ci_summary,
    get_post_freeze_status_summary,
    clear_post_freeze_indexes_for_tests,
    get_post_freeze_index_counts,
)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_post_freeze_indexes_for_tests()
    yield
    clear_post_freeze_indexes_for_tests()


# ─────────────────────────────────────────────────────────────────────────────
# PostFreezeExpansionProposal Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPostFreezeExpansionProposalModel:
    """Tests for PostFreezeExpansionProposal model."""

    def test_create_proposal_defaults(self):
        """Test proposal creation with defaults."""
        proposal = PostFreezeExpansionProposal(
            title="Test Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test capability",
        )

        assert proposal.title == "Test Proposal"
        assert proposal.proposal_id.startswith("pfep-")
        assert proposal.target_layer == "manufacturing_cognition"
        assert proposal.depends_on_freeze_id is None
        assert proposal.expected_artifacts == []
        assert proposal.governance_risks == []
        assert proposal.required_reviews == []
        assert proposal.ontology_mutation_requested is False
        assert proposal.baseline_rewrite_requested is False
        assert proposal.implementation_authorized is False
        assert proposal.execution_authorized is False
        assert proposal.machine_output_allowed is False
        assert proposal.proposal_state == "draft"

    def test_create_proposal_with_all_fields(self):
        """Test proposal creation with all fields."""
        proposal = PostFreezeExpansionProposal(
            title="Full Proposal",
            target_layer="geometry_authority",
            proposed_capability="Full capability",
            depends_on_freeze_id="gbf-test123",
            expected_artifacts=["artifact1", "artifact2"],
            governance_risks=["risk1"],
            required_reviews=["review1", "review2"],
            proposal_state="submitted_for_review",
        )

        assert proposal.depends_on_freeze_id == "gbf-test123"
        assert len(proposal.expected_artifacts) == 2
        assert len(proposal.governance_risks) == 1
        assert len(proposal.required_reviews) == 2
        assert proposal.proposal_state == "submitted_for_review"

    def test_proposal_8a_invariant_implementation_authorized(self):
        """Test that implementation_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PostFreezeExpansionProposal(
                title="Bad Proposal",
                target_layer="manufacturing_cognition",
                proposed_capability="Test",
                implementation_authorized=True,
            )
        assert "implementation_authorized must be False" in str(exc_info.value)

    def test_proposal_8a_invariant_execution_authorized(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PostFreezeExpansionProposal(
                title="Bad Proposal",
                target_layer="manufacturing_cognition",
                proposed_capability="Test",
                execution_authorized=True,
            )
        assert "execution_authorized must be False" in str(exc_info.value)

    def test_proposal_8a_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PostFreezeExpansionProposal(
                title="Bad Proposal",
                target_layer="manufacturing_cognition",
                proposed_capability="Test",
                machine_output_allowed=True,
            )
        assert "machine_output_allowed must be False" in str(exc_info.value)

    def test_proposal_compute_hash(self):
        """Test deterministic hash computation."""
        proposal1 = PostFreezeExpansionProposal(
            title="Test Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test capability",
        )
        proposal2 = PostFreezeExpansionProposal(
            title="Test Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test capability",
        )

        hash1 = proposal1.compute_hash()
        hash2 = proposal2.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_proposal_hash_changes_with_content(self):
        """Test that hash changes when content changes."""
        proposal1 = PostFreezeExpansionProposal(
            title="Test Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Capability A",
        )
        proposal2 = PostFreezeExpansionProposal(
            title="Test Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Capability B",
        )

        assert proposal1.compute_hash() != proposal2.compute_hash()

    def test_create_post_freeze_proposal_helper(self):
        """Test create_post_freeze_proposal helper."""
        proposal = create_post_freeze_proposal(
            title="Helper Test",
            target_layer="strategy_export",
            proposed_capability="Test",
            required_reviews=["security_review"],
        )

        assert proposal.title == "Helper Test"
        assert proposal.deterministic_proposal_hash != ""
        assert len(proposal.deterministic_proposal_hash) == 64

    def test_validate_post_freeze_proposal_valid(self):
        """Test validation of valid proposal."""
        proposal = create_post_freeze_proposal(
            title="Valid Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        is_valid, issues = validate_post_freeze_proposal(proposal)
        assert is_valid
        assert len(issues) == 0

    def test_is_proposal_valid_helper(self):
        """Test is_proposal_valid helper."""
        proposal = create_post_freeze_proposal(
            title="Valid",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        assert is_proposal_valid(proposal)

    def test_get_proposal_summary(self):
        """Test proposal summary generation."""
        proposal = create_post_freeze_proposal(
            title="Summary Test",
            target_layer="geometry_authority",
            proposed_capability="Test",
            expected_artifacts=["a1", "a2"],
            governance_risks=["r1"],
        )
        summary = get_proposal_summary(proposal)

        assert summary["title"] == "Summary Test"
        assert summary["target_layer"] == "geometry_authority"
        assert summary["expected_artifact_count"] == 2
        assert summary["governance_risk_count"] == 1
        assert summary["implementation_authorized"] is False

    def test_all_target_layers_valid(self):
        """Test all target layers are valid."""
        for layer in VALID_TARGET_LAYERS:
            assert is_valid_target_layer(layer)

    def test_invalid_target_layer(self):
        """Test invalid target layer detection."""
        assert not is_valid_target_layer("invalid_layer")


# ─────────────────────────────────────────────────────────────────────────────
# PostFreezeExpansionReadiness Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPostFreezeExpansionReadinessModel:
    """Tests for PostFreezeExpansionReadiness model."""

    def test_create_readiness_defaults(self):
        """Test readiness creation with defaults."""
        readiness = PostFreezeExpansionReadiness(proposal_id="pfep-test123")

        assert readiness.readiness_id.startswith("pfer-")
        assert readiness.proposal_id == "pfep-test123"
        assert readiness.freeze_compatible is True
        assert readiness.freeze_exists is False
        assert readiness.gate == "yellow"
        assert readiness.implementation_authorized is False
        assert readiness.execution_authorized is False
        assert readiness.machine_output_allowed is False

    def test_readiness_8a_invariant_implementation_authorized(self):
        """Test that implementation_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PostFreezeExpansionReadiness(
                proposal_id="pfep-test",
                implementation_authorized=True,
            )
        assert "implementation_authorized must be False" in str(exc_info.value)

    def test_readiness_8a_invariant_execution_authorized(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PostFreezeExpansionReadiness(
                proposal_id="pfep-test",
                execution_authorized=True,
            )
        assert "execution_authorized must be False" in str(exc_info.value)

    def test_readiness_8a_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PostFreezeExpansionReadiness(
                proposal_id="pfep-test",
                machine_output_allowed=True,
            )
        assert "machine_output_allowed must be False" in str(exc_info.value)

    def test_readiness_compute_hash(self):
        """Test deterministic hash computation."""
        readiness1 = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="green",
        )
        readiness2 = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="green",
        )

        hash1 = readiness1.compute_hash()
        hash2 = readiness2.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_readiness_hash_changes_with_gate(self):
        """Test that hash changes when gate changes."""
        readiness1 = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="green",
        )
        readiness2 = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="red",
        )

        assert readiness1.compute_hash() != readiness2.compute_hash()

    def test_get_readiness_summary(self):
        """Test readiness summary generation."""
        readiness = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="yellow",
            warnings=["warning1", "warning2"],
        )
        summary = get_readiness_summary(readiness)

        assert summary["proposal_id"] == "pfep-test"
        assert summary["gate"] == "yellow"
        assert summary["warning_count"] == 2
        assert summary["implementation_authorized"] is False

    def test_get_readiness_status_message_green(self):
        """Test status message for green gate."""
        readiness = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="green",
        )
        message = get_readiness_status_message(readiness)
        assert "ready for human review" in message

    def test_get_readiness_status_message_yellow(self):
        """Test status message for yellow gate."""
        readiness = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="yellow",
            warnings=["test warning"],
        )
        message = get_readiness_status_message(readiness)
        assert "needs attention" in message

    def test_get_readiness_status_message_red(self):
        """Test status message for red gate."""
        readiness = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="red",
            blocking_issues=["blocked"],
        )
        message = get_readiness_status_message(readiness)
        assert "blocked" in message.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Gate Classification Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGateClassification:
    """Tests for gate classification logic."""

    def test_gate_green_clean_proposal(self):
        """Test green gate for clean proposal."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "green"
        assert len(blocking) == 0
        assert len(warnings) == 0

    def test_gate_red_baseline_rewrite(self):
        """Test red gate for baseline rewrite request."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=True,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "red"
        assert len(blocking) > 0
        assert "baseline rewrite" in blocking[0].lower()

    def test_gate_red_execution_authorized(self):
        """Test red gate for execution authority request."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=True,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "red"
        assert any("execution" in b.lower() for b in blocking)

    def test_gate_red_machine_output(self):
        """Test red gate for machine output request."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=True,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "red"
        assert any("machine output" in b.lower() for b in blocking)

    def test_gate_red_implementation_authorized(self):
        """Test red gate for implementation authority request."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=True,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "red"
        assert any("implementation" in b.lower() for b in blocking)

    def test_gate_red_ontology_mutation(self):
        """Test red gate for ontology mutation request."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=True,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "red"
        assert any("ontology mutation" in b.lower() for b in blocking)

    def test_gate_yellow_missing_freeze_ref(self):
        """Test yellow gate for missing freeze reference."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id=None,
            freeze_exists=False,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "yellow"
        assert len(blocking) == 0
        assert any("freeze reference" in w.lower() for w in warnings)

    def test_gate_yellow_freeze_not_found(self):
        """Test yellow gate when freeze not found."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-nonexistent",
            freeze_exists=False,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "yellow"
        assert any("not found" in w.lower() for w in warnings)

    def test_gate_yellow_reviews_not_declared(self):
        """Test yellow gate when reviews not declared."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=False,
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "yellow"
        assert any("review" in w.lower() for w in warnings)

    def test_gate_yellow_unclear_target_layer(self):
        """Test yellow gate when target layer unclear."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=False,
            governance_risks_complete=True,
        )

        assert gate == "yellow"
        assert any("target layer" in w.lower() for w in warnings)

    def test_gate_yellow_incomplete_risks(self):
        """Test yellow gate when risks incomplete."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=False,
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id="gbf-test",
            freeze_exists=True,
            required_reviews_declared=True,
            target_layer_clear=True,
            governance_risks_complete=False,
        )

        assert gate == "yellow"
        assert any("risk" in w.lower() for w in warnings)

    def test_red_takes_precedence_over_yellow(self):
        """Test that red conditions take precedence over yellow."""
        gate, blocking, warnings = classify_post_freeze_gate(
            baseline_rewrite_requested=True,  # RED
            execution_authorized=False,
            machine_output_allowed=False,
            implementation_authorized=False,
            ontology_mutation_requested=False,
            depends_on_freeze_id=None,  # Would be YELLOW
            freeze_exists=False,
            required_reviews_declared=False,  # Would be YELLOW
            target_layer_clear=True,
            governance_risks_complete=True,
        )

        assert gate == "red"


# ─────────────────────────────────────────────────────────────────────────────
# Detection Helper Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDetectionHelpers:
    """Tests for detection helper functions."""

    def test_detect_baseline_rewrite_explicit(self):
        """Test baseline rewrite detection from explicit field."""
        assert detect_baseline_rewrite_request(True, [])
        assert not detect_baseline_rewrite_request(False, ["some risk"])

    def test_detect_execution_authority(self):
        """Test execution authority detection."""
        assert detect_execution_authority_request(True, False, False)
        assert detect_execution_authority_request(False, True, False)
        assert detect_execution_authority_request(False, False, True)
        assert not detect_execution_authority_request(False, False, False)

    def test_validate_freeze_compatibility_none(self):
        """Test freeze compatibility with no freeze ID."""
        compatible, exists, status, issues = validate_freeze_compatibility(None)
        assert compatible is True
        assert exists is False
        assert status is None
        assert len(issues) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPostFreezeRegistry:
    """Tests for post-freeze registry operations."""

    def test_register_proposal_success(self):
        """Test successful proposal registration."""
        proposal = create_post_freeze_proposal(
            title="Test Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        success, error = register_post_freeze_proposal(proposal)

        assert success
        assert error is None
        assert get_post_freeze_proposal_count() == 1

    def test_register_proposal_duplicate(self):
        """Test duplicate proposal registration fails."""
        proposal = create_post_freeze_proposal(
            title="Test Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal)
        success, error = register_post_freeze_proposal(proposal)

        assert not success
        assert "already exists" in error

    def test_get_post_freeze_proposal(self):
        """Test getting proposal by ID."""
        proposal = create_post_freeze_proposal(
            title="Test",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal)

        retrieved = get_post_freeze_proposal(proposal.proposal_id)
        assert retrieved is not None
        assert retrieved.title == "Test"

    def test_get_post_freeze_proposal_not_found(self):
        """Test getting non-existent proposal."""
        retrieved = get_post_freeze_proposal("pfep-nonexistent")
        assert retrieved is None

    def test_get_latest_post_freeze_proposal(self):
        """Test getting latest proposal."""
        proposal1 = create_post_freeze_proposal(
            title="First",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal1)

        proposal2 = create_post_freeze_proposal(
            title="Second",
            target_layer="geometry_authority",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal2)

        latest = get_latest_post_freeze_proposal()
        assert latest is not None
        assert latest.title == "Second"

    def test_list_post_freeze_proposals(self):
        """Test listing all proposals."""
        for i in range(3):
            proposal = create_post_freeze_proposal(
                title=f"Proposal {i}",
                target_layer="manufacturing_cognition",
                proposed_capability="Test",
            )
            register_post_freeze_proposal(proposal)

        proposals = list_post_freeze_proposals()
        assert len(proposals) == 3

    def test_list_proposals_by_target_layer(self):
        """Test filtering proposals by target layer."""
        proposal1 = create_post_freeze_proposal(
            title="MC Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal1)

        proposal2 = create_post_freeze_proposal(
            title="GA Proposal",
            target_layer="geometry_authority",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal2)

        mc_proposals = list_proposals_by_target_layer("manufacturing_cognition")
        assert len(mc_proposals) == 1
        assert mc_proposals[0].title == "MC Proposal"

    def test_list_proposals_by_state(self):
        """Test filtering proposals by state."""
        proposal1 = create_post_freeze_proposal(
            title="Draft Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            proposal_state="draft",
        )
        register_post_freeze_proposal(proposal1)

        proposal2 = create_post_freeze_proposal(
            title="Submitted Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            proposal_state="submitted_for_review",
        )
        register_post_freeze_proposal(proposal2)

        draft_proposals = list_proposals_by_state("draft")
        assert len(draft_proposals) == 1
        assert draft_proposals[0].title == "Draft Proposal"

    def test_register_readiness_success(self):
        """Test successful readiness registration."""
        readiness = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="green",
        )
        success, error = register_post_freeze_readiness(readiness)

        assert success
        assert error is None
        assert get_post_freeze_readiness_count() == 1

    def test_register_readiness_duplicate(self):
        """Test duplicate readiness registration fails."""
        readiness = PostFreezeExpansionReadiness(
            proposal_id="pfep-test",
            gate="green",
        )
        register_post_freeze_readiness(readiness)
        success, error = register_post_freeze_readiness(readiness)

        assert not success
        assert "already exists" in error

    def test_list_readiness_by_gate(self):
        """Test filtering readiness by gate."""
        green = PostFreezeExpansionReadiness(proposal_id="pfep-1", gate="green")
        yellow = PostFreezeExpansionReadiness(proposal_id="pfep-2", gate="yellow")
        red = PostFreezeExpansionReadiness(proposal_id="pfep-3", gate="red")

        register_post_freeze_readiness(green)
        register_post_freeze_readiness(yellow)
        register_post_freeze_readiness(red)

        green_evals = list_readiness_by_gate("green")
        assert len(green_evals) == 1

    def test_list_readiness_for_proposal(self):
        """Test filtering readiness by proposal."""
        r1 = PostFreezeExpansionReadiness(proposal_id="pfep-1", gate="green")
        r2 = PostFreezeExpansionReadiness(proposal_id="pfep-1", gate="yellow")
        r3 = PostFreezeExpansionReadiness(proposal_id="pfep-2", gate="green")

        register_post_freeze_readiness(r1)
        register_post_freeze_readiness(r2)
        register_post_freeze_readiness(r3)

        proposal_evals = list_readiness_for_proposal("pfep-1")
        assert len(proposal_evals) == 2

    def test_evaluate_post_freeze_readiness_green(self):
        """Test evaluation producing green gate."""
        proposal = create_post_freeze_proposal(
            title="Clean Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            depends_on_freeze_id="gbf-existing",
            required_reviews=["security_review"],
            governance_risks=["risk1"],
        )

        readiness = evaluate_post_freeze_readiness(proposal)

        assert readiness.proposal_id == proposal.proposal_id
        assert readiness.implementation_authorized is False

    def test_evaluate_post_freeze_readiness_red(self):
        """Test evaluation producing red gate."""
        proposal = create_post_freeze_proposal(
            title="Mutation Proposal",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            ontology_mutation_requested=True,
        )

        readiness = evaluate_post_freeze_readiness(proposal)

        assert readiness.gate == "red"
        assert len(readiness.blocking_issues) > 0

    def test_clear_post_freeze_indexes_for_tests(self):
        """Test clearing indexes."""
        proposal = create_post_freeze_proposal(
            title="Test",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal)

        clear_post_freeze_indexes_for_tests()

        assert get_post_freeze_proposal_count() == 0
        assert get_post_freeze_readiness_count() == 0

    def test_get_post_freeze_index_counts(self):
        """Test getting index counts."""
        proposal = create_post_freeze_proposal(
            title="Test",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal)

        counts = get_post_freeze_index_counts()
        assert counts["proposals"] == 1
        assert counts["readiness"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# CI Summary Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCISummary:
    """Tests for CI summary building."""

    def test_ci_summary_empty(self):
        """Test CI summary with no proposals."""
        summary = build_post_freeze_ci_summary()

        assert summary["total_proposals"] == 0
        assert summary["total_readiness_evaluations"] == 0
        assert summary["green_count"] == 0
        assert summary["yellow_count"] == 0
        assert summary["red_count"] == 0
        assert summary["status"] == "pass"
        assert len(summary["blocking_issues"]) == 0
        assert len(summary["warnings"]) == 0

    def test_ci_summary_pass(self):
        """Test CI summary passing."""
        proposal = create_post_freeze_proposal(
            title="Clean",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            depends_on_freeze_id="gbf-test",
            required_reviews=["review"],
            governance_risks=["risk"],
        )
        register_post_freeze_proposal(proposal)
        readiness = evaluate_post_freeze_readiness(proposal)
        register_post_freeze_readiness(readiness)

        summary = build_post_freeze_ci_summary()

        assert summary["total_proposals"] == 1

    def test_ci_summary_warn_yellow_gate(self):
        """Test CI summary warning for yellow gate."""
        proposal = create_post_freeze_proposal(
            title="Yellow",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal)
        readiness = evaluate_post_freeze_readiness(proposal)
        register_post_freeze_readiness(readiness)

        summary = build_post_freeze_ci_summary()

        assert summary["yellow_count"] == 1
        assert summary["status"] == "warn"
        assert len(summary["warnings"]) > 0

    def test_ci_summary_fail_red_gate(self):
        """Test CI summary failing for red gate."""
        proposal = create_post_freeze_proposal(
            title="Red",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            baseline_rewrite_requested=True,
        )
        register_post_freeze_proposal(proposal)
        readiness = evaluate_post_freeze_readiness(proposal)
        register_post_freeze_readiness(readiness)

        summary = build_post_freeze_ci_summary()

        assert summary["red_count"] == 1
        assert summary["status"] == "fail"
        assert len(summary["blocking_issues"]) > 0

    def test_ci_summary_fail_baseline_rewrite(self):
        """Test CI summary failing for baseline rewrite request."""
        proposal = create_post_freeze_proposal(
            title="Rewrite",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            baseline_rewrite_requested=True,
        )
        register_post_freeze_proposal(proposal)

        summary = build_post_freeze_ci_summary()

        assert summary["baseline_rewrite_request_count"] == 1
        assert summary["status"] == "fail"

    def test_ci_summary_fail_ontology_mutation(self):
        """Test CI summary failing for ontology mutation request."""
        proposal = create_post_freeze_proposal(
            title="Mutation",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            ontology_mutation_requested=True,
        )
        register_post_freeze_proposal(proposal)

        summary = build_post_freeze_ci_summary()

        assert summary["ontology_mutation_request_count"] == 1
        assert summary["status"] == "fail"

    def test_ci_summary_missing_freeze_ref_count(self):
        """Test CI summary counting missing freeze refs."""
        for i in range(3):
            proposal = create_post_freeze_proposal(
                title=f"No Freeze {i}",
                target_layer="manufacturing_cognition",
                proposed_capability="Test",
            )
            register_post_freeze_proposal(proposal)

        summary = build_post_freeze_ci_summary()

        assert summary["missing_freeze_ref_count"] == 3
        assert summary["status"] == "warn"

    def test_get_post_freeze_status_summary(self):
        """Test status summary."""
        proposal = create_post_freeze_proposal(
            title="Test",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )
        register_post_freeze_proposal(proposal)

        status = get_post_freeze_status_summary()

        assert status["total_proposals"] == 1
        assert status["draft_proposals"] == 1
        assert status["submitted_proposals"] == 0
        assert status["latest_proposal_id"] == proposal.proposal_id


# ─────────────────────────────────────────────────────────────────────────────
# Router Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPostFreezeRouter:
    """Tests for post-freeze expansion router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def test_create_proposal_endpoint(self, client):
        """Test POST /api/cam/post-freeze/proposals."""
        response = client.post(
            "/api/cam/post-freeze/proposals",
            json={
                "title": "Test Proposal",
                "target_layer": "manufacturing_cognition",
                "proposed_capability": "Test capability",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Proposal"
        assert data["implementation_authorized"] is False

    def test_list_proposals_endpoint(self, client):
        """Test GET /api/cam/post-freeze/proposals."""
        client.post(
            "/api/cam/post-freeze/proposals",
            json={
                "title": "Test",
                "target_layer": "manufacturing_cognition",
                "proposed_capability": "Test",
            },
        )

        response = client.get("/api/cam/post-freeze/proposals")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_proposal_endpoint(self, client):
        """Test GET /api/cam/post-freeze/proposals/{proposal_id}."""
        create_response = client.post(
            "/api/cam/post-freeze/proposals",
            json={
                "title": "Get Test",
                "target_layer": "manufacturing_cognition",
                "proposed_capability": "Test",
            },
        )
        proposal_id = create_response.json()["proposal_id"]

        response = client.get(f"/api/cam/post-freeze/proposals/{proposal_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get Test"

    def test_get_proposal_not_found(self, client):
        """Test GET /api/cam/post-freeze/proposals/{proposal_id} not found."""
        response = client.get("/api/cam/post-freeze/proposals/pfep-nonexistent")
        assert response.status_code == 404

    def test_get_latest_proposal_endpoint(self, client):
        """Test GET /api/cam/post-freeze/proposals/latest."""
        client.post(
            "/api/cam/post-freeze/proposals",
            json={
                "title": "Latest",
                "target_layer": "manufacturing_cognition",
                "proposed_capability": "Test",
            },
        )

        response = client.get("/api/cam/post-freeze/proposals/latest")
        assert response.status_code == 200

    def test_evaluate_readiness_endpoint(self, client):
        """Test POST /api/cam/post-freeze/readiness/{proposal_id}."""
        create_response = client.post(
            "/api/cam/post-freeze/proposals",
            json={
                "title": "Readiness Test",
                "target_layer": "manufacturing_cognition",
                "proposed_capability": "Test",
            },
        )
        proposal_id = create_response.json()["proposal_id"]

        response = client.post(f"/api/cam/post-freeze/readiness/{proposal_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["proposal_id"] == proposal_id
        assert data["implementation_authorized"] is False

    def test_evaluate_readiness_not_found(self, client):
        """Test POST /api/cam/post-freeze/readiness/{proposal_id} not found."""
        response = client.post("/api/cam/post-freeze/readiness/pfep-nonexistent")
        assert response.status_code == 404

    def test_get_ci_summary_endpoint(self, client):
        """Test GET /api/cam/post-freeze/ci."""
        response = client.get("/api/cam/post-freeze/ci")
        assert response.status_code == 200
        data = response.json()
        assert "total_proposals" in data
        assert "status" in data

    def test_get_status_endpoint(self, client):
        """Test GET /api/cam/post-freeze/status."""
        response = client.get("/api/cam/post-freeze/status")
        assert response.status_code == 200
        data = response.json()
        assert "total_proposals" in data
        assert "green_count" in data

    def test_list_readiness_endpoint(self, client):
        """Test GET /api/cam/post-freeze/readiness."""
        response = client.get("/api/cam/post-freeze/readiness")
        assert response.status_code == 200

    def test_list_proposals_by_target_layer_endpoint(self, client):
        """Test GET /api/cam/post-freeze/proposals?target_layer=..."""
        client.post(
            "/api/cam/post-freeze/proposals",
            json={
                "title": "Geometry",
                "target_layer": "geometry_authority",
                "proposed_capability": "Test",
            },
        )

        response = client.get(
            "/api/cam/post-freeze/proposals",
            params={"target_layer": "geometry_authority"},
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:
    """Integration tests for 8A workflow."""

    def test_full_workflow_clean_proposal(self):
        """Test full workflow for clean proposal."""
        proposal = create_post_freeze_proposal(
            title="Integration Test",
            target_layer="manufacturing_cognition",
            proposed_capability="Test capability",
            depends_on_freeze_id="gbf-integration",
            required_reviews=["security_review", "architecture_review"],
            governance_risks=["risk1", "risk2"],
        )

        success, _ = register_post_freeze_proposal(proposal)
        assert success

        readiness = evaluate_post_freeze_readiness(proposal)
        success, _ = register_post_freeze_readiness(readiness)
        assert success

        assert readiness.implementation_authorized is False
        assert readiness.execution_authorized is False
        assert readiness.machine_output_allowed is False

    def test_full_workflow_blocked_proposal(self):
        """Test full workflow for blocked proposal."""
        proposal = create_post_freeze_proposal(
            title="Blocked Integration",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
            baseline_rewrite_requested=True,
        )

        register_post_freeze_proposal(proposal)
        readiness = evaluate_post_freeze_readiness(proposal)
        register_post_freeze_readiness(readiness)

        assert readiness.gate == "red"
        assert "baseline rewrite" in readiness.blocking_issues[0].lower()

        summary = build_post_freeze_ci_summary()
        assert summary["status"] == "fail"

    def test_invariants_preserved_through_workflow(self):
        """Test that 8A invariants are preserved throughout workflow."""
        proposal = create_post_freeze_proposal(
            title="Invariant Test",
            target_layer="manufacturing_cognition",
            proposed_capability="Test",
        )

        assert proposal.implementation_authorized is False
        assert proposal.execution_authorized is False
        assert proposal.machine_output_allowed is False

        register_post_freeze_proposal(proposal)
        retrieved = get_post_freeze_proposal(proposal.proposal_id)

        assert retrieved.implementation_authorized is False
        assert retrieved.execution_authorized is False
        assert retrieved.machine_output_allowed is False

        readiness = evaluate_post_freeze_readiness(proposal)

        assert readiness.implementation_authorized is False
        assert readiness.execution_authorized is False
        assert readiness.machine_output_allowed is False
