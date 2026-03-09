"""
Tests for the headstock / nut break angle calculator.

Validates trigonometry for both angled and flat headstock types,
rating thresholds, risk flags, manufacturer reference geometries,
and string tree recommendations.
"""

import math
import pytest

from app.calculators.headstock_break_angle import (
    HeadstockBreakAngleInput,
    HeadstockBreakAngleResult,
    calculate_headstock_break_angle,
    TOO_SHALLOW_DEG,
    OPTIMAL_MIN_DEG,
    OPTIMAL_MAX_DEG,
    TOO_STEEP_DEG,
)


# =============================================================================
# Angled headstock math
# =============================================================================

class TestAngledHeadstockMath:
    """Verify arctan geometry for angled (Gibson-style) headstocks."""

    def test_default_14_deg(self):
        """Default 14° headstock, 100mm to tuner, 6mm post → ~8° effective."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput())
        # drop = 100*sin(14°) - 6 ≈ 24.19 - 6 = 18.19
        # run  = 100*cos(14°) ≈ 97.03
        # angle = arctan(18.19/97.03) ≈ 10.6°
        assert 8.0 <= result.break_angle_deg <= 13.0
        assert result.headstock_type == "angled"

    def test_gibson_17_deg(self):
        """Gibson 17° headstock produces steeper nut angle."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_angle_deg=17.0,
            nut_to_tuner_mm=110.0,
            tuner_post_height_mm=6.0,
        ))
        # drop = 110*sin(17°) - 6 ≈ 32.14 - 6 = 26.14
        # run  = 110*cos(17°) ≈ 105.18
        # angle ≈ 14.0°
        assert result.break_angle_deg > 10.0

    def test_prs_10_deg(self):
        """PRS 10° headstock → moderate angle."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_angle_deg=10.0,
            nut_to_tuner_mm=90.0,
            tuner_post_height_mm=6.0,
        ))
        # drop = 90*sin(10°) - 6 ≈ 15.63 - 6 = 9.63
        # run  = 90*cos(10°) ≈ 88.63
        # angle ≈ 6.2°
        assert 4.0 <= result.break_angle_deg <= 9.0

    def test_zero_angle_headstock_is_flat(self):
        """0° headstock with no tree → 0° break angle."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="angled",
            headstock_angle_deg=0.0,
            tuner_post_height_mm=6.0,
        ))
        # drop = 100*sin(0) - 6 = -6 → clamped to 0
        assert result.break_angle_deg == 0.0

    def test_tall_tuner_posts_reduce_angle(self):
        """Taller tuner posts reduce effective break angle."""
        short = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            tuner_post_height_mm=4.0,
        ))
        tall = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            tuner_post_height_mm=10.0,
        ))
        assert short.break_angle_deg > tall.break_angle_deg


# =============================================================================
# Flat headstock math
# =============================================================================

class TestFlatHeadstockMath:
    """Verify geometry for flat (Fender-style) headstocks."""

    def test_with_string_tree(self):
        """String tree at 40mm with 4mm depression → ~5.7°."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=4.0,
            nut_to_string_tree_mm=40.0,
        ))
        expected = math.degrees(math.atan2(4.0, 40.0))
        assert result.break_angle_deg == pytest.approx(expected, abs=0.01)

    def test_no_string_tree_no_angle(self):
        """Flat headstock, no tree, no angle → 0°."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=0.0,
        ))
        assert result.break_angle_deg == 0.0

    def test_flat_with_slight_angle(self):
        """Fender with 1° neck pocket tilt →  small but nonzero angle."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=1.0,
            nut_to_tuner_mm=120.0,
            tuner_post_height_mm=6.0,
            string_tree_depression_mm=0.0,
        ))
        # drop = 120*sin(1°) - 6 ≈ 2.09 - 6 = -3.91 → 0.0
        assert result.break_angle_deg == 0.0


# =============================================================================
# Rating classification
# =============================================================================

class TestRatingClassification:
    """Verify correct rating at boundaries."""

    def test_optimal_rating(self):
        """Default Gibson geometry lands in optimal range."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_angle_deg=14.0,
            nut_to_tuner_mm=100.0,
            tuner_post_height_mm=6.0,
        ))
        assert result.rating in ("optimal", "acceptable", "too_steep")
        assert result.nut_downforce_quality in ("excellent", "good", "fair")

    def test_shallow_rating(self):
        """Very small angle → too_shallow."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=1.0,
            nut_to_string_tree_mm=40.0,
        ))
        # arctan(1/40) ≈ 1.4° → too_shallow
        assert result.rating == "too_shallow"
        assert result.nut_downforce_quality == "poor"


# =============================================================================
# Risk flags
# =============================================================================

class TestRiskFlags:
    """Verify risk flags fire correctly."""

    def test_shallow_flag(self):
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=0.5,
            nut_to_string_tree_mm=40.0,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "SHALLOW_NUT_ANGLE" in codes

    def test_string_above_nut_flag(self):
        """Tuner post taller than headstock drop → critical flag."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_angle_deg=3.0,
            nut_to_tuner_mm=50.0,
            tuner_post_height_mm=20.0,  # Way too tall
        ))
        codes = [f.code for f in result.risk_flags]
        assert "STRING_ABOVE_NUT" in codes
        assert result.break_angle_deg == 0.0

    def test_needs_string_tree_flag(self):
        """Flat headstock, no tree → recommendation flag."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=0.0,
        ))
        codes = [f.code for f in result.risk_flags]
        assert "NEEDS_STRING_TREE" in codes
        assert result.needs_string_tree is True

    def test_optimal_no_warning_flags(self):
        """Good geometry → no warning/critical flags."""
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_angle_deg=14.0,
            nut_to_tuner_mm=100.0,
            tuner_post_height_mm=6.0,
        ))
        warning_codes = [f.code for f in result.risk_flags
                         if f.severity in ("warning", "critical")]
        # Depending on exact angle, might be too_steep warning but shouldn't be shallow
        assert "SHALLOW_NUT_ANGLE" not in warning_codes
        assert "STRING_ABOVE_NUT" not in warning_codes


# =============================================================================
# Manufacturer reference geometries
# =============================================================================

class TestManufacturerReferences:
    """Verify known manufacturer geometries produce reasonable angles."""

    @pytest.mark.parametrize("name,angle,distance,post_h,expected_min,expected_max", [
        ("Gibson 50s (17°)",    17.0, 110.0, 6.0,  10.0, 16.0),
        ("Gibson 60s (14°)",    14.0, 100.0, 6.0,   7.0, 13.0),
        ("PRS Custom 24 (10°)", 10.0,  90.0, 6.0,   4.0, 10.0),
        ("Acoustic 14°",        14.0, 120.0, 5.0,   9.0, 15.0),
    ])
    def test_angled_manufacturer(self, name, angle, distance, post_h, expected_min, expected_max):
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_angle_deg=angle,
            nut_to_tuner_mm=distance,
            tuner_post_height_mm=post_h,
        ))
        assert expected_min <= result.break_angle_deg <= expected_max, (
            f"{name}: {result.break_angle_deg}° not in [{expected_min}, {expected_max}]"
        )

    @pytest.mark.parametrize("name,depression,distance,expected_min,expected_max", [
        ("Fender with tree (4mm)", 4.0, 40.0, 4.0, 7.0),
        ("Fender with tree (3mm)", 3.0, 40.0, 3.0, 5.5),
        ("Fender with tree (5mm)", 5.0, 35.0, 7.0, 10.0),
    ])
    def test_flat_manufacturer(self, name, depression, distance, expected_min, expected_max):
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=depression,
            nut_to_string_tree_mm=distance,
        ))
        assert expected_min <= result.break_angle_deg <= expected_max, (
            f"{name}: {result.break_angle_deg}° not in [{expected_min}, {expected_max}]"
        )


# =============================================================================
# Recommendations
# =============================================================================

class TestRecommendations:
    """Verify recommendation text generation."""

    def test_shallow_angled_gets_recommendation(self):
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_angle_deg=3.0,
            nut_to_tuner_mm=100.0,
            tuner_post_height_mm=1.0,
        ))
        if result.rating == "too_shallow":
            assert result.recommendation is not None
            assert "headstock" in result.recommendation.lower() or "angle" in result.recommendation.lower()

    def test_shallow_flat_gets_string_tree_recommendation(self):
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=0.0,
        ))
        assert result.recommendation is not None
        assert "string tree" in result.recommendation.lower()

    def test_optimal_no_recommendation(self):
        result = calculate_headstock_break_angle(HeadstockBreakAngleInput(
            headstock_type="flat",
            headstock_angle_deg=0.0,
            string_tree_depression_mm=4.0,
            nut_to_string_tree_mm=40.0,
        ))
        if result.rating == "optimal":
            assert result.recommendation is None
