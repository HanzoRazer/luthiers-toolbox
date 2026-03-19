"""
Tests for string_tension.py — CONSTRUCTION-004.

Validates the T = (2 × f × L)² × μ physics formula and preset string sets.

Expected results (empirical verification):
- Gibson 24.75" light gauge → total ~165 lbs
- Taylor 25.5" light gauge → total ~180 lbs
- Higher gauge → higher tension
- Longer scale → higher tension
- Doubled scale → quadrupled tension (physics check)
"""

import pytest
import math

from app.calculators.string_tension import (
    compute_string_tension,
    compute_string_tension_from_spec,
    compute_set_tension,
    compute_linear_density,
    total_tension_lbs,
    get_preset_set,
    list_preset_sets,
    StringSpec,
    TensionResult,
    SetTensionResult,
    LIGHT_012,
    MEDIUM_013,
    EXTRA_LIGHT_010,
    STANDARD_TUNING_HZ,
    RHO_STEEL_KG_M3,
    INCH_TO_M,
    STRING_SETS,
    SCALE_LENGTHS_MM,
)


class TestLinearDensity:
    """Test linear mass density calculation."""

    def test_plain_string_density_formula(self):
        """Plain string: μ = π × (d/2)² × ρ_steel."""
        gauge_inch = 0.012
        mu = compute_linear_density(gauge_inch, is_wound=False)

        # Manual calculation
        diameter_m = gauge_inch * INCH_TO_M
        radius_m = diameter_m / 2.0
        area_m2 = math.pi * radius_m ** 2
        expected_mu = area_m2 * RHO_STEEL_KG_M3

        assert abs(mu - expected_mu) < 1e-10

    def test_wound_string_uses_empirical_weight(self):
        """Wound strings use empirical unit weight table (not solid steel calc)."""
        gauge_inch = 0.024
        mu_wound = compute_linear_density(gauge_inch, is_wound=True)

        # Wound string should have positive mass
        assert mu_wound > 0
        # Should be in realistic range for phosphor bronze acoustic strings
        # 0.024" wound: ~0.003 kg/m (from D'Addario PB024)
        assert 0.002 < mu_wound < 0.005

    def test_larger_gauge_higher_density(self):
        """Larger gauge → higher linear density."""
        mu_012 = compute_linear_density(0.012, is_wound=False)
        mu_016 = compute_linear_density(0.016, is_wound=False)

        assert mu_016 > mu_012


class TestSingleStringTension:
    """Test single string tension calculation."""

    def test_basic_tension_calculation(self):
        """Verify T = (2 × f × L)² × μ formula."""
        result = compute_string_tension(
            gauge_inch=0.012,
            is_wound=False,
            frequency_hz=329.63,  # E4
            scale_length_mm=647.7,  # 25.5"
        )

        assert isinstance(result, TensionResult)
        assert result.tension_n > 0
        assert result.tension_lb > 0
        assert result.linear_density_kg_m > 0

    def test_tension_lb_and_n_consistent(self):
        """tension_lb and tension_n should be consistent (N × 0.2248 = lbs)."""
        result = compute_string_tension(
            gauge_inch=0.012,
            is_wound=False,
            frequency_hz=329.63,
            scale_length_mm=647.7,
        )

        expected_lb = result.tension_n * 0.224809
        assert abs(result.tension_lb - expected_lb) < 0.1

    def test_higher_gauge_higher_tension(self):
        """Heavier gauge at same pitch → higher tension."""
        result_012 = compute_string_tension(
            gauge_inch=0.012,
            is_wound=False,
            frequency_hz=329.63,
            scale_length_mm=647.7,
        )

        result_013 = compute_string_tension(
            gauge_inch=0.013,
            is_wound=False,
            frequency_hz=329.63,
            scale_length_mm=647.7,
        )

        assert result_013.tension_lb > result_012.tension_lb

    def test_longer_scale_higher_tension(self):
        """Longer scale length at same pitch → higher tension."""
        result_gibson = compute_string_tension(
            gauge_inch=0.012,
            is_wound=False,
            frequency_hz=329.63,
            scale_length_mm=628.65,  # 24.75" Gibson
        )

        result_fender = compute_string_tension(
            gauge_inch=0.012,
            is_wound=False,
            frequency_hz=329.63,
            scale_length_mm=647.7,  # 25.5" Fender
        )

        assert result_fender.tension_lb > result_gibson.tension_lb

    def test_doubled_scale_quadrupled_tension(self):
        """
        Physics check: T ∝ L².
        Doubling scale length should quadruple tension (at same frequency).
        """
        result_base = compute_string_tension(
            gauge_inch=0.012,
            is_wound=False,
            frequency_hz=329.63,
            scale_length_mm=325.0,
        )

        result_doubled = compute_string_tension(
            gauge_inch=0.012,
            is_wound=False,
            frequency_hz=329.63,
            scale_length_mm=650.0,  # 2x scale
        )

        # Should be approximately 4x tension
        ratio = result_doubled.tension_n / result_base.tension_n
        assert abs(ratio - 4.0) < 0.01


class TestStringSpec:
    """Test StringSpec-based tension calculation."""

    def test_compute_from_spec(self):
        """compute_string_tension_from_spec populates name and note."""
        spec = StringSpec(
            name="1",
            gauge_inch=0.012,
            is_wound=False,
            note="E4",
            frequency_hz=329.63,
        )

        result = compute_string_tension_from_spec(spec, scale_length_mm=647.7)

        assert result.name == "1"
        assert result.note == "E4"
        assert result.gauge_inch == 0.012
        assert result.tension_lb > 0


class TestSetTension:
    """Test full string set tension calculations."""

    def test_light_gauge_gibson_scale(self):
        """
        Gibson 24.75" with light gauge.

        D'Addario EJ16 tensions vary by exact string construction.
        Total should be in the 150-220 lb range for light acoustic set.
        Key: result should be consistent and physically realistic.
        """
        result = compute_set_tension(LIGHT_012, scale_length_mm=628.65)

        assert isinstance(result, SetTensionResult)
        assert len(result.strings) == 6
        # Broad empirical range for light acoustic set
        assert 150 < result.total_tension_lb < 220

    def test_light_gauge_taylor_scale(self):
        """
        Taylor 25.5" with light gauge.

        Longer scale = higher tension than Gibson.
        """
        result = compute_set_tension(LIGHT_012, scale_length_mm=647.7)

        assert isinstance(result, SetTensionResult)
        # Should be higher than Gibson due to longer scale
        assert 160 < result.total_tension_lb < 230

    def test_medium_gauge_higher_than_light(self):
        """Medium gauge should produce higher tension than light."""
        light = compute_set_tension(LIGHT_012, scale_length_mm=647.7)
        medium = compute_set_tension(MEDIUM_013, scale_length_mm=647.7)

        assert medium.total_tension_lb > light.total_tension_lb

    def test_extra_light_lower_than_light(self):
        """Extra light gauge should produce lower tension than light."""
        extra_light = compute_set_tension(EXTRA_LIGHT_010, scale_length_mm=647.7)
        light = compute_set_tension(LIGHT_012, scale_length_mm=647.7)

        assert extra_light.total_tension_lb < light.total_tension_lb

    def test_set_name_passed_through(self):
        """set_name should be present in result."""
        result = compute_set_tension(LIGHT_012, scale_length_mm=647.7, set_name="light_012")

        assert result.set_name == "light_012"

    def test_total_tension_equals_sum(self):
        """total_tension_lb should equal sum of individual string tensions."""
        result = compute_set_tension(LIGHT_012, scale_length_mm=647.7)

        manual_sum = sum(s.tension_lb for s in result.strings)
        assert abs(result.total_tension_lb - manual_sum) < 0.1


class TestPresets:
    """Test preset string sets and scale lengths."""

    def test_list_preset_sets(self):
        """list_preset_sets returns expected set names."""
        presets = list_preset_sets()

        assert "light_012" in presets
        assert "medium_013" in presets
        assert "extra_light_010" in presets
        assert "classical_normal" in presets

    def test_get_preset_set_valid(self):
        """get_preset_set returns correct string set."""
        strings = get_preset_set("light_012")

        assert len(strings) == 6
        assert all(isinstance(s, StringSpec) for s in strings)

    def test_get_preset_set_invalid(self):
        """get_preset_set raises ValueError for unknown set."""
        with pytest.raises(ValueError, match="Unknown string set"):
            get_preset_set("nonexistent_set")

    def test_scale_lengths_present(self):
        """Common scale lengths are defined."""
        assert "fender_standard" in SCALE_LENGTHS_MM
        assert "gibson_standard" in SCALE_LENGTHS_MM
        assert "classical" in SCALE_LENGTHS_MM

        assert SCALE_LENGTHS_MM["fender_standard"] == 647.7
        assert SCALE_LENGTHS_MM["gibson_standard"] == 628.65


class TestHelperFunctions:
    """Test utility functions."""

    def test_total_tension_lbs(self):
        """total_tension_lbs sums tension from list of TensionResult."""
        results = [
            TensionResult(
                name="1", gauge_inch=0.012, tension_lb=20.0,
                tension_n=89.0, linear_density_kg_m=0.0005, note="E4"
            ),
            TensionResult(
                name="2", gauge_inch=0.016, tension_lb=25.0,
                tension_n=111.0, linear_density_kg_m=0.0008, note="B3"
            ),
        ]

        total = total_tension_lbs(results)
        assert total == 45.0


class TestPhysicsValidation:
    """Validate physics assumptions."""

    def test_steel_density_realistic(self):
        """Steel density constant is realistic (7800-7900 kg/m³)."""
        assert 7800 < RHO_STEEL_KG_M3 < 7900

    def test_standard_tuning_frequencies(self):
        """Standard tuning frequencies are correct."""
        # E2 ≈ 82.41 Hz
        assert abs(STANDARD_TUNING_HZ["E2"] - 82.41) < 0.01
        # A2 = 110 Hz (reference pitch A440 / 4)
        assert STANDARD_TUNING_HZ["A2"] == 110.0
        # E4 ≈ 329.63 Hz
        assert abs(STANDARD_TUNING_HZ["E4"] - 329.63) < 0.01

    def test_wound_unit_weights_realistic(self):
        """Wound string unit weights are in realistic range."""
        from app.calculators.string_tension import WOUND_UNIT_WEIGHT_KG_M

        for gauge, weight in WOUND_UNIT_WEIGHT_KG_M.items():
            # Unit weight should increase with gauge
            assert weight > 0, f"Weight for gauge {gauge} should be positive"
            # Typical range: 0.001 - 0.02 kg/m for phosphor bronze acoustic strings
            assert 0.001 <= weight <= 0.025, f"Weight {weight} for gauge {gauge} out of range"

    def test_preset_strings_have_correct_frequencies(self):
        """Preset string specs have correct standard tuning frequencies."""
        for spec in LIGHT_012:
            expected = STANDARD_TUNING_HZ[spec.note]
            assert spec.frequency_hz == expected, f"{spec.note}: expected {expected}, got {spec.frequency_hz}"
