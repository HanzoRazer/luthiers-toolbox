"""
Tests for the bridge break angle calculator (v2).

Validates trigonometry, rating thresholds, risk flags, and manufacturer
reference geometries against Carruth empirical 6 deg minimum.

v2 test updates:
    - Uses MINIMUM_ADEQUATE_DEG (6 deg) not fabricated 23-31 deg optimal
    - Rating is binary: adequate | too_shallow | too_steep
    - Tests account for slot_offset_mm in effective distance calculation
"""

import math
import pytest

from app.calculators.bridge_break_angle import (
    BreakAngleInput,
    BreakAngleResult,
    RiskFlag,
    calculate_break_angle,
    calculate_break_angle_v1_compat,
    MINIMUM_ADEQUATE_DEG,
    TOO_STEEP_DEG,
    MINIMUM_PROJECTION_MM,
)


# =============================================================================
# Core trigonometry
# =============================================================================

class TestBreakAngleMath:
    """Verify the basic arctan formula produces correct angles."""

    def test_default_values(self):
        """Default: 5.5mm pin distance - 1.2mm slot offset = 4.3mm effective, 2.5mm projection."""
        result = calculate_break_angle(BreakAngleInput())
        # effective_distance = 5.5 - 1.2 = 4.3 mm
        expected = math.degrees(math.atan2(2.5, 4.3))
        assert result.break_angle_deg == pytest.approx(expected, abs=0.1)
        assert result.rating == "adequate"
        assert result.energy_coupling == "adequate"
        assert result.effective_distance_mm == pytest.approx(4.3, abs=0.01)

    def test_known_45_degrees(self):
        """Equal effective distance and projection -> 45 deg (too steep)."""
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=5.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=5.0,
        ))
        assert result.break_angle_deg == pytest.approx(45.0, abs=0.01)
        assert result.rating == "too_steep"

    def test_very_shallow(self):
        """Large distance, small projection -> shallow angle below 6 deg."""
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=10.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=0.5,
        ))
        expected = math.degrees(math.atan2(0.5, 10.0))
        assert result.break_angle_deg == pytest.approx(expected, abs=0.01)
        assert result.rating == "too_shallow"
        assert result.energy_coupling == "inadequate"

    def test_slot_offset_increases_angle(self):
        """Slot offset reduces effective distance, increasing angle."""
        no_offset = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=6.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=2.0,
        ))
        with_offset = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=6.0,
            slot_offset_mm=1.5,
            saddle_projection_mm=2.0,
        ))
        # With offset, effective_distance = 4.5 instead of 6.0, so angle is steeper
        assert with_offset.break_angle_deg > no_offset.break_angle_deg


# =============================================================================
# Rating thresholds (v2: binary above 6 deg)
# =============================================================================

class TestRatingClassification:
    """Verify correct classification at threshold boundaries."""

    def test_adequate_at_minimum(self):
        """Angle right at MINIMUM_ADEQUATE_DEG should be adequate."""
        d = 6.0
        h = d * math.tan(math.radians(MINIMUM_ADEQUATE_DEG))
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            slot_offset_mm=0.0,
            saddle_projection_mm=h,
        ))
        assert result.rating == "adequate"

    def test_too_shallow_below_minimum(self):
        """Angle below MINIMUM_ADEQUATE_DEG should be too_shallow."""
        d = 10.0
        h = d * math.tan(math.radians(MINIMUM_ADEQUATE_DEG - 1.0))  # 5 deg
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            slot_offset_mm=0.0,
            saddle_projection_mm=h,
        ))
        assert result.rating == "too_shallow"

    def test_adequate_well_above_minimum(self):
        """Angle well above minimum (e.g. 20 deg) is adequate, not optimal."""
        d = 6.0
        h = d * math.tan(math.radians(20.0))
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            slot_offset_mm=0.0,
            saddle_projection_mm=h,
        ))
        # v2: no optimal rating - adequate is adequate
        assert result.rating == "adequate"

    def test_too_steep_at_limit(self):
        """Angle above TOO_STEEP_DEG should be too_steep."""
        d = 5.0
        h = d * math.tan(math.radians(TOO_STEEP_DEG + 1.0))
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=d,
            slot_offset_mm=0.0,
            saddle_projection_mm=h,
        ))
        assert result.rating == "too_steep"


# =============================================================================
# Risk flags
# =============================================================================

class TestRiskFlags:
    """Verify risk flags fire at the correct thresholds."""

    def test_shallow_angle_flag(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=10.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=0.5,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "SHALLOW_ANGLE" in codes

    def test_steep_angle_flag(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=3.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=5.0,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "STEEP_ANGLE" in codes

    def test_adequate_no_angle_flags(self):
        result = calculate_break_angle(BreakAngleInput())
        codes = [f.code for f in result.risk_flags]
        assert "SHALLOW_ANGLE" not in codes
        assert "STEEP_ANGLE" not in codes

    def test_low_projection_flag(self):
        """Projection below MINIMUM_PROJECTION_MM -> warning."""
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=5.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=1.0,  # below 1.6mm
        ))
        codes = [f.code for f in result.risk_flags]
        assert "LOW_PROJECTION" in codes

    def test_adequate_projection_no_flag(self):
        """Projection at or above minimum -> no warning."""
        result = calculate_break_angle(BreakAngleInput(
            saddle_projection_mm=2.5,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "LOW_PROJECTION" not in codes

    def test_low_seat_depth_flag(self):
        """Saddle blank barely taller than projection -> low seat warning."""
        result = calculate_break_angle(BreakAngleInput(
            saddle_projection_mm=3.0,
            saddle_blank_height_mm=6.0,  # seated = 3 mm, slot = 10 mm -> 30pct < 50pct
            saddle_slot_depth_mm=10.0,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "LOW_SEAT_DEPTH" in codes

    def test_adequate_seat_depth_no_flag(self):
        """Standard blank (12mm) with 2.5mm projection -> no seat warning."""
        result = calculate_break_angle(BreakAngleInput())
        codes = [f.code for f in result.risk_flags]
        assert "LOW_SEAT_DEPTH" not in codes


# =============================================================================
# Manufacturer reference geometries (v2: with slot offset)
# =============================================================================

class TestManufacturerReferences:
    """Verify known manufacturer geometries produce adequate angles with v2 model."""

    @pytest.mark.parametrize("name,pin_distance,slot_offset,projection,expected_min,expected_max", [
        # v2: effective_distance = pin_distance - slot_offset
        # Martin D-28: 5.5 - 1.2 = 4.3mm effective, 3.0mm projection -> ~35 deg
        ("Martin D-28",     5.5, 1.2, 3.0, 30.0, 40.0),
        # Taylor 814ce: 5.5 - 1.2 = 4.3mm, 3.2mm projection -> ~37 deg
        ("Taylor 814ce",    5.5, 1.2, 3.2, 32.0, 42.0),
        # Gibson J-45: 6.5 - 1.0 = 5.5mm, 3.0mm projection -> ~29 deg
        ("Gibson J-45",     6.5, 1.0, 3.0, 25.0, 35.0),
        # Collings OM: 5.5 - 1.2 = 4.3mm, 3.0mm projection -> ~35 deg
        ("Collings OM",     5.5, 1.2, 3.0, 30.0, 40.0),
    ])
    def test_manufacturer_angle_in_range(self, name, pin_distance, slot_offset, projection, expected_min, expected_max):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=pin_distance,
            slot_offset_mm=slot_offset,
            saddle_projection_mm=projection,
        ))
        assert expected_min <= result.break_angle_deg <= expected_max, (
            f"{name}: {result.break_angle_deg} deg not in [{expected_min}, {expected_max}]"
        )
        # All these should be adequate
        assert result.rating == "adequate"


# =============================================================================
# Recommendation text
# =============================================================================

class TestRecommendations:
    """Verify recommendations are generated for out-of-spec geometry."""

    def test_shallow_gets_recommendation(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=10.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=0.5,
        ))
        assert result.recommendation is not None
        assert "raise" in result.recommendation.lower() or "projection" in result.recommendation.lower()

    def test_steep_gets_recommendation(self):
        result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=3.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=5.0,
        ))
        assert result.recommendation is not None
        assert "lower" in result.recommendation.lower() or "projection" in result.recommendation.lower()

    def test_adequate_no_recommendation(self):
        result = calculate_break_angle(BreakAngleInput())
        assert result.recommendation is None


# =============================================================================
# Backward compatibility
# =============================================================================

class TestV1Compat:
    """Verify v1 compatibility wrapper works."""

    def test_v1_compat_returns_result(self):
        result = calculate_break_angle_v1_compat(
            pin_to_saddle_center_mm=6.0,
            saddle_protrusion_mm=3.0,
        )
        assert isinstance(result, BreakAngleResult)
        # v1 compat uses slot_offset=0, so effective_distance = pin distance
        assert result.effective_distance_mm == 6.0

    def test_v1_compat_same_as_no_offset(self):
        v1_result = calculate_break_angle_v1_compat(
            pin_to_saddle_center_mm=6.0,
            saddle_protrusion_mm=3.0,
        )
        v2_result = calculate_break_angle(BreakAngleInput(
            pin_to_saddle_center_mm=6.0,
            slot_offset_mm=0.0,
            saddle_projection_mm=3.0,
        ))
        assert v1_result.break_angle_deg == v2_result.break_angle_deg
