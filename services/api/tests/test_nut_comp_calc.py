"""Tests for nut_comp_calc.py (GEOMETRY-007)."""

import pytest
import math

from app.calculators.nut_comp_calc import (
    NutCompSpec,
    compute_nut_compensation,
    compare_nut_types,
    compute_per_string_compensation,
)


class TestComputeNutCompensation:
    """Tests for compute_nut_compensation function."""

    def test_traditional_returns_positive_compensation(self):
        """Traditional nut should return positive compensation."""
        spec = compute_nut_compensation(
            nut_type="traditional",
            nut_width_mm=3.0,
            break_angle_deg=10.0,
            scale_length_mm=648.0,
        )
        assert spec.nut_type == "traditional"
        assert spec.compensation_mm > 0
        assert spec.gate == "GREEN"

    def test_zero_fret_has_minimal_error(self):
        """Zero-fret should have near-zero pitch error."""
        spec = compute_nut_compensation(
            nut_type="zero_fret",
            nut_width_mm=3.0,
            break_angle_deg=10.0,
            scale_length_mm=648.0,
        )
        assert spec.nut_type == "zero_fret"
        assert spec.open_string_pitch_error_cents == 0.0

    def test_traditional_pitch_error_increases_with_nut_width(self):
        """Wider nut should produce more pitch error."""
        narrow = compute_nut_compensation(
            nut_type="traditional",
            nut_width_mm=2.0,
            break_angle_deg=10.0,
            scale_length_mm=648.0,
        )
        wide = compute_nut_compensation(
            nut_type="traditional",
            nut_width_mm=5.0,
            break_angle_deg=10.0,
            scale_length_mm=648.0,
        )
        assert wide.open_string_pitch_error_cents > narrow.open_string_pitch_error_cents

    def test_effective_scale_traditional_less_than_nominal(self):
        """Traditional nut effective scale should be less than nominal."""
        spec = compute_nut_compensation(
            nut_type="traditional",
            nut_width_mm=3.0,
            break_angle_deg=10.0,
            scale_length_mm=648.0,
        )
        assert spec.effective_scale_length_mm < 648.0

    def test_low_break_angle_triggers_warning(self):
        """Break angle below 3° should trigger warning."""
        spec = compute_nut_compensation(
            nut_type="traditional",
            nut_width_mm=3.0,
            break_angle_deg=2.0,
            scale_length_mm=648.0,
        )
        assert spec.gate == "YELLOW"
        assert "break angle" in spec.recommendation.lower()


class TestCompareNutTypes:
    """Tests for compare_nut_types function."""

    def test_returns_both_types(self):
        """Should return specs for both nut types."""
        result = compare_nut_types(scale_length_mm=648.0)
        assert "traditional" in result
        assert "zero_fret" in result
        assert "comparison" in result

    def test_zero_fret_has_advantage_field(self):
        """Comparison should include zero-fret advantage."""
        result = compare_nut_types(scale_length_mm=648.0)
        assert "zero_fret_advantage" in result["comparison"]

    def test_pitch_error_difference_positive(self):
        """Traditional should have more error than zero-fret."""
        result = compare_nut_types(scale_length_mm=648.0)
        assert result["comparison"]["pitch_error_difference_cents"] > 0


class TestComputePerStringCompensation:
    """Tests for compute_per_string_compensation function."""

    def test_heavier_strings_more_compensation(self):
        """Heavier gauge strings should get more compensation."""
        gauges = [0.254, 0.330, 0.432]  # Light E, A, D
        is_wound = [False, True, True]

        comps = compute_per_string_compensation(
            gauges_mm=gauges,
            is_wound=is_wound,
            nut_width_mm=3.0,
            break_angle_deg=10.0,
        )

        # Each successive string is heavier, should have more compensation
        assert comps[1] > comps[0]
        assert comps[2] > comps[1]

    def test_wound_strings_more_than_plain(self):
        """Wound string should get more compensation than plain of same gauge."""
        gauges = [0.330, 0.330]
        is_wound = [False, True]

        comps = compute_per_string_compensation(
            gauges_mm=gauges,
            is_wound=is_wound,
            nut_width_mm=3.0,
            break_angle_deg=10.0,
        )

        assert comps[1] > comps[0]  # Wound > plain


class TestNutCompSpecDataclass:
    """Tests for NutCompSpec dataclass."""

    def test_to_dict_returns_all_keys(self):
        """to_dict should return all expected keys."""
        spec = NutCompSpec(
            nut_type="traditional",
            compensation_mm=0.456789,
            effective_scale_length_mm=647.543211,
            open_string_pitch_error_cents=2.34567,
            gate="GREEN",
            recommendation="Apply compensation",
        )
        d = spec.to_dict()
        assert d["nut_type"] == "traditional"
        assert d["compensation_mm"] == 0.457  # Rounded to 3 decimals
        assert d["effective_scale_length_mm"] == 647.54  # Rounded to 2 decimals
        assert d["open_string_pitch_error_cents"] == 2.3  # Rounded to 1 decimal
        assert d["gate"] == "GREEN"
        assert d["recommendation"] == "Apply compensation"
