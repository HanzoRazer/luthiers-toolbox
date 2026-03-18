"""
Tests for bridge_break_angle.py v2 corrected geometry.

Validates:
1. Known geometry → expected angle
2. θ < 4° → RED gate (insufficient downforce)
3. 4° <= θ < 6° → YELLOW gate (marginal)
4. θ >= 6° → GREEN gate (adequate)
5. Carruth minimum h_min calculation
"""

import math
import pytest

from app.calculators.bridge_break_angle import (
    calculate_break_angle,
    BreakAngleInput,
    CARRUTH_MIN_DEG,
    MARGINAL_MIN_DEG,
    TOO_STEEP_DEG,
    DEFAULT_SLOT_OFFSET_MM,
)


class TestKnownGeometry:
    """Test known geometry produces expected angle."""

    def test_martin_d28_typical(self):
        """Martin D-28 typical geometry: d=4.3mm, h=2.5mm → ~30°."""
        # d = 5.5 - 1.2 = 4.3mm (pin center - slot offset)
        # h = 2.5mm
        # θ = arctan(2.5 / 4.3) = 30.17°
        inp = BreakAngleInput(
            saddle_projection_mm=2.5,
            pin_to_saddle_mm=5.5,
            slot_offset_mm=1.2,
        )
        result = calculate_break_angle(inp)

        assert result.effective_distance_mm == pytest.approx(4.3, rel=0.01)
        expected_angle = math.degrees(math.atan2(2.5, 4.3))
        assert result.break_angle_deg == pytest.approx(expected_angle, rel=0.01)

    def test_effective_distance_calculation(self):
        """Verify d = pin_to_saddle - slot_offset."""
        inp = BreakAngleInput(
            saddle_projection_mm=3.0,
            pin_to_saddle_mm=6.0,
            slot_offset_mm=1.5,
        )
        result = calculate_break_angle(inp)

        assert result.effective_distance_mm == pytest.approx(4.5, rel=0.01)

    def test_angle_formula(self):
        """Verify θ = arctan(h / d)."""
        h = 2.0
        d_pin = 5.0
        offset = 1.0
        d_eff = d_pin - offset  # 4.0

        inp = BreakAngleInput(
            saddle_projection_mm=h,
            pin_to_saddle_mm=d_pin,
            slot_offset_mm=offset,
        )
        result = calculate_break_angle(inp)

        expected = math.degrees(math.atan2(h, d_eff))
        assert result.break_angle_deg == pytest.approx(expected, rel=0.01)


class TestCarruthGate:
    """Test Carruth gate classification (GREEN/YELLOW/RED)."""

    def test_red_gate_below_4_degrees(self):
        """θ < 4° → RED gate (insufficient downforce)."""
        # Need very small h relative to d to get < 4°
        # tan(3°) ≈ 0.0524, so h/d < 0.0524
        # With d_eff = 5.0, h < 0.262
        inp = BreakAngleInput(
            saddle_projection_mm=0.2,
            pin_to_saddle_mm=5.0,
            slot_offset_mm=0.0,
        )
        result = calculate_break_angle(inp)

        assert result.break_angle_deg < MARGINAL_MIN_DEG
        assert result.gate == "RED"
        assert result.rating == "too_shallow"
        assert result.energy_coupling == "inadequate"

    def test_yellow_gate_4_to_6_degrees(self):
        """4° <= θ < 6° → YELLOW gate (marginal)."""
        # tan(5°) ≈ 0.0875, so h/d ≈ 0.0875
        # With d_eff = 4.0, h ≈ 0.35
        inp = BreakAngleInput(
            saddle_projection_mm=0.35,
            pin_to_saddle_mm=4.0,
            slot_offset_mm=0.0,
        )
        result = calculate_break_angle(inp)

        assert MARGINAL_MIN_DEG <= result.break_angle_deg < CARRUTH_MIN_DEG
        assert result.gate == "YELLOW"
        assert result.rating == "marginal"
        assert result.energy_coupling == "marginal"

    def test_green_gate_at_6_degrees(self):
        """θ >= 6° → GREEN gate (adequate)."""
        # tan(6°) ≈ 0.1051, so h/d ≈ 0.1051
        # With d_eff = 4.0, h ≈ 0.42
        inp = BreakAngleInput(
            saddle_projection_mm=0.5,
            pin_to_saddle_mm=4.0,
            slot_offset_mm=0.0,
        )
        result = calculate_break_angle(inp)

        assert result.break_angle_deg >= CARRUTH_MIN_DEG
        assert result.gate == "GREEN"
        assert result.rating == "adequate"
        assert result.energy_coupling == "adequate"

    def test_green_gate_typical_acoustic(self):
        """Typical acoustic guitar geometry → GREEN."""
        inp = BreakAngleInput(
            saddle_projection_mm=2.5,
            pin_to_saddle_mm=5.5,
            slot_offset_mm=1.25,
        )
        result = calculate_break_angle(inp)

        assert result.gate == "GREEN"
        assert result.break_angle_deg > 20  # Typical is 20-35°

    def test_red_gate_too_steep(self):
        """θ > 38° → RED gate (too steep)."""
        # tan(40°) ≈ 0.839, so h/d ≈ 0.839
        # With d_eff = 3.0, h ≈ 2.52
        inp = BreakAngleInput(
            saddle_projection_mm=3.0,
            pin_to_saddle_mm=3.5,
            slot_offset_mm=0.0,
        )
        result = calculate_break_angle(inp)

        assert result.break_angle_deg > TOO_STEEP_DEG
        assert result.gate == "RED"
        assert result.rating == "too_steep"


class TestCarruthMinProjection:
    """Test Carruth minimum h_min calculation."""

    def test_h_min_formula(self):
        """h_min = d × tan(6°) = d × 0.1051."""
        d_eff = 4.5
        expected_h_min = d_eff * math.tan(math.radians(CARRUTH_MIN_DEG))

        inp = BreakAngleInput(
            saddle_projection_mm=2.0,
            pin_to_saddle_mm=d_eff + DEFAULT_SLOT_OFFSET_MM,  # Account for offset
            slot_offset_mm=DEFAULT_SLOT_OFFSET_MM,
        )
        result = calculate_break_angle(inp)

        assert result.carruth_min_projection_mm == pytest.approx(expected_h_min, rel=0.01)

    def test_h_min_at_different_distances(self):
        """h_min scales with effective distance."""
        for d_eff in [3.0, 4.0, 5.0, 6.0]:
            expected_h_min = round(d_eff * math.tan(math.radians(CARRUTH_MIN_DEG)), 2)

            inp = BreakAngleInput(
                saddle_projection_mm=2.0,
                pin_to_saddle_mm=d_eff,
                slot_offset_mm=0.0,
            )
            result = calculate_break_angle(inp)

            assert result.carruth_min_projection_mm == expected_h_min


class TestBackwardCompat:
    """Test v1 field backward compatibility."""

    def test_v1_fields_with_migration_note(self):
        """Using v1 fields produces migration note."""
        inp = BreakAngleInput(
            saddle_protrusion_mm=2.5,  # v1 field
            pin_to_saddle_center_mm=5.5,  # v1 field
        )
        result = calculate_break_angle(inp)

        assert result.migration_note is not None
        assert "deprecated" in result.migration_note.lower()
        assert result.saddle_projection_mm == 2.5

    def test_v2_fields_no_migration_note(self):
        """Using v2 fields produces no migration note."""
        inp = BreakAngleInput(
            saddle_projection_mm=2.5,
            pin_to_saddle_mm=5.5,
        )
        result = calculate_break_angle(inp)

        assert result.migration_note is None


class TestRiskFlags:
    """Test risk flag generation."""

    def test_shallow_angle_flag(self):
        """Shallow angle generates SHALLOW_ANGLE flag."""
        inp = BreakAngleInput(
            saddle_projection_mm=0.2,
            pin_to_saddle_mm=5.0,
            slot_offset_mm=0.0,
        )
        result = calculate_break_angle(inp)

        assert any(f.code == "SHALLOW_ANGLE" for f in result.risk_flags)

    def test_low_projection_flag(self):
        """Low projection generates LOW_PROJECTION flag."""
        inp = BreakAngleInput(
            saddle_projection_mm=1.0,  # Below 1.6mm minimum
            pin_to_saddle_mm=5.0,
            slot_offset_mm=0.0,
        )
        result = calculate_break_angle(inp)

        assert any(f.code == "LOW_PROJECTION" for f in result.risk_flags)

    def test_recommendation_for_shallow(self):
        """Shallow angle generates recommendation."""
        inp = BreakAngleInput(
            saddle_projection_mm=0.3,
            pin_to_saddle_mm=5.0,
            slot_offset_mm=0.0,
        )
        result = calculate_break_angle(inp)

        assert result.recommendation is not None
        assert "raise" in result.recommendation.lower() or "projection" in result.recommendation.lower()
