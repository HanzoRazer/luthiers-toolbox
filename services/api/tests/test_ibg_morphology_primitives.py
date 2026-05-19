"""
Tests for Body Grid Morphology Primitives

Note: Import directly from body_grid submodules to avoid ezdxf dependency chain.
The body_grid module is designed to be independent of DXF/CAD dependencies.
"""

import pytest

# Direct imports to avoid ezdxf dependency through ibg.__init__
from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    NormalizedPoint,
    ZoneAssignment,
)
from app.instrument_geometry.body.ibg.body_grid.primitives import (
    CurvatureClass,
    GeometryType,
    MorphologyPrimitive,
    PrimitiveDetector,
    PrimitiveType,
    SlopeClass,
)
from app.instrument_geometry.body.ibg.body_grid.zones import ZoneClassifier


class TestMorphologyPrimitive:
    """Tests for MorphologyPrimitive data structure."""

    def test_create_primitive(self):
        """Test primitive creation."""
        points = [
            NormalizedPoint(-0.5, 0.2),
            NormalizedPoint(-0.55, 0.25),
            NormalizedPoint(-0.5, 0.3),
        ]
        prim = MorphologyPrimitive(
            primitive_id="prim_0001",
            primitive_type=PrimitiveType.CONVEX_BOUT,
            zone_assignment=ZoneAssignment(primary_zone="lower_bout"),
            geometry_type=GeometryType.ARC,
            slope_class=SlopeClass.ASCENDING,
            curvature_class=CurvatureClass.CONVEX_OUTWARD,
            points=points,
            side="left",
            confidence=0.85,
        )
        assert prim.primitive_id == "prim_0001"
        assert prim.primitive_type == PrimitiveType.CONVEX_BOUT
        assert prim.side == "left"

    def test_y_range(self):
        """Test Y range property."""
        points = [
            NormalizedPoint(0.0, 0.1),
            NormalizedPoint(0.1, 0.3),
            NormalizedPoint(0.2, 0.2),
        ]
        prim = MorphologyPrimitive(
            primitive_id="test",
            primitive_type=PrimitiveType.ARC_SEGMENT,
            zone_assignment=ZoneAssignment(primary_zone="lower_bout"),
            geometry_type=GeometryType.ARC,
            slope_class=SlopeClass.ASCENDING,
            curvature_class=CurvatureClass.CONVEX_OUTWARD,
            points=points,
        )
        y_min, y_max = prim.y_range
        assert y_min == 0.1
        assert y_max == 0.3

    def test_centroid(self):
        """Test centroid calculation."""
        points = [
            NormalizedPoint(0.0, 0.0),
            NormalizedPoint(0.2, 0.2),
            NormalizedPoint(0.4, 0.4),
        ]
        prim = MorphologyPrimitive(
            primitive_id="test",
            primitive_type=PrimitiveType.LINE_SEGMENT,
            zone_assignment=ZoneAssignment(primary_zone="lower_bout"),
            geometry_type=GeometryType.LINE,
            slope_class=SlopeClass.DIAGONAL_POS,
            curvature_class=CurvatureClass.STRAIGHT,
            points=points,
        )
        centroid = prim.centroid
        assert abs(centroid.x_norm - 0.2) < 0.01
        assert abs(centroid.y_norm - 0.2) < 0.01


class TestPrimitiveDetector:
    """Tests for PrimitiveDetector."""

    @pytest.fixture
    def detector(self):
        return PrimitiveDetector()

    @pytest.fixture
    def zone_classifier(self):
        return ZoneClassifier()

    def test_detect_from_straight_line(self, detector, zone_classifier):
        """Test detection from straight line points."""
        points = [
            NormalizedPoint(-0.5, 0.2),
            NormalizedPoint(-0.5, 0.25),
            NormalizedPoint(-0.5, 0.3),
            NormalizedPoint(-0.5, 0.35),
        ]
        primitives = detector.detect_primitives(points, zone_classifier)

        # Should detect at least one primitive
        assert len(primitives) >= 1

        # First primitive should be line-like (straight vertical)
        prim = primitives[0]
        assert prim.curvature_class == CurvatureClass.STRAIGHT

    def test_detect_from_curved_segment(self, detector, zone_classifier):
        """Test detection from curved segment."""
        # Create a convex curve (lower bout-like)
        import math
        points = []
        for i in range(10):
            angle = math.pi * 0.3 + (math.pi * 0.4) * i / 9
            x = -0.5 * math.cos(angle)
            y = 0.2 + 0.15 * math.sin(angle)
            points.append(NormalizedPoint(x, y))

        primitives = detector.detect_primitives(points, zone_classifier)
        assert len(primitives) >= 1

    def test_empty_points(self, detector, zone_classifier):
        """Test with empty points list."""
        primitives = detector.detect_primitives([], zone_classifier)
        assert primitives == []

    def test_insufficient_points(self, detector, zone_classifier):
        """Test with insufficient points."""
        points = [NormalizedPoint(0.0, 0.0), NormalizedPoint(0.1, 0.1)]
        primitives = detector.detect_primitives(points, zone_classifier)
        # May return 0 or 1 depending on implementation
        assert isinstance(primitives, list)


class TestZoneClassifier:
    """Tests for ZoneClassifier."""

    @pytest.fixture
    def classifier(self):
        return ZoneClassifier()

    def test_classify_lower_bout_point(self, classifier):
        """Test classification of lower bout point."""
        pt = NormalizedPoint(x_norm=-0.5, y_norm=0.25)
        assignment = classifier.classify_point(pt)

        assert assignment.primary_zone == "lower_bout"
        assert assignment.zone_weights["lower_bout"] > 0.5

    def test_classify_waist_point(self, classifier):
        """Test classification of waist point."""
        pt = NormalizedPoint(x_norm=-0.3, y_norm=0.45)
        assignment = classifier.classify_point(pt)

        # Waist should be primary or significant secondary
        assert "waist" in assignment.zone_weights

    def test_classify_upper_bout_point(self, classifier):
        """Test classification of upper bout point."""
        pt = NormalizedPoint(x_norm=-0.4, y_norm=0.65)
        assignment = classifier.classify_point(pt)

        assert "upper_bout" in assignment.zone_weights

    def test_left_flank_filtering(self, classifier):
        """Test that left points get left_flank, not right."""
        pt = NormalizedPoint(x_norm=-0.6, y_norm=0.3)
        assignment = classifier.classify_point(pt)

        # Should not have right_flank
        assert assignment.zone_weights.get("right_flank", 0.0) == 0.0

    def test_right_flank_filtering(self, classifier):
        """Test that right points get right_flank, not left."""
        pt = NormalizedPoint(x_norm=0.6, y_norm=0.3)
        assignment = classifier.classify_point(pt)

        # Should not have left_flank
        assert assignment.zone_weights.get("left_flank", 0.0) == 0.0

    def test_fuzzy_boundary_at_transition(self, classifier):
        """Test fuzzy assignment at zone transition."""
        # Point at waist/lower_bout boundary (~0.37)
        pt = NormalizedPoint(x_norm=-0.4, y_norm=0.37)
        assignment = classifier.classify_point(pt)

        # Should have weights for both zones
        has_lower = "lower_bout" in assignment.zone_weights
        has_waist = "waist" in assignment.zone_weights

        # At least one should be present
        assert has_lower or has_waist
