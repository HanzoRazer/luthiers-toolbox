"""Tests for soundhole_stiffness.py (DECOMP-002 Phase 4 — stiffness reduction analysis)."""

from __future__ import annotations

import math

import pytest

from app.calculators.soundhole_stiffness import (
    STIFFNESS_K,
    BRACING_RESTORE_DEFAULT,
    BRACING_PRESCRIPTIONS,
    StiffnessResult,
    BracingIndicatorResult,
    compute_top_stiffness_reduction,
    get_bracing_implication,
)


class TestConstants:
    """Tests for module constants."""

    def test_stiffness_k_calibration_value(self):
        """STIFFNESS_K is the Gore-calibrated constant."""
        assert STIFFNESS_K == pytest.approx(0.798, rel=0.01)

    def test_bracing_restore_default_value(self):
        """Default bracing restoration is ~70%."""
        assert BRACING_RESTORE_DEFAULT == pytest.approx(0.70, rel=0.01)

    def test_bracing_prescriptions_structure(self):
        """BRACING_PRESCRIPTIONS is a list of dicts with required keys."""
        assert isinstance(BRACING_PRESCRIPTIONS, list)
        assert len(BRACING_PRESCRIPTIONS) >= 4
        required_keys = {
            "raw_reduction_max_pct",
            "level",
            "status",
            "label",
            "patch_required",
            "radial_braces",
            "brace_spec",
            "description",
            "construction",
        }
        for p in BRACING_PRESCRIPTIONS:
            assert required_keys.issubset(p.keys())


class TestComputeTopStiffnessReduction:
    """Tests for compute_top_stiffness_reduction()."""

    def test_returns_stiffness_result(self):
        """Function returns a StiffnessResult dataclass."""
        result = compute_top_stiffness_reduction(
            hole_area_m2=0.0075,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
        )
        assert isinstance(result, StiffnessResult)

    def test_standard_om_calibration_point(self):
        """Standard OM config: ~6% raw reduction, ~1.8% net with default bracing."""
        # Standard OM: 96mm hole at 165mm, 495x380mm plate
        hole_diameter_mm = 96
        hole_area_m2 = math.pi * (hole_diameter_mm / 2000) ** 2

        result = compute_top_stiffness_reduction(
            hole_area_m2=hole_area_m2,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=BRACING_RESTORE_DEFAULT,
        )
        # Gore calibration target: ~6% raw reduction
        assert 5.0 < result.raw_reduction_pct < 7.0
        # With 70% bracing restore: ~1.8% net
        assert 1.5 < result.net_reduction_pct < 2.5
        assert result.status == "moderate"

    def test_no_bracing_gives_full_reduction(self):
        """bracing_restore=0 gives net_reduction == raw_reduction."""
        result = compute_top_stiffness_reduction(
            hole_area_m2=0.0075,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.0,
        )
        assert result.net_reduction_pct == pytest.approx(
            result.raw_reduction_pct, rel=0.01
        )
        assert result.bracing_recovered_pct == pytest.approx(0.0, abs=0.01)

    def test_full_bracing_gives_zero_net_reduction(self):
        """bracing_restore=1.0 gives zero net reduction."""
        result = compute_top_stiffness_reduction(
            hole_area_m2=0.0075,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=1.0,
        )
        assert result.net_reduction_pct == pytest.approx(0.0, abs=0.01)

    def test_mode_coupling_at_one_third_position(self):
        """Mode coupling at x=1/3 body length is ~0.866 (sin(pi/3))."""
        result = compute_top_stiffness_reduction(
            hole_area_m2=0.007,
            x_from_neck_mm=165,  # 165/495 = 1/3
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
        )
        expected_coupling = math.sin(math.pi / 3)  # ~0.866
        assert result.mode_coupling == pytest.approx(expected_coupling, rel=0.02)

    def test_mode_coupling_at_center_is_one(self):
        """Mode coupling at center (x=0.5) is exactly 1.0."""
        result = compute_top_stiffness_reduction(
            hole_area_m2=0.007,
            x_from_neck_mm=250,  # 250/500 = 0.5
            body_length_mm=500,
            plate_length_mm=500,
            plate_width_mm=380,
        )
        assert result.mode_coupling == pytest.approx(1.0, rel=0.01)

    def test_freq_ratio_decreases_with_larger_hole(self):
        """Larger hole area → lower freq_ratio."""
        small_hole = compute_top_stiffness_reduction(
            hole_area_m2=0.005,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
        )
        large_hole = compute_top_stiffness_reduction(
            hole_area_m2=0.010,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
        )
        assert large_hole.freq_ratio < small_hole.freq_ratio
        assert large_hole.net_reduction_pct > small_hole.net_reduction_pct

    def test_status_classification(self):
        """Status is correctly classified based on net_reduction."""
        # Small hole → minimal
        result_small = compute_top_stiffness_reduction(
            hole_area_m2=0.002,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
        )
        assert result_small.status == "minimal"

        # Large hole with weak bracing → significant
        result_large = compute_top_stiffness_reduction(
            hole_area_m2=0.012,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.3,
        )
        assert result_large.status == "significant"


class TestStiffnessResultConstructionNote:
    """Tests for StiffnessResult.construction_note property."""

    def test_minimal_note(self):
        """Minimal status gives 'no additional braces' note."""
        result = compute_top_stiffness_reduction(
            hole_area_m2=0.002,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
        )
        note = result.construction_note
        assert "No additional radial braces" in note

    def test_significant_note(self):
        """Significant status gives reduction guidance."""
        result = compute_top_stiffness_reduction(
            hole_area_m2=0.012,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.3,
        )
        note = result.construction_note
        assert "mandatory" in note.lower() or "significant" in note.lower()


class TestGetBracingImplication:
    """Tests for get_bracing_implication()."""

    def test_returns_bracing_indicator_result(self):
        """Function returns BracingIndicatorResult dataclass."""
        stiffness = compute_top_stiffness_reduction(
            hole_area_m2=0.0075,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.0,  # Use raw reduction for prescription
        )
        result = get_bracing_implication(stiffness)
        assert isinstance(result, BracingIndicatorResult)

    def test_small_hole_no_reinforcement(self):
        """Small hole (low raw_reduction) → no reinforcement."""
        stiffness = compute_top_stiffness_reduction(
            hole_area_m2=0.0020,  # ~50mm diameter
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.0,
        )
        result = get_bracing_implication(stiffness)
        assert result.level == "none"
        assert result.patch_required is False
        assert result.radial_braces == 0

    def test_standard_hole_requires_patch_and_braces(self):
        """Standard 96-105mm hole requires patch + 2 braces."""
        # ~100mm diameter hole
        hole_area_m2 = math.pi * (100 / 2000) ** 2
        stiffness = compute_top_stiffness_reduction(
            hole_area_m2=hole_area_m2,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.0,
        )
        result = get_bracing_implication(stiffness)
        # Should be "patch_braces_light" or "patch_braces_heavy"
        assert "patch" in result.level
        assert result.patch_required is True
        assert result.radial_braces >= 2

    def test_to_dict_keys(self):
        """to_dict() returns expected keys."""
        stiffness = compute_top_stiffness_reduction(
            hole_area_m2=0.0075,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.0,
        )
        result = get_bracing_implication(stiffness)
        d = result.to_dict()
        expected_keys = {
            "status",
            "label",
            "patch_required",
            "radial_braces",
            "brace_spec",
            "raw_reduction_pct",
            "construction_steps",
        }
        assert set(d.keys()) == expected_keys

    def test_custom_diameter_passed_through(self):
        """main_port_diameter_equiv_mm is passed through."""
        stiffness = compute_top_stiffness_reduction(
            hole_area_m2=0.0075,
            x_from_neck_mm=165,
            body_length_mm=495,
            plate_length_mm=495,
            plate_width_mm=380,
            bracing_restore=0.0,
        )
        result = get_bracing_implication(stiffness, main_port_diameter_equiv_mm=100.0)
        assert result.hole_diameter_equiv_mm == pytest.approx(100.0, rel=0.01)


class TestBackwardCompatibility:
    """Tests for backward compatibility via soundhole_calc.py imports."""

    def test_imports_from_soundhole_calc(self):
        """Stiffness symbols importable from soundhole_calc.py."""
        from app.calculators.soundhole_calc import (
            STIFFNESS_K as SK,
            BRACING_RESTORE_DEFAULT as BRD,
            BRACING_PRESCRIPTIONS as BP,
            StiffnessResult as SR,
            BracingIndicatorResult as BIR,
            compute_top_stiffness_reduction as ctsr,
            get_bracing_implication as gbi,
        )
        # Verify they're the same objects
        assert SK == STIFFNESS_K
        assert BRD == BRACING_RESTORE_DEFAULT
        assert BP is BRACING_PRESCRIPTIONS
        assert SR is StiffnessResult
        assert BIR is BracingIndicatorResult
        assert ctsr is compute_top_stiffness_reduction
        assert gbi is get_bracing_implication
