"""
Tests for regression invariants.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

import pytest

from app.regression.blueprint_signature import BlueprintOutputSignature
from app.regression.invariants import (
    InvariantCheck,
    InvariantResult,
    InvariantSeverity,
    InvariantCheckResults,
    BLUEPRINT_READER_INVARIANTS,
    check_invariants,
)


class TestInvariantCheck:
    """Tests for InvariantCheck."""

    def test_passing_invariant(self):
        """Test an invariant that passes."""
        check = InvariantCheck(
            id="TEST_001",
            description="Test check",
            severity=InvariantSeverity.CRITICAL,
            check_fn=lambda sig: sig.body_width_mm > 0,
            failure_message="Width must be positive",
        )
        sig = BlueprintOutputSignature(
            artifact_id="test",
            body_width_mm=100.0,
        )
        result = check.check(sig)

        assert result.passed is True
        assert result.message is None

    def test_failing_invariant(self):
        """Test an invariant that fails."""
        check = InvariantCheck(
            id="TEST_001",
            description="Test check",
            severity=InvariantSeverity.CRITICAL,
            check_fn=lambda sig: sig.body_width_mm > 0,
            failure_message="Width must be positive",
        )
        sig = BlueprintOutputSignature(
            artifact_id="test",
            body_width_mm=0.0,
        )
        result = check.check(sig)

        assert result.passed is False
        assert result.message == "Width must be positive"

    def test_invariant_with_exception(self):
        """Test invariant that raises exception."""
        check = InvariantCheck(
            id="TEST_001",
            description="Test check",
            severity=InvariantSeverity.WARNING,
            check_fn=lambda sig: 1 / 0,  # Will raise
            failure_message="Never shown",
        )
        sig = BlueprintOutputSignature(artifact_id="test")
        result = check.check(sig)

        assert result.passed is False
        assert result.severity == InvariantSeverity.CRITICAL
        assert "error" in result.message.lower()


class TestBlueprintReaderInvariants:
    """Tests for Blueprint Reader invariants."""

    def test_valid_signature_passes_all(self):
        """Test that a valid signature passes all invariants."""
        sig = BlueprintOutputSignature(
            artifact_id="valid_test",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=1247,
            dxf_closed_contours=3,
            svg_present=True,
            candidate_count=12,
            selected_index=3,
            selection_score=0.72,
            recommendation_confidence=0.72,
            recommendation_action="accept",
        )
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert results.all_passed is True
        assert results.critical_failures == 0

    def test_zero_dimensions_fails(self):
        """Test that zero dimensions trigger failure."""
        sig = BlueprintOutputSignature(
            artifact_id="zero_dims",
            body_width_mm=0.0,
            body_height_mm=0.0,
        )
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert results.all_passed is False
        assert results.critical_failures > 0

    def test_empty_dxf_fails(self):
        """Test that empty DXF triggers failure."""
        sig = BlueprintOutputSignature(
            artifact_id="empty_dxf",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=0,
        )
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert results.has_critical_failures is True

    def test_invalid_selection_index_fails(self):
        """Test that invalid selection index triggers failure."""
        sig = BlueprintOutputSignature(
            artifact_id="bad_selection",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=100,
            candidate_count=5,
            selected_index=10,  # Out of bounds
        )
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert results.has_critical_failures is True

    def test_out_of_bounds_confidence_fails(self):
        """Test that confidence > 1.0 triggers failure."""
        sig = BlueprintOutputSignature(
            artifact_id="bad_confidence",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=100,
            selection_score=1.5,  # Out of bounds
        )
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert results.has_critical_failures is True

    def test_accepted_without_artifacts_fails(self):
        """Test that 'accept' without artifacts triggers failure."""
        sig = BlueprintOutputSignature(
            artifact_id="missing_artifacts",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=0,
            svg_present=False,
            recommendation_action="accept",
        )
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert results.has_critical_failures is True


class TestCheckInvariants:
    """Tests for check_invariants function."""

    def test_returns_results_object(self):
        """Test that function returns InvariantCheckResults."""
        sig = BlueprintOutputSignature(artifact_id="test")
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert isinstance(results, InvariantCheckResults)
        assert results.total_checks == len(BLUEPRINT_READER_INVARIANTS)

    def test_counts_are_correct(self):
        """Test that pass/fail counts are accurate."""
        sig = BlueprintOutputSignature(
            artifact_id="test",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=100,
            dxf_closed_contours=1,
            svg_present=True,
            selection_score=0.5,
            recommendation_confidence=0.5,
        )
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)

        assert results.passed + results.failed == results.total_checks

    def test_to_dict_serialization(self):
        """Test results can be serialized."""
        sig = BlueprintOutputSignature(artifact_id="test")
        results = check_invariants(sig, BLUEPRINT_READER_INVARIANTS)
        data = results.to_dict()

        assert "system_id" in data
        assert "total_checks" in data
        assert "results" in data
        assert isinstance(data["results"], list)
