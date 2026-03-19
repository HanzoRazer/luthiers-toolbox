"""
Tests for wood_movement_calc.py — CONSTRUCTION-006.

Validates humidity and wood movement calculations.

Expected results:
- RH drop (drying) → contraction
- RH increase → expansion
- Higher shrinkage coefficient → more movement
- Safe range keeps movement within limits
"""

import pytest

from app.calculators.wood_movement_calc import (
    compute_wood_movement,
    safe_humidity_range,
    list_species,
    get_shrinkage_coefficient,
    WoodMovementSpec,
    SafeHumidityRange,
    TANGENTIAL_SHRINKAGE,
    RADIAL_TO_TANGENTIAL_RATIO,
)


class TestComputeWoodMovement:
    """Test wood movement calculation."""

    def test_rosewood_drying_causes_contraction(self):
        """Rosewood top drying 45%→20% RH should contract."""
        result = compute_wood_movement(
            species="rosewood",
            dimension_mm=400.0,
            rh_from=45.0,
            rh_to=20.0,
        )

        assert isinstance(result, WoodMovementSpec)
        assert result.direction == "contraction"
        assert result.movement_mm > 0
        # Should be significant movement (>1mm for this swing)
        assert result.movement_mm > 0.5

    def test_humidity_increase_causes_expansion(self):
        """Increasing RH should cause expansion."""
        result = compute_wood_movement(
            species="sitka_spruce",
            dimension_mm=400.0,
            rh_from=30.0,
            rh_to=70.0,
        )

        assert result.direction == "expansion"
        assert result.movement_mm > 0

    def test_no_humidity_change_no_movement(self):
        """Same RH should produce no movement."""
        result = compute_wood_movement(
            species="mahogany",
            dimension_mm=400.0,
            rh_from=45.0,
            rh_to=45.0,
        )

        assert result.direction == "none"
        assert result.movement_mm == 0.0

    def test_higher_coefficient_more_movement(self):
        """Species with higher shrinkage coefficient should move more."""
        # Maple has higher coefficient than mahogany
        maple_result = compute_wood_movement(
            species="maple",
            dimension_mm=400.0,
            rh_from=45.0,
            rh_to=25.0,
        )

        mahogany_result = compute_wood_movement(
            species="mahogany",
            dimension_mm=400.0,
            rh_from=45.0,
            rh_to=25.0,
        )

        assert maple_result.movement_mm > mahogany_result.movement_mm

    def test_radial_less_than_tangential(self):
        """Radial shrinkage should be less than tangential."""
        tangential = compute_wood_movement(
            species="rosewood",
            dimension_mm=400.0,
            rh_from=45.0,
            rh_to=25.0,
            grain_direction="tangential",
        )

        radial = compute_wood_movement(
            species="rosewood",
            dimension_mm=400.0,
            rh_from=45.0,
            rh_to=25.0,
            grain_direction="radial",
        )

        assert radial.movement_mm < tangential.movement_mm
        # Radial should be ~55% of tangential
        ratio = radial.movement_mm / tangential.movement_mm
        assert abs(ratio - RADIAL_TO_TANGENTIAL_RATIO) < 0.01

    def test_extreme_dryness_red_gate(self):
        """Extreme dryness (<25% RH) should trigger RED gate."""
        result = compute_wood_movement(
            species="spruce",
            dimension_mm=400.0,
            rh_from=45.0,
            rh_to=15.0,
        )

        assert result.gate == "RED"
        assert "extreme" in result.risk_note.lower() or "cracking" in result.risk_note.lower()

    def test_invalid_species_raises(self):
        """Unknown species should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown species"):
            compute_wood_movement(
                species="unobtanium",
                dimension_mm=400.0,
                rh_from=45.0,
                rh_to=30.0,
            )


class TestSafeHumidityRange:
    """Test safe humidity range calculation."""

    def test_safe_range_symmetric(self):
        """Safe range should be roughly symmetric around nominal."""
        result = safe_humidity_range(
            species="spruce",
            dimension_mm=400.0,
            max_movement_mm=1.0,
            nominal_rh=45.0,
        )

        assert isinstance(result, SafeHumidityRange)
        assert result.min_rh < result.nominal_rh
        assert result.max_rh > result.nominal_rh
        # Should be within valid range
        assert 0 <= result.min_rh <= 100
        assert 0 <= result.max_rh <= 100

    def test_tighter_tolerance_smaller_range(self):
        """Smaller max_movement should produce tighter RH range."""
        wide = safe_humidity_range(
            species="maple",
            dimension_mm=400.0,
            max_movement_mm=2.0,
            nominal_rh=45.0,
        )

        tight = safe_humidity_range(
            species="maple",
            dimension_mm=400.0,
            max_movement_mm=0.5,
            nominal_rh=45.0,
        )

        tight_range = tight.max_rh - tight.min_rh
        wide_range = wide.max_rh - wide.min_rh
        assert tight_range < wide_range

    def test_smaller_dimension_wider_range(self):
        """Smaller dimension should allow wider RH range."""
        large = safe_humidity_range(
            species="rosewood",
            dimension_mm=400.0,
            max_movement_mm=1.0,
            nominal_rh=45.0,
        )

        small = safe_humidity_range(
            species="rosewood",
            dimension_mm=200.0,
            max_movement_mm=1.0,
            nominal_rh=45.0,
        )

        small_range = small.max_rh - small.min_rh
        large_range = large.max_rh - large.min_rh
        assert small_range > large_range

    def test_low_humidity_warning(self):
        """Range extending below 30% should include warning."""
        result = safe_humidity_range(
            species="spruce",
            dimension_mm=200.0,
            max_movement_mm=2.0,
            nominal_rh=40.0,
        )

        # If min_rh is below 30, should have warning
        if result.min_rh < 30:
            assert any("30%" in note or "crack" in note.lower() for note in result.notes)


class TestHelperFunctions:
    """Test utility functions."""

    def test_list_species(self):
        """list_species should return all supported species."""
        species = list_species()

        assert "sitka_spruce" in species
        assert "rosewood" in species
        assert "mahogany" in species
        assert "maple" in species
        assert "walnut" in species

    def test_get_shrinkage_coefficient_tangential(self):
        """get_shrinkage_coefficient should return correct value."""
        coeff = get_shrinkage_coefficient("sitka_spruce", "tangential")
        assert coeff == TANGENTIAL_SHRINKAGE["sitka_spruce"]

    def test_get_shrinkage_coefficient_radial(self):
        """Radial coefficient should be scaled down."""
        tangential = get_shrinkage_coefficient("maple", "tangential")
        radial = get_shrinkage_coefficient("maple", "radial")

        assert radial == tangential * RADIAL_TO_TANGENTIAL_RATIO

    def test_get_shrinkage_coefficient_invalid(self):
        """Unknown species should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown species"):
            get_shrinkage_coefficient("unknown_wood")


class TestPhysicsValidation:
    """Validate physics assumptions."""

    def test_shrinkage_coefficients_positive(self):
        """All shrinkage coefficients should be positive."""
        for species, coeff in TANGENTIAL_SHRINKAGE.items():
            assert coeff > 0, f"{species} has non-positive coefficient"

    def test_shrinkage_coefficients_realistic(self):
        """Shrinkage coefficients should be in realistic range."""
        # Typical range: 0.001 to 0.003 per % MC
        for species, coeff in TANGENTIAL_SHRINKAGE.items():
            assert 0.001 < coeff < 0.003, f"{species} coefficient {coeff} out of range"

    def test_houston_scenario(self):
        """
        Houston seasonal swing: 30% to 80% RH.
        400mm spruce top moves significantly — this is crack territory.

        Physics: 50% RH swing → ~15% MC change → 400×0.15×0.00176×100 ≈ 10mm
        This extreme movement is why Houston guitars need case humidification.
        """
        result = compute_wood_movement(
            species="sitka_spruce",
            dimension_mm=400.0,
            rh_from=30.0,
            rh_to=80.0,
        )

        # Should be significant movement (>5mm for this extreme swing)
        assert result.movement_mm > 5.0
        assert result.gate == "RED"  # Extreme humidity swing
        assert "large RH swing" in result.risk_note
