# services/api/app/tests/calculators/test_fret_slots_math.py
"""
Fret Slots Math Tests

Pure scale/intonation validation tests that verify fret math
matches 12-TET (12-tone equal temperament) formulas.

Wave 2 Implementation (Math Golden Path)
"""

from __future__ import annotations

import math
import pytest

from app.instrument_geometry.neck.fret_math import (
    compute_fret_positions_mm,
    compute_multiscale_fret_positions_mm,
    FanFretPoint,
    SEMITONE_RATIO,
    PERP_ANGLE_EPS,
)


class TestFretPositionsMath:
    """Tests for standard (non-fan) fret position calculations."""
    
    def test_semitone_ratio_is_12th_root_of_2(self):
        """Verify SEMITONE_RATIO equals 2^(1/12)."""
        expected = 2.0 ** (1.0 / 12.0)
        assert math.isclose(SEMITONE_RATIO, expected, rel_tol=1e-10)
    
    def test_fret_positions_strictly_increasing(self):
        """Fret positions should be strictly increasing from nut."""
        scale_mm = 648.0
        fret_count = 24
        
        frets = compute_fret_positions_mm(scale_mm, fret_count)
        
        assert len(frets) == fret_count
        for i in range(1, len(frets)):
            assert frets[i] > frets[i - 1], f"Fret {i+1} is not further than fret {i}"
    
    def test_12th_fret_is_half_scale_length(self):
        """
        12th fret should be at exactly half the scale length (octave).
        This is a fundamental property of 12-TET tuning.
        """
        scale_mm = 648.0
        frets = compute_fret_positions_mm(scale_mm, 12)
        
        twelfth_fret = frets[11]  # 0-indexed
        half_scale = scale_mm / 2.0
        
        assert math.isclose(twelfth_fret, half_scale, rel_tol=0.001), (
            f"12th fret ({twelfth_fret:.4f}mm) not at half scale ({half_scale:.4f}mm)"
        )
    
    def test_24th_fret_is_three_quarters_scale(self):
        """24th fret (2 octaves) should be at 3/4 of scale length."""
        scale_mm = 648.0
        frets = compute_fret_positions_mm(scale_mm, 24)
        
        fret_24 = frets[23]
        three_quarters = scale_mm * 0.75
        
        assert math.isclose(fret_24, three_quarters, rel_tol=0.001), (
            f"24th fret ({fret_24:.4f}mm) not at 3/4 scale ({three_quarters:.4f}mm)"
        )
    
    def test_last_fret_less_than_scale_length(self):
        """Last fret should always be less than scale length."""
        for scale_mm in [625.0, 648.0, 686.0]:
            for fret_count in [20, 22, 24]:
                frets = compute_fret_positions_mm(scale_mm, fret_count)
                assert frets[-1] < scale_mm
    
    def test_first_fret_reasonable_distance_from_nut(self):
        """First fret should be about 3-4% of scale length from nut."""
        scale_mm = 648.0
        frets = compute_fret_positions_mm(scale_mm, 22)
        
        first_fret = frets[0]
        # First fret ≈ scale / 17.817 ≈ 36.37mm for 648mm scale
        expected = scale_mm / 17.817
        
        assert math.isclose(first_fret, expected, rel_tol=0.01)
    
    def test_various_standard_scale_lengths(self):
        """Test common scale lengths used in guitar building."""
        scales = {
            "Fender": 647.7,    # 25.5"
            "Gibson": 628.65,  # 24.75"
            "PRS": 635.0,      # 25"
            "Baritone": 686.0, # 27"
        }
        
        for name, scale_mm in scales.items():
            frets = compute_fret_positions_mm(scale_mm, 22)
            twelfth = frets[11]
            assert math.isclose(twelfth, scale_mm / 2.0, rel_tol=0.001), (
                f"{name} scale: 12th fret incorrect"
            )


class TestMultiscaleFretPositions:
    """Tests for fan-fret (multiscale) calculations."""
    
    def test_multiscale_returns_fan_fret_points(self):
        """Multiscale should return FanFretPoint objects."""
        frets = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0,
            treble_scale_mm=648.0,
            fret_count=22,
            string_count=6,
            perpendicular_fret=7,
        )
        
        assert len(frets) == 22
        assert len(frets[0]) == 6  # 6 strings
        assert isinstance(frets[0][0], FanFretPoint)
    
    def test_perpendicular_fret_is_marked(self):
        """The designated perpendicular fret should be marked."""
        perp_fret = 7
        frets = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0,
            treble_scale_mm=648.0,
            fret_count=22,
            string_count=6,
            perpendicular_fret=perp_fret,
        )
        
        # 7th fret is index 6 (0-indexed)
        for point in frets[perp_fret - 1]:
            assert point.is_perpendicular is True
    
    def test_non_perpendicular_frets_have_angle(self):
        """Non-perpendicular frets should have non-zero angles."""
        perp_fret = 12
        frets = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0,
            treble_scale_mm=648.0,
            fret_count=22,
            string_count=6,
            perpendicular_fret=perp_fret,
        )
        
        # Check fret 1 (should have an angle)
        assert frets[0][0].is_perpendicular is False
        assert abs(frets[0][0].angle_rad) > PERP_ANGLE_EPS
    
    def test_equal_scales_produces_straight_frets(self):
        """Equal bass/treble scales should produce nearly straight frets."""
        frets = compute_multiscale_fret_positions_mm(
            bass_scale_mm=648.0,
            treble_scale_mm=648.0,
            fret_count=22,
            string_count=6,
            perpendicular_fret=12,
        )
        
        for fret_line in frets:
            for point in fret_line:
                # All angles should be very small
                assert abs(point.angle_rad) < 0.01, (
                    f"Fret {point.fret_number} has unexpected angle with equal scales"
                )
    
    def test_bass_positions_follow_bass_scale(self):
        """Bass string positions should follow bass scale length."""
        bass_scale = 686.0
        treble_scale = 648.0
        
        frets = compute_multiscale_fret_positions_mm(
            bass_scale_mm=bass_scale,
            treble_scale_mm=treble_scale,
            fret_count=22,
            string_count=6,
            perpendicular_fret=12,
        )
        
        # Check 12th fret bass position
        bass_12th = frets[11][0].x_mm  # First string is bass
        expected = bass_scale / 2.0
        
        assert math.isclose(bass_12th, expected, rel_tol=0.01)
    
    def test_treble_positions_follow_treble_scale(self):
        """Treble string positions should follow treble scale length."""
        bass_scale = 686.0
        treble_scale = 648.0
        
        frets = compute_multiscale_fret_positions_mm(
            bass_scale_mm=bass_scale,
            treble_scale_mm=treble_scale,
            fret_count=22,
            string_count=6,
            perpendicular_fret=12,
        )
        
        # Check 12th fret treble position
        treble_12th = frets[11][5].x_mm  # Last string is treble
        expected = treble_scale / 2.0
        
        assert math.isclose(treble_12th, expected, rel_tol=0.01)


class TestFanFretPointDataclass:
    """Tests for FanFretPoint dataclass properties."""
    
    def test_fan_fret_point_position_tuple(self):
        """position_mm property should return (x, y) tuple."""
        pt = FanFretPoint(
            fret_number=5,
            string_index=2,
            x_mm=100.0,
            y_mm=-10.0,
        )
        
        assert pt.position_mm == (100.0, -10.0)
    
    def test_fan_fret_point_angle_deg(self):
        """angle_deg property should convert radians to degrees."""
        angle_rad = math.pi / 6  # 30 degrees
        pt = FanFretPoint(
            fret_number=5,
            string_index=2,
            x_mm=100.0,
            y_mm=-10.0,
            angle_rad=angle_rad,
        )
        
        assert math.isclose(pt.angle_deg, 30.0, rel_tol=0.001)
    
    def test_fan_fret_point_distance_to(self):
        """distance_to should calculate Euclidean distance."""
        pt1 = FanFretPoint(fret_number=1, string_index=0, x_mm=0.0, y_mm=0.0)
        pt2 = FanFretPoint(fret_number=1, string_index=5, x_mm=3.0, y_mm=4.0)
        
        assert math.isclose(pt1.distance_to(pt2), 5.0, rel_tol=0.001)
