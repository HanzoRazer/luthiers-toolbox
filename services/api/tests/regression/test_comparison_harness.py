"""
Tests for baseline comparison harness.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.regression.signature_schema import ComparisonResult
from app.regression.blueprint_signature import BlueprintOutputSignature
from app.regression.comparison_harness import (
    BaselineComparison,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)


class TestBaselineSaveLoad:
    """Tests for baseline save/load functionality."""

    def test_save_baseline(self):
        """Test saving a baseline signature."""
        with TemporaryDirectory() as tmpdir:
            sig = BlueprintOutputSignature(
                artifact_id="test_001",
                body_width_mm=381.0,
                body_height_mm=520.0,
            )
            path = save_baseline(sig, baseline_dir=Path(tmpdir))

            assert path.exists()
            assert "blueprint_reader_mvp" in str(path)
            assert "test_001.json" in str(path)

    def test_load_baseline(self):
        """Test loading a saved baseline."""
        with TemporaryDirectory() as tmpdir:
            # Save first
            sig = BlueprintOutputSignature(
                artifact_id="test_002",
                body_width_mm=400.0,
                body_height_mm=550.0,
                dxf_entity_count=1000,
            )
            save_baseline(sig, baseline_dir=Path(tmpdir))

            # Load it back
            loaded = load_baseline(
                "test_002",
                "BLUEPRINT_READER_MVP",
                BlueprintOutputSignature,
                baseline_dir=Path(tmpdir),
            )

            assert loaded is not None
            assert loaded.artifact_id == "test_002"
            assert loaded.body_width_mm == 400.0
            assert loaded.dxf_entity_count == 1000

    def test_load_nonexistent_returns_none(self):
        """Test loading nonexistent baseline returns None."""
        with TemporaryDirectory() as tmpdir:
            loaded = load_baseline(
                "nonexistent",
                "BLUEPRINT_READER_MVP",
                BlueprintOutputSignature,
                baseline_dir=Path(tmpdir),
            )
            assert loaded is None

    def test_save_overwrite_protection(self):
        """Test that overwrite=False prevents overwriting."""
        with TemporaryDirectory() as tmpdir:
            sig = BlueprintOutputSignature(
                artifact_id="test_003",
                body_width_mm=381.0,
            )
            save_baseline(sig, baseline_dir=Path(tmpdir))

            with pytest.raises(FileExistsError):
                save_baseline(sig, baseline_dir=Path(tmpdir), overwrite=False)

    def test_save_with_overwrite(self):
        """Test that overwrite=True allows overwriting."""
        with TemporaryDirectory() as tmpdir:
            sig1 = BlueprintOutputSignature(
                artifact_id="test_004",
                body_width_mm=381.0,
            )
            save_baseline(sig1, baseline_dir=Path(tmpdir))

            sig2 = BlueprintOutputSignature(
                artifact_id="test_004",
                body_width_mm=400.0,
            )
            save_baseline(sig2, baseline_dir=Path(tmpdir), overwrite=True)

            loaded = load_baseline(
                "test_004",
                "BLUEPRINT_READER_MVP",
                BlueprintOutputSignature,
                baseline_dir=Path(tmpdir),
            )
            assert loaded.body_width_mm == 400.0


class TestCompareToBaseline:
    """Tests for compare_to_baseline function."""

    def test_baseline_missing(self):
        """Test comparison when baseline doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            current = BlueprintOutputSignature(
                artifact_id="new_artifact",
                body_width_mm=381.0,
                body_height_mm=520.0,
            )
            result = compare_to_baseline(current, baseline_dir=Path(tmpdir))

            assert result.comparison_result == ComparisonResult.BASELINE_MISSING
            assert any("No baseline found" in w for w in result.warnings)

    def test_match_comparison(self):
        """Test comparison when signatures match."""
        with TemporaryDirectory() as tmpdir:
            # Create and save baseline
            baseline = BlueprintOutputSignature(
                artifact_id="match_test",
                body_width_mm=381.0,
                body_height_mm=520.0,
                dxf_entity_count=1000,
                dxf_closed_contours=3,
                svg_present=True,
                selection_score=0.72,
                recommendation_confidence=0.72,
            )
            save_baseline(baseline, baseline_dir=Path(tmpdir))

            # Compare identical signature
            current = BlueprintOutputSignature(
                artifact_id="match_test",
                body_width_mm=381.0,
                body_height_mm=520.0,
                dxf_entity_count=1000,
                dxf_closed_contours=3,
                svg_present=True,
                selection_score=0.72,
                recommendation_confidence=0.72,
            )
            result = compare_to_baseline(current, baseline_dir=Path(tmpdir))

            assert result.comparison_result == ComparisonResult.MATCH
            assert result.is_acceptable is True

    def test_drift_detection(self):
        """Test that dimension drift is detected."""
        with TemporaryDirectory() as tmpdir:
            # Create baseline
            baseline = BlueprintOutputSignature(
                artifact_id="drift_test",
                body_width_mm=381.0,
                body_height_mm=520.0,
                dxf_entity_count=1000,
                dxf_closed_contours=1,
                svg_present=True,
                selection_score=0.5,
                recommendation_confidence=0.5,
            )
            save_baseline(baseline, baseline_dir=Path(tmpdir))

            # Create current with drift
            current = BlueprintOutputSignature(
                artifact_id="drift_test",
                body_width_mm=420.0,  # 10% larger
                body_height_mm=520.0,
                dxf_entity_count=1000,
                dxf_closed_contours=1,
                svg_present=True,
                selection_score=0.5,
                recommendation_confidence=0.5,
            )
            result = compare_to_baseline(
                current,
                baseline_dir=Path(tmpdir),
                dimension_tolerance_pct=5.0,
            )

            assert result.comparison_result == ComparisonResult.DRIFT
            assert len(result.warnings) > 0

    def test_invariant_failures_reported(self):
        """Test that invariant failures are included in results."""
        with TemporaryDirectory() as tmpdir:
            # Create invalid signature (zero dimensions)
            current = BlueprintOutputSignature(
                artifact_id="invalid_test",
                body_width_mm=0.0,
                body_height_mm=0.0,
            )
            result = compare_to_baseline(current, baseline_dir=Path(tmpdir))

            assert result.invariant_results is not None
            assert result.invariant_results.has_critical_failures is True
            assert result.is_acceptable is False


class TestBaselineComparison:
    """Tests for BaselineComparison dataclass."""

    def test_to_dict(self):
        """Test serialization of comparison result."""
        result = BaselineComparison(
            artifact_id="test_001",
            system_id="BLUEPRINT_READER_MVP",
            comparison_result=ComparisonResult.MATCH,
            is_acceptable=True,
        )
        data = result.to_dict()

        assert data["artifact_id"] == "test_001"
        assert data["comparison_result"] == "match"
        assert data["is_acceptable"] is True
