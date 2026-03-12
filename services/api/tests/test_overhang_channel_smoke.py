# tests/test_overhang_channel_smoke.py

"""
Smoke tests for fretboard overhang channel calculator.

GAP-05: Verifies overhang channel geometry for 24-fret guitars.
"""

import pytest
import math

from app.calculators.overhang_channel_calc import (
    calculate_overhang_channel,
    calculate_24fret_strat_overhang,
    calculate_24fret_lespaul_overhang,
    fret_position_from_nut_mm,
    interpolate_fretboard_width,
    OverhangChannelParams,
    ChannelShape,
)


class TestFretPositionCalculation:
    """Tests for fret position math."""

    def test_fret_12_is_half_scale(self):
        """12th fret is at half scale length."""
        scale = 648.0
        pos = fret_position_from_nut_mm(scale, 12)
        assert pos == pytest.approx(324.0, abs=0.1)

    def test_fret_24_position_648mm_scale(self):
        """24th fret position for 25.5\" scale."""
        pos = fret_position_from_nut_mm(648.0, 24)
        # 486.27mm from handoff doc
        assert pos == pytest.approx(486.27, abs=0.5)

    def test_fret_22_position_648mm_scale(self):
        """22nd fret position for 25.5\" scale."""
        pos = fret_position_from_nut_mm(648.0, 22)
        # 466.38mm from handoff doc
        assert pos == pytest.approx(466.38, abs=0.5)


class TestWidthInterpolation:
    """Tests for fretboard width interpolation."""

    def test_width_at_nut(self):
        """Width at position 0 equals nut width."""
        width = interpolate_fretboard_width(42.0, 56.0, 400.0, 0.0)
        assert width == pytest.approx(42.0, abs=0.01)

    def test_width_at_heel(self):
        """Width at heel position equals heel width."""
        width = interpolate_fretboard_width(42.0, 56.0, 400.0, 400.0)
        assert width == pytest.approx(56.0, abs=0.01)

    def test_width_at_midpoint(self):
        """Width at midpoint is average of nut and heel."""
        width = interpolate_fretboard_width(42.0, 56.0, 400.0, 200.0)
        expected = (42.0 + 56.0) / 2
        assert width == pytest.approx(expected, abs=0.01)


class TestNoOverhangNeeded:
    """Tests for guitars that don't need overhang channels."""

    def test_22_fret_no_overhang(self):
        """22-fret guitar needs no overhang channel."""
        result = calculate_overhang_channel(fret_count=22)
        assert result.overhang_length_mm == 0.0
        assert result.channel_length_mm == 0.0
        assert len(result.outline_points_mm) == 0

    def test_21_fret_no_overhang(self):
        """21-fret guitar needs no overhang channel."""
        result = calculate_overhang_channel(fret_count=21)
        assert result.overhang_length_mm == 0.0

    def test_no_overhang_includes_note(self):
        """No-overhang result includes explanatory note."""
        result = calculate_overhang_channel(fret_count=22)
        assert any("No overhang needed" in note for note in result.notes)


class TestOverhangGeometry:
    """Tests for overhang channel geometry calculation."""

    def test_24fret_has_overhang(self):
        """24-fret guitar has positive overhang length."""
        result = calculate_overhang_channel(fret_count=24)
        assert result.overhang_length_mm > 0
        # ~20mm overhang expected
        assert result.overhang_length_mm == pytest.approx(20.0, abs=2.0)

    def test_channel_extends_past_last_fret(self):
        """Channel end extends past the last fret position."""
        result = calculate_overhang_channel(fret_count=24, end_clearance_mm=2.0)
        assert result.channel_end_mm > result.fret_24_position_mm

    def test_channel_has_positive_depth(self):
        """Channel has positive depth for clearing fretboard."""
        result = calculate_overhang_channel(fret_count=24, channel_depth_mm=2.0)
        assert result.channel_depth_mm == 2.0

    def test_channel_width_includes_clearance(self):
        """Channel width is fretboard width + clearance."""
        result = calculate_overhang_channel(
            fret_count=24,
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            side_clearance_mm=3.0,
        )
        # Channel should be wider than fretboard at that position
        assert result.channel_width_at_end_mm > result.fretboard_width_at_24_mm


class TestOutlineGeneration:
    """Tests for channel outline point generation."""

    def test_squared_outline_is_closed(self):
        """Squared channel outline forms a closed polygon."""
        result = calculate_overhang_channel(
            fret_count=24,
            end_shape=ChannelShape.SQUARED,
        )
        outline = result.outline_points_mm
        assert len(outline) >= 4
        # First and last points should match (closed)
        assert outline[0] == pytest.approx(outline[-1], abs=0.001)

    def test_rounded_outline_is_closed(self):
        """Rounded channel outline forms a closed polygon."""
        result = calculate_overhang_channel(
            fret_count=24,
            end_shape=ChannelShape.ROUNDED,
        )
        outline = result.outline_points_mm
        assert len(outline) > 4  # More points for arc
        assert outline[0] == pytest.approx(outline[-1], abs=0.001)

    def test_contoured_outline_is_closed(self):
        """Contoured channel outline forms a closed polygon."""
        result = calculate_overhang_channel(
            fret_count=24,
            end_shape=ChannelShape.CONTOURED,
        )
        outline = result.outline_points_mm
        assert len(outline) > 10  # More points for smooth contour
        assert outline[0] == pytest.approx(outline[-1], abs=0.001)

    def test_outline_points_are_symmetric(self):
        """Outline has symmetric Y values (bass/treble sides)."""
        result = calculate_overhang_channel(
            fret_count=24,
            end_shape=ChannelShape.SQUARED,
        )
        outline = result.outline_points_mm

        # For squared, points 0 and 3 should have opposite Y (same X)
        # Point 0: (start, +half_width)
        # Point 3: (start, -half_width)
        assert outline[0][0] == pytest.approx(outline[3][0], abs=0.1)  # Same X
        assert outline[0][1] == pytest.approx(-outline[3][1], abs=0.1)  # Opposite Y


class TestPresetFunctions:
    """Tests for convenience preset functions."""

    def test_24fret_strat_preset(self):
        """24-fret Strat preset returns valid result."""
        result = calculate_24fret_strat_overhang()
        assert result.overhang_length_mm > 0
        assert result.fret_22_position_mm == pytest.approx(466.38, abs=1.0)
        assert len(result.outline_points_mm) > 0

    def test_24fret_lespaul_preset(self):
        """24-fret Les Paul preset returns valid result."""
        result = calculate_24fret_lespaul_overhang()
        assert result.overhang_length_mm > 0
        # Gibson 24.75" scale has different fret positions
        assert result.fret_22_position_mm < 466.0  # Shorter scale


class TestSerialization:
    """Tests for result serialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict() includes all expected fields."""
        result = calculate_overhang_channel(fret_count=24)
        data = result.to_dict()

        expected_keys = [
            "fret_22_position_mm",
            "fret_24_position_mm",
            "body_junction_mm",
            "overhang_length_mm",
            "channel_start_mm",
            "channel_end_mm",
            "channel_length_mm",
            "channel_depth_mm",
            "outline_points_mm",
            "notes",
        ]
        for key in expected_keys:
            assert key in data

    def test_to_dict_values_are_rounded(self):
        """to_dict() rounds values appropriately."""
        result = calculate_overhang_channel(fret_count=24)
        data = result.to_dict()

        # Check that values are numeric and reasonable
        assert isinstance(data["overhang_length_mm"], float)
        assert 15.0 < data["overhang_length_mm"] < 25.0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_25_fret_guitar(self):
        """25-fret guitar has larger overhang."""
        result_24 = calculate_overhang_channel(fret_count=24)
        result_25 = calculate_overhang_channel(fret_count=25)
        assert result_25.overhang_length_mm > result_24.overhang_length_mm

    def test_different_scale_lengths(self):
        """Different scale lengths produce different results."""
        result_fender = calculate_overhang_channel(
            scale_length_mm=647.7, fret_count=24
        )
        result_gibson = calculate_overhang_channel(
            scale_length_mm=628.65, fret_count=24
        )
        # Gibson has shorter overhang (shorter scale)
        assert result_gibson.overhang_length_mm < result_fender.overhang_length_mm

    def test_params_object_works(self):
        """OverhangChannelParams object works correctly."""
        params = OverhangChannelParams(
            scale_length_mm=647.7,
            fret_count=24,
            channel_depth_mm=3.0,
        )
        result = calculate_overhang_channel(params)
        assert result.channel_depth_mm == 3.0
