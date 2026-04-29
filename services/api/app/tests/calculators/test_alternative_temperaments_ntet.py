# services/api/app/tests/calculators/test_alternative_temperaments_ntet.py
"""
Tests for N-TET temperament support and temperament resolution dispatcher.

Sprint FRET-A Phase 1.5, Commit 1.
"""

import pytest

from app.calculators.alternative_temperaments import (
    TemperamentSystem,
    compute_n_tet_ratios,
    resolve_temperament_ratios,
    compute_fret_positions_from_ratios_mm,
)
from app.instrument_geometry.neck.fret_math import (
    compute_fret_positions_mm,
    perpendicular_distance_for_fret,
)


class TestNTET:
    """Tests for compute_n_tet_ratios function."""

    def test_12tet_matches_existing_compute_fret_positions_mm(self):
        """compute_n_tet_ratios(12, 22) → ratios → positions must equal
        compute_fret_positions_mm(scale, 22) within 1e-9 mm."""
        scale = 647.7
        fret_count = 22

        ratios = compute_n_tet_ratios(12, fret_count)
        positions_via_ratios = compute_fret_positions_from_ratios_mm(scale, ratios)
        positions_direct = compute_fret_positions_mm(scale, fret_count)

        assert len(positions_via_ratios) == len(positions_direct)
        for via_ratio, direct in zip(positions_via_ratios, positions_direct):
            assert abs(via_ratio - direct) < 1e-9, (
                f"Position mismatch: {via_ratio} vs {direct}"
            )

    def test_19tet_first_fret_ratio(self):
        """First fret ratio in 19-TET should be 2^(1/19)."""
        ratios = compute_n_tet_ratios(19, 19)
        expected_first = 2 ** (1 / 19)
        assert abs(ratios[0] - expected_first) < 1e-12
        # Last fret (fret 19) should be octave
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_24tet_quarter_tones(self):
        """24-TET fret 2 ≈ 12-TET fret 1 (quarter-tone relationship)."""
        ratios_24 = compute_n_tet_ratios(24, 24)
        ratios_12 = compute_n_tet_ratios(12, 12)
        # Fret 2 of 24-TET should equal fret 1 of 12-TET
        assert abs(ratios_24[1] - ratios_12[0]) < 1e-12

    def test_31tet_octave_at_fret_31(self):
        """31-TET should reach octave (2.0) at fret 31."""
        ratios = compute_n_tet_ratios(31, 31)
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_n_tet_validation_n_too_small(self):
        """n < 2 should raise ValueError."""
        with pytest.raises(ValueError, match=">= 2"):
            compute_n_tet_ratios(1, 12)

    def test_n_tet_validation_fret_count_zero(self):
        """fret_count < 1 should raise ValueError."""
        with pytest.raises(ValueError, match=">= 1"):
            compute_n_tet_ratios(12, 0)


class TestResolveTemperament:
    """Tests for resolve_temperament_ratios dispatcher."""

    def test_resolves_12tet(self):
        """12-TET should produce 22 ratios with octave at fret 12."""
        ratios = resolve_temperament_ratios(TemperamentSystem.EQUAL_12TET, 22)
        assert len(ratios) == 22
        # Fret 12 should be octave (index 11)
        assert abs(ratios[11] - 2.0) < 1e-9

    def test_resolves_19tet(self):
        """19-TET should produce correct ratios."""
        ratios = resolve_temperament_ratios(TemperamentSystem.EQUAL_19TET, 19)
        assert len(ratios) == 19
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_resolves_24tet(self):
        """24-TET should produce correct ratios."""
        ratios = resolve_temperament_ratios(TemperamentSystem.EQUAL_24TET, 24)
        assert len(ratios) == 24
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_resolves_31tet(self):
        """31-TET should produce correct ratios."""
        ratios = resolve_temperament_ratios(TemperamentSystem.EQUAL_31TET, 31)
        assert len(ratios) == 31
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_resolves_just_major(self):
        """Just major should produce 12 ratios per octave."""
        ratios = resolve_temperament_ratios(TemperamentSystem.JUST_MAJOR, 12)
        assert len(ratios) == 12
        # Ratios should be monotonically increasing
        for i in range(1, len(ratios)):
            assert ratios[i] > ratios[i - 1]

    def test_resolves_pythagorean(self):
        """Pythagorean should produce valid ratios."""
        ratios = resolve_temperament_ratios(TemperamentSystem.PYTHAGOREAN, 12)
        assert len(ratios) == 12
        # Perfect fifth at fret 7 should be close to 3/2 = 1.5
        # (Actually in Pythagorean tuning, the fifth IS 3/2)
        assert abs(ratios[6] - 1.5) < 0.01

    def test_resolves_meantone(self):
        """Meantone should produce valid ratios."""
        ratios = resolve_temperament_ratios(TemperamentSystem.MEANTONE_QUARTER, 12)
        assert len(ratios) == 12

    def test_custom_requires_ratios(self):
        """CUSTOM without custom_ratios should raise ValueError."""
        with pytest.raises(ValueError, match="CUSTOM"):
            resolve_temperament_ratios(TemperamentSystem.CUSTOM, 12)

    def test_custom_passes_through(self):
        """CUSTOM with ratios should return them verbatim."""
        custom = [1.1, 1.5, 2.0]
        ratios = resolve_temperament_ratios(
            TemperamentSystem.CUSTOM, 3, custom_ratios=custom
        )
        assert ratios == custom


class TestPerpendicularDistanceForFret:
    """Tests for perpendicular_distance_for_fret helper."""

    def test_fret_0_is_zero(self):
        """Fret 0 (nut) should have PD = 0."""
        pd = perpendicular_distance_for_fret(0)
        assert pd == 0.0

    def test_fret_12_is_half(self):
        """Fret 12 should have PD = 0.5 (octave)."""
        pd = perpendicular_distance_for_fret(12)
        assert abs(pd - 0.5) < 1e-9

    def test_fret_24_is_three_quarters(self):
        """Fret 24 should have PD = 0.75."""
        pd = perpendicular_distance_for_fret(24)
        assert abs(pd - 0.75) < 1e-9

    def test_fret_7_known_value(self):
        """Fret 7 should have PD ≈ 0.33258."""
        pd = perpendicular_distance_for_fret(7)
        assert abs(pd - 0.33258) < 1e-4

    def test_negative_fret_raises(self):
        """Negative fret number should raise ValueError."""
        with pytest.raises(ValueError, match=">= 0"):
            perpendicular_distance_for_fret(-1)

    def test_invalid_semitones_raises(self):
        """semitones_per_octave < 1 should raise ValueError."""
        with pytest.raises(ValueError, match=">= 1"):
            perpendicular_distance_for_fret(12, semitones_per_octave=0)


class TestFretFindParity:
    """Tests for FretFind2D parameter parity in compute_multiscale_fret_positions_mm."""

    def test_perpendicular_distance_half_matches_fret_12(self):
        """PD=0.5 should produce same perpendicular fret as perpendicular_fret=12."""
        from app.instrument_geometry.neck.fret_math import compute_multiscale_fret_positions_mm

        result_pd = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
            perpendicular_distance=0.5,
        )
        result_int = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
            perpendicular_fret=12,
        )
        # Compare 12th fret is_perpendicular flag on both
        for s in range(6):
            assert result_pd[11][s].is_perpendicular is True
            assert result_int[11][s].is_perpendicular is True

    def test_perpendicular_distance_third_matches_fret_7(self):
        """PD for fret 7 should be ~0.33258."""
        pd = perpendicular_distance_for_fret(7)
        assert abs(pd - 0.33258) < 1e-4

    def test_per_string_scale_array_matches_linear_interp(self):
        """A linear-progression scale_lengths_mm array should equal bass/treble interp."""
        from app.instrument_geometry.neck.fret_math import compute_multiscale_fret_positions_mm

        # 6 strings, linear from 686 to 648
        linear = [686.0 - (686.0 - 648.0) * i / 5 for i in range(6)]

        result_array = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
            scale_lengths_mm=linear,
        )
        result_interp = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
        )
        for f in range(22):
            for s in range(6):
                assert abs(result_array[f][s].x_mm - result_interp[f][s].x_mm) < 1e-6
                assert abs(result_array[f][s].y_mm - result_interp[f][s].y_mm) < 1e-6

    def test_per_string_scale_nonlinear_diverges_from_interp(self):
        """A non-linear scale array should produce different geometry than linear interp."""
        from app.instrument_geometry.neck.fret_math import compute_multiscale_fret_positions_mm

        nonlinear = [686.0, 685.0, 680.0, 670.0, 655.0, 648.0]  # bunched at bass
        result_nonlinear = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
            scale_lengths_mm=nonlinear,
        )
        result_interp = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
        )
        # At least one fret position should differ by more than 0.1mm
        max_diff = max(
            abs(result_nonlinear[f][s].x_mm - result_interp[f][s].x_mm)
            for f in range(22) for s in range(6)
        )
        assert max_diff > 0.1

    def test_v1_signature_byte_identical(self):
        """Call with no new params — output must match pre-Phase-1.5 baseline."""
        from app.instrument_geometry.neck.fret_math import compute_multiscale_fret_positions_mm

        result = compute_multiscale_fret_positions_mm(
            bass_scale_mm=647.7, treble_scale_mm=647.7,
            fret_count=22, string_count=6,
        )
        # Single-scale collapses to compute_fret_positions_mm
        baseline = compute_fret_positions_mm(647.7, 22)
        for f in range(22):
            # Take any string (geometry is identical when bass==treble)
            assert abs(result[f][0].x_mm - baseline[f]) < 1e-9

    def test_pd_and_int_fret_both_set_raises(self):
        """Specifying both perpendicular_distance and perpendicular_fret raises."""
        from app.instrument_geometry.neck.fret_math import compute_multiscale_fret_positions_mm

        with pytest.raises(ValueError, match="pick one"):
            compute_multiscale_fret_positions_mm(
                bass_scale_mm=686.0, treble_scale_mm=648.0,
                fret_count=22, string_count=6,
                perpendicular_fret=12,
                perpendicular_distance=0.5,
            )
