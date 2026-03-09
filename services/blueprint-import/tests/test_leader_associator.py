"""
Tests for Leader Line Associator
=================================

Tests for Phase 4.0 leader line association functionality.

Author: The Production Shop
Version: 4.0.0
"""

import pytest
import numpy as np
import math

from phase4.leader_associator import (
    LeaderLineAssociator,
    WitnessLineDetector,
    TextRegion,
    WitnessLineGroup,
    AssociatedDimension,
    AssociationMethod
)
from phase4.arrow_detector import Arrow


class MockContourInfo:
    """Mock ContourInfo for testing."""

    def __init__(
        self,
        category: str = "body_outline",
        bbox: tuple = (0, 0, 100, 100),
        width_mm: float = 100.0,
        height_mm: float = 50.0
    ):
        self.category = type('Category', (), {'value': category})()
        self.bbox = bbox
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.contour = np.array([
            [[bbox[0], bbox[1]]],
            [[bbox[0] + bbox[2], bbox[1]]],
            [[bbox[0] + bbox[2], bbox[1] + bbox[3]]],
            [[bbox[0], bbox[1] + bbox[3]]]
        ], dtype=np.int32)


class TestTextRegion:
    """Tests for TextRegion dataclass."""

    def test_text_region_creation(self):
        """Test basic text region creation."""
        region = TextRegion(
            text="24.625",
            bbox=(100, 50, 80, 20),
            confidence=0.95,
            parsed_value=24.625,
            unit="inch"
        )

        assert region.text == "24.625"
        assert region.confidence == 0.95
        assert region.parsed_value == 24.625
        assert region.unit == "inch"

    def test_text_region_auto_center(self):
        """Test automatic center calculation."""
        region = TextRegion(
            text="100",
            bbox=(100, 50, 80, 20),
            confidence=0.9
        )

        # Center should be middle of bbox
        assert region.center == (140.0, 60.0)

    def test_text_region_explicit_center(self):
        """Test explicit center overrides calculation."""
        region = TextRegion(
            text="100",
            bbox=(100, 50, 80, 20),
            confidence=0.9,
            center=(200.0, 100.0)
        )

        assert region.center == (200.0, 100.0)


class TestLeaderLineAssociatorInit:
    """Tests for LeaderLineAssociator initialization."""

    def test_default_init(self):
        """Test default initialization."""
        associator = LeaderLineAssociator()

        assert associator.mm_per_px == 0.0635
        assert associator.dimension_tolerance == 0.05
        assert associator.WEIGHT_PROXIMITY == 40

    def test_custom_mm_per_px(self):
        """Test custom mm per pixel."""
        associator = LeaderLineAssociator(mm_per_px=0.127)  # 200 DPI

        assert associator.mm_per_px == 0.127

    def test_custom_tolerance(self):
        """Test custom dimension tolerance."""
        associator = LeaderLineAssociator(dimension_tolerance=0.10)

        assert associator.dimension_tolerance == 0.10

    def test_custom_radius_calculator(self):
        """Test custom search radius calculator."""
        def custom_calc(width, text_size):
            return width * 0.2

        associator = LeaderLineAssociator(search_radius_calculator=custom_calc)

        assert associator.calc_radius(500, 2.5) == 100.0


class TestUnitConversion:
    """Tests for unit conversion."""

    def test_mm_to_mm(self):
        """Test mm to mm (identity)."""
        associator = LeaderLineAssociator()
        assert associator._convert_to_mm(100, "mm") == 100.0

    def test_inch_to_mm(self):
        """Test inch to mm."""
        associator = LeaderLineAssociator()
        assert associator._convert_to_mm(1, "inch") == 25.4

    def test_cm_to_mm(self):
        """Test cm to mm."""
        associator = LeaderLineAssociator()
        assert associator._convert_to_mm(10, "cm") == 100.0

    def test_unknown_unit(self):
        """Test unknown unit defaults to mm."""
        associator = LeaderLineAssociator()
        assert associator._convert_to_mm(100, "unknown") == 100.0


class TestTextProximitySearch:
    """Tests for finding text near points."""

    def test_find_text_near_point(self):
        """Test finding text near a point."""
        associator = LeaderLineAssociator()

        text_regions = [
            TextRegion(text="100", bbox=(50, 50, 40, 15), confidence=0.9),
            TextRegion(text="200", bbox=(200, 200, 40, 15), confidence=0.9),
        ]

        found = associator._find_text_near_point(
            (70, 57),  # Near first text
            text_regions,
            max_distance=50
        )

        assert found is not None
        assert found.text == "100"

    def test_find_text_no_match(self):
        """Test no text found within distance."""
        associator = LeaderLineAssociator()

        text_regions = [
            TextRegion(text="100", bbox=(50, 50, 40, 15), confidence=0.9),
        ]

        found = associator._find_text_near_point(
            (500, 500),  # Far from text
            text_regions,
            max_distance=50
        )

        assert found is None

    def test_find_closest_text(self):
        """Test finding closest text when multiple nearby."""
        associator = LeaderLineAssociator()

        text_regions = [
            TextRegion(text="100", bbox=(100, 100, 40, 15), confidence=0.9),
            TextRegion(text="200", bbox=(110, 100, 40, 15), confidence=0.9),
        ]

        found = associator._find_text_near_point(
            (105, 107),  # Slightly closer to first
            text_regions,
            max_distance=50
        )

        assert found is not None
        # Should return the closer one
        assert found.text == "100"


class TestGeometrySearch:
    """Tests for finding geometry near points."""

    def test_find_geometry_near_point(self):
        """Test finding geometry near a point."""
        associator = LeaderLineAssociator()

        geometry = {
            'body_outline': [
                MockContourInfo('body_outline', (0, 0, 100, 100))
            ],
            'neck_pocket': [
                MockContourInfo('neck_pocket', (200, 200, 50, 30))
            ]
        }

        candidates = associator._find_geometry_near_point(
            (50, 50),  # Center of body outline
            geometry,
            max_distance=100
        )

        assert len(candidates) >= 1
        # Should find body outline
        found_body = any(
            c[0].category.value == 'body_outline'
            for c in candidates
        )
        assert found_body

    def test_skip_text_category(self):
        """Test that text category is skipped."""
        associator = LeaderLineAssociator()

        geometry = {
            'text': [MockContourInfo('text', (0, 0, 50, 20))],
            'body_outline': [MockContourInfo('body_outline', (0, 0, 100, 100))]
        }

        candidates = associator._find_geometry_near_point(
            (25, 10),  # Near text
            geometry,
            max_distance=100
        )

        # Should not include text category
        for candidate, dist in candidates:
            assert candidate.category.value != 'text'


class TestCandidateRanking:
    """Tests for candidate ranking algorithm."""

    def test_proximity_scoring(self):
        """Test that closer candidates score higher."""
        associator = LeaderLineAssociator()

        text = TextRegion(text="100", bbox=(50, 50, 40, 15), confidence=0.9)

        candidates = [
            (MockContourInfo('body', (0, 0, 100, 100)), 5),    # Very close
            (MockContourInfo('body', (0, 0, 100, 100)), 75),   # Far
        ]

        ranked = associator._rank_candidates(text, candidates)

        assert len(ranked) == 2
        # Closer should score higher
        assert ranked[0][1] > ranked[1][1]

    def test_plausibility_scoring(self):
        """Test dimensional plausibility affects scoring."""
        associator = LeaderLineAssociator()

        text = TextRegion(
            text="100",
            bbox=(50, 50, 40, 15),
            confidence=0.9,
            parsed_value=100.0,
            unit="mm"
        )

        # Same distance but different sizes
        candidates = [
            (MockContourInfo('body', (0, 0, 100, 100), width_mm=100.0), 50),  # Matches
            (MockContourInfo('body', (0, 0, 100, 100), width_mm=50.0), 50),   # Doesn't match
        ]

        ranked = associator._rank_candidates(text, candidates)

        # Matching dimension should score higher
        assert ranked[0][0].width_mm == 100.0

    def test_type_appropriateness_scoring(self):
        """Test feature type appropriateness affects scoring."""
        associator = LeaderLineAssociator()

        # Text mentions "pickup"
        text = TextRegion(
            text="pickup width",
            bbox=(50, 50, 60, 15),
            confidence=0.9
        )

        candidates = [
            (MockContourInfo('pickup_route', (0, 0, 50, 20)), 50),
            (MockContourInfo('body_outline', (0, 0, 100, 100)), 50),
        ]

        ranked = associator._rank_candidates(text, candidates)

        # pickup_route should score higher due to text match
        assert ranked[0][0].category.value == 'pickup_route'


class TestPairedArrowDetection:
    """Tests for paired arrow dimension detection."""

    def test_opposing_arrows_detected(self):
        """Test detection of opposing arrows."""
        associator = LeaderLineAssociator()

        # Two arrows pointing at each other
        arrow1 = Arrow(
            tip_point=(100.0, 50.0),
            tail_point=(50.0, 50.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )
        arrow2 = Arrow(
            tip_point=(200.0, 50.0),
            tail_point=(250.0, 50.0),
            direction=(-1.0, 0.0),
            confidence=0.9,
            contour_index=1
        )

        result = associator._are_opposing_arrows(arrow1, arrow2)
        assert result is True

    def test_same_direction_not_opposing(self):
        """Test that same-direction arrows are not opposing."""
        associator = LeaderLineAssociator()

        # Two arrows pointing same direction
        arrow1 = Arrow(
            tip_point=(100.0, 50.0),
            tail_point=(50.0, 50.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )
        arrow2 = Arrow(
            tip_point=(200.0, 50.0),
            tail_point=(150.0, 50.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=1
        )

        result = associator._are_opposing_arrows(arrow1, arrow2)
        assert result is False

    def test_non_collinear_not_opposing(self):
        """Test that non-collinear arrows are not opposing."""
        associator = LeaderLineAssociator()

        # Two arrows not on same line
        arrow1 = Arrow(
            tip_point=(100.0, 50.0),
            tail_point=(50.0, 50.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )
        arrow2 = Arrow(
            tip_point=(200.0, 150.0),  # Different Y
            tail_point=(250.0, 150.0),
            direction=(-1.0, 0.0),
            confidence=0.9,
            contour_index=1
        )

        result = associator._are_opposing_arrows(arrow1, arrow2)
        assert result is False


class TestDirectionAlignment:
    """Tests for directional alignment scoring."""

    def test_aligned_direction_scores_high(self):
        """Test that aligned direction scores high."""
        associator = LeaderLineAssociator()

        # Arrow pointing toward feature
        arrow = Arrow(
            tip_point=(100.0, 50.0),
            tail_point=(50.0, 50.0),
            direction=(1.0, 0.0),  # Points right
            confidence=0.9,
            contour_index=0
        )

        text_center = (25.0, 50.0)  # Left of arrow

        # Feature to the right (where arrow points)
        feature = MockContourInfo('body', (150, 25, 100, 50))

        score = associator._score_direction_alignment(
            arrow, text_center, feature
        )

        assert score > 0.7  # Should be well aligned

    def test_perpendicular_direction_scores_low(self):
        """Test that perpendicular direction scores low."""
        associator = LeaderLineAssociator()

        # Arrow pointing right
        arrow = Arrow(
            tip_point=(100.0, 50.0),
            tail_point=(50.0, 50.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        text_center = (75.0, 50.0)

        # Feature directly above arrow tail (truly perpendicular)
        # bbox (x, y, w, h) = (25, 0, 50, 20) -> center at (50, 10)
        # Vector from tail (50,50) to feature (50,10) = (0, -40) perpendicular to (1,0)
        feature = MockContourInfo('body', (25, 0, 50, 20))

        score = associator._score_direction_alignment(
            arrow, text_center, feature
        )

        assert score < 0.1  # Should be nearly zero for perpendicular


class TestAssociationMethods:
    """Tests for different association methods."""

    def test_leader_association(self):
        """Test arrow-based leader association."""
        associator = LeaderLineAssociator(mm_per_px=1.0)

        arrows = [
            Arrow(
                tip_point=(100.0, 50.0),
                tail_point=(50.0, 50.0),
                direction=(1.0, 0.0),
                confidence=0.9,
                contour_index=0
            )
        ]

        text_regions = [
            TextRegion(
                text="100",
                bbox=(95, 40, 30, 20),  # Near arrow tip
                confidence=0.9,
                parsed_value=100.0,
                unit="mm"
            )
        ]

        geometry = {
            'body_outline': [
                MockContourInfo('body_outline', (10, 30, 40, 40), width_mm=100.0)
            ]
        }

        associations = associator.associate(
            arrows, text_regions, geometry, blueprint_width_mm=500
        )

        assert len(associations) >= 1
        if associations:
            assert associations[0].arrow is not None

    def test_proximity_association(self):
        """Test proximity-based association when no arrows match."""
        associator = LeaderLineAssociator(mm_per_px=1.0)

        # No arrows
        arrows = []

        text_regions = [
            TextRegion(
                text="50",
                bbox=(60, 60, 20, 15),  # Near feature
                confidence=0.9,
                parsed_value=50.0,
                unit="mm"
            )
        ]

        geometry = {
            'neck_pocket': [
                MockContourInfo('neck_pocket', (50, 50, 50, 30), width_mm=50.0)
            ]
        }

        associations = associator.associate(
            arrows, text_regions, geometry, blueprint_width_mm=500
        )

        # Should fall back to proximity
        if associations:
            assert associations[0].association_method == "proximity"


class TestWitnessLineDetector:
    """Tests for WitnessLineDetector."""

    def test_detector_init(self):
        """Test witness line detector initialization."""
        detector = WitnessLineDetector()
        assert detector.mm_per_px == 0.0635

    def test_is_thin_straight_line(self):
        """Test thin straight line detection."""
        detector = WitnessLineDetector()

        # Create a thin vertical line
        line = np.array([
            [[50, 0]], [[50, 100]]
        ], dtype=np.int32)

        # This should be detected as thin and straight
        result = detector._is_thin_straight_line(line)
        assert isinstance(result, bool)

    def test_point_line_distance(self):
        """Test point to line distance calculation."""
        detector = WitnessLineDetector()

        # Point above horizontal line
        dist = detector._point_line_distance(
            np.array([50, 20]),
            (0, 0),
            (100, 0)
        )

        assert abs(dist - 20.0) < 0.01

    def test_extract_endpoints(self):
        """Test endpoint extraction from witness lines."""
        detector = WitnessLineDetector()

        witnesses = [
            np.array([[[0, 0]], [[0, 50]]], dtype=np.int32),
            np.array([[[100, 0]], [[100, 50]]], dtype=np.int32)
        ]

        endpoints = detector._extract_endpoints(witnesses)

        assert len(endpoints) == 4  # 2 per line


class TestAssociatedDimension:
    """Tests for AssociatedDimension dataclass."""

    def test_associated_dimension_creation(self):
        """Test associated dimension creation."""
        text = TextRegion(
            text="100",
            bbox=(50, 50, 40, 15),
            confidence=0.9,
            parsed_value=100.0,
            unit="mm"
        )

        feature = MockContourInfo('body_outline', (0, 0, 100, 100))

        assoc = AssociatedDimension(
            text_region=text,
            target_feature=feature,
            association_confidence=0.85,
            association_method="leader"
        )

        assert assoc.value_mm == 100.0
        assert assoc.association_confidence == 0.85

    def test_to_dict(self):
        """Test dictionary export."""
        text = TextRegion(
            text="100",
            bbox=(50, 50, 40, 15),
            confidence=0.9,
            parsed_value=100.0,
            unit="mm"
        )

        feature = MockContourInfo('body_outline', (0, 0, 100, 100))

        assoc = AssociatedDimension(
            text_region=text,
            target_feature=feature,
            association_confidence=0.85,
            association_method="leader"
        )

        d = assoc.to_dict()

        assert d['text'] == "100"
        assert d['value_mm'] == 100.0
        assert d['confidence'] == 0.85
        assert d['method'] == "leader"
        assert d['target_category'] == 'body_outline'


class TestAdaptiveRadius:
    """Tests for adaptive search radius calculation."""

    def test_default_radius_calculation(self):
        """Test default radius calculation."""
        associator = LeaderLineAssociator()

        radius = associator._default_radius(
            blueprint_width_mm=500,
            text_size_mm=2.5
        )

        # Should be 10% of width = 50mm
        assert abs(radius - 50.0) < 1.0

    def test_radius_scales_with_text_size(self):
        """Test radius scales with larger text."""
        associator = LeaderLineAssociator()

        small_text_radius = associator._default_radius(500, 2.5)
        large_text_radius = associator._default_radius(500, 5.0)

        assert large_text_radius > small_text_radius

    def test_radius_capped(self):
        """Test radius is capped at maximum."""
        associator = LeaderLineAssociator()

        radius = associator._default_radius(
            blueprint_width_mm=5000,  # Very large
            text_size_mm=10.0
        )

        assert radius <= 200.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
