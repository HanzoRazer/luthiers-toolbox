"""
IBG Candidate Confidence Vocabulary Migration Tests
====================================================

Dev Order 83: Semantic migration guards for the confidence → candidate_rank rename.

These tests verify:
1. candidate_rank accepts numeric heuristic rank
2. confidence_value still loads for backward compatibility
3. When rank_score is adapted, candidate_rank is populated
4. epistemic_status defaults to "heuristic" for IBG candidates
5. Candidate serialization preserves both old and new fields during transition
6. Candidate documentation/string output does not imply measurement confidence
7. No test or serializer treats candidate_rank as approval
8. No DXF export lifecycle class changes from BLOCKED_PROVENANCE

Author: Dev Order 83 — Convergence Stabilization Cleanup
Date: 2026-05-24
"""

import pytest
from datetime import datetime, timezone

from app.instrument_geometry.body.ibg.body_evidence_candidate import (
    BodyEvidenceCandidate,
    create_candidate_from_evidence,
)
from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    BodyEvidence,
    EvidenceSource,
)
from app.governance import ConfidenceType


def _create_minimal_evidence() -> BodyEvidence:
    """Create minimal BodyEvidence for testing."""
    return BodyEvidence(
        outline_points=[(0, 0), (100, 0), (100, 200), (0, 200), (0, 0)],
        source_type=EvidenceSource.VECTORIZER_DXF,
    )


class TestCandidateRankAcceptsNumericValue:
    """Test 1: candidate_rank accepts numeric heuristic rank."""

    def test_candidate_rank_accepts_float(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.85,
        )
        assert candidate.confidence.value == 0.85

    def test_candidate_rank_accepts_zero(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.0,
        )
        assert candidate.confidence.value == 0.0

    def test_candidate_rank_accepts_one(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=1.0,
        )
        assert candidate.confidence.value == 1.0


class TestConfidenceValueBackwardCompatibility:
    """Test 2: confidence_value still loads for backward compatibility."""

    def test_confidence_value_still_works(self):
        evidence = _create_minimal_evidence()
        # Using deprecated parameter
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            confidence_value=0.75,
        )
        assert candidate.confidence.value == 0.75

    def test_candidate_rank_takes_precedence(self):
        evidence = _create_minimal_evidence()
        # Both provided — candidate_rank should win
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.90,
            confidence_value=0.50,
        )
        assert candidate.confidence.value == 0.90

    def test_default_when_neither_provided(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
        )
        # Default should be 0.5
        assert candidate.confidence.value == 0.5


class TestRankScoreAdaptation:
    """Test 3: When rank_score is adapted, candidate_rank is populated."""

    def test_serialization_includes_candidate_rank(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.85,
        )
        result = candidate.to_dict()
        assert "candidate_rank" in result
        assert result["candidate_rank"] == 0.85

    def test_serialization_includes_rank_is_heuristic_marker(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.85,
        )
        result = candidate.to_dict()
        assert "_rank_is_heuristic" in result
        assert result["_rank_is_heuristic"] is True


class TestEpistemicStatusDefault:
    """Test 4: epistemic_status defaults to "heuristic" for IBG candidates."""

    def test_default_epistemic_status_is_heuristic(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
        )
        assert candidate.confidence.confidence_type == ConfidenceType.HEURISTIC

    def test_serialization_includes_epistemic_status(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
        )
        result = candidate.to_dict()
        assert "epistemic_status" in result
        assert result["epistemic_status"] == "heuristic"


class TestSerializationPreservesBothFields:
    """Test 5: Candidate serialization preserves both old and new fields."""

    def test_to_dict_includes_confidence_block(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.75,
        )
        result = candidate.to_dict()

        # New fields
        assert "candidate_rank" in result
        assert "epistemic_status" in result
        assert "_rank_is_heuristic" in result

        # Original confidence block preserved
        assert "confidence" in result
        assert result["confidence"]["value"] == 0.75


class TestNoMeasurementConfidenceImplication:
    """Test 6: Candidate documentation/string does not imply measurement confidence."""

    def test_confidence_interpretation_includes_disclaimer(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.85,
        )
        interpretation = candidate.confidence.interpretation
        assert "does not imply" in interpretation.lower() or "epistemic_status" in interpretation.lower()

    def test_confidence_type_is_heuristic_not_measurement(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
        )
        # Must NOT be measurement types
        assert candidate.confidence.confidence_type != ConfidenceType.STATISTICAL
        assert candidate.confidence.confidence_type != ConfidenceType.HUMAN_ASSESSED
        assert candidate.confidence.confidence_type == ConfidenceType.HEURISTIC


class TestCandidateRankNotApproval:
    """Test 7: No test or serializer treats candidate_rank as approval."""

    def test_high_rank_does_not_imply_approval(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.99,  # Very high rank
        )

        # Even with high rank, should NOT be approved
        assert not candidate.approved_for_ibg_memory
        assert candidate.review_required

    def test_high_rank_does_not_bypass_review(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=1.0,  # Maximum rank
        )

        # Review is still required
        assert candidate.review_required
        assert not candidate.review_completed

    def test_confidence_implies_correctness_is_false(self):
        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.95,
        )

        # Constitutional safeguards
        assert not candidate.confidence.implies_correctness()
        assert not candidate.confidence.implies_canonicity()
        assert not candidate.confidence.implies_review_bypass()
        assert not candidate.confidence.implies_ibg_eligibility()


class TestBlockedProvenanceUnchanged:
    """Test 8: IBG DXF export lifecycle class remains BLOCKED_PROVENANCE."""

    def test_lifecycle_matrix_documents_blocked_provenance(self):
        """
        Verify that the lifecycle matrix still documents BLOCKED_PROVENANCE
        for IBG save points. This is a documentation/governance test.
        """
        from pathlib import Path

        matrix_path = Path(__file__).parent.parent.parent.parent / "docs" / "governance" / "EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md"

        if not matrix_path.exists():
            pytest.skip("Lifecycle matrix not found at expected path")

        content = matrix_path.read_text(encoding="utf-8")

        # Verify blocked paths are still documented
        assert "BLOCKED_PROVENANCE" in content
        assert "body_contour_solver.py" in content
        assert "arc_reconstructor.py" in content

    def test_ibg_intake_gate_blocks_without_approval(self):
        """Verify that IBG intake gate blocks candidates without human approval."""
        from app.instrument_geometry.body.ibg.ibg_intake_gate import (
            create_default_intake_gate,
            RejectionReason,
        )

        evidence = _create_minimal_evidence()
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
            candidate_rank=0.99,
        )

        gate = create_default_intake_gate()
        result = gate.validate(candidate)

        # Must be blocked (not valid) because review not completed
        assert not result.is_valid
        assert RejectionReason.REVIEW_REQUIRED in result.rejections or \
               RejectionReason.AUTHORITY_INSUFFICIENT in result.rejections
