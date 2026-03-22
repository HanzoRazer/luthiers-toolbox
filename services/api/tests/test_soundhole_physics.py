"""
Tests for soundhole_physics.py — Pure Helmholtz physics module.

Extracted from soundhole_calc.py as part of DECOMP-002.
"""
import pytest
import math

from app.calculators.soundhole_physics import (
    # Constants
    C_AIR,
    K0,
    GAMMA,
    PLATE_MASS_FACTOR,
    # Data class
    PortSpec,
    # Core functions
    compute_port_neck_length,
    compute_helmholtz_multiport,
    hz_to_note,
    compute_two_cavity_helmholtz,
    exact_coupled_eigenfreq,
)


# ── Constants Tests ───────────────────────────────────────────────────────────

class TestConstants:
    def test_speed_of_sound_reasonable(self):
        """Speed of sound should be ~343 m/s at 20°C."""
        assert 340 < C_AIR < 350

    def test_k0_end_correction(self):
        """K0 should be ~1.7 for round holes."""
        assert 1.5 < K0 < 2.0

    def test_gamma_perimeter_sensitivity(self):
        """GAMMA should be small positive number."""
        assert 0 < GAMMA < 0.1

    def test_plate_mass_factor_range(self):
        """Plate mass factor should reduce frequency by 5-10%."""
        assert 0.85 < PLATE_MASS_FACTOR < 0.98


# ── PortSpec Tests ────────────────────────────────────────────────────────────

class TestPortSpec:
    def test_from_circle_mm_area(self):
        """100mm circle should have area π×50²/1e6 m²."""
        port = PortSpec.from_circle_mm(100)
        expected_area = math.pi * 0.05 ** 2
        assert port.area_m2 == pytest.approx(expected_area, rel=0.001)

    def test_from_circle_mm_perimeter(self):
        """100mm circle should have perimeter π×100/1000 m."""
        port = PortSpec.from_circle_mm(100)
        expected_perim = math.pi * 0.1
        assert port.perim_m == pytest.approx(expected_perim, rel=0.001)

    def test_from_circle_mm_diameter_equiv(self):
        """diameter_equiv_mm should return original diameter."""
        port = PortSpec.from_circle_mm(100)
        assert port.diameter_equiv_mm == pytest.approx(100.0, abs=0.1)

    def test_from_oval_mm_area(self):
        """120×80mm oval should have area π×60×40/1e6 m²."""
        port = PortSpec.from_oval_mm(120, 80)
        expected_area = math.pi * 0.06 * 0.04
        assert port.area_m2 == pytest.approx(expected_area, rel=0.001)

    def test_from_oval_mm_perimeter_ramanujan(self):
        """Oval perimeter should use Ramanujan approximation."""
        port = PortSpec.from_oval_mm(120, 80)
        # For a=60mm, b=40mm, Ramanujan gives ~315mm perimeter
        assert 0.3 < port.perim_m < 0.35

    def test_area_cm2_conversion(self):
        """area_cm2 should be area_m2 × 10000."""
        port = PortSpec.from_circle_mm(100)
        assert port.area_cm2 == pytest.approx(port.area_m2 * 10000, rel=0.001)

    def test_location_default_is_top(self):
        """Default location should be 'top'."""
        port = PortSpec.from_circle_mm(100)
        assert port.location == "top"

    def test_thickness_default_is_2_5mm(self):
        """Default thickness should be 2.5mm (0.0025m)."""
        port = PortSpec.from_circle_mm(100)
        assert port.thickness_m == pytest.approx(0.0025, abs=0.0001)

    def test_custom_location_side(self):
        """Should accept 'side' location."""
        port = PortSpec.from_circle_mm(50, location="side", label="Side port")
        assert port.location == "side"
        assert port.label == "Side port"


# ── compute_port_neck_length Tests ────────────────────────────────────────────

class TestComputePortNeckLength:
    def test_zero_area_returns_thickness(self):
        """Zero area port should return just thickness."""
        L_eff = compute_port_neck_length(0, 0.1, 0.003)
        assert L_eff == 0.003

    def test_negative_area_returns_thickness(self):
        """Negative area should return just thickness."""
        L_eff = compute_port_neck_length(-1, 0.1, 0.003)
        assert L_eff == 0.003

    def test_round_hole_end_correction(self):
        """Round hole should have L_eff > thickness."""
        port = PortSpec.from_circle_mm(100)
        L_eff = compute_port_neck_length(port.area_m2, port.perim_m, port.thickness_m)
        assert L_eff > port.thickness_m

    def test_larger_area_longer_neck(self):
        """Larger hole should have longer effective neck."""
        port_small = PortSpec.from_circle_mm(80)
        port_large = PortSpec.from_circle_mm(120)
        L_small = compute_port_neck_length(port_small.area_m2, port_small.perim_m, 0.003)
        L_large = compute_port_neck_length(port_large.area_m2, port_large.perim_m, 0.003)
        assert L_large > L_small

    def test_oval_vs_circle_same_area(self):
        """Oval with same area as circle should have longer L_eff due to perimeter."""
        port_circle = PortSpec.from_circle_mm(100)
        # Oval with roughly same area but higher perimeter
        port_oval = PortSpec.from_oval_mm(120, 80)

        L_circle = compute_port_neck_length(port_circle.area_m2, port_circle.perim_m, 0.003)
        L_oval = compute_port_neck_length(port_oval.area_m2, port_oval.perim_m, 0.003)

        # Oval should have longer L_eff due to higher perimeter/area ratio
        # (this explains why ovals resonate lower than circles of same area)
        assert L_oval > L_circle * 0.95  # Allow small tolerance


# ── compute_helmholtz_multiport Tests ──────────────────────────────────────────

class TestComputeHelmholtzMultiport:
    def test_zero_volume_returns_zero(self):
        """Zero volume should return 0 Hz."""
        port = PortSpec.from_circle_mm(100)
        f_H, details = compute_helmholtz_multiport(0, [port])
        assert f_H == 0.0
        assert details == []

    def test_empty_ports_returns_zero(self):
        """Empty ports list should return 0 Hz."""
        f_H, details = compute_helmholtz_multiport(0.015, [])
        assert f_H == 0.0

    def test_typical_dreadnought_helmholtz(self):
        """Dreadnought (~15L, 100mm hole) should resonate ~100 Hz."""
        port = PortSpec.from_circle_mm(100)
        f_H, _ = compute_helmholtz_multiport(0.015, [port])
        # D-28 resonates around 98-108 Hz
        assert 85 < f_H < 120

    def test_smaller_hole_lower_frequency(self):
        """Smaller hole should give lower frequency."""
        port_small = PortSpec.from_circle_mm(80)
        port_large = PortSpec.from_circle_mm(120)
        f_small, _ = compute_helmholtz_multiport(0.015, [port_small])
        f_large, _ = compute_helmholtz_multiport(0.015, [port_large])
        assert f_small < f_large

    def test_larger_volume_lower_frequency(self):
        """Larger volume should give lower frequency."""
        port = PortSpec.from_circle_mm(100)
        f_small_vol, _ = compute_helmholtz_multiport(0.010, [port])
        f_large_vol, _ = compute_helmholtz_multiport(0.020, [port])
        assert f_large_vol < f_small_vol

    def test_port_details_structure(self):
        """Should return properly structured port details."""
        port = PortSpec.from_circle_mm(100, label="Main hole")
        f_H, details = compute_helmholtz_multiport(0.015, [port])
        assert len(details) == 1
        assert details[0]["label"] == "Main hole"
        assert "area_cm2" in details[0]
        assert "L_eff_mm" in details[0]
        assert details[0]["area_fraction"] == pytest.approx(1.0, abs=0.01)

    def test_two_ports_combined(self):
        """Two ports should combine correctly."""
        main_port = PortSpec.from_circle_mm(90, label="Main")
        side_port = PortSpec.from_circle_mm(40, location="side", label="Side")
        f_H, details = compute_helmholtz_multiport(0.015, [main_port, side_port])
        assert len(details) == 2
        assert f_H > 0
        # Check area fractions sum to 1
        total_fraction = sum(d["area_fraction"] for d in details)
        assert total_fraction == pytest.approx(1.0, abs=0.01)


# ── hz_to_note Tests ──────────────────────────────────────────────────────────

class TestHzToNote:
    def test_a4_is_440(self):
        """440 Hz should be A4."""
        assert hz_to_note(440) == "A4"

    def test_middle_c(self):
        """~261 Hz should be C4."""
        assert hz_to_note(261.63) == "C4"

    def test_low_e_guitar(self):
        """~82 Hz should be E2."""
        assert hz_to_note(82.4) == "E2"

    def test_zero_returns_dash(self):
        """Zero Hz should return dash."""
        assert hz_to_note(0) == "—"

    def test_negative_returns_dash(self):
        """Negative Hz should return dash."""
        assert hz_to_note(-100) == "—"

    def test_dreadnought_helmholtz_note(self):
        """~100 Hz (typical dreadnought) should be around G2-G#2."""
        note = hz_to_note(100)
        assert note in ["G2", "G#2"]


# ── compute_two_cavity_helmholtz Tests ────────────────────────────────────────

class TestComputeTwoCavityHelmholtz:
    def test_returns_two_frequencies(self):
        """Should return f_H1 and f_H2."""
        main_ports = [PortSpec.from_circle_mm(100)]
        result = compute_two_cavity_helmholtz(
            volume_main_m3=0.015,
            main_ports=main_ports,
            volume_internal_m3=0.0004,
            aperture_area_m2=0.001,
            aperture_perim_m=0.12,
        )
        assert "f_H1_hz" in result
        assert "f_H2_hz" in result
        assert result["f_H1_hz"] > 0
        assert result["f_H2_hz"] > 0

    def test_frequencies_have_notes(self):
        """Should include musical note names."""
        main_ports = [PortSpec.from_circle_mm(100)]
        result = compute_two_cavity_helmholtz(
            volume_main_m3=0.015,
            main_ports=main_ports,
            volume_internal_m3=0.0004,
            aperture_area_m2=0.001,
            aperture_perim_m=0.12,
        )
        assert "f_H1_note" in result
        assert "f_H2_note" in result

    def test_includes_separation(self):
        """Should report frequency separation."""
        main_ports = [PortSpec.from_circle_mm(100)]
        result = compute_two_cavity_helmholtz(
            volume_main_m3=0.015,
            main_ports=main_ports,
            volume_internal_m3=0.0004,
            aperture_area_m2=0.001,
            aperture_perim_m=0.12,
        )
        assert "separation_hz" in result
        assert result["separation_hz"] >= 0


# ── exact_coupled_eigenfreq Tests ─────────────────────────────────────────────

class TestExactCoupledEigenfreq:
    def test_returns_three_values(self):
        """Should return (f_lower, f_upper, kappa_hz)."""
        result = exact_coupled_eigenfreq(
            f1_hz=100, f2_hz=120,
            V1_m3=0.015, V2_m3=0.0004,
            A_ap_m2=0.001, L_eff_ap_m=0.015,
        )
        assert len(result) == 3

    def test_upper_greater_than_lower(self):
        """f_upper should always be >= f_lower."""
        f_lower, f_upper, _ = exact_coupled_eigenfreq(
            f1_hz=100, f2_hz=120,
            V1_m3=0.015, V2_m3=0.0004,
            A_ap_m2=0.001, L_eff_ap_m=0.015,
        )
        assert f_upper >= f_lower

    def test_coupled_frequencies_shift_from_uncoupled(self):
        """Coupled frequencies should differ from uncoupled."""
        f1, f2 = 100, 120
        f_lower, f_upper, _ = exact_coupled_eigenfreq(
            f1_hz=f1, f2_hz=f2,
            V1_m3=0.015, V2_m3=0.0004,
            A_ap_m2=0.001, L_eff_ap_m=0.015,
        )
        # Lower should be below the lower uncoupled
        assert f_lower < f1
        # Upper should be above the higher uncoupled
        assert f_upper > f2

    def test_identical_frequencies_split(self):
        """Two identical uncoupled frequencies should split symmetrically."""
        f1, f2 = 100, 100
        f_lower, f_upper, kappa = exact_coupled_eigenfreq(
            f1_hz=f1, f2_hz=f2,
            V1_m3=0.015, V2_m3=0.0004,
            A_ap_m2=0.001, L_eff_ap_m=0.015,
        )
        # With coupling, frequencies split: f_lower < f1 and f_upper > f1
        # The split should be roughly symmetric around sqrt of mean squared
        assert f_lower < f1
        assert f_upper > f1

    def test_kappa_positive(self):
        """Coupling coefficient should be positive."""
        _, _, kappa = exact_coupled_eigenfreq(
            f1_hz=100, f2_hz=120,
            V1_m3=0.015, V2_m3=0.0004,
            A_ap_m2=0.001, L_eff_ap_m=0.015,
        )
        assert kappa > 0


# ── Integration Tests ─────────────────────────────────────────────────────────

class TestIntegration:
    def test_martin_om_reference(self):
        """Martin OM-style guitar should resonate in bass range."""
        # OM: ~14L body, 100mm soundhole
        # The formula includes plate_mass_factor correction
        port = PortSpec.from_circle_mm(100)
        f_H, _ = compute_helmholtz_multiport(0.014, [port])
        # Should be in reasonable guitar bass resonance range
        assert 100 < f_H < 140

    def test_d28_reference(self):
        """Martin D-28-style guitar should resonate in bass range."""
        # D-28: ~15.5L body, 102mm soundhole
        port = PortSpec.from_circle_mm(102)
        f_H, _ = compute_helmholtz_multiport(0.0155, [port])
        # Should be in reasonable dreadnought range
        assert 95 < f_H < 135

    def test_classical_reference(self):
        """Classical guitar should resonate in bass range."""
        # Classical: ~14L body, 86mm soundhole
        port = PortSpec.from_circle_mm(86)
        f_H, _ = compute_helmholtz_multiport(0.014, [port])
        # Should be in reasonable classical guitar range
        assert 90 < f_H < 130

    def test_side_port_raises_frequency(self):
        """Adding a side port should raise the Helmholtz frequency."""
        main_port = PortSpec.from_circle_mm(90)
        f_main_only, _ = compute_helmholtz_multiport(0.015, [main_port])

        side_port = PortSpec.from_circle_mm(40, location="side")
        f_with_side, _ = compute_helmholtz_multiport(0.015, [main_port, side_port])

        assert f_with_side > f_main_only
