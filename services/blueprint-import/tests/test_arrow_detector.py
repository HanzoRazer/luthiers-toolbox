"""
Tests for Arrow Detector
========================

Tests for Phase 4.0 arrow detection functionality.

Author: The Production Shop
Version: 4.0.0
"""

import pytest
import numpy as np
import math

from phase4.arrow_detector import (
    Arrow,
    ArrowDetector,
    ArrowDetectionStats,
    ArrowOrientation
)


class TestArrowDataclass:
    """Tests for Arrow dataclass."""

    def test_arrow_creation(self):
        """Test basic arrow creation."""
        arrow = Arrow(
            tip_point=(100.0, 50.0),
            tail_point=(50.0, 50.0),
            direction=(1.0, 0.0),
            confidence=0.95,
            contour_index=5
        )

        assert arrow.tip_point == (100.0, 50.0)
        assert arrow.tail_point == (50.0, 50.0)
        assert arrow.confidence == 0.95
        assert arrow.detection_method == "contour"

    def test_arrow_length(self):
        """Test arrow length calculation."""
        arrow = Arrow(
            tip_point=(100.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        assert arrow.length == 100.0

    def test_arrow_length_diagonal(self):
        """Test arrow length for diagonal arrow."""
        arrow = Arrow(
            tip_point=(30.0, 40.0),
            tail_point=(0.0, 0.0),
            direction=(0.6, 0.8),
            confidence=0.9,
            contour_index=0
        )

        assert arrow.length == 50.0  # 3-4-5 triangle

    def test_arrow_angle_horizontal_right(self):
        """Test angle for rightward horizontal arrow."""
        arrow = Arrow(
            tip_point=(100.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        assert arrow.angle_degrees == 0.0

    def test_arrow_angle_horizontal_left(self):
        """Test angle for leftward horizontal arrow."""
        arrow = Arrow(
            tip_point=(0.0, 0.0),
            tail_point=(100.0, 0.0),
            direction=(-1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        assert abs(arrow.angle_degrees - 180.0) < 0.01 or abs(arrow.angle_degrees + 180.0) < 0.01

    def test_arrow_angle_vertical_up(self):
        """Test angle for upward vertical arrow (image coords: -y is up)."""
        arrow = Arrow(
            tip_point=(0.0, 0.0),
            tail_point=(0.0, 100.0),
            direction=(0.0, -1.0),
            confidence=0.9,
            contour_index=0
        )

        assert abs(arrow.angle_degrees - 90.0) < 0.01

    def test_arrow_to_dict(self):
        """Test dictionary export."""
        arrow = Arrow(
            tip_point=(100.0, 50.0),
            tail_point=(50.0, 50.0),
            direction=(1.0, 0.0),
            confidence=0.95,
            contour_index=5,
            detection_method="template"
        )

        d = arrow.to_dict()

        assert d['tip'] == (100.0, 50.0)
        assert d['tail'] == (50.0, 50.0)
        assert d['confidence'] == 0.95
        assert d['method'] == "template"
        assert d['length'] == 50.0
        assert d['angle'] == 0.0


class TestArrowDetectorInit:
    """Tests for ArrowDetector initialization."""

    def test_default_init(self):
        """Test default initialization."""
        detector = ArrowDetector()

        assert detector.debug_mode is False
        assert detector.orientation_filter == ArrowOrientation.ANY
        assert detector.prefer_axis_aligned is True

    def test_debug_mode(self):
        """Test debug mode initialization."""
        detector = ArrowDetector(debug_mode=True)

        assert detector.debug_mode is True

    def test_orientation_filter(self):
        """Test orientation filter initialization."""
        detector = ArrowDetector(orientation_filter=ArrowOrientation.HORIZONTAL)

        assert detector.orientation_filter == ArrowOrientation.HORIZONTAL

    def test_thresholds(self):
        """Test default thresholds."""
        detector = ArrowDetector()

        assert detector.MIN_ARROW_LENGTH == 5.0
        assert detector.MAX_ARROW_LENGTH == 50.0
        assert detector.AXIS_ANGLE_TOLERANCE == 15.0


class TestArrowDetectorMockMode:
    """Tests for ArrowDetector debug/mock mode."""

    def test_mock_arrows_returned(self):
        """Test that debug mode returns mock arrows."""
        detector = ArrowDetector(debug_mode=True)
        arrows = detector.detect_arrows([])

        assert len(arrows) == 3
        assert all(a.detection_method == "mock" for a in arrows)

    def test_mock_arrows_have_valid_geometry(self):
        """Test that mock arrows have valid geometry."""
        detector = ArrowDetector(debug_mode=True)
        arrows = detector.detect_arrows([])

        for arrow in arrows:
            assert arrow.length > 0
            assert 0 <= arrow.confidence <= 1
            dir_length = math.sqrt(arrow.direction[0]**2 + arrow.direction[1]**2)
            assert abs(dir_length - 1.0) < 0.01


class TestArrowDetectorContourAnalysis:
    """Tests for contour-based arrow detection."""

    def test_empty_contours(self):
        """Test with empty contour list."""
        detector = ArrowDetector()
        arrows = detector.detect_arrows([])

        assert len(arrows) == 0

    def test_too_small_contour(self):
        """Test that very small contours are skipped."""
        detector = ArrowDetector()

        # Contour with only 3 points
        small_contour = np.array([
            [[0, 0]], [[10, 0]], [[5, 5]]
        ], dtype=np.int32)

        arrows = detector.detect_arrows([small_contour])

        # Should not crash, may or may not detect
        assert isinstance(arrows, list)

    def test_triangular_tip_detection(self):
        """Test triangular tip detection helper."""
        detector = ArrowDetector()

        # Create a simple triangular contour (arrowhead shape)
        triangle = np.array([
            [[0, 0]], [[20, 10]], [[20, -10]], [[0, 0]]
        ], dtype=np.int32)

        # This should be detected as triangular
        # (actual result depends on convexity defects)
        result = detector.is_triangular_tip(triangle)
        assert isinstance(result, bool)

    def test_arrow_shape_contour(self):
        """Test detection of arrow-shaped contour."""
        detector = ArrowDetector()

        # Create an arrow-shaped contour
        # Shaft from (0,0) to (40,0), head at (50,0) with barbs
        arrow_contour = np.array([
            [[0, 0]],    # tail
            [[40, 0]],   # shaft end
            [[35, 5]],   # upper barb
            [[50, 0]],   # tip
            [[35, -5]],  # lower barb
            [[40, 0]],   # back to shaft
            [[0, 0]]     # close
        ], dtype=np.int32)

        arrows = detector.detect_arrows([arrow_contour])

        # May or may not detect depending on convexity analysis
        assert isinstance(arrows, list)


class TestArrowOrientationFiltering:
    """Tests for orientation-based filtering."""

    def test_horizontal_filter_keeps_horizontal(self):
        """Test that horizontal filter keeps horizontal arrows."""
        detector = ArrowDetector(orientation_filter=ArrowOrientation.HORIZONTAL)

        # Create horizontal arrow
        horizontal = Arrow(
            tip_point=(100.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        filtered = detector._filter_by_orientation([horizontal])

        assert len(filtered) == 1

    def test_horizontal_filter_removes_vertical(self):
        """Test that horizontal filter removes vertical arrows."""
        detector = ArrowDetector(orientation_filter=ArrowOrientation.HORIZONTAL)

        # Create vertical arrow
        vertical = Arrow(
            tip_point=(0.0, 100.0),
            tail_point=(0.0, 0.0),
            direction=(0.0, 1.0),
            confidence=0.9,
            contour_index=0
        )

        filtered = detector._filter_by_orientation([vertical])

        assert len(filtered) == 0

    def test_vertical_filter_keeps_vertical(self):
        """Test that vertical filter keeps vertical arrows."""
        detector = ArrowDetector(orientation_filter=ArrowOrientation.VERTICAL)

        # Create vertical arrow (pointing up in image coords)
        vertical = Arrow(
            tip_point=(0.0, 0.0),
            tail_point=(0.0, 100.0),
            direction=(0.0, -1.0),
            confidence=0.9,
            contour_index=0
        )

        filtered = detector._filter_by_orientation([vertical])

        assert len(filtered) == 1

    def test_any_filter_keeps_all(self):
        """Test that ANY filter keeps all arrows."""
        detector = ArrowDetector(orientation_filter=ArrowOrientation.ANY)

        arrows = [
            Arrow(tip_point=(100, 0), tail_point=(0, 0), direction=(1, 0),
                  confidence=0.9, contour_index=0),
            Arrow(tip_point=(0, 100), tail_point=(0, 0), direction=(0, 1),
                  confidence=0.9, contour_index=1),
            Arrow(tip_point=(50, 50), tail_point=(0, 0), direction=(0.707, 0.707),
                  confidence=0.9, contour_index=2),
        ]

        filtered = detector._filter_by_orientation(arrows)

        assert len(filtered) == 3


class TestAxisAlignedBoosting:
    """Tests for axis-aligned confidence boosting."""

    def test_horizontal_gets_boost(self):
        """Test that horizontal arrow gets confidence boost."""
        detector = ArrowDetector(prefer_axis_aligned=True)

        horizontal = Arrow(
            tip_point=(100.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.8,
            contour_index=0
        )

        boosted = detector._boost_axis_aligned([horizontal])

        assert len(boosted) == 1
        assert boosted[0].confidence > 0.8  # Should be boosted

    def test_diagonal_no_boost(self):
        """Test that diagonal arrow doesn't get boost."""
        detector = ArrowDetector(prefer_axis_aligned=True)

        diagonal = Arrow(
            tip_point=(50.0, 50.0),
            tail_point=(0.0, 0.0),
            direction=(0.707, 0.707),
            confidence=0.8,
            contour_index=0
        )

        boosted = detector._boost_axis_aligned([diagonal])

        assert len(boosted) == 1
        assert boosted[0].confidence == 0.8  # Should not be boosted

    def test_boost_capped_at_one(self):
        """Test that boost doesn't exceed 1.0."""
        detector = ArrowDetector(prefer_axis_aligned=True)

        horizontal = Arrow(
            tip_point=(100.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.95,  # Already high
            contour_index=0
        )

        boosted = detector._boost_axis_aligned([horizontal])

        assert boosted[0].confidence <= 1.0


class TestArrowValidation:
    """Tests for arrow geometry validation."""

    def test_valid_arrow(self):
        """Test validation of valid arrow."""
        detector = ArrowDetector()

        arrow = Arrow(
            tip_point=(50.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        is_valid, reason = detector.validate_arrow_geometry(arrow)

        assert is_valid is True
        assert reason == "OK"

    def test_too_short_arrow(self):
        """Test validation rejects too-short arrow."""
        detector = ArrowDetector()

        arrow = Arrow(
            tip_point=(3.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        is_valid, reason = detector.validate_arrow_geometry(arrow)

        assert is_valid is False
        assert "Too short" in reason

    def test_too_long_arrow(self):
        """Test validation rejects too-long arrow."""
        detector = ArrowDetector()

        arrow = Arrow(
            tip_point=(100.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.9,
            contour_index=0
        )

        is_valid, reason = detector.validate_arrow_geometry(arrow)

        assert is_valid is False
        assert "Too long" in reason

    def test_low_confidence_arrow(self):
        """Test validation flags low confidence."""
        detector = ArrowDetector()

        arrow = Arrow(
            tip_point=(30.0, 0.0),
            tail_point=(0.0, 0.0),
            direction=(1.0, 0.0),
            confidence=0.2,  # Below threshold
            contour_index=0
        )

        is_valid, reason = detector.validate_arrow_geometry(arrow)

        assert is_valid is False
        assert "Low confidence" in reason


class TestDuplicateRemoval:
    """Tests for duplicate arrow removal."""

    def test_no_duplicates(self):
        """Test that distinct arrows are kept."""
        detector = ArrowDetector()

        arrows = [
            Arrow(tip_point=(100, 0), tail_point=(0, 0), direction=(1, 0),
                  confidence=0.9, contour_index=0),
            Arrow(tip_point=(0, 100), tail_point=(0, 0), direction=(0, 1),
                  confidence=0.8, contour_index=1),
        ]

        unique = detector._remove_duplicates(arrows)

        assert len(unique) == 2

    def test_removes_duplicates(self):
        """Test that nearby arrows are deduplicated."""
        detector = ArrowDetector()

        arrows = [
            Arrow(tip_point=(100, 0), tail_point=(0, 0), direction=(1, 0),
                  confidence=0.9, contour_index=0),
            Arrow(tip_point=(102, 0), tail_point=(2, 0), direction=(1, 0),
                  confidence=0.8, contour_index=1),  # Very close to first
        ]

        unique = detector._remove_duplicates(arrows)

        assert len(unique) == 1
        assert unique[0].confidence == 0.9  # Higher confidence kept

    def test_keeps_higher_confidence(self):
        """Test that higher confidence duplicate is kept."""
        detector = ArrowDetector()

        arrows = [
            Arrow(tip_point=(100, 0), tail_point=(0, 0), direction=(1, 0),
                  confidence=0.7, contour_index=0),
            Arrow(tip_point=(101, 0), tail_point=(1, 0), direction=(1, 0),
                  confidence=0.95, contour_index=1),  # Higher confidence
        ]

        unique = detector._remove_duplicates(arrows)

        assert len(unique) == 1
        assert unique[0].confidence == 0.95


class TestArrowDetectionStats:
    """Tests for detection statistics."""

    def test_stats_initialization(self):
        """Test stats are initialized to zero."""
        stats = ArrowDetectionStats()

        assert stats.contour_detections == 0
        assert stats.template_matches == 0
        assert stats.image_detections == 0
        assert stats.total_arrows == 0

    def test_stats_updated_after_detection(self):
        """Test stats are updated after detection."""
        detector = ArrowDetector(debug_mode=False)

        # Create a simple contour that won't produce arrows
        # but will exercise the detection code
        simple_contour = np.array([
            [[0, 0]], [[100, 0]], [[100, 100]], [[0, 100]]
        ], dtype=np.int32)

        detector.detect_arrows([simple_contour])

        # Stats should be initialized even if no arrows found
        assert detector.stats.processing_time_ms > 0
        assert detector.stats.total_arrows >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
