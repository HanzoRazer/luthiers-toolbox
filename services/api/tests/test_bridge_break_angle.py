"""
Tests for the bridge break angle calculator.

Validates trigonometry, rating thresholds, risk flags, and manufacturer
reference geometries against known good values.
"""

import math
import pytest

from app.calculators.bridge_break_angle import (
    BreakAngleInput,
    BreakAngleResult,
    RiskFlag,
    calculate_break_angle,
    TOO_SHALLOW_DEG,
    OPTIMAL_MIN_DEG,
    OPTIMAL_MAX_DEG,
    TOO_STEEP_DEG,
)


# =============================================================================
# Core trigonometry
# =============================================================================

class TestBreakAngleMath:
    """Verify the basic arctan formula produces correct angles."""

    def test_default_values(self):
        """Default 6mm distance, 3mm protrusion → ~26.6°."""
        result = calculate_break_angle(BreakAngleInput())
        expected = math.degrees(math.atan2(3.0, 6.0))
        assert result.break_angle_deg == pytest.approx(expected, abs=0.01)
        assert result.rating == "optimal"
        assert result.energy_coupling == "excellent"

    def test_known_45_degrees(self):
        """Equal distance and protrusion → 45° (too steep)."""
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=5.0,
            saddle_protrusion_mm=5.0,
        ))
        assert result.break_angle_deg == pytest.approx(45.0, abs=0.01)
        assert result.rating == "too_steep"

    def test_very_shallow(self):
        """Large distance, small protrusion → shallow angle."""
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=10.0,
            saddle_protrusion_mm=1.0,
        ))
        expected = math.degrees(math.atan2(1.0, 10.0))
        assert result.break_angle_deg == pytest.approx(expected, abs=0.01)
        assert result.rating == "too_shallow"


# =============================================================================
# Rating thresholds
# =============================================================================

class TestRatingClassification:
    """Verify correct classification at threshold boundaries."""

    def test_optimal_lower_boundary(self):
        """Angle right at OPTIMAL_MIN should be optimal."""
        d = 6.0
        h = d * math.tan(math.radians(OPTIMAL_MIN_DEG))
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            saddle_protrusion_mm=h,
        ))
        assert result.rating == "optimal"

    def test_optimal_upper_boundary(self):
        """Angle right at OPTIMAL_MAX should be optimal."""
        d = 6.0
        h = d * math.tan(math.radians(OPTIMAL_MAX_DEG))
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            saddle_protrusion_mm=h,
        ))
        assert result.rating == "optimal"

    def test_acceptable_between_shallow_and_optimal(self):
        """Angle between TOO_SHALLOW and OPTIMAL_MIN → acceptable."""
        mid_angle = (TOO_SHALLOW_DEG + OPTIMAL_MIN_DEG) / 2
        d = 6.0
        h = d * math.tan(math.radians(mid_angle))
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            saddle_protrusion_mm=h,
        ))
        assert result.rating == "acceptable"
        assert result.energy_coupling == "good"

    def test_acceptable_between_optimal_and_steep(self):
        """Angle between OPTIMAL_MAX and TOO_STEEP → acceptable."""
        mid_angle = (OPTIMAL_MAX_DEG + TOO_STEEP_DEG) / 2
        d = 6.0
        h = d * math.tan(math.radians(mid_angle))
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            saddle_protrusion_mm=h,
        ))
        assert result.rating == "acceptable"


# =============================================================================
# Risk flags
# =============================================================================

class TestRiskFlags:
    """Verify risk flags fire at the correct thresholds."""

    def test_shallow_angle_flag(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=10.0,
            saddle_protrusion_mm=1.0,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "SHALLOW_ANGLE" in codes

    def test_steep_angle_flag(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=3.0,
            saddle_protrusion_mm=5.0,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "STEEP_ANGLE" in codes

    def test_optimal_no_angle_flags(self):
        result = calculate_break_angle(BreakAngleInput())
        codes = [f.code for f in result.risk_flags]
        assert "SHALLOW_ANGLE" not in codes
        assert "STEEP_ANGLE" not in codes

    def test_low_seat_depth_flag(self):
        """Saddle blank barely taller than protrusion → low seat warning."""
        result = calculate_break_angle(BreakAngleInput(
            saddle_protrusion_mm=3.0,
            saddle_blank_height_mm=6.0,  # seated = 3 mm, slot = 10 mm → 30% < 50%
            saddle_slot_depth_mm=10.0,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "LOW_SEAT_DEPTH" in codes

    def test_adequate_seat_depth_no_flag(self):
        """Standard blank (12mm) with 3mm protrusion → no seat warning."""
        result = calculate_break_angle(BreakAngleInput())
        codes = [f.code for f in result.risk_flags]
        assert "LOW_SEAT_DEPTH" not in codes


# =============================================================================
# Manufacturer reference geometries
# =============================================================================

class TestManufacturerReferences:
    """Verify known manufacturer geometries produce expected angles."""

    @pytest.mark.parametrize("name,distance,protrusion,expected_min,expected_max", [
        ("Martin D-28",     5.5, 3.0, 25.0, 30.0),
        ("Taylor 814ce",    5.5, 3.2, 26.0, 32.0),
        ("Gibson J-45",     6.5, 3.0, 22.0, 28.0),
        ("Collings OM",     5.5, 3.0, 25.0, 30.0),
        ("Generic default", 6.0, 3.0, 25.0, 28.0),
    ])
    def test_manufacturer_angle_in_range(self, name, distance, protrusion, expected_min, expected_max):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=distance,
            saddle_protrusion_mm=protrusion,
        ))
        assert expected_min <= result.break_angle_deg <= expected_max, (
            f"{name}: {result.break_angle_deg}° not in [{expected_min}, {expected_max}]"
        )


# =============================================================================
# Recommendation text
# =============================================================================

class TestRecommendations:
    """Verify recommendations are generated for out-of-spec geometry."""

    def test_shallow_gets_recommendation(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=10.0,
            saddle_protrusion_mm=1.0,
        ))
        assert result.recommendation is not None
        assert "raise" in result.recommendation.lower() or "protrusion" in result.recommendation.lower()

    def test_steep_gets_recommendation(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=3.0,
            saddle_protrusion_mm=5.0,
        ))
        assert result.recommendation is not None
        assert "lower" in result.recommendation.lower() or "protrusion" in result.recommendation.lower()

    def test_optimal_no_recommendation(self):
        result = calculate_break_angle(BreakAngleInput())
        assert result.recommendation is None
