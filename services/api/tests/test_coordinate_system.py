# tests/test_coordinate_system.py

"""
Unit tests for unified coordinate system (VINE-05, INLAY-04).

Tests coordinate transformations, geometry bounds computation,
and inlay positioning across fretboard and headstock regions.
"""

import pytest
import math
from app.instrument_geometry.coordinate_system import (
    Point2D,
    Point3D,
    BoundingBox,
    CoordinateRegion,
    HeadstockOriginSpec,
    UnifiedNeckGeometry,
    InlayPosition,
    # Transformation functions
    fret_to_unified_y,
    unified_y_to_fret,
    string_to_unified_x,
    headstock_local_to_unified,
    unified_to_headstock_local,
    fretboard_width_at_y,
    # Inlay functions
    compute_dot_inlay_position,
    compute_block_inlay_position,
    compute_headstock_inlay_position,
    compute_all_standard_inlay_positions,
    # Factory functions
    create_strat_geometry,
    create_lespaul_geometry,
    create_classical_geometry,
    create_geometry_from_specs,
)


# =============================================================================
# Point2D Tests
# =============================================================================

class TestPoint2D:
    """Test Point2D dataclass operations."""

    def test_creation(self):
        """Point2D should store x and y coordinates."""
        p = Point2D(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0

    def test_addition(self):
        """Point2D addition should work element-wise."""
        p1 = Point2D(10.0, 20.0)
        p2 = Point2D(5.0, 15.0)
        result = p1 + p2
        assert result.x == 15.0
        assert result.y == 35.0

    def test_subtraction(self):
        """Point2D subtraction should work element-wise."""
        p1 = Point2D(10.0, 20.0)
        p2 = Point2D(5.0, 15.0)
        result = p1 - p2
        assert result.x == 5.0
        assert result.y == 5.0

    def test_distance_to(self):
        """Distance calculation should be correct."""
        p1 = Point2D(0.0, 0.0)
        p2 = Point2D(3.0, 4.0)
        assert p1.distance_to(p2) == 5.0  # 3-4-5 triangle

    def test_distance_to_same_point(self):
        """Distance to self should be zero."""
        p = Point2D(10.0, 20.0)
        assert p.distance_to(p) == 0.0

    def test_to_tuple(self):
        """Should convert to tuple."""
        p = Point2D(10.0, 20.0)
        assert p.to_tuple() == (10.0, 20.0)

    def test_from_tuple(self):
        """Should create from tuple."""
        p = Point2D.from_tuple((10.0, 20.0))
        assert p.x == 10.0
        assert p.y == 20.0

    def test_to_dict(self):
        """Should serialize to dict with rounding."""
        p = Point2D(10.123456, 20.987654)
        d = p.to_dict()
        assert d["x"] == 10.1235  # Rounded to 4 decimals
        assert d["y"] == 20.9877


# =============================================================================
# Point3D Tests
# =============================================================================

class TestPoint3D:
    """Test Point3D dataclass operations."""

    def test_creation(self):
        """Point3D should store x, y, z coordinates."""
        p = Point3D(10.0, 20.0, 5.0)
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.z == 5.0

    def test_to_2d(self):
        """Should convert to Point2D, dropping z."""
        p3 = Point3D(10.0, 20.0, 5.0)
        p2 = p3.to_2d()
        assert isinstance(p2, Point2D)
        assert p2.x == 10.0
        assert p2.y == 20.0

    def test_to_dict(self):
        """Should serialize to dict."""
        p = Point3D(10.0, 20.0, -5.0)
        d = p.to_dict()
        assert d["x"] == 10.0
        assert d["y"] == 20.0
        assert d["z"] == -5.0


# =============================================================================
# BoundingBox Tests
# =============================================================================

class TestBoundingBox:
    """Test BoundingBox dataclass operations."""

    def test_creation(self):
        """BoundingBox should store min/max coordinates."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        assert bb.min_x == -10
        assert bb.max_x == 10
        assert bb.min_y == 0
        assert bb.max_y == 100

    def test_width(self):
        """Width should be max_x - min_x."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        assert bb.width == 20

    def test_height(self):
        """Height should be max_y - min_y."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        assert bb.height == 100

    def test_center(self):
        """Center should be midpoint."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        center = bb.center
        assert center.x == 0.0
        assert center.y == 50.0

    def test_contains_inside(self):
        """Point inside bbox should return True."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        assert bb.contains(Point2D(0.0, 50.0)) is True

    def test_contains_on_edge(self):
        """Point on edge should return True."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        assert bb.contains(Point2D(-10.0, 0.0)) is True
        assert bb.contains(Point2D(10.0, 100.0)) is True

    def test_contains_outside(self):
        """Point outside bbox should return False."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        assert bb.contains(Point2D(15.0, 50.0)) is False
        assert bb.contains(Point2D(0.0, 150.0)) is False

    def test_to_dict(self):
        """Should serialize to dict with computed fields."""
        bb = BoundingBox(min_x=-10, max_x=10, min_y=0, max_y=100)
        d = bb.to_dict()
        assert d["min_x"] == -10
        assert d["max_x"] == 10
        assert d["width"] == 20
        assert d["height"] == 100


# =============================================================================
# HeadstockOriginSpec Tests
# =============================================================================

class TestHeadstockOriginSpec:
    """Test HeadstockOriginSpec dataclass."""

    def test_default_values(self):
        """Default should be origin at nut with no angle."""
        spec = HeadstockOriginSpec()
        assert spec.origin_offset_mm == 0.0
        assert spec.angle_deg == 0.0
        assert spec.thickness_transition_mm == 0.0

    def test_custom_values(self):
        """Should accept custom values."""
        spec = HeadstockOriginSpec(
            origin_offset_mm=-5.0,
            angle_deg=17.0,
            thickness_transition_mm=25.0,
        )
        assert spec.origin_offset_mm == -5.0
        assert spec.angle_deg == 17.0
        assert spec.thickness_transition_mm == 25.0

    def test_to_dict(self):
        """Should serialize to dict."""
        spec = HeadstockOriginSpec(origin_offset_mm=-5.0, angle_deg=17.0)
        d = spec.to_dict()
        assert d["origin_offset_mm"] == -5.0
        assert d["angle_deg"] == 17.0


# =============================================================================
# Fret Position Transformation Tests
# =============================================================================

class TestFretToUnifiedY:
    """Test fret number to Y coordinate conversion."""

    def test_fret_zero_is_nut(self):
        """Fret 0 should be at Y=0 (nut)."""
        y = fret_to_unified_y(0, 647.7)
        assert y == 0.0

    def test_negative_fret_is_nut(self):
        """Negative fret should return 0."""
        y = fret_to_unified_y(-1, 647.7)
        assert y == 0.0

    def test_fret_12_is_half_scale(self):
        """Fret 12 should be at half the scale length."""
        scale = 647.7
        y = fret_to_unified_y(12, scale)
        assert abs(y - scale / 2) < 0.01

    def test_fret_positions_increase(self):
        """Higher frets should have larger Y values."""
        scale = 647.7
        y5 = fret_to_unified_y(5, scale)
        y12 = fret_to_unified_y(12, scale)
        y22 = fret_to_unified_y(22, scale)
        assert y5 < y12 < y22

    def test_fractional_fret(self):
        """Should handle fractional fret numbers."""
        scale = 647.7
        y5 = fret_to_unified_y(5, scale)
        y6 = fret_to_unified_y(6, scale)
        y5_5 = fret_to_unified_y(5.5, scale)
        assert y5 < y5_5 < y6


class TestUnifiedYToFret:
    """Test Y coordinate to fret number conversion."""

    def test_y_zero_is_nut(self):
        """Y=0 should be fret 0."""
        fret = unified_y_to_fret(0, 647.7)
        assert fret == 0.0

    def test_negative_y_is_nut(self):
        """Negative Y should return 0 (headstock region)."""
        fret = unified_y_to_fret(-50, 647.7)
        assert fret == 0.0

    def test_half_scale_is_fret_12(self):
        """Y at half scale should be fret 12."""
        scale = 647.7
        fret = unified_y_to_fret(scale / 2, scale)
        assert abs(fret - 12.0) < 0.01

    def test_past_bridge_is_inf(self):
        """Y past scale length should return inf."""
        scale = 647.7
        fret = unified_y_to_fret(scale + 10, scale)
        assert fret == float('inf')

    def test_roundtrip(self):
        """Converting fret->Y->fret should return original."""
        scale = 647.7
        for f in [1, 5, 7, 12, 15, 22]:
            y = fret_to_unified_y(f, scale)
            f_back = unified_y_to_fret(y, scale)
            assert abs(f_back - f) < 0.001


# =============================================================================
# String Position Tests
# =============================================================================

class TestStringToUnifiedX:
    """Test string number to X coordinate conversion."""

    def test_center_strings(self):
        """Middle strings should be near centerline."""
        x3 = string_to_unified_x(3, 0, 43, 43, 6)
        x4 = string_to_unified_x(4, 0, 43, 43, 6)
        assert x3 < 0  # Bass side
        assert x4 > 0  # Treble side
        # Should be close to center
        assert abs(x3) < 10
        assert abs(x4) < 10

    def test_outer_strings(self):
        """Outer strings should be farthest from center."""
        x1 = string_to_unified_x(1, 0, 43, 43, 6)  # Low E (bass)
        x6 = string_to_unified_x(6, 0, 43, 43, 6)  # High E (treble)
        assert x1 < 0  # Bass side = negative X
        assert x6 > 0  # Treble side = positive X
        assert abs(x1) > abs(string_to_unified_x(2, 0, 43, 43, 6))

    def test_single_string(self):
        """Single string should be at centerline."""
        x = string_to_unified_x(1, 0, 43, 43, 1)
        assert x == 0.0


# =============================================================================
# Headstock Coordinate Transformation Tests
# =============================================================================

class TestHeadstockTransformations:
    """Test headstock local <-> unified coordinate transforms."""

    def test_identity_transform(self):
        """With zero offset, local == unified."""
        origin = HeadstockOriginSpec(origin_offset_mm=0.0)
        local = Point2D(5.0, -50.0)
        unified = headstock_local_to_unified(local, origin)
        assert unified.x == local.x
        assert unified.y == local.y

    def test_offset_transform(self):
        """Non-zero offset should shift Y."""
        origin = HeadstockOriginSpec(origin_offset_mm=-10.0)
        local = Point2D(5.0, -50.0)
        unified = headstock_local_to_unified(local, origin)
        assert unified.x == 5.0
        assert unified.y == -60.0  # -50 + (-10)

    def test_roundtrip_transform(self):
        """local -> unified -> local should return original."""
        origin = HeadstockOriginSpec(origin_offset_mm=-15.0)
        local = Point2D(10.0, -80.0)
        unified = headstock_local_to_unified(local, origin)
        back = unified_to_headstock_local(unified, origin)
        assert abs(back.x - local.x) < 0.001
        assert abs(back.y - local.y) < 0.001


# =============================================================================
# Fretboard Width Tests
# =============================================================================

class TestFretboardWidthAtY:
    """Test fretboard width interpolation."""

    def test_width_at_nut(self):
        """Width at Y=0 should be nut width."""
        w = fretboard_width_at_y(0, 43.0, 56.0, 400.0)
        assert w == 43.0

    def test_width_at_last_fret(self):
        """Width at end should be last fret width."""
        w = fretboard_width_at_y(400.0, 43.0, 56.0, 400.0)
        assert w == 56.0

    def test_width_at_middle(self):
        """Width at midpoint should be average."""
        w = fretboard_width_at_y(200.0, 43.0, 56.0, 400.0)
        assert abs(w - 49.5) < 0.01  # (43 + 56) / 2

    def test_width_before_nut(self):
        """Width before nut should return nut width."""
        w = fretboard_width_at_y(-50.0, 43.0, 56.0, 400.0)
        assert w == 43.0

    def test_width_past_end(self):
        """Width past end should return end width."""
        w = fretboard_width_at_y(500.0, 43.0, 56.0, 400.0)
        assert w == 56.0


# =============================================================================
# UnifiedNeckGeometry Tests
# =============================================================================

class TestUnifiedNeckGeometry:
    """Test UnifiedNeckGeometry bounds and region detection."""

    def test_default_strat_geometry(self):
        """Default should be Strat-like specs."""
        geom = UnifiedNeckGeometry()
        assert geom.scale_length_mm == 647.7
        assert geom.fret_count == 22
        assert geom.nut_width_mm == 43.0

    def test_fretboard_length_calculation(self):
        """Fretboard length should be calculated from frets."""
        geom = UnifiedNeckGeometry(scale_length_mm=647.7, fret_count=22)
        # Fret 22 is ~466mm (scale * (1 - 2^(-22/12))), plus 15mm margin = ~481mm
        assert 475 < geom.fretboard_length_mm < 490

    def test_fretboard_bounds(self):
        """Fretboard bounds should be positive Y."""
        geom = create_strat_geometry()
        bounds = geom.fretboard_bounds
        assert bounds.min_y == 0.0
        assert bounds.max_y > 0

    def test_headstock_bounds(self):
        """Headstock bounds should be negative Y."""
        geom = create_strat_geometry()
        bounds = geom.headstock_bounds
        assert bounds.max_y <= 0.0
        assert bounds.min_y < bounds.max_y

    def test_total_bounds_spans_both(self):
        """Total bounds should include both regions."""
        geom = create_strat_geometry()
        total = geom.total_bounds
        fb = geom.fretboard_bounds
        hs = geom.headstock_bounds
        assert total.min_y == hs.min_y
        assert total.max_y == fb.max_y

    def test_region_detection_fretboard(self):
        """Points on fretboard should be detected."""
        geom = create_strat_geometry()
        point = Point2D(0.0, 100.0)  # 100mm from nut = fretboard
        assert geom.get_region(point) == CoordinateRegion.FRETBOARD

    def test_region_detection_headstock(self):
        """Points on headstock should be detected."""
        geom = create_strat_geometry()
        point = Point2D(0.0, -50.0)  # 50mm into headstock
        assert geom.get_region(point) == CoordinateRegion.HEADSTOCK

    def test_region_detection_nut(self):
        """Points at nut should be detected."""
        geom = create_strat_geometry()
        point = Point2D(0.0, 0.0)  # At nut
        assert geom.get_region(point) == CoordinateRegion.NUT

    def test_region_detection_body_joint(self):
        """Points past fretboard should be body joint."""
        geom = create_strat_geometry()
        point = Point2D(0.0, 500.0)  # Past fretboard
        assert geom.get_region(point) == CoordinateRegion.BODY_JOINT

    def test_to_dict(self):
        """Should serialize to complete dict."""
        geom = create_strat_geometry()
        d = geom.to_dict()
        assert "scale_length_mm" in d
        assert "bounds" in d
        assert "fretboard" in d["bounds"]
        assert "headstock" in d["bounds"]
        assert "total" in d["bounds"]


# =============================================================================
# Inlay Position Tests
# =============================================================================

class TestComputeDotInlayPosition:
    """Test dot inlay position computation."""

    def test_center_dot(self):
        """Center dot should be on centerline."""
        geom = create_strat_geometry()
        pos = compute_dot_inlay_position(5, geom, "center")
        assert pos.center.x == 0.0
        assert pos.fret_number == 5
        assert pos.region == CoordinateRegion.FRETBOARD

    def test_bass_side_dot(self):
        """Bass dot should have negative X."""
        geom = create_strat_geometry()
        pos = compute_dot_inlay_position(12, geom, "bass")
        assert pos.center.x < 0

    def test_treble_side_dot(self):
        """Treble dot should have positive X."""
        geom = create_strat_geometry()
        pos = compute_dot_inlay_position(12, geom, "treble")
        assert pos.center.x > 0

    def test_y_between_frets(self):
        """Y should be between fret positions."""
        geom = create_strat_geometry()
        pos = compute_dot_inlay_position(5, geom, "center")
        y4 = fret_to_unified_y(4, geom.scale_length_mm)
        y5 = fret_to_unified_y(5, geom.scale_length_mm)
        assert y4 < pos.center.y < y5


class TestComputeBlockInlayPosition:
    """Test block inlay position computation."""

    def test_block_centered(self):
        """Block should be centered."""
        geom = create_lespaul_geometry()
        pos = compute_block_inlay_position(5, geom)
        assert pos.center.x == 0.0
        assert pos.fret_number == 5

    def test_block_y_between_frets(self):
        """Y should be between fret positions."""
        geom = create_lespaul_geometry()
        pos = compute_block_inlay_position(7, geom)
        y6 = fret_to_unified_y(6, geom.scale_length_mm)
        y7 = fret_to_unified_y(7, geom.scale_length_mm)
        assert y6 < pos.center.y < y7


class TestComputeHeadstockInlayPosition:
    """Test headstock inlay position computation."""

    def test_headstock_inlay_negative_y(self):
        """Headstock inlay should have negative Y."""
        geom = create_strat_geometry()
        pos = compute_headstock_inlay_position(50.0, geom)
        assert pos.center.y < 0.0
        assert pos.region == CoordinateRegion.HEADSTOCK

    def test_headstock_inlay_x_offset(self):
        """Should respect X offset."""
        geom = create_strat_geometry()
        pos = compute_headstock_inlay_position(50.0, geom, x_offset_mm=20.0)
        assert pos.center.x == 20.0


class TestComputeAllStandardInlayPositions:
    """Test standard inlay pattern generation."""

    def test_dot_pattern_count(self):
        """Dot pattern should have correct count."""
        geom = create_strat_geometry()
        positions = compute_all_standard_inlay_positions(geom, "dots", double_dots_at_12=True)
        # Standard frets: 3, 5, 7, 9, 12 (double), 15, 17, 19, 21
        # = 8 positions + 1 extra for double at 12 = 10
        assert len(positions) == 10

    def test_dot_pattern_no_double_12(self):
        """Without double dots at 12, should have fewer."""
        geom = create_strat_geometry()
        positions = compute_all_standard_inlay_positions(geom, "dots", double_dots_at_12=False)
        assert len(positions) == 9

    def test_block_pattern(self):
        """Block pattern should have one per fret."""
        geom = create_strat_geometry()
        positions = compute_all_standard_inlay_positions(geom, "blocks")
        # Standard frets: 3, 5, 7, 9, 12, 15, 17, 19, 21 = 9
        assert len(positions) == 9

    def test_limited_fret_count(self):
        """Should respect fret count limit."""
        geom = UnifiedNeckGeometry(fret_count=12)
        positions = compute_all_standard_inlay_positions(geom, "dots", double_dots_at_12=True)
        # Only frets 3, 5, 7, 9, 12 (double) = 5 + 1 = 6
        assert len(positions) == 6

    def test_all_positions_in_fretboard(self):
        """All positions should be in fretboard region."""
        geom = create_strat_geometry()
        positions = compute_all_standard_inlay_positions(geom, "dots")
        for pos in positions:
            assert pos.region == CoordinateRegion.FRETBOARD


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestFactoryFunctions:
    """Test geometry factory functions."""

    def test_create_strat_geometry(self):
        """Strat geometry should have correct specs."""
        geom = create_strat_geometry()
        assert geom.scale_length_mm == 647.7  # 25.5"
        assert geom.fret_count == 22
        assert geom.headstock_angle_deg == 13.0

    def test_create_lespaul_geometry(self):
        """Les Paul geometry should have correct specs."""
        geom = create_lespaul_geometry()
        assert geom.scale_length_mm == 628.65  # 24.75"
        assert geom.fret_count == 22
        assert geom.headstock_angle_deg == 17.0

    def test_create_classical_geometry(self):
        """Classical geometry should have correct specs."""
        geom = create_classical_geometry()
        assert geom.scale_length_mm == 650.0
        assert geom.fret_count == 19
        assert geom.nut_width_mm == 52.0

    def test_create_geometry_from_specs(self):
        """Custom specs should create matching geometry."""
        geom = create_geometry_from_specs(
            scale_length_mm=660.0,
            fret_count=24,
            nut_width_mm=45.0,
            width_at_last_fret_mm=60.0,
            headstock_length_mm=180.0,
            headstock_width_mm=90.0,
            headstock_angle_deg=15.0,
        )
        assert geom.scale_length_mm == 660.0
        assert geom.fret_count == 24
        assert geom.nut_width_mm == 45.0
        assert geom.headstock_angle_deg == 15.0


# =============================================================================
# InlayPosition Serialization Tests
# =============================================================================

class TestInlayPositionSerialization:
    """Test InlayPosition to_dict serialization."""

    def test_to_dict(self):
        """Should serialize all fields."""
        pos = InlayPosition(
            center=Point2D(5.0, 100.0),
            fret_number=5,
            string_number=3,
            region=CoordinateRegion.FRETBOARD,
            rotation_deg=45.0,
        )
        d = pos.to_dict()
        assert d["center"]["x"] == 5.0
        assert d["center"]["y"] == 100.0
        assert d["fret_number"] == 5
        assert d["string_number"] == 3
        assert d["region"] == "fretboard"
        assert d["rotation_deg"] == 45.0

    def test_to_dict_optional_fields(self):
        """Optional fields should serialize as None."""
        pos = InlayPosition(
            center=Point2D(0.0, 0.0),
            region=CoordinateRegion.HEADSTOCK,
        )
        d = pos.to_dict()
        assert d["fret_number"] is None
        assert d["string_number"] is None


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_fret_24_position(self):
        """24-fret guitars should compute positions correctly."""
        geom = UnifiedNeckGeometry(scale_length_mm=647.7, fret_count=24)
        y24 = fret_to_unified_y(24, geom.scale_length_mm)
        # Fret 24 is exactly 75% of scale length: scale * (1 - 1/2^2) = scale * 0.75
        assert abs(y24 - geom.scale_length_mm * 0.75) < 0.01

    def test_7_string_spacing(self):
        """7-string guitars should compute string positions."""
        x1 = string_to_unified_x(1, 0, 48, 48, 7)
        x7 = string_to_unified_x(7, 0, 48, 48, 7)
        assert x1 < 0  # Bass side
        assert x7 > 0  # Treble side
        assert abs(x1) == abs(x7)  # Symmetric

    def test_zero_width_fretboard(self):
        """Zero width should not cause division errors."""
        # This is an invalid case but shouldn't crash
        w = fretboard_width_at_y(100.0, 0.0, 0.0, 400.0)
        assert w == 0.0

    def test_very_long_scale(self):
        """Very long scale (bass) should work."""
        scale = 864.0  # 34" bass scale
        y12 = fret_to_unified_y(12, scale)
        assert abs(y12 - scale / 2) < 0.01
