"""
Tests for Body Curvature Correction — Instrument-Specific Profiles

Validates that:
1. InstrumentCurvatureProfile loads correctly for known specs
2. Zone-specific stability thresholds work
3. get_correction_epsilon returns instrument-appropriate values
4. Unknown specs fall back to generic profile

Author: Production Shop
Date: 2026-04-14
"""

import pytest

from app.instrument_geometry.curvature_correction import (
    InstrumentCurvatureProfile,
    get_instrument_profile,
    get_correction_epsilon,
    ZONE_DEFAULT,
    ZONE_WAIST,
    ZONE_BOUT,
    ZONE_HORN_TIP,
    ZONE_CUTAWAY,
    MEASURED_RADII,
    DEFAULT_STABILITY_BY_ZONE,
)


class TestInstrumentCurvatureProfile:
    """Test InstrumentCurvatureProfile dataclass."""

    def test_default_profile_has_generic_name(self):
        """Profile without spec_name is labeled 'generic'."""
        profile = get_instrument_profile(None)
        assert profile.spec_name == "generic"

    def test_explorer_profile_has_low_min_radius(self):
        """Explorer allows smaller radii for sharp horn tips."""
        profile = get_instrument_profile("gibson_explorer")
        assert profile.min_profile_radius_mm < 30.0
        assert profile.min_profile_radius_mm == 15.0

    def test_dreadnought_profile_has_high_max_radius(self):
        """Acoustic guitars have larger, smoother curves."""
        profile = get_instrument_profile("dreadnought")
        assert profile.max_profile_radius_mm > 800.0
        assert profile.max_profile_radius_mm == 900.0

    def test_get_stability_returns_zone_specific_value(self):
        """Zone-specific stability thresholds override default."""
        profile = get_instrument_profile("gibson_explorer")
        # Horn tip should be looser than default
        horn_tip_stability = profile.get_stability(ZONE_HORN_TIP)
        default_stability = profile.get_stability(ZONE_DEFAULT)
        assert horn_tip_stability > default_stability
        assert horn_tip_stability == 0.85

    def test_get_stability_falls_back_to_default(self):
        """Unknown zone falls back to global stability_threshold."""
        profile = get_instrument_profile("stratocaster")
        unknown_zone = profile.get_stability("unknown_zone")
        # Should equal the global default
        assert unknown_zone == profile.stability_threshold


class TestMeasuredRadii:
    """Test empirical radius data."""

    def test_explorer_has_sharp_horn_tip(self):
        """Explorer horn_tip radius is smaller than waist."""
        explorer_radii = MEASURED_RADII.get("gibson_explorer", {})
        assert "horn_tip" in explorer_radii
        assert explorer_radii["horn_tip"] < explorer_radii.get("waist", 1000)
        assert explorer_radii["horn_tip"] == 25.0

    def test_dreadnought_has_smooth_bouts(self):
        """Dreadnought bout radius is larger than waist."""
        dread_radii = MEASURED_RADII.get("dreadnought", {})
        assert "bout" in dread_radii
        assert dread_radii["bout"] > dread_radii.get("waist", 0)
        assert dread_radii["bout"] == 280.0


class TestCorrectionEpsilon:
    """Test get_correction_epsilon function."""

    def test_micro_fragment_gets_zero_epsilon(self):
        """Micro fragments should not be simplified."""
        epsilon = get_correction_epsilon("stratocaster", ZONE_DEFAULT, "micro_fragment")
        assert epsilon == 0.0

    def test_horn_tip_zone_reduces_epsilon(self):
        """Horn tip zone should have tighter epsilon (0.5x)."""
        base = get_correction_epsilon("stratocaster", ZONE_DEFAULT, "profile_curve")
        horn = get_correction_epsilon("stratocaster", ZONE_HORN_TIP, "profile_curve")
        assert horn == base * 0.5

    def test_cutaway_zone_reduces_epsilon(self):
        """Cutaway zone should have tighter epsilon (0.75x)."""
        base = get_correction_epsilon("les_paul", ZONE_DEFAULT, "profile_curve")
        cutaway = get_correction_epsilon("les_paul", ZONE_CUTAWAY, "profile_curve")
        assert cutaway == base * 0.75


class TestProfileIntegration:
    """Test profile integration with CurvatureProfiler."""

    def test_profiler_accepts_profile(self):
        """CurvatureProfiler should accept instrument_profile parameter."""
        from app.services.curvature_profiler import CurvatureProfiler

        profile = get_instrument_profile("flying_v")
        profiler = CurvatureProfiler(instrument_profile=profile)

        # Profiler should use profile's thresholds
        assert profiler._stability_threshold_profile == profile.stability_threshold
        assert profiler._min_profile_radius_mm == profile.min_profile_radius_mm
        assert profiler.profile is profile

    def test_profiler_loads_profile_by_spec_name(self):
        """CurvatureProfiler should load profile when given spec_name."""
        from app.services.curvature_profiler import CurvatureProfiler

        profiler = CurvatureProfiler(spec_name="cuatro")

        # Should have cuatro-specific thresholds
        assert profiler.profile is not None
        assert profiler.profile.spec_name == "cuatro"
        assert profiler._max_profile_radius_mm == 500.0

    def test_profiler_uses_defaults_without_profile(self):
        """CurvatureProfiler without profile should use class defaults."""
        from app.services.curvature_profiler import CurvatureProfiler

        profiler = CurvatureProfiler()

        assert profiler.profile is None
        assert profiler._stability_threshold_profile == CurvatureProfiler._DEFAULT_STABILITY_PROFILE
        assert profiler._min_profile_radius_mm == CurvatureProfiler._DEFAULT_MIN_RADIUS_MM
