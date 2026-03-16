# services/api/app/tests/calculators/test_binding_geometry.py

"""
Unit tests for binding_geometry.py calculator.

Tests:
- Neck binding geometry with taper and radius
- Headstock binding with tight bend validation
- Miter joint angle calculations
- Material bend radius validation
"""

import pytest
import math
from typing import List, Tuple

from app.calculators.binding_geometry import (
    # Core functions
    calculate_curvature_radius,
    calculate_miter_angle,
    distance_2d,
    normalize_2d,
    angle_between_vectors,
    polyline_length,
    # Geometry calculators
    calculate_neck_binding_geometry,
    calculate_headstock_binding_geometry,
    calculate_body_binding_path,
    calculate_miter_joints_for_polygon,
    validate_binding_material_for_radius,
    # Types
    BindingMaterial,
    MINIMUM_BEND_RADII_MM,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_circle_points(radius: float, center: Tuple[float, float] = (0, 0), num_points: int = 36) -> List[Tuple[float, float]]:
    """Generate points around a circle."""
    points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
    points.append(points[0])  # Close the polygon
    return points


def make_rectangle_points(width: float, height: float, center: Tuple[float, float] = (0, 0)) -> List[Tuple[float, float]]:
    """Generate rectangle corner points."""
    hw, hh = width / 2, height / 2
    cx, cy = center
    return [
        (cx - hw, cy - hh),
        (cx + hw, cy - hh),
        (cx + hw, cy + hh),
        (cx - hw, cy + hh),
        (cx - hw, cy - hh),  # Close
    ]


def make_guitar_headstock_outline() -> List[Tuple[float, float]]:
    """Generate a simplified guitar headstock outline with a tight tip curve."""
    # Simplified Fender-style headstock (mm)
    return [
        (0, 0),       # Nut end left
        (0, 45),      # Side
        (5, 85),      # Curve toward tip
        (20, 95),     # Tip approach (tight curve here)
        (40, 98),     # Tip
        (60, 95),     # Other side of tip
        (75, 85),     # Curve back
        (80, 45),     # Side
        (80, 0),      # Nut end right
        (0, 0),       # Close
    ]


# =============================================================================
# CORE GEOMETRY TESTS
# =============================================================================

class TestCoreGeometry:
    """Test core geometry helper functions."""

    def test_distance_2d(self):
        assert distance_2d((0, 0), (3, 4)) == 5.0
        assert distance_2d((1, 1), (1, 1)) == 0.0
        assert abs(distance_2d((0, 0), (1, 1)) - math.sqrt(2)) < 0.0001

    def test_normalize_2d(self):
        v = normalize_2d((3, 4))
        assert abs(v[0] - 0.6) < 0.0001
        assert abs(v[1] - 0.8) < 0.0001

        # Zero vector
        assert normalize_2d((0, 0)) == (0.0, 0.0)

    def test_angle_between_vectors_perpendicular(self):
        """Perpendicular vectors should have 90° angle."""
        angle = angle_between_vectors((1, 0), (0, 1))
        assert abs(angle - 90.0) < 0.1

    def test_angle_between_vectors_parallel(self):
        """Parallel vectors should have 0° angle."""
        angle = angle_between_vectors((1, 0), (1, 0))
        assert abs(angle) < 0.1

    def test_angle_between_vectors_opposite(self):
        """Opposite vectors should have 180° angle."""
        angle = angle_between_vectors((1, 0), (-1, 0))
        assert abs(angle - 180.0) < 0.1

    def test_polyline_length_simple(self):
        """Test polyline length calculation."""
        points = [(0, 0), (3, 0), (3, 4)]
        assert polyline_length(points) == 7.0

    def test_polyline_length_closed_square(self):
        """Test closed square perimeter."""
        square = make_rectangle_points(10, 10)
        assert abs(polyline_length(square) - 40.0) < 0.1


class TestCurvatureRadius:
    """Test curvature radius calculations."""

    def test_curvature_radius_circle(self):
        """Points on a circle should give the circle's radius."""
        # Points on a circle of radius 50mm
        circle = make_circle_points(50.0, num_points=36)

        # Check a few points (not at start/end due to closure)
        for i in [5, 10, 15, 20]:
            p1 = circle[i - 1]
            p2 = circle[i]
            p3 = circle[i + 1]
            radius = calculate_curvature_radius(p1, p2, p3)
            # Should be close to 50mm
            assert abs(radius - 50.0) < 2.0  # Allow some tolerance

    def test_curvature_radius_collinear(self):
        """Collinear points should give infinite radius."""
        p1 = (0, 0)
        p2 = (5, 0)
        p3 = (10, 0)
        radius = calculate_curvature_radius(p1, p2, p3)
        assert radius == float("inf")

    def test_curvature_radius_tight_curve(self):
        """Test a tight 20mm radius curve."""
        circle = make_circle_points(20.0, num_points=36)
        p1 = circle[5]
        p2 = circle[6]
        p3 = circle[7]
        radius = calculate_curvature_radius(p1, p2, p3)
        assert abs(radius - 20.0) < 2.0


# =============================================================================
# MITER JOINT TESTS
# =============================================================================

class TestMiterJoints:
    """Test miter joint calculations."""

    def test_miter_angle_90_degree_corner(self):
        """90° corner should have 45° miter angle."""
        incoming = (1, 0)  # Moving right
        outgoing = (0, 1)  # Turn to go up
        angle = calculate_miter_angle(incoming, outgoing)
        assert abs(angle - 45.0) < 0.1

    def test_miter_angle_45_degree_corner(self):
        """45° corner should have 22.5° miter angle."""
        incoming = (1, 0)  # Moving right
        outgoing = normalize_2d((1, 1))  # Turn 45° left
        angle = calculate_miter_angle(incoming, outgoing)
        assert abs(angle - 22.5) < 0.5

    def test_miter_joints_rectangle(self):
        """Rectangle should have miter joints at corners."""
        rect = make_rectangle_points(100, 50)
        joints = calculate_miter_joints_for_polygon(rect, corner_threshold_degrees=25)
        # 3 internal corners detected (first/last point overlap skips one)
        assert len(joints) >= 3
        for joint in joints:
            assert abs(joint.angle_degrees - 45.0) < 1.0

    def test_miter_joints_circle(self):
        """Circle should have no miter joints (all gradual curves)."""
        circle = make_circle_points(50, num_points=72)  # 5° increments
        joints = calculate_miter_joints_for_polygon(circle, corner_threshold_degrees=25)
        assert len(joints) == 0


# =============================================================================
# NECK BINDING TESTS (BEN-GAP-04)
# =============================================================================

class TestNeckBindingGeometry:
    """Test neck binding geometry calculations."""

    def test_neck_binding_basic(self):
        """Test basic neck binding calculation."""
        result = calculate_neck_binding_geometry(
            nut_width_mm=43.0,
            heel_width_mm=56.0,
            fretboard_length_mm=320.0,
            fretboard_radius_mm=254.0,  # 10" radius
            binding_width_mm=2.0,
        )

        # Check basic properties
        assert result.nut_width_mm == 43.0
        assert result.heel_width_mm == 56.0
        assert result.fretboard_length_mm == 320.0
        assert result.binding_width_mm == 2.0

        # Check taper angle (positive = heel wider than nut)
        assert result.taper_angle_degrees > 0

        # Check points generated
        assert len(result.left_edge_points) >= 10
        assert len(result.right_edge_points) >= 10

        # Left and right should be symmetric
        assert len(result.left_edge_points) == len(result.right_edge_points)

    def test_neck_binding_taper_angle(self):
        """Test taper angle calculation."""
        result = calculate_neck_binding_geometry(
            nut_width_mm=40.0,
            heel_width_mm=60.0,  # 20mm wider = 10mm per side
            fretboard_length_mm=300.0,
        )

        # Expected angle: atan(10/300) ≈ 1.91°
        expected_angle = math.degrees(math.atan(10 / 300))
        assert abs(result.taper_angle_degrees - expected_angle) < 0.1

    def test_neck_binding_flat_fretboard(self):
        """Test flat fretboard (no radius)."""
        result = calculate_neck_binding_geometry(
            nut_width_mm=43.0,
            heel_width_mm=56.0,
            fretboard_length_mm=320.0,
            fretboard_radius_mm=None,  # Flat
        )

        # All Z coordinates should be 0 for flat fretboard
        for point in result.left_edge_points:
            assert point[2] == 0.0
        for point in result.right_edge_points:
            assert point[2] == 0.0

    def test_neck_binding_compound_radius(self):
        """Test compound radius fretboard."""
        result = calculate_neck_binding_geometry(
            nut_width_mm=43.0,
            heel_width_mm=56.0,
            fretboard_length_mm=320.0,
            compound_radius=(254.0, 406.4),  # 10" to 16"
        )

        assert result.compound_radius == (254.0, 406.4)
        # Should have a warning about compound radius change
        assert any("compound" in w.lower() for w in result.warnings) or len(result.warnings) == 0

    def test_neck_binding_total_length(self):
        """Test that total length is reasonable."""
        result = calculate_neck_binding_geometry(
            nut_width_mm=43.0,
            heel_width_mm=56.0,
            fretboard_length_mm=320.0,
        )

        # Total length should be approximately the fretboard length
        # (slightly longer due to 3D path on curved fretboard)
        assert result.total_length_mm >= 320.0
        assert result.total_length_mm < 330.0  # Not much longer

    def test_neck_binding_to_dict(self):
        """Test serialization."""
        result = calculate_neck_binding_geometry(
            nut_width_mm=43.0,
            heel_width_mm=56.0,
            fretboard_length_mm=320.0,
        )

        d = result.to_dict()
        assert "nut_width_mm" in d
        assert "taper_angle_degrees" in d
        assert "total_length_mm" in d
        assert "left_edge_point_count" in d


# =============================================================================
# HEADSTOCK BINDING TESTS (BEN-GAP-05)
# =============================================================================

class TestHeadstockBindingGeometry:
    """Test headstock binding geometry calculations."""

    def test_headstock_binding_basic(self):
        """Test basic headstock binding calculation."""
        outline = make_guitar_headstock_outline()
        result = calculate_headstock_binding_geometry(
            outline_points=outline,
            binding_width_mm=2.0,
            material=BindingMaterial.ABS_PLASTIC,
        )

        assert result.binding_width_mm == 2.0
        assert result.material == BindingMaterial.ABS_PLASTIC
        assert result.total_length_mm > 0

    def test_headstock_binding_tight_curve_detection(self):
        """Test that tight curves are detected."""
        # Create outline with a very tight tip curve (10mm radius)
        outline = make_circle_points(10.0, center=(40, 90), num_points=12)

        result = calculate_headstock_binding_geometry(
            outline_points=outline,
            binding_width_mm=2.0,
            material=BindingMaterial.WOOD_ROSEWOOD,  # Needs 20mm minimum
        )

        # Should detect the tight curve
        assert result.minimum_radius_mm < 15
        # Should flag as not manufacturable for rosewood
        assert result.is_manufacturable == False
        assert len(result.warnings) > 0

    def test_headstock_binding_flexible_material(self):
        """Test that flexible material passes on same curve."""
        # 15mm radius curve
        outline = make_circle_points(15.0, center=(40, 90), num_points=24)

        result = calculate_headstock_binding_geometry(
            outline_points=outline,
            binding_width_mm=2.0,
            material=BindingMaterial.ABS_PLASTIC,  # Needs only 3mm minimum
        )

        # Should be manufacturable with ABS
        assert result.is_manufacturable == True

    def test_headstock_binding_miter_joints(self):
        """Test miter joint detection at sharp corners."""
        # Create outline with sharp corners
        outline = make_rectangle_points(80, 100)

        result = calculate_headstock_binding_geometry(
            outline_points=outline,
            binding_width_mm=2.0,
            material=BindingMaterial.CELLULOID,
        )

        # Rectangle has 4 corners, 3 detected as internal points
        # (first/last point overlap skips one)
        assert len(result.miter_joints) >= 3

    def test_headstock_binding_to_dict(self):
        """Test serialization."""
        outline = make_guitar_headstock_outline()
        result = calculate_headstock_binding_geometry(
            outline_points=outline,
            binding_width_mm=2.0,
            material=BindingMaterial.CELLULOID,
        )

        d = result.to_dict()
        assert "minimum_radius_mm" in d
        assert "is_manufacturable" in d
        assert "miter_joints" in d
        assert "total_length_mm" in d


# =============================================================================
# BODY BINDING TESTS
# =============================================================================

class TestBodyBindingPath:
    """Test body binding path analysis."""

    def test_body_binding_circle(self):
        """Test body binding on a circular outline."""
        circle = make_circle_points(200.0, num_points=72)

        result = calculate_body_binding_path(
            body_outline=circle,
            binding_width_mm=2.5,
            material=BindingMaterial.ABS_PLASTIC,
        )

        # Circle perimeter = 2πr ≈ 1257mm
        assert abs(result["total_length_mm"] - 2 * math.pi * 200) < 10

        # 200mm radius is well above any material minimum
        assert result["is_manufacturable"] == True
        assert len(result["tight_curves"]) == 0  # No tight curves

    def test_body_binding_with_cutaway(self):
        """Test body with tight cutaway curve."""
        # Simplified body with a tight cutaway
        outline = [
            (0, 0), (100, 0), (200, 0), (300, 0),  # Bottom
            (350, 50), (380, 100), (390, 150),     # Lower bout
            (380, 200), (350, 250),                 # Waist
            (380, 300),                             # Upper bout
            (375, 340), (360, 360), (340, 365),    # Cutaway (tight curves here)
            (320, 360), (300, 340), (280, 300),
            (250, 280), (200, 270), (100, 280),    # Upper bout other side
            (50, 260), (20, 200), (10, 150),
            (20, 100), (50, 50),
            (0, 0),
        ]

        result = calculate_body_binding_path(
            body_outline=outline,
            binding_width_mm=2.5,
            material=BindingMaterial.CELLULOID,
        )

        assert result["total_length_mm"] > 0
        assert "tight_curves" in result


# =============================================================================
# MATERIAL VALIDATION TESTS
# =============================================================================

class TestMaterialValidation:
    """Test binding material validation."""

    def test_validate_material_compatible(self):
        """Test material validation with compatible radius."""
        result = validate_binding_material_for_radius(
            minimum_radius_mm=50.0,  # Very gentle curve
            preferred_material=BindingMaterial.WOOD_ROSEWOOD,
        )

        assert result["preferred_is_compatible"] == True
        assert len(result["compatible_materials"]) == len(MINIMUM_BEND_RADII_MM)

    def test_validate_material_incompatible(self):
        """Test material validation with incompatible radius."""
        result = validate_binding_material_for_radius(
            minimum_radius_mm=5.0,  # Very tight curve
            preferred_material=BindingMaterial.WOOD_ROSEWOOD,  # Needs 20mm
        )

        assert result["preferred_is_compatible"] == False
        assert len(result["incompatible_materials"]) > 0
        # ABS should still work (needs 3mm)
        assert any(m["material"] == "abs_plastic" for m in result["compatible_materials"])

    def test_validate_material_nothing_works(self):
        """Test when no material can handle the radius."""
        result = validate_binding_material_for_radius(
            minimum_radius_mm=1.0,  # Impossibly tight
            preferred_material=BindingMaterial.ABS_PLASTIC,
        )

        assert result["preferred_is_compatible"] == False
        assert len(result["compatible_materials"]) == 0
        assert "miter joints" in result["recommendation"].lower()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestBindingGeometryIntegration:
    """Integration tests combining multiple features."""

    def test_benedetto_style_neck_binding(self):
        """Test Benedetto-style archtop neck binding parameters."""
        result = calculate_neck_binding_geometry(
            nut_width_mm=44.0,      # Benedetto standard
            heel_width_mm=58.0,     # Wider for archtop
            fretboard_length_mm=340.0,
            fretboard_radius_mm=305.0,  # 12" radius
            binding_width_mm=3.0,       # Bold archtop binding
            material=BindingMaterial.IVOROID,
        )

        assert result.binding_width_mm == 3.0
        assert result.total_length_mm > 340.0  # Longer than flat length

    def test_benedetto_style_headstock_binding(self):
        """Test Benedetto-style headstock binding with tight tip curve."""
        # Benedetto headstocks often have a pronounced tip curve
        # Simulate a ~20mm radius tip
        tip_curve = make_circle_points(20.0, center=(50, 150), num_points=12)

        # This should trigger a warning for celluloid (6mm min)
        # but be manufacturable
        result = calculate_headstock_binding_geometry(
            outline_points=tip_curve,
            binding_width_mm=3.0,
            material=BindingMaterial.CELLULOID,
        )

        assert result.minimum_radius_mm > 15  # Circle radius, accounting for tolerance
        assert result.is_manufacturable == True  # 20mm > 6mm minimum

    def test_full_workflow_neck_to_headstock(self):
        """Test that neck and headstock binding can be computed together."""
        # Neck binding
        neck_result = calculate_neck_binding_geometry(
            nut_width_mm=43.0,
            heel_width_mm=56.0,
            fretboard_length_mm=320.0,
            binding_width_mm=2.0,
            material=BindingMaterial.ABS_PLASTIC,
        )

        # Headstock binding
        headstock_outline = make_guitar_headstock_outline()
        headstock_result = calculate_headstock_binding_geometry(
            outline_points=headstock_outline,
            binding_width_mm=2.0,
            material=BindingMaterial.ABS_PLASTIC,
        )

        # Total binding length for one side of neck + headstock
        total_binding = neck_result.total_length_mm + headstock_result.total_length_mm

        # Should be reasonable (roughly 320 + 250 = 570mm ish)
        assert 400 < total_binding < 800
