"""
Tests for Constitutional Artifact Body Evidence Adapter

DEV ORDER 2A: Constitutional Adapter Integration

Tests verify:
- Adapter emits BodyEvidenceCandidate with provenance
- IBGIntakeGate blocks by default
- Missing/weak provenance cannot enter IBG memory
- Review-ready JSON output is complete
"""

import pytest
import base64

from app.governance import (
    AuthorityState,
    ReviewDecision,
)

from app.instrument_geometry.body.ibg.body_evidence_candidate import (
    BodyEvidenceCandidate,
)

from app.instrument_geometry.body.ibg.ibg_intake_gate import (
    IntakeRejectionReason,
    create_default_intake_gate,
)

from app.instrument_geometry.body.ibg.morphology_harvest.artifact_body_evidence_adapter import (
    ArtifactBodyEvidenceAdapter,
    ConstitutionalAdapterResult,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def adapter():
    """Create adapter instance."""
    return ArtifactBodyEvidenceAdapter()


@pytest.fixture
def minimal_dxf_base64():
    """Create minimal valid DXF content as base64."""
    dxf_content = """0
SECTION
2
HEADER
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
0
10
0.0
20
0.0
11
350.0
21
0.0
0
LINE
8
0
10
350.0
20
0.0
11
350.0
21
450.0
0
LINE
8
0
10
350.0
20
450.0
11
0.0
21
450.0
0
LINE
8
0
10
0.0
20
450.0
11
0.0
21
0.0
0
ENDSEC
0
EOF
"""
    return base64.b64encode(dxf_content.encode()).decode()


@pytest.fixture
def empty_svg():
    """Create empty SVG that will fail parsing."""
    return "<svg></svg>"


# =============================================================================
# Constitutional Adapter Output Tests
# =============================================================================

class TestConstitutionalAdapterOutput:
    """Tests for BodyEvidenceCandidate production."""

    def test_produces_body_evidence_candidate(self, adapter, minimal_dxf_base64):
        """Adapter produces BodyEvidenceCandidate, not plain BodyEvidence."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert result.success is True
        assert result.candidate is not None
        assert isinstance(result.candidate, BodyEvidenceCandidate)

    def test_candidate_has_provenance(self, adapter, minimal_dxf_base64):
        """Candidate includes provenance record."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert result.candidate.provenance is not None
        assert result.candidate.provenance.source_artifact == "/blueprints/test_guitar.dxf"
        assert len(result.candidate.provenance.transformation_history) >= 1

    def test_candidate_has_confidence_declaration(self, adapter, minimal_dxf_base64):
        """Candidate includes typed confidence declaration."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert result.candidate.confidence is not None
        assert result.candidate.confidence.origin == "artifact_body_evidence_adapter"
        assert 0.0 <= result.candidate.confidence.value <= 1.0

    def test_defaults_to_advisory_candidate(self, adapter, minimal_dxf_base64):
        """Candidate defaults to advisory_candidate authority."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert result.candidate.authority_state == AuthorityState.ADVISORY_CANDIDATE

    def test_review_required_true(self, adapter, minimal_dxf_base64):
        """Candidate has review_required = True."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert result.candidate.review_required is True

    def test_approved_for_ibg_memory_false(self, adapter, minimal_dxf_base64):
        """Candidate has approved_for_ibg_memory = False."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert result.candidate.approved_for_ibg_memory is False


# =============================================================================
# Gate Blocking Tests
# =============================================================================

class TestGateBlocking:
    """Tests that IBGIntakeGate blocks by default."""

    def test_gate_blocks_new_candidate(self, adapter, minimal_dxf_base64):
        """Gate blocks newly created candidate."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert result.gate_result is not None
        assert result.gate_result.is_valid is False

    def test_gate_rejects_insufficient_authority(self, adapter, minimal_dxf_base64):
        """Gate rejects for insufficient authority."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert IntakeRejectionReason.AUTHORITY_INSUFFICIENT in result.gate_result.rejections

    def test_gate_rejects_pending_review(self, adapter, minimal_dxf_base64):
        """Gate rejects for pending review."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert IntakeRejectionReason.REVIEW_REQUIRED in result.gate_result.rejections

    def test_gate_passes_after_approval(self, adapter, minimal_dxf_base64):
        """Gate passes after human approval."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        # Approve the candidate
        result.candidate.record_review(
            "human:test_reviewer",
            ReviewDecision.APPROVE,
            "Verified body outline",
        )

        # Re-validate
        gate = create_default_intake_gate()
        new_result = gate.validate(result.candidate)

        assert new_result.is_valid is True


# =============================================================================
# Topology Integrity Tests
# =============================================================================

class TestTopologyIntegrity:
    """Tests for topology integrity scoring and downgrade."""

    def test_topology_integrity_computed(self, adapter, minimal_dxf_base64):
        """Topology integrity is computed and included."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        assert 0.0 <= result.topology_integrity <= 1.0

    def test_poor_topology_downgrades_to_sandbox(self, adapter):
        """Poor topology degrades authority to sandbox_experimental.

        This test IS the poor-topology case, so the preconditions are asserted
        unconditionally (not guarded behind `if`) — a guarded version would pass
        vacuously if the fixture ever stopped producing a poor-topology
        candidate. The empty SVG parses to a body with zero topology integrity.
        """
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=None,
            svg_content="<svg></svg>",  # parses to an empty, zero-integrity body
            source_file="/blueprints/empty.svg",
            source_mode="pdf",
        )

        # Preconditions the downgrade depends on — asserted, not guarded.
        assert result.success is True
        assert result.candidate is not None
        assert result.topology_integrity < 0.5

        # The candidate must end up downgraded.
        assert result.candidate.authority_state == AuthorityState.SANDBOX_EXPERIMENTAL

        # And the downgrade must be an auditable, inspectable transition: the
        # last recorded transition is the poor-topology downgrade, carrying the
        # topology score in its derivation context.
        downgrade = result.candidate.authority.transition_history[-1]
        assert downgrade.from_state == AuthorityState.ADVISORY_CANDIDATE
        assert downgrade.to_state == AuthorityState.SANDBOX_EXPERIMENTAL
        assert downgrade.actor == "system:artifact_body_evidence_adapter"
        assert downgrade.reason == "poor_topology_integrity"
        assert downgrade.derivation_context is not None
        assert downgrade.derivation_context["topology_integrity"] == result.topology_integrity


# =============================================================================
# Review-Ready JSON Tests
# =============================================================================

class TestReviewReadyJSON:
    """Tests for review-ready JSON output."""

    def test_review_json_has_required_fields(self, adapter, minimal_dxf_base64):
        """Review JSON includes all required fields."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        review_json = result.to_review_json()

        required_fields = [
            "candidate_id",
            "source_dxf",
            "provenance",
            "authority_state",
            "confidence_declaration",
            "topology_integrity",
            "gate_decision",
            "review_required",
            "review_notes_placeholder",
        ]

        for field in required_fields:
            assert field in review_json, f"Missing required field: {field}"

    def test_review_json_gate_decision_structure(self, adapter, minimal_dxf_base64):
        """Gate decision has proper structure."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        review_json = result.to_review_json()
        gate_decision = review_json["gate_decision"]

        assert "is_valid" in gate_decision
        assert "rejections" in gate_decision
        assert "gate_results" in gate_decision
        assert gate_decision["is_valid"] is False

    def test_review_json_provenance_included(self, adapter, minimal_dxf_base64):
        """Provenance is included in review JSON."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/test_guitar.dxf",
            source_mode="pdf",
        )

        review_json = result.to_review_json()

        assert review_json["provenance"] is not None
        assert "source_artifact" in review_json["provenance"]
        assert "transformation_history" in review_json["provenance"]


# =============================================================================
# Failure Mode Tests
# =============================================================================

class TestFailureModes:
    """Tests for failure scenarios."""

    def test_no_artifact_fails(self, adapter):
        """No artifact provided fails gracefully."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=None,
            svg_content=None,
            source_file="/blueprints/missing.dxf",
            source_mode="pdf",
        )

        assert result.success is False
        assert result.candidate is None
        assert result.errors is not None

    def test_invalid_dxf_handles_gracefully(self, adapter):
        """Invalid DXF content handles gracefully."""
        invalid_dxf = base64.b64encode(b"not a valid dxf").decode()

        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=invalid_dxf,
            source_file="/blueprints/invalid.dxf",
            source_mode="pdf",
        )

        # Should either fail or produce low-quality result
        if result.success:
            assert result.topology_integrity < 1.0

    def test_failed_result_review_json(self, adapter):
        """Failed result produces valid review JSON."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=None,
            svg_content=None,
            source_file="/blueprints/missing.dxf",
            source_mode="pdf",
        )

        review_json = result.to_review_json()

        assert review_json["success"] is False
        assert "errors" in review_json


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for full flow."""

    def test_full_flow_blocked_to_approved(self, adapter, minimal_dxf_base64):
        """Full flow: create → blocked → approve → pass gate."""
        # Create candidate
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/full_flow_test.dxf",
            source_mode="pdf",
        )

        assert result.success is True
        assert result.gate_result.is_valid is False

        # Approve
        result.candidate.record_review(
            "human:integration_test",
            ReviewDecision.APPROVE,
            "Full flow test approval",
        )

        # Re-validate
        gate = create_default_intake_gate()
        final_result = gate.validate(result.candidate)

        assert final_result.is_valid is True
        assert result.candidate.approved_for_ibg_memory is True

    def test_candidate_cannot_bypass_gate(self, adapter, minimal_dxf_base64):
        """Candidate cannot bypass gate without approval."""
        result = adapter.from_vectorizer_response_constitutional(
            dxf_base64=minimal_dxf_base64,
            source_file="/blueprints/bypass_test.dxf",
            source_mode="pdf",
        )

        # Try to use candidate without approval
        from app.instrument_geometry.body.ibg.body_evidence_candidate import CandidateNotApprovedError

        with pytest.raises(CandidateNotApprovedError):
            result.candidate.require_approval("populate IBG memory")
