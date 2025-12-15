"""
Tests for the instrument_geometry package.

These tests validate the core instrument geometry calculations
against known values from lutherie references.

See docs/KnowledgeBase/Instrument_Geometry/ for formula derivations.
"""

import pytest
from math import isclose

from app.instrument_geometry.scale_length import (
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    compute_compensated_scale_length_mm,
    compute_fret_to_bridge_mm,
    SCALE_LENGTHS_MM,
)
from app.instrument_geometry.profiles import (
    InstrumentSpec,
    FretboardSpec,
    BridgeSpec,
    RadiusProfile,
)
from app.instrument_geometry.fretboard_geometry import (
    compute_fretboard_outline,
    compute_width_at_position_mm,
    compute_fret_slot_lines,
)
from app.instrument_geometry.radius_profiles import (
    compute_compound_radius_at_fret,
    compute_radius_drop_mm,
    compute_radius_arc_points,
)
from app.instrument_geometry.bridge_geometry import (
    compute_bridge_location_mm,
    compute_saddle_positions_mm,
)


# ─────────────────────────────────────────────────────────────────────────────
# Scale Length Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFretPositions:
    """Test fret position calculations."""

    def test_12th_fret_is_half_scale_length(self):
        """The 12th fret should be at exactly half the scale length."""
        scale = 648.0  # 25.5" Fender scale
        positions = compute_fret_positions_mm(scale, 22)
        
        # 12th fret (index 11) should be at half scale
        assert isclose(positions[11], scale / 2, rel_tol=1e-6)

    def test_fret_positions_increasing(self):
        """Fret positions should monotonically increase."""
        positions = compute_fret_positions_mm(648.0, 22)
        
        for i in range(1, len(positions)):
            assert positions[i] > positions[i - 1]

    def test_fret_positions_count(self):
        """Should return exactly fret_count positions."""
        for count in [19, 20, 21, 22, 24]:
            positions = compute_fret_positions_mm(648.0, count)
            assert len(positions) == count

    def test_known_fret_positions_fender(self):
        """Test against known Fender 25.5" scale positions."""
        # These are industry-standard values
        scale = 648.0
        positions = compute_fret_positions_mm(scale, 22)
        
        # Known positions (rounded to 2 decimal places)
        # Note: Index 0 = 1st fret, Index 11 = 12th fret, etc.
        expected = {
            0: 36.40,   # 1st fret
            4: 162.65,  # 5th fret
            11: 324.00, # 12th fret (octave = half scale)
        }
        
        for idx, expected_pos in expected.items():
            assert isclose(positions[idx], expected_pos, rel_tol=0.01)

    def test_invalid_scale_length_raises(self):
        """Zero or negative scale length should raise ValueError."""
        with pytest.raises(ValueError):
            compute_fret_positions_mm(0, 22)
        with pytest.raises(ValueError):
            compute_fret_positions_mm(-100, 22)

    def test_invalid_fret_count_raises(self):
        """Zero or negative fret count should raise ValueError."""
        with pytest.raises(ValueError):
            compute_fret_positions_mm(648.0, 0)
        with pytest.raises(ValueError):
            compute_fret_positions_mm(648.0, -5)


class TestFretSpacing:
    """Test fret spacing calculations."""

    def test_spacing_decreases(self):
        """Fret spacing should decrease as you go higher."""
        spacings = compute_fret_spacing_mm(648.0, 22)
        
        for i in range(1, len(spacings)):
            assert spacings[i] < spacings[i - 1]

    def test_spacing_sum_equals_last_position(self):
        """Sum of spacings should equal the last fret position."""
        scale = 648.0
        fret_count = 22
        
        positions = compute_fret_positions_mm(scale, fret_count)
        spacings = compute_fret_spacing_mm(scale, fret_count)
        
        assert isclose(sum(spacings), positions[-1], rel_tol=1e-6)


class TestCompensation:
    """Test scale length compensation."""

    def test_saddle_compensation_adds(self):
        """Saddle compensation should increase effective length."""
        result = compute_compensated_scale_length_mm(648.0, 2.5)
        assert result == 650.5

    def test_nut_compensation_subtracts(self):
        """Nut compensation should decrease effective length."""
        result = compute_compensated_scale_length_mm(648.0, 2.5, 0.5)
        assert result == 650.0

    def test_fret_to_bridge_distance(self):
        """Distance from fret to bridge should be scale - fret position."""
        scale = 648.0
        distance = compute_fret_to_bridge_mm(scale, 12)
        assert isclose(distance, 324.0, rel_tol=1e-6)


# ─────────────────────────────────────────────────────────────────────────────
# Profile Dataclass Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestInstrumentSpec:
    """Test InstrumentSpec dataclass."""

    def test_basic_creation(self):
        """Should create a basic instrument spec."""
        spec = InstrumentSpec(
            instrument_type="electric",
            scale_length_mm=648.0,
            fret_count=22,
            string_count=6,
        )
        assert spec.instrument_type == "electric"
        assert spec.scale_length_mm == 648.0

    def test_compound_radius_detection(self):
        """Should detect compound radius correctly."""
        single = InstrumentSpec("electric", 648.0, 22, 6, base_radius_mm=241.3)
        assert not single.is_compound_radius()
        
        compound = InstrumentSpec("electric", 648.0, 22, 6, 
                                   base_radius_mm=241.3, end_radius_mm=406.4)
        assert compound.is_compound_radius()

    def test_multiscale_detection(self):
        """Should detect multiscale correctly."""
        regular = InstrumentSpec("electric", 648.0, 22, 6)
        assert not regular.is_multiscale()
        
        fanned = InstrumentSpec("electric", 648.0, 24, 7,
                                multiscale=True,
                                bass_scale_length_mm=685.8,
                                treble_scale_length_mm=635.0)
        assert fanned.is_multiscale()


class TestFretboardSpec:
    """Test FretboardSpec dataclass."""

    def test_taper_calculation(self):
        """Should calculate taper rate correctly."""
        spec = FretboardSpec(
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            scale_length_mm=648.0,
            fret_count=22,
        )
        
        # (56 - 42) / 648 = 0.0216 mm/mm
        assert isclose(spec.taper_per_mm(), 14.0 / 648.0, rel_tol=1e-6)


class TestBridgeSpec:
    """Test BridgeSpec dataclass."""

    def test_compensated_position(self):
        """Should calculate compensated saddle position."""
        spec = BridgeSpec(
            scale_length_mm=648.0,
            intonation_offsets_mm={"E6": 2.5, "E1": 2.0},
            base_height_mm=12.0,
        )
        
        assert spec.get_compensated_position_mm("E6") == 650.5
        assert spec.get_compensated_position_mm("E1") == 650.0
        assert spec.get_compensated_position_mm("unknown") == 648.0


# ─────────────────────────────────────────────────────────────────────────────
# Fretboard Geometry Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFretboardOutline:
    """Test fretboard outline generation."""

    def test_outline_has_four_points(self):
        """Should return 4 corner points."""
        outline = compute_fretboard_outline(42.0, 56.0, 648.0, 22)
        assert len(outline) == 4

    def test_outline_symmetry(self):
        """Outline should be symmetric about X axis."""
        outline = compute_fretboard_outline(42.0, 56.0, 648.0, 22)
        
        # Nut points should be symmetric
        assert outline[0][1] == -outline[3][1]
        # Heel points should be symmetric
        assert outline[1][1] == -outline[2][1]


class TestWidthAtPosition:
    """Test width interpolation."""

    def test_width_at_nut(self):
        """Width at position 0 should be nut width."""
        width = compute_width_at_position_mm(42.0, 56.0, 648.0, 22, 0)
        assert width == 42.0

    def test_width_increases_with_position(self):
        """Width should increase along the fretboard."""
        w1 = compute_width_at_position_mm(42.0, 56.0, 648.0, 22, 100)
        w2 = compute_width_at_position_mm(42.0, 56.0, 648.0, 22, 200)
        assert w2 > w1


# ─────────────────────────────────────────────────────────────────────────────
# Radius Profile Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestRadiusProfiles:
    """Test radius calculations."""

    def test_compound_radius_at_nut(self):
        """Radius at fret 0 should equal start radius."""
        radius = compute_compound_radius_at_fret(0, 22, 241.3, 406.4)
        assert radius == 241.3

    def test_compound_radius_at_last_fret(self):
        """Radius at last fret should equal end radius."""
        radius = compute_compound_radius_at_fret(22, 22, 241.3, 406.4)
        assert radius == 406.4

    def test_compound_radius_at_midpoint(self):
        """Radius at midpoint should be average."""
        radius = compute_compound_radius_at_fret(11, 22, 241.3, 406.4)
        expected = (241.3 + 406.4) / 2
        assert isclose(radius, expected, rel_tol=1e-6)

    def test_radius_drop_at_center(self):
        """Drop at center (offset=0) should be zero."""
        drop = compute_radius_drop_mm(241.3, 0)
        assert drop == 0.0

    def test_radius_drop_increases_with_offset(self):
        """Drop should increase as offset increases."""
        drop1 = compute_radius_drop_mm(241.3, 10)
        drop2 = compute_radius_drop_mm(241.3, 20)
        assert drop2 > drop1

    def test_radius_drop_known_value(self):
        """Test against calculated value for 9.5" radius, 42mm board."""
        # For R=241.3mm, offset=21mm (half of 42mm width)
        # drop = 241.3 - sqrt(241.3^2 - 21^2) ≈ 0.92mm
        drop = compute_radius_drop_mm(241.3, 21.0)
        assert isclose(drop, 0.92, rel_tol=0.02)


class TestRadiusArcPoints:
    """Test radius arc point generation."""

    def test_arc_point_count(self):
        """Should return requested number of points."""
        points = compute_radius_arc_points(241.3, 42.0, 50)
        assert len(points) == 50

    def test_arc_endpoints_at_edges(self):
        """First and last points should be at ±half_width."""
        points = compute_radius_arc_points(241.3, 42.0, 50)
        
        assert isclose(points[0][0], -21.0, rel_tol=1e-3)
        assert isclose(points[-1][0], 21.0, rel_tol=1e-3)


# ─────────────────────────────────────────────────────────────────────────────
# Bridge Geometry Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestBridgeGeometry:
    """Test bridge position calculations."""

    def test_bridge_location(self):
        """Bridge location should equal scale length."""
        location = compute_bridge_location_mm(648.0)
        assert location == 648.0

    def test_saddle_positions_with_compensation(self):
        """Saddle positions should include compensation."""
        comps = {"E6": 2.5, "B2": 1.5}
        positions = compute_saddle_positions_mm(648.0, comps)
        
        assert positions["E6"] == 650.5
        assert positions["B2"] == 649.5


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestIntegration:
    """Integration tests combining multiple modules."""

    def test_full_fretboard_generation(self):
        """Should generate complete fretboard geometry."""
        spec = FretboardSpec(
            nut_width_mm=42.0,
            heel_width_mm=56.0,
            scale_length_mm=648.0,
            fret_count=22,
            base_radius_mm=241.3,
            end_radius_mm=406.4,
        )
        
        # Get outline
        outline = compute_fretboard_outline(
            spec.nut_width_mm,
            spec.heel_width_mm,
            spec.scale_length_mm,
            spec.fret_count,
        )
        assert len(outline) == 4
        
        # Get fret slots
        slots = compute_fret_slot_lines(spec)
        assert len(slots) == 22
        
        # Verify slot widths increase
        first_slot_width = abs(slots[0][1][1] - slots[0][0][1])
        last_slot_width = abs(slots[-1][1][1] - slots[-1][0][1])
        assert last_slot_width > first_slot_width

    def test_gibson_scale_12th_fret(self):
        """Gibson 24.75" scale should have 12th fret at ~314mm."""
        scale = SCALE_LENGTHS_MM["gibson_standard"]  # 628.65mm
        positions = compute_fret_positions_mm(scale, 22)
        
        # 12th fret at half scale
        assert isclose(positions[11], scale / 2, rel_tol=1e-6)
        assert isclose(positions[11], 314.325, rel_tol=0.01)
