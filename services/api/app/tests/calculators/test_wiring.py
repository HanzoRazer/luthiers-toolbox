"""
Tests for Wiring Calculators

Tests treble bleed, switch validation, and impedance calculations.
"""
import pytest

from app.calculators.wiring.treble_bleed import (
    suggest_treble_bleed,
    TrebleBleedResult,
)
from app.calculators.wiring.switch_validator import (
    validate_switch_config,
    SwitchValidationResult,
    PickupConfig,
)
from app.calculators.wiring.impedance_math import (
    calculate_parallel_resistance,
    calculate_tone_rolloff,
    calculate_pickup_load,
    suggest_cable_length,
)


class TestTrebleBleed:
    """Tests for treble bleed calculator."""

    def test_250k_pot_series_resistor(self):
        """Test standard 250K pot treble bleed."""
        result = suggest_treble_bleed(
            pot_value_kohm=250,
            circuit_type="series_resistor",
        )
        
        assert isinstance(result, TrebleBleedResult)
        assert result.circuit_type == "series_resistor"
        assert result.capacitance_nf > 0
        assert result.resistance_kohm is not None
        assert result.resistance_kohm > 0

    def test_500k_pot_capacitor_only(self):
        """Test 500K pot with capacitor only."""
        result = suggest_treble_bleed(
            pot_value_kohm=500,
            circuit_type="capacitor_only",
        )
        
        assert result.circuit_type == "capacitor_only"
        assert result.capacitance_nf > 0
        # Capacitor-only has no resistor
        assert result.resistance_kohm is None

    def test_brightness_affects_capacitance(self):
        """Test that brightness preference affects cap value."""
        bright = suggest_treble_bleed(
            pot_value_kohm=500,
            circuit_type="series_resistor",
            brightness=0.9,  # Brighter
        )
        
        dark = suggest_treble_bleed(
            pot_value_kohm=500,
            circuit_type="series_resistor",
            brightness=0.1,  # Darker
        )
        
        # Brighter = higher capacitance
        assert bright.capacitance_nf >= dark.capacitance_nf


class TestSwitchValidator:
    """Tests for switch configuration validator."""

    def test_3way_toggle_valid(self):
        """Test valid 3-way toggle configuration."""
        pickups = [
            PickupConfig(name="Neck", pickup_type="humbucker", position="neck"),
            PickupConfig(name="Bridge", pickup_type="humbucker", position="bridge"),
        ]
        
        result = validate_switch_config(
            switch_type="3way_toggle",
            pickups=pickups,
        )
        
        assert isinstance(result, SwitchValidationResult)
        assert result.is_valid is True
        assert len(result.positions) == 3
        assert len(result.errors) == 0

    def test_5way_strat_valid(self):
        """Test valid 5-way Strat configuration."""
        pickups = [
            PickupConfig(name="Neck", pickup_type="single_coil", position="neck"),
            PickupConfig(name="Middle", pickup_type="single_coil", position="middle"),
            PickupConfig(name="Bridge", pickup_type="single_coil", position="bridge"),
        ]
        
        result = validate_switch_config(
            switch_type="5way_blade",
            pickups=pickups,
        )
        
        assert result.is_valid is True
        assert len(result.positions) == 5

    def test_5way_insufficient_pickups(self):
        """Test that 5-way with 2 pickups fails validation."""
        pickups = [
            PickupConfig(name="Neck", pickup_type="single_coil", position="neck"),
            PickupConfig(name="Bridge", pickup_type="single_coil", position="bridge"),
        ]
        
        result = validate_switch_config(
            switch_type="5way_blade",
            pickups=pickups,
        )
        
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_4way_tele_has_series(self):
        """Test that 4-way Tele includes series position."""
        pickups = [
            PickupConfig(name="Neck", pickup_type="single_coil", position="neck"),
            PickupConfig(name="Bridge", pickup_type="single_coil", position="bridge"),
        ]
        
        result = validate_switch_config(
            switch_type="4way_tele",
            pickups=pickups,
        )
        
        assert result.is_valid is True
        assert len(result.positions) == 4
        # Check for series position
        series_pos = [p for p in result.positions if p.wiring == "series"]
        assert len(series_pos) == 1


class TestImpedanceMath:
    """Tests for impedance calculations."""

    def test_parallel_resistance_two(self):
        """Test parallel resistance of two resistors."""
        # 500K || 500K = 250K
        result = calculate_parallel_resistance(500, 500)
        assert abs(result - 250) < 0.1

    def test_parallel_resistance_three(self):
        """Test parallel resistance of three resistors."""
        # 500K || 250K || 1000K
        result = calculate_parallel_resistance(500, 250, 1000)
        # 1/(1/500 + 1/250 + 1/1000) ≈ 142.86K
        assert abs(result - 142.86) < 1

    def test_tone_rolloff_full_up(self):
        """Test tone rolloff with pot full up (minimal effect)."""
        result = calculate_tone_rolloff(
            pot_value_kohm=500,
            capacitor_nf=22,
            pot_position=1.0,  # Full up
        )
        
        # At full up, cutoff should be very high (minimal effect)
        assert result.cutoff_frequency_hz > 10000

    def test_tone_rolloff_rolled_off(self):
        """Test tone rolloff with pot turned down."""
        result = calculate_tone_rolloff(
            pot_value_kohm=500,
            capacitor_nf=22,
            pot_position=0.0,  # Full down
        )
        
        # At full down, should have significant rolloff
        assert result.cutoff_frequency_hz < 2000

    def test_pickup_load_calculation(self):
        """Test pickup loading with pots and cable."""
        result = calculate_pickup_load(
            pickup_dcr_kohm=7.5,
            pickup_inductance_h=2.5,
            volume_pot_kohm=500,
            tone_pot_kohm=500,
            cable_capacitance_pf=500,
        )
        
        assert result.total_load_kohm == 250  # 500 || 500
        assert result.resonant_peak_hz is not None
        assert result.resonant_peak_hz > 0

    def test_cable_length_suggestion(self):
        """Test cable length recommendation."""
        result = suggest_cable_length(
            desired_brightness=0.8,  # Bright
            pickup_inductance_h=2.5,
        )
        
        assert "max_cable_feet" in result
        assert result["max_cable_feet"] > 0
        assert result["capacitance_budget_pf"] > 0
