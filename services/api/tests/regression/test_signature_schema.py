"""
Tests for regression signature schema.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

import pytest
from datetime import datetime

from app.regression.signature_schema import (
    RegressionSignature,
    SignatureComparison,
    ComparisonResult,
)


class TestRegressionSignature:
    """Tests for RegressionSignature base class."""

    def test_create_signature(self):
        """Test basic signature creation."""
        sig = RegressionSignature(
            system_id="TEST_SYSTEM",
            artifact_id="test_artifact_001",
        )
        assert sig.system_id == "TEST_SYSTEM"
        assert sig.artifact_id == "test_artifact_001"
        assert sig.signature_version == "1.0.0"

    def test_signature_with_dimensions(self):
        """Test signature with dimensional data."""
        sig = RegressionSignature(
            system_id="TEST_SYSTEM",
            artifact_id="test_001",
            dimensions={"width": 100.0, "height": 200.0},
        )
        assert sig.dimensions["width"] == 100.0
        assert sig.dimensions["height"] == 200.0

    def test_signature_with_counts(self):
        """Test signature with count data."""
        sig = RegressionSignature(
            system_id="TEST_SYSTEM",
            artifact_id="test_001",
            counts={"entities": 50, "layers": 3},
        )
        assert sig.counts["entities"] == 50
        assert sig.counts["layers"] == 3

    def test_signature_with_flags(self):
        """Test signature with boolean flags."""
        sig = RegressionSignature(
            system_id="TEST_SYSTEM",
            artifact_id="test_001",
            flags={"has_closed": True, "is_valid": False},
        )
        assert sig.flags["has_closed"] is True
        assert sig.flags["is_valid"] is False

    def test_to_dict_roundtrip(self):
        """Test serialization and deserialization."""
        original = RegressionSignature(
            system_id="TEST_SYSTEM",
            artifact_id="test_001",
            dimensions={"width": 100.0},
            counts={"entities": 50},
            flags={"valid": True},
            input_hash="abc123",
            notes="Test note",
        )
        data = original.to_dict()
        restored = RegressionSignature.from_dict(data)

        assert restored.system_id == original.system_id
        assert restored.artifact_id == original.artifact_id
        assert restored.dimensions == original.dimensions
        assert restored.counts == original.counts
        assert restored.flags == original.flags
        assert restored.input_hash == original.input_hash
        assert restored.notes == original.notes


class TestSignatureComparison:
    """Tests for SignatureComparison."""

    def test_create_comparison_match(self):
        """Test creating a match comparison."""
        comp = SignatureComparison(
            result=ComparisonResult.MATCH,
            baseline_id="baseline_001",
            current_id="current_001",
        )
        assert comp.result == ComparisonResult.MATCH
        assert comp.is_acceptable is True

    def test_create_comparison_drift(self):
        """Test creating a drift comparison."""
        comp = SignatureComparison(
            result=ComparisonResult.DRIFT,
            baseline_id="baseline_001",
            current_id="current_001",
            dimension_deltas={"width": 5.0},
            dimension_drift_pct={"width": 2.5},
            warnings=["Width drifted 2.5%"],
        )
        assert comp.result == ComparisonResult.DRIFT
        assert comp.warnings == ["Width drifted 2.5%"]

    def test_comparison_to_dict(self):
        """Test comparison serialization."""
        comp = SignatureComparison(
            result=ComparisonResult.REGRESSION,
            baseline_id="baseline_001",
            current_id="current_001",
            flag_changes={"valid": (True, False)},
            blocking_issues=["Validity changed"],
            is_acceptable=False,
        )
        data = comp.to_dict()

        assert data["result"] == "regression"
        assert data["is_acceptable"] is False
        assert data["flag_changes"]["valid"] == [True, False]


class TestComparisonResult:
    """Tests for ComparisonResult enum."""

    def test_comparison_result_values(self):
        """Test enum values."""
        assert ComparisonResult.MATCH.value == "match"
        assert ComparisonResult.DRIFT.value == "drift"
        assert ComparisonResult.REGRESSION.value == "regression"
        assert ComparisonResult.BASELINE_MISSING.value == "baseline_missing"
