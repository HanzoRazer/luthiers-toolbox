"""Tests for fret_leveling_calc.py (CONSTRUCTION-003)."""

import pytest
import math

from app.calculators.fret_leveling_calc import (
    FretProfile,
    LevelingPlan,
    analyze_fret_heights,
    compute_leveling_radius,
    check_single_fret,
    HIGH_FRET_TOLERANCE_MM,
    MIN_PLAYABLE_HEIGHT_MM,
)


class TestAnalyzeFretHeights:
    """Tests for analyze_fret_heights function."""

    def test_uniform_heights_returns_green(self):
        """Uniform fret heights should return GREEN with no high frets."""
        heights = [1.2] * 22  # 22 frets all at 1.2mm
        plan = analyze_fret_heights(
            heights_mm=heights,
            scale_length_mm=648.0,
        )
        assert plan.gate == "GREEN"
        assert plan.high_fret_count == 0
        assert plan.material_removal_mm == 0.0

    def test_single_high_fret_detected(self):
        """A single high fret should be detected."""
        heights = [1.2] * 22
        heights[7] = 1.28  # Fret 8 is 0.08mm high
        plan = analyze_fret_heights(
            heights_mm=heights,
            scale_length_mm=648.0,
        )
        assert plan.high_fret_count >= 1
        assert any(f.fret_number == 8 and f.status == "high" for f in plan.frets)

    def test_multiple_high_frets_triggers_yellow(self):
        """Multiple high frets (>30%) should trigger YELLOW."""
        heights = [1.2] * 20
        # Make 8 frets high (40%)
        for i in [0, 2, 4, 6, 8, 10, 12, 14]:
            heights[i] = 1.28
        plan = analyze_fret_heights(
            heights_mm=heights,
            scale_length_mm=648.0,
        )
        assert plan.gate == "YELLOW"
        assert plan.high_fret_count >= 6

    def test_low_fret_needing_replacement_triggers_red(self):
        """Fret that would be too low after leveling should trigger RED."""
        # Start with frets at 0.6mm (just above minimum)
        heights = [0.6] * 22
        # Make one fret very high
        heights[5] = 0.85  # Fret 6 is 0.25mm high
        # After leveling, other frets would be at 0.35mm < MIN_PLAYABLE_HEIGHT_MM
        plan = analyze_fret_heights(
            heights_mm=heights,
            scale_length_mm=648.0,
        )
        assert plan.gate == "RED"
        assert len(plan.replacement_needed) > 0

    def test_empty_heights_returns_red(self):
        """Empty heights list should return RED."""
        plan = analyze_fret_heights(
            heights_mm=[],
            scale_length_mm=648.0,
        )
        assert plan.gate == "RED"
        assert "No fret heights" in plan.notes[0]

    def test_material_removal_equals_max_deviation(self):
        """Material removal should equal maximum deviation."""
        heights = [1.2] * 22
        heights[10] = 1.35  # Fret 11 is ~0.15mm high
        plan = analyze_fret_heights(
            heights_mm=heights,
            scale_length_mm=648.0,
        )
        assert plan.material_removal_mm > 0
        assert abs(plan.material_removal_mm - plan.max_deviation_mm) < 0.001


class TestComputeLevelingRadius:
    """Tests for compute_leveling_radius function."""

    def test_typical_relief_gives_large_radius(self):
        """Typical relief (0.2mm) should give very large radius."""
        radius = compute_leveling_radius(
            scale_length_mm=648.0,
            relief_mm=0.2,
        )
        # R = 648^2 / (8 × 0.2) = 419904 / 1.6 ≈ 262440mm ≈ 262m
        assert radius > 200000  # Very large radius

    def test_zero_relief_returns_infinity(self):
        """Zero relief should return infinite radius (flat beam)."""
        radius = compute_leveling_radius(
            scale_length_mm=648.0,
            relief_mm=0.0,
        )
        assert math.isinf(radius)


class TestCheckSingleFret:
    """Tests for check_single_fret function."""

    def test_fret_within_tolerance_returns_ok(self):
        """Fret within tolerance of neighbors should return ok."""
        status = check_single_fret(
            fret_height=1.20,
            neighbor_avg=1.19,
            tolerance_mm=0.03,
        )
        assert status == "ok"

    def test_high_fret_returns_high(self):
        """Fret above neighbors by more than tolerance should return high."""
        status = check_single_fret(
            fret_height=1.25,
            neighbor_avg=1.20,
            tolerance_mm=0.03,
        )
        assert status == "high"

    def test_low_fret_returns_low(self):
        """Fret below neighbors by more than tolerance should return low."""
        status = check_single_fret(
            fret_height=1.15,
            neighbor_avg=1.20,
            tolerance_mm=0.03,
        )
        assert status == "low"


class TestFretProfileDataclass:
    """Tests for FretProfile dataclass."""

    def test_to_dict_returns_correct_keys(self):
        """to_dict should return all expected keys."""
        profile = FretProfile(
            fret_number=5,
            height_mm=1.234567,
            deviation_mm=0.0456789,
            status="high",
        )
        d = profile.to_dict()
        assert d["fret_number"] == 5
        assert d["height_mm"] == 1.235  # Rounded to 3 decimals
        assert d["deviation_mm"] == 0.046  # Rounded to 3 decimals
        assert d["status"] == "high"
