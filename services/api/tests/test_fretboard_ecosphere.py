"""
Tests for the Fretboard Ecosphere canonical schema.

Sprint FRET-A Phase 1: Core schema validation tests.
"""

import pytest
from pydantic import ValidationError

from app.instrument_geometry.neck.fretboard_ecosphere import (
    FretboardEcosphere,
    FretboardInput,
    FretLine,
    FretPoint,
    RadiusSpec,
    ScaleType,
    StringPath,
    TemperamentType,
)


class TestFretboardInput:
    """Tests for input validation."""

    def test_default_input_valid(self):
        """Default input parameters should be valid."""
        params = FretboardInput()
        assert params.scale_length_mm == 648.0
        assert params.fret_count == 22
        assert params.string_count == 6

    def test_standard_scale_no_bass_required(self):
        """Standard scale type doesn't require bass_scale_length_mm."""
        params = FretboardInput(scale_type=ScaleType.STANDARD)
        assert params.bass_scale_length_mm is None

    def test_multiscale_requires_bass_scale(self):
        """Multiscale requires bass_scale_length_mm."""
        with pytest.raises(ValidationError) as exc_info:
            FretboardInput(scale_type=ScaleType.MULTISCALE)
        assert "bass_scale_length_mm required" in str(exc_info.value)

    def test_multiscale_valid_config(self):
        """Valid multiscale configuration."""
        params = FretboardInput(
            scale_type=ScaleType.MULTISCALE,
            scale_length_mm=648.0,
            bass_scale_length_mm=686.0,
            perpendicular_fret=7,
        )
        assert params.scale_type == ScaleType.MULTISCALE
        assert params.bass_scale_length_mm == 686.0

    def test_bass_scale_should_be_larger(self):
        """Bass scale should be >= treble scale (convention)."""
        with pytest.raises(ValidationError):
            FretboardInput(
                scale_type=ScaleType.MULTISCALE,
                scale_length_mm=686.0,
                bass_scale_length_mm=648.0,  # Bass < treble
            )

    def test_perpendicular_fret_within_range(self):
        """Perpendicular fret must be within fret count."""
        with pytest.raises(ValidationError):
            FretboardInput(
                scale_type=ScaleType.MULTISCALE,
                scale_length_mm=648.0,
                bass_scale_length_mm=686.0,
                fret_count=22,
                perpendicular_fret=25,  # > 22
            )

    def test_fret_count_limits(self):
        """Fret count must be 1-36."""
        with pytest.raises(ValidationError):
            FretboardInput(fret_count=0)
        with pytest.raises(ValidationError):
            FretboardInput(fret_count=37)

    def test_string_count_limits(self):
        """String count must be 1-18."""
        with pytest.raises(ValidationError):
            FretboardInput(string_count=0)
        with pytest.raises(ValidationError):
            FretboardInput(string_count=19)


class TestRadiusSpec:
    """Tests for radius specification."""

    def test_flat_fretboard(self):
        """None radius = flat fretboard."""
        spec = RadiusSpec()
        assert spec.is_flat
        assert not spec.is_compound
        assert spec.radius_at_position(0.5) is None

    def test_single_radius(self):
        """Single constant radius."""
        spec = RadiusSpec(nut_radius_mm=241.3)
        assert not spec.is_flat
        assert not spec.is_compound
        assert spec.radius_at_position(0.0) == 241.3
        assert spec.radius_at_position(1.0) == 241.3

    def test_compound_radius(self):
        """Compound radius interpolation."""
        spec = RadiusSpec(nut_radius_mm=241.3, heel_radius_mm=304.8)
        assert spec.is_compound
        # At nut
        assert spec.radius_at_position(0.0) == 241.3
        # At heel
        assert spec.radius_at_position(1.0) == 304.8
        # Halfway
        mid = spec.radius_at_position(0.5)
        assert 270.0 < mid < 275.0  # ~273.05


class TestFretboardEcosphere:
    """Tests for computed FretboardEcosphere."""

    def test_compute_standard_frets(self):
        """Compute standard fretboard geometry."""
        params = FretboardInput()
        eco = FretboardEcosphere.compute(params)

        # Should have fret_count + 1 fret lines (includes nut)
        assert len(eco.fret_lines) == 23  # 0-22

        # Fret 0 (nut) should be at x=0
        nut = eco.get_fret_line(0)
        assert nut is not None
        assert nut.center_x_mm == 0.0

        # All standard frets should be perpendicular
        for fl in eco.fret_lines:
            assert fl.is_perpendicular

    def test_compute_multiscale_frets(self):
        """Compute multiscale fretboard geometry."""
        params = FretboardInput(
            scale_type=ScaleType.MULTISCALE,
            scale_length_mm=648.0,
            bass_scale_length_mm=686.0,
            perpendicular_fret=7,
            string_count=6,
        )
        eco = FretboardEcosphere.compute(params)

        # Perpendicular fret (7) should have angle = 0
        perp = eco.get_fret_line(7)
        assert perp is not None
        assert perp.is_perpendicular
        assert abs(perp.angle_rad) < 0.001

        # Other frets should be angled
        fret_1 = eco.get_fret_line(1)
        assert fret_1 is not None
        assert not fret_1.is_perpendicular
        assert abs(fret_1.angle_rad) > 0.001

        # Max angle should be recorded
        assert eco.max_fret_angle_deg > 0.0

    def test_string_paths(self):
        """String paths should be computed."""
        params = FretboardInput(string_count=6)
        eco = FretboardEcosphere.compute(params)

        assert len(eco.string_paths) == 6

        # Bass string (index 0)
        bass = eco.get_string_path(0)
        assert bass is not None
        assert bass.scale_length_mm == 648.0
        assert bass.nut_position[0] == 0.0  # x = 0 at nut

        # Treble string (index 5)
        treble = eco.get_string_path(5)
        assert treble is not None

    def test_outline_points(self):
        """Outline should be a 4-point polygon."""
        params = FretboardInput(nut_width_mm=42.0, heel_width_mm=56.0)
        eco = FretboardEcosphere.compute(params)

        assert len(eco.outline_points) == 4
        # Nut points at x=0
        assert eco.outline_points[0][0] == 0.0
        assert eco.outline_points[3][0] == 0.0
        # Width at nut
        assert abs(eco.outline_points[0][1]) == 21.0  # half of 42
        assert abs(eco.outline_points[3][1]) == 21.0

    def test_perpendicular_distance_standard(self):
        """Perpendicular distance for standard frets."""
        params = FretboardInput()
        eco = FretboardEcosphere.compute(params)

        # For standard fretting, perpendicular distance = x position
        # All strings have same perpendicular distance at each fret
        fret_12_distance = eco.perpendicular_distance(12, 0)
        # 12th fret should be at half scale length
        assert 323.0 < fret_12_distance < 325.0  # ~324mm

        # Same for all strings
        for string in range(6):
            assert abs(eco.perpendicular_distance(12, string) - fret_12_distance) < 0.01

    def test_perpendicular_distance_multiscale(self):
        """Perpendicular distance varies per string for multiscale."""
        params = FretboardInput(
            scale_type=ScaleType.MULTISCALE,
            scale_length_mm=648.0,
            bass_scale_length_mm=686.0,
            perpendicular_fret=7,
        )
        eco = FretboardEcosphere.compute(params)

        # At perpendicular fret, all strings should have same distance
        perp_bass = eco.perpendicular_distance(7, 0)
        perp_treble = eco.perpendicular_distance(7, 5)
        assert abs(perp_bass - perp_treble) < 0.1

        # At other frets, bass and treble differ
        fret_1_bass = eco.perpendicular_distance(1, 0)
        fret_1_treble = eco.perpendicular_distance(1, 5)
        # Bass scale is longer, so fret positions differ
        assert abs(fret_1_bass - fret_1_treble) > 0.5

    def test_scala_intervals(self):
        """Export Scala-compatible intervals."""
        params = FretboardInput(fret_count=12)
        eco = FretboardEcosphere.compute(params)

        intervals = eco.to_scala_intervals()

        # Should have 12 intervals (frets 1-12)
        assert len(intervals) == 12

        # 12th fret should be ~1200 cents (octave)
        assert 1199.0 < intervals[-1] < 1201.0

        # Intervals should be monotonically increasing
        for i in range(1, len(intervals)):
            assert intervals[i] > intervals[i - 1]

    def test_intonation_offsets(self):
        """Intonation offsets should affect bridge position."""
        params = FretboardInput(
            intonation_offsets_mm={0: 2.5, 5: 1.5},  # Bass +2.5, treble +1.5
        )
        eco = FretboardEcosphere.compute(params)

        bass = eco.get_string_path(0)
        treble = eco.get_string_path(5)

        assert bass.intonation_offset_mm == 2.5
        assert treble.intonation_offset_mm == 1.5
        assert bass.compensated_length_mm == 650.5
        assert treble.compensated_length_mm == 649.5

    def test_temperament_equal_19(self):
        """19-TET should produce 19 frets per octave."""
        params = FretboardInput(
            temperament=TemperamentType.EQUAL_19,
            fret_count=19,
        )
        eco = FretboardEcosphere.compute(params)

        # 19th fret should be at octave position
        fret_19 = eco.get_fret_line(19)
        assert fret_19 is not None
        # Octave = half scale length
        assert 323.0 < fret_19.center_x_mm < 325.0


class TestFretLineProperties:
    """Tests for FretLine computed properties."""

    def test_bass_and_treble_points(self):
        """Bass/treble point properties."""
        points = [
            FretPoint(fret_number=1, string_index=0, x_mm=36.0, y_mm=-21.0),
            FretPoint(fret_number=1, string_index=5, x_mm=36.0, y_mm=21.0),
        ]
        fl = FretLine(fret_number=1, points=points)

        assert fl.bass_point is not None
        assert fl.bass_point.y_mm == -21.0
        assert fl.treble_point is not None
        assert fl.treble_point.y_mm == 21.0

    def test_center_x(self):
        """Center x calculation."""
        # For angled fret
        points = [
            FretPoint(fret_number=1, string_index=0, x_mm=38.0, y_mm=-21.0),
            FretPoint(fret_number=1, string_index=1, x_mm=36.0, y_mm=21.0),
        ]
        fl = FretLine(fret_number=1, points=points)
        assert fl.center_x_mm == 37.0


class TestImmutability:
    """Tests for model immutability."""

    def test_fretboard_input_frozen(self):
        """FretboardInput should be frozen."""
        params = FretboardInput()
        with pytest.raises(ValidationError):
            params.scale_length_mm = 600.0

    def test_fretboard_ecosphere_frozen(self):
        """FretboardEcosphere should be frozen."""
        params = FretboardInput()
        eco = FretboardEcosphere.compute(params)
        with pytest.raises(ValidationError):
            eco.total_length_mm = 999.0
