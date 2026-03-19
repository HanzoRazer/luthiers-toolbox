"""
Tests for GEOMETRY-007: Nut Compensation Calculator - Zero-Fret vs Traditional.
"""

import pytest
from app.calculators.nut_compensation_calc import (
    NutCompensationSpec,
    compute_nut_compensation,
    compare_nut_types,
    compute_zero_fret_positions,
    list_nut_types,
    get_nut_type_info,
    COMPENSATION_FACTORS,
)


class TestComputeNutCompensation:
    """Tests for compute_nut_compensation function."""

    def test_traditional_nut_returns_positive_setback(self):
        """Traditional nut with action above fret height should have positive setback."""
        spec = compute_nut_compensation(
            action_at_nut_mm=1.0,
            fret_height_mm=0.8,
            scale_length_mm=648.0,
            nut_type="traditional",
        )
        assert spec.nut_type == "traditional"
        assert spec.setback_mm > 0.0
        assert spec.setback_mm < 1.0  # Should be small fraction of mm

    def test_zero_fret_returns_zero_setback(self):
        """Zero-fret should always have zero setback."""
        spec = compute_nut_compensation(
            action_at_nut_mm=1.0,
            fret_height_mm=0.8,
            scale_length_mm=648.0,
            nut_type="zero_fret",
        )
        assert spec.nut_type == "zero_fret"
        assert spec.setback_mm == 0.0
        assert spec.intonation_error_cents == 0.0

    def test_zero_fret_always_green_gate(self):
        """Zero-fret should always get GREEN gate (no intonation error)."""
        spec = compute_nut_compensation(
            action_at_nut_mm=2.0,  # High action
            fret_height_mm=0.5,
            scale_length_mm=648.0,
            nut_type="zero_fret",
        )
        assert spec.gate == "GREEN"

    def test_compensated_nut_higher_factor_than_traditional(self):
        """Compensated nut should have higher compensation factor."""
        trad = compute_nut_compensation(
            action_at_nut_mm=1.2,
            fret_height_mm=0.8,
            scale_length_mm=648.0,
            nut_type="traditional",
        )
        comp = compute_nut_compensation(
            action_at_nut_mm=1.2,
            fret_height_mm=0.8,
            scale_length_mm=648.0,
            nut_type="compensated",
        )
        # Compensated has higher factor (0.75 vs 0.65)
        assert comp.setback_mm > trad.setback_mm


class TestCompareNutTypes:
    """Tests for compare_nut_types function."""

    def test_returns_three_options(self):
        """Should return specs for all three nut types."""
        results = compare_nut_types(
            action_at_nut_mm=1.0,
            fret_height_mm=0.8,
            scale_length_mm=648.0,
        )
        assert len(results) == 3
        nut_types = {r.nut_type for r in results}
        assert nut_types == {"traditional", "zero_fret", "compensated"}

    def test_sorted_by_error_lowest_first(self):
        """Results should be sorted by intonation error (lowest first)."""
        results = compare_nut_types(
            action_at_nut_mm=1.5,
            fret_height_mm=0.8,
            scale_length_mm=648.0,
        )
        errors = [r.intonation_error_cents for r in results]
        assert errors == sorted(errors)

    def test_zero_fret_always_first_best(self):
        """Zero-fret should always be first (best) option."""
        results = compare_nut_types(
            action_at_nut_mm=1.5,
            fret_height_mm=0.8,
            scale_length_mm=648.0,
        )
        assert results[0].nut_type == "zero_fret"
        assert results[0].intonation_error_cents == 0.0


class TestComputeZeroFretPositions:
    """Tests for compute_zero_fret_positions function."""

    def test_zero_fret_at_origin(self):
        """Zero fret should be at position 0."""
        result = compute_zero_fret_positions(
            scale_length_mm=648.0,
            fret_count=22,
        )
        assert result["zero_fret_position_mm"] == 0.0

    def test_nut_guide_behind_zero_fret(self):
        """Nut guide should be behind (negative) zero fret."""
        result = compute_zero_fret_positions(
            scale_length_mm=648.0,
            fret_count=22,
        )
        assert result["nut_guide_position_mm"] < 0.0
        assert result["nut_guide_offset_mm"] == 1.5

    def test_correct_fret_count(self):
        """Should return correct number of fret positions."""
        result = compute_zero_fret_positions(
            scale_length_mm=648.0,
            fret_count=24,
        )
        assert len(result["fret_positions_mm"]) == 24
        assert result["fret_count"] == 24

    def test_fret_positions_increasing(self):
        """Fret positions should monotonically increase."""
        result = compute_zero_fret_positions(
            scale_length_mm=648.0,
            fret_count=22,
        )
        positions = result["fret_positions_mm"]
        for i in range(1, len(positions)):
            assert positions[i] > positions[i - 1]


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_list_nut_types(self):
        """list_nut_types should return all three types."""
        types = list_nut_types()
        assert "traditional" in types
        assert "zero_fret" in types
        assert "compensated" in types
        assert len(types) == 3

    def test_get_nut_type_info_traditional(self):
        """get_nut_type_info should return correct info for traditional."""
        info = get_nut_type_info("traditional")
        assert info["name"] == "Traditional Nut"
        assert info["compensation_factor"] == COMPENSATION_FACTORS["traditional"]
        assert "pros" in info
        assert "cons" in info

    def test_get_nut_type_info_zero_fret(self):
        """get_nut_type_info should return correct info for zero_fret."""
        info = get_nut_type_info("zero_fret")
        assert info["name"] == "Zero Fret"
        assert info["compensation_factor"] == 0.0
        assert "Perfect open string intonation" in info["pros"]


class TestGateLogic:
    """Tests for gate (GREEN/YELLOW/RED) assignment."""

    def test_low_error_green_gate(self):
        """Low intonation error should get GREEN gate."""
        spec = compute_nut_compensation(
            action_at_nut_mm=0.9,  # Close to fret height
            fret_height_mm=0.8,
            scale_length_mm=648.0,
            nut_type="traditional",
        )
        # Small height difference = low error
        assert spec.gate in ["GREEN", "YELLOW"]

    def test_high_action_traditional_yellow_or_red(self):
        """High action with traditional nut should get YELLOW or RED gate."""
        spec = compute_nut_compensation(
            action_at_nut_mm=2.0,  # High action
            fret_height_mm=0.5,   # Low frets
            scale_length_mm=648.0,
            nut_type="traditional",
        )
        # Large height difference = higher error
        assert spec.gate in ["YELLOW", "RED"]
        assert "compensated" in spec.recommendation.lower() or "zero-fret" in spec.recommendation.lower()
