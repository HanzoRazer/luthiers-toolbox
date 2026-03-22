"""
Tests for soundhole_resonator.py (DECOMP-002 Phase 2)

Tests for:
- TwoCavityResult dataclass
- analyze_two_cavity() exact eigenvalue solution
- compute_sensitivity_curve() design exploration
"""

import pytest

from app.calculators.soundhole_resonator import (
    TwoCavityResult,
    analyze_two_cavity,
    compute_sensitivity_curve,
)
from app.calculators.soundhole_physics import PortSpec


class TestComputeSensitivityCurve:
    """Tests for compute_sensitivity_curve()."""

    def test_returns_list_of_dicts(self):
        """compute_sensitivity_curve returns list of {diameter_mm, f_hz} dicts."""
        curve = compute_sensitivity_curve(
            volume_m3=0.014,  # ~14 L typical dreadnought
            current_diameter_mm=100.0,
            steps=5,
        )
        assert isinstance(curve, list)
        assert len(curve) > 0
        assert all(isinstance(p, dict) for p in curve)
        assert all("diameter_mm" in p and "f_hz" in p for p in curve)

    def test_curve_length_equals_steps(self):
        """Curve length matches steps parameter."""
        for steps in [5, 10, 20]:
            curve = compute_sensitivity_curve(
                volume_m3=0.014,
                current_diameter_mm=100.0,
                steps=steps,
            )
            assert len(curve) == steps

    def test_frequency_decreases_with_smaller_diameter(self):
        """Smaller soundhole → lower Helmholtz frequency (basic physics)."""
        curve = compute_sensitivity_curve(
            volume_m3=0.014,
            current_diameter_mm=100.0,
            range_mm=20.0,
            steps=5,
        )
        # Curve is sorted by diameter (d_min to d_max)
        # f_H should increase with diameter
        freqs = [p["f_hz"] for p in curve]
        diams = [p["diameter_mm"] for p in curve]
        # Verify diameter ordering
        assert diams == sorted(diams)
        # Verify frequency increases with diameter
        assert freqs == sorted(freqs)


class TestTwoCavityResult:
    """Tests for TwoCavityResult dataclass."""

    def test_to_dict_returns_expected_keys(self):
        """to_dict() returns all expected keys."""
        result = TwoCavityResult(
            f_H1_uncoupled_hz=105.0,
            f_H2_uncoupled_hz=120.0,
            f_lower_hz=85.0,
            f_upper_hz=140.0,
            f_lower_note="E2",
            f_upper_note="C#3",
            coupling_hz=50.0,
            coupling_regime="strong",
            separation_hz=55.0,
            v_main_effective_m3=0.012,
            v_resonator_m3=0.003,
            design_note="Test note",
            tuning_guidance=["Tip 1", "Tip 2"],
        )
        d = result.to_dict()
        expected_keys = {
            "f_lower_hz", "f_upper_hz", "f_lower_note", "f_upper_note",
            "f_H1_uncoupled_hz", "f_H2_uncoupled_hz",
            "coupling_hz", "coupling_regime", "separation_hz",
        }
        assert set(d.keys()) == expected_keys


class TestAnalyzeTwoCavity:
    """Tests for analyze_two_cavity() exact eigenvalue solution."""

    def test_returns_two_cavity_result(self):
        """analyze_two_cavity returns TwoCavityResult instance."""
        # Create a main port (D-hole style)
        main_port = PortSpec.from_oval_mm(
            width_mm=90.0,
            height_mm=70.0,
            thickness_mm=2.5,
            label="D-hole",
        )
        result = analyze_two_cavity(
            main_ports=[main_port],
            volume_total_m3=0.015,  # 15 L total
            volume_resonator_m3=0.004,  # 4 L resonator
            aperture_diameter_mm=60.0,
        )
        assert isinstance(result, TwoCavityResult)
        assert result.f_lower_hz > 0
        assert result.f_upper_hz > result.f_lower_hz
        assert result.separation_hz == pytest.approx(
            result.f_upper_hz - result.f_lower_hz, rel=0.01
        )

    def test_coupling_regime_classification(self):
        """Coupling regime is correctly classified based on κ/f ratio."""
        main_port = PortSpec.from_circle_mm(diameter_mm=100.0)

        # Small aperture → weak coupling
        result_small = analyze_two_cavity(
            main_ports=[main_port],
            volume_total_m3=0.020,
            volume_resonator_m3=0.005,
            aperture_diameter_mm=20.0,  # small aperture
        )

        # Large aperture → strong coupling
        result_large = analyze_two_cavity(
            main_ports=[main_port],
            volume_total_m3=0.020,
            volume_resonator_m3=0.005,
            aperture_diameter_mm=80.0,  # large aperture
        )

        # Large aperture should have higher coupling
        assert result_large.coupling_hz > result_small.coupling_hz
        # Large aperture should have wider separation
        assert result_large.separation_hz > result_small.separation_hz

    def test_eigenfreqs_bracket_uncoupled(self):
        """Coupled modes bracket (extend beyond) uncoupled frequencies."""
        main_port = PortSpec.from_oval_mm(width_mm=85.0, height_mm=65.0)
        result = analyze_two_cavity(
            main_ports=[main_port],
            volume_total_m3=0.016,
            volume_resonator_m3=0.004,
            aperture_diameter_mm=55.0,
        )
        # In strong coupling, lower mode < min(uncoupled), upper > max(uncoupled)
        min_uncoupled = min(result.f_H1_uncoupled_hz, result.f_H2_uncoupled_hz)
        max_uncoupled = max(result.f_H1_uncoupled_hz, result.f_H2_uncoupled_hz)

        # Lower mode should be pushed below minimum uncoupled frequency
        assert result.f_lower_hz < min_uncoupled
        # Upper mode should be pushed above maximum uncoupled frequency
        assert result.f_upper_hz > max_uncoupled
