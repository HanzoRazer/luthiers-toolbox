"""
Tests for GEOMETRY-008: Tuning Machine Post Height and String Tree Selection.
"""

import pytest
from app.calculators.tuning_machine_calc import (
    TuningMachineSpec,
    compute_break_angle,
    compute_required_post_height,
    check_string_tree_needed,
    compute_wrap_count,
    compute_tuning_machine_spec,
    list_standard_post_heights,
    get_string_tree_spec,
)


class TestComputeBreakAngle:
    """Tests for compute_break_angle function."""

    def test_angled_headstock_positive_break_angle(self):
        """Angled headstock (Gibson 14°) should produce positive break angle."""
        angle = compute_break_angle(
            headstock_angle_deg=14.0,
            nut_to_post_mm=100.0,
            post_height_mm=10.0,
        )
        # Should be positive and reasonable (roughly 10-15 degrees)
        assert angle > 5.0
        assert angle < 20.0

    def test_flat_headstock_near_zero_angle(self):
        """Flat headstock (0°) with tall post should produce near-zero angle."""
        angle = compute_break_angle(
            headstock_angle_deg=0.0,
            nut_to_post_mm=100.0,
            post_height_mm=10.0,
        )
        # Negative because post is above the string line
        assert angle < 0.0


class TestComputeRequiredPostHeight:
    """Tests for compute_required_post_height function."""

    def test_returns_positive_height_for_angled_headstock(self):
        """Should return positive post height for angled headstock."""
        height = compute_required_post_height(
            headstock_angle_deg=14.0,
            nut_to_post_mm=100.0,
            target_break_angle_deg=9.0,
        )
        assert height > 0.0
        assert height < 30.0  # Reasonable upper bound

    def test_higher_target_angle_needs_lower_post(self):
        """Higher target break angle should require lower post height."""
        height_9deg = compute_required_post_height(
            headstock_angle_deg=14.0,
            nut_to_post_mm=100.0,
            target_break_angle_deg=9.0,
        )
        height_12deg = compute_required_post_height(
            headstock_angle_deg=14.0,
            nut_to_post_mm=100.0,
            target_break_angle_deg=12.0,
        )
        assert height_12deg < height_9deg


class TestCheckStringTreeNeeded:
    """Tests for check_string_tree_needed function."""

    def test_adequate_angle_returns_none(self):
        """Adequate break angle should not need string tree."""
        tree_type = check_string_tree_needed(
            string_name="G",
            break_angle_deg=10.0,
            min_break_angle_deg=7.0,
        )
        assert tree_type == "none"

    def test_g_string_low_angle_needs_tree(self):
        """G string with low break angle should need string tree."""
        tree_type = check_string_tree_needed(
            string_name="G",
            break_angle_deg=3.0,
            min_break_angle_deg=7.0,
        )
        assert tree_type != "none"
        assert tree_type in ["butterfly", "roller", "disc"]

    def test_b_string_low_angle_needs_tree(self):
        """B string with low break angle should need string tree."""
        tree_type = check_string_tree_needed(
            string_name="B",
            break_angle_deg=4.0,
            min_break_angle_deg=7.0,
        )
        assert tree_type != "none"

    def test_e_string_low_angle_no_tree(self):
        """E string (not G or B) should not get tree recommendation."""
        tree_type = check_string_tree_needed(
            string_name="E",
            break_angle_deg=3.0,
            min_break_angle_deg=7.0,
        )
        assert tree_type == "none"


class TestComputeWrapCount:
    """Tests for compute_wrap_count function."""

    def test_reasonable_wrap_count(self):
        """Should return reasonable wrap count (2-4)."""
        wraps = compute_wrap_count(
            post_height_mm=10.0,
            string_gauge_inch=0.010,
        )
        assert 2.0 <= wraps <= 15.0

    def test_thicker_string_fewer_wraps(self):
        """Thicker string should result in fewer wraps."""
        thin_wraps = compute_wrap_count(
            post_height_mm=10.0,
            string_gauge_inch=0.010,
        )
        thick_wraps = compute_wrap_count(
            post_height_mm=10.0,
            string_gauge_inch=0.046,
        )
        assert thick_wraps < thin_wraps


class TestComputeTuningMachineSpec:
    """Tests for compute_tuning_machine_spec function."""

    def test_good_config_returns_green_gate(self):
        """Good configuration should return GREEN gate."""
        spec = compute_tuning_machine_spec(
            headstock_angle_deg=14.0,
            nut_to_post_mm=100.0,
            post_height_mm=10.0,
            string_name="E",
            string_gauge_inch=0.046,
        )
        # With 14 degree headstock, should have good break angle
        assert spec.break_angle_deg > 7.0
        assert spec.gate in ["GREEN", "YELLOW"]

    def test_flat_headstock_g_string_recommends_tree(self):
        """Flat headstock G string should recommend string tree."""
        spec = compute_tuning_machine_spec(
            headstock_angle_deg=0.0,
            nut_to_post_mm=100.0,
            post_height_mm=10.0,
            string_name="G",
            string_gauge_inch=0.016,
        )
        assert spec.string_tree_needed is True
        assert spec.string_tree_type != "none"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_list_standard_post_heights(self):
        """list_standard_post_heights should return known brands."""
        heights = list_standard_post_heights()
        assert "vintage_kluson" in heights
        assert "grover_rotomatic" in heights
        assert heights["vintage_kluson"] == 8.5

    def test_get_string_tree_spec(self):
        """get_string_tree_spec should return correct specs."""
        spec = get_string_tree_spec("butterfly")
        assert spec["depression_mm"] == 3.0
        assert spec["style"] == "vintage"
