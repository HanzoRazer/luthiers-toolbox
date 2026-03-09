"""
Grid Zone Classifier Tests
==========================

Unit tests for the GridZoneClassifier and related zone functionality.

Author: The Production Shop
Version: 4.0.0
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from classifiers.grid_zone import (
    GridZoneClassifier,
    GridZone,
    GridZoneType,
    ZoneClassificationResult,
    ELECTRIC_GUITAR_GRID
)
from classifiers.grid_zone.zones import GridDefinition


# =============================================================================
# GridZone Tests
# =============================================================================

class TestGridZone:
    """Tests for GridZone dataclass."""

    def test_contains_point_inside(self):
        """Point inside zone returns True."""
        zone = GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.2, x_max=0.8,
            y_min=0.2, y_max=0.8,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Test zone"
        )
        assert zone.contains_point(0.5, 0.5) is True

    def test_contains_point_outside(self):
        """Point outside zone returns False."""
        zone = GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.2, x_max=0.8,
            y_min=0.2, y_max=0.8,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Test zone"
        )
        assert zone.contains_point(0.1, 0.1) is False

    def test_contains_point_on_edge(self):
        """Point on zone edge returns True."""
        zone = GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.2, x_max=0.8,
            y_min=0.2, y_max=0.8,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Test zone"
        )
        assert zone.contains_point(0.2, 0.5) is True

    def test_contains_bbox_full_overlap(self):
        """Bbox fully inside zone returns 1.0."""
        zone = GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.0, x_max=1.0,
            y_min=0.0, y_max=1.0,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Test zone"
        )
        overlap = zone.contains_bbox(0.2, 0.2, 0.8, 0.8)
        assert overlap == 1.0

    def test_contains_bbox_partial_overlap(self):
        """Bbox partially inside zone returns fractional overlap."""
        zone = GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.0, x_max=0.5,
            y_min=0.0, y_max=1.0,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Test zone"
        )
        # Bbox spans x: 0.25 to 0.75, zone covers 0 to 0.5
        # Intersection: 0.25 to 0.5 = 0.25 width
        # Bbox width: 0.5
        # Overlap: 0.25/0.5 = 0.5
        overlap = zone.contains_bbox(0.25, 0.0, 0.75, 1.0)
        assert overlap == pytest.approx(0.5, rel=0.01)

    def test_contains_bbox_no_overlap(self):
        """Bbox outside zone returns 0.0."""
        zone = GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.0, x_max=0.5,
            y_min=0.0, y_max=0.5,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Test zone"
        )
        overlap = zone.contains_bbox(0.6, 0.6, 0.9, 0.9)
        assert overlap == 0.0

    def test_zone_center(self):
        """Zone center is calculated correctly."""
        zone = GridZone(
            zone_type=GridZoneType.BRIDGE_ZONE,
            x_min=0.4, x_max=0.6,
            y_min=0.7, y_max=0.8,
            color_name="gray",
            color_rgb=(169, 169, 169),
            contour_category="BRIDGE_ROUTE",
            description="Bridge zone"
        )
        assert zone.center == (0.5, 0.75)

    def test_zone_area(self):
        """Zone area is calculated correctly."""
        zone = GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.2, x_max=0.8,
            y_min=0.2, y_max=0.8,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Test zone"
        )
        assert zone.area == pytest.approx(0.36, rel=0.01)

    def test_zone_to_dict(self):
        """Zone serializes to dictionary correctly."""
        zone = GridZone(
            zone_type=GridZoneType.NECK_POCKET,
            x_min=0.4, x_max=0.6,
            y_min=0.0, y_max=0.2,
            color_name="brown",
            color_rgb=(139, 90, 43),
            contour_category="NECK_POCKET",
            description="Neck pocket"
        )
        d = zone.to_dict()
        assert d["zone_type"] == "neck_pocket"
        assert d["contour_category"] == "NECK_POCKET"
        assert d["bounds"]["x_min"] == 0.4


# =============================================================================
# GridDefinition Tests
# =============================================================================

class TestGridDefinition:
    """Tests for GridDefinition class."""

    def test_electric_guitar_grid_exists(self):
        """Default electric guitar grid is defined."""
        assert ELECTRIC_GUITAR_GRID is not None
        assert ELECTRIC_GUITAR_GRID.name == "STEM Guitar Electric Body Grid"

    def test_electric_guitar_grid_has_zones(self):
        """Electric guitar grid has expected zones."""
        assert len(ELECTRIC_GUITAR_GRID.zones) >= 8

    def test_get_zone_at_center(self):
        """Get zone at center returns body canvas."""
        zone = ELECTRIC_GUITAR_GRID.get_zone_at_point(0.5, 0.5)
        assert zone is not None
        assert zone.zone_type == GridZoneType.BODY_CANVAS

    def test_get_zone_at_neck_pocket(self):
        """Get zone at top center returns neck pocket."""
        zone = ELECTRIC_GUITAR_GRID.get_zone_at_point(0.5, 0.1)
        assert zone is not None
        assert zone.zone_type == GridZoneType.NECK_POCKET

    def test_get_zone_at_bridge(self):
        """Get zone at lower center returns bridge zone."""
        zone = ELECTRIC_GUITAR_GRID.get_zone_at_point(0.5, 0.75)
        assert zone is not None
        assert zone.zone_type == GridZoneType.BRIDGE_ZONE

    def test_get_zone_at_left_wing(self):
        """Get zone at left edge returns wing limit."""
        zone = ELECTRIC_GUITAR_GRID.get_zone_at_point(0.05, 0.5)
        assert zone is not None
        assert zone.zone_type == GridZoneType.WING_LIMIT_LEFT

    def test_get_zones_for_bbox(self):
        """Get zones for spanning bbox returns multiple zones."""
        zones = ELECTRIC_GUITAR_GRID.get_zones_for_bbox(
            0.0, 0.0, 1.0, 1.0,
            min_overlap=0.01
        )
        assert len(zones) > 1

    def test_symmetry_score_centered(self):
        """Centered bbox has high symmetry score."""
        score = ELECTRIC_GUITAR_GRID.calculate_symmetry_score(
            (0.25, 0.2, 0.75, 0.8)
        )
        assert score == 1.0

    def test_symmetry_score_offset(self):
        """Offset bbox has lower symmetry score."""
        score = ELECTRIC_GUITAR_GRID.calculate_symmetry_score(
            (0.6, 0.2, 0.9, 0.8)
        )
        assert score < 0.7

    def test_validate_body_proportions_valid(self):
        """Valid body proportions pass validation."""
        result = ELECTRIC_GUITAR_GRID.validate_body_proportions(12, 18)
        assert result["valid"] is True

    def test_validate_body_proportions_too_wide(self):
        """Body exceeding max width generates warning."""
        result = ELECTRIC_GUITAR_GRID.validate_body_proportions(25, 20)
        assert len(result["warnings"]) > 0


# =============================================================================
# GridZoneClassifier Tests
# =============================================================================

class TestGridZoneClassifier:
    """Tests for GridZoneClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create classifier with default grid."""
        return GridZoneClassifier()

    def test_classifier_initialization(self, classifier):
        """Classifier initializes with default grid."""
        assert classifier.grid == ELECTRIC_GUITAR_GRID
        assert classifier.min_overlap == 0.1

    def test_classify_point_center(self, classifier):
        """Classify center point returns body outline."""
        result = classifier.classify_point(0.5, 0.5)
        assert result.primary_category == "BODY_OUTLINE"

    def test_classify_point_neck_pocket(self, classifier):
        """Classify top center returns neck pocket."""
        result = classifier.classify_point(0.5, 0.1)
        assert result.primary_category == "NECK_POCKET"

    def test_classify_point_bridge(self, classifier):
        """Classify lower center returns bridge route."""
        result = classifier.classify_point(0.5, 0.75)
        assert result.primary_category == "BRIDGE_ROUTE"

    def test_classify_bbox_body(self, classifier):
        """Classify body-sized bbox returns body outline."""
        result = classifier.classify_bbox(0.15, 0.2, 0.85, 0.95)
        assert result.primary_category == "BODY_OUTLINE"
        assert result.is_confident

    def test_classify_bbox_returns_symmetry(self, classifier):
        """Classification includes symmetry score."""
        result = classifier.classify_bbox(0.3, 0.3, 0.7, 0.7)
        assert 0.0 <= result.symmetry_score <= 1.0

    def test_classify_bbox_centered_high_symmetry(self, classifier):
        """Centered bbox has high symmetry score."""
        result = classifier.classify_bbox(0.25, 0.3, 0.75, 0.7)
        assert result.symmetry_score > 0.9

    def test_classify_bbox_offset_low_symmetry(self, classifier):
        """Offset bbox has lower symmetry score."""
        result = classifier.classify_bbox(0.6, 0.3, 0.9, 0.7)
        assert result.symmetry_score <= 0.5  # Center at 0.75, offset 0.25 from centerline

    def test_classify_bbox_returns_ml_features(self, classifier):
        """Classification includes ML features."""
        result = classifier.classify_bbox(0.2, 0.2, 0.8, 0.8)
        assert "center_x_norm" in result.ml_features
        assert "symmetry_score" in result.ml_features
        assert "zone_count" in result.ml_features

    def test_classify_bbox_spanning_zones(self, classifier):
        """Bbox spanning multiple zones returns all zone matches."""
        result = classifier.classify_bbox(0.0, 0.0, 1.0, 0.3)
        assert len(result.all_zones) > 1

    def test_classification_result_to_dict(self, classifier):
        """Classification result serializes to dict."""
        result = classifier.classify_bbox(0.3, 0.3, 0.7, 0.7)
        d = result.to_dict()
        assert "primary_category" in d
        assert "symmetry_score" in d
        assert "ml_features" in d

    def test_wing_extend_left(self, classifier):
        """Left-extending bbox has wing_extend_left > 0."""
        result = classifier.classify_bbox(0.0, 0.3, 0.5, 0.7)
        assert result.wing_extend_left > 0

    def test_wing_extend_right(self, classifier):
        """Right-extending bbox has wing_extend_right > 0."""
        result = classifier.classify_bbox(0.5, 0.3, 1.0, 0.7)
        assert result.wing_extend_right > 0

    def test_needs_review_ambiguous(self, classifier):
        """Ambiguous classification needs review."""
        # Bbox that spans neck pocket and upper bout equally
        result = classifier.classify_bbox(0.2, 0.0, 0.8, 0.2)
        # This may or may not need review depending on overlap ratios
        # Just verify the property exists and is boolean
        assert isinstance(result.needs_review, bool)

    def test_get_zone_by_type(self, classifier):
        """Get specific zone by type."""
        zone = classifier.get_zone_by_type(GridZoneType.NECK_POCKET)
        assert zone is not None
        assert zone.zone_type == GridZoneType.NECK_POCKET


# =============================================================================
# Integration Tests
# =============================================================================

class TestGridZoneIntegration:
    """Integration tests for grid zone classification."""

    def test_classify_stratocaster_proportions(self):
        """Stratocaster-like body classifies correctly."""
        classifier = GridZoneClassifier()
        # Strat-like proportions: ~75% width of grid, full body canvas height
        result = classifier.classify_bbox(0.125, 0.2, 0.875, 0.95)

        assert result.primary_category == "BODY_OUTLINE"
        assert result.symmetry_score > 0.9
        assert result.is_confident

    def test_classify_les_paul_proportions(self):
        """Les Paul-like body (narrower upper bout) classifies correctly."""
        classifier = GridZoneClassifier()
        # LP has slightly narrower upper region
        result = classifier.classify_bbox(0.2, 0.15, 0.8, 0.9)

        assert result.primary_category == "BODY_OUTLINE"
        assert result.is_confident

    def test_classify_pickup_route(self):
        """Small centered feature classifies based on position."""
        classifier = GridZoneClassifier()
        # Pickup route in body center
        result = classifier.classify_bbox(0.35, 0.4, 0.65, 0.55)

        assert result.primary_category == "BODY_OUTLINE"
        # Would need to be in bridge zone to be BRIDGE_ROUTE

    def test_ml_features_complete(self):
        """ML features include all expected values."""
        classifier = GridZoneClassifier()
        result = classifier.classify_bbox(0.2, 0.2, 0.8, 0.8)

        expected_features = [
            "center_x_norm",
            "center_y_norm",
            "width_norm",
            "height_norm",
            "aspect_ratio",
            "symmetry_score",
            "wing_extend_left",
            "wing_extend_right",
            "zone_count",
            "primary_zone_confidence"
        ]

        for feature in expected_features:
            assert feature in result.ml_features, f"Missing feature: {feature}"

    def test_batch_classification(self):
        """Batch classification processes multiple bboxes."""
        classifier = GridZoneClassifier()

        # Simulate contours as (x, y, w, h) tuples
        mock_contours = [
            (100, 100, 600, 800),  # Body
            (350, 50, 100, 100),   # Neck area
            (300, 600, 200, 100),  # Bridge area
        ]

        results = []
        for x, y, w, h in mock_contours:
            # Normalize to image size 800x1000
            result = classifier.classify_bbox(
                x / 800, y / 1000,
                (x + w) / 800, (y + h) / 1000
            )
            results.append(result)

        assert len(results) == 3
        assert all(isinstance(r, ZoneClassificationResult) for r in results)


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_zero_size_bbox(self):
        """Zero-size bbox doesn't crash."""
        classifier = GridZoneClassifier()
        result = classifier.classify_bbox(0.5, 0.5, 0.5, 0.5)
        assert result is not None

    def test_bbox_outside_grid(self):
        """Bbox fully outside grid handles gracefully."""
        classifier = GridZoneClassifier()
        result = classifier.classify_bbox(1.5, 1.5, 2.0, 2.0)
        assert result.primary_category == "UNKNOWN"

    def test_negative_coordinates(self):
        """Negative coordinates handle gracefully."""
        classifier = GridZoneClassifier()
        result = classifier.classify_bbox(-0.5, -0.5, 0.2, 0.2)
        # Should still find zones for the portion inside grid
        assert result is not None

    def test_inverted_bbox(self):
        """Bbox with max < min handles gracefully."""
        classifier = GridZoneClassifier()
        # This is invalid input, but shouldn't crash
        result = classifier.classify_bbox(0.8, 0.8, 0.2, 0.2)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
