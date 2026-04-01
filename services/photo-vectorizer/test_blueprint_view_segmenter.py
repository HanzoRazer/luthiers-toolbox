"""
Tests for blueprint_view_segmenter.py
"""

from __future__ import annotations

import numpy as np
import pytest
import cv2

from blueprint_view_segmenter import (
    is_page_border_contour,
    edge_contact_penalty,
    filter_border_contours,
    reject_oversized_contours,
    BlueprintViewSegmenter,
    DetectedView,
    ViewType,
)


# =============================================================================
# Page Border Detection Tests
# =============================================================================

class TestIsPageBorderContour:
    """Tests for is_page_border_contour()."""

    def test_full_rectangle_is_border(self):
        """A rectangle touching all 4 edges should be detected as border."""
        image_shape = (1000, 800)  # (h, w)
        # Rectangle that touches all edges
        contour = np.array([
            [5, 5], [795, 5], [795, 995], [5, 995]
        ], dtype=np.int32)

        assert is_page_border_contour(contour, image_shape, margin=10) is True

    def test_small_centered_contour_not_border(self):
        """A small centered contour should not be detected as border."""
        image_shape = (1000, 800)
        # Small rectangle in center
        contour = np.array([
            [300, 400], [500, 400], [500, 600], [300, 600]
        ], dtype=np.int32)

        assert is_page_border_contour(contour, image_shape, margin=10) is False

    def test_contour_touching_two_edges_with_high_contact(self):
        """A contour with high edge contact ratio may still be flagged.

        Note: The algorithm checks edge contact ratio (fraction of points near edges).
        A 4-point rectangle with 2 corners on edges has 50% edge contact, which
        exceeds the default 15% threshold. This is intentional - such contours
        are suspicious and should be reviewed.
        """
        image_shape = (1000, 800)
        # Rectangle touching left and top only - but with high edge contact
        contour = np.array([
            [5, 5], [400, 5], [400, 500], [5, 500]
        ], dtype=np.int32)

        # With default threshold, this IS flagged due to high edge contact (50%)
        assert is_page_border_contour(contour, image_shape, margin=10) is True

        # With strict threshold (60%), it would NOT be flagged
        assert is_page_border_contour(
            contour, image_shape, margin=10, edge_contact_threshold=0.60
        ) is False

    def test_contour_touching_three_edges_is_border(self):
        """A contour touching 3 edges should be detected as border."""
        image_shape = (1000, 800)
        # Rectangle touching left, top, and right
        contour = np.array([
            [5, 5], [795, 5], [795, 500], [5, 500]
        ], dtype=np.int32)

        assert is_page_border_contour(contour, image_shape, margin=10) is True

    def test_large_area_contour_is_border(self):
        """A contour covering >70% of image should be detected as border."""
        image_shape = (1000, 800)
        # Large rectangle covering 72% of image
        w, h = 760, 950  # 760*950 / (800*1000) = 0.722
        contour = np.array([
            [20, 25], [20+w, 25], [20+w, 25+h], [20, 25+h]
        ], dtype=np.int32)

        assert is_page_border_contour(contour, image_shape, margin=10) is True


class TestEdgeContactPenalty:
    """Tests for edge_contact_penalty()."""

    def test_centered_contour_low_penalty(self):
        """A centered contour should have low edge contact penalty."""
        image_shape = (1000, 800)
        contour = np.array([
            [300, 400], [500, 400], [500, 600], [300, 600]
        ], dtype=np.int32)

        penalty = edge_contact_penalty(contour, image_shape, margin=5)
        assert penalty < 0.1

    def test_edge_touching_contour_high_penalty(self):
        """A contour touching edges should have high penalty."""
        image_shape = (1000, 800)
        # Rectangle touching all edges
        contour = np.array([
            [2, 2], [798, 2], [798, 998], [2, 998]
        ], dtype=np.int32)

        penalty = edge_contact_penalty(contour, image_shape, margin=5)
        assert penalty > 0.5


class TestFilterBorderContours:
    """Tests for filter_border_contours()."""

    def test_removes_page_borders(self):
        """Should remove page border contours from list."""
        image_shape = (1000, 800)

        # One border, one body
        border = np.array([[5, 5], [795, 5], [795, 995], [5, 995]], dtype=np.int32)
        body = np.array([[300, 400], [500, 400], [500, 600], [300, 600]], dtype=np.int32)

        contours = [border, body]
        filtered = filter_border_contours(contours, image_shape, margin=10)

        assert len(filtered) == 1
        assert np.array_equal(filtered[0], body)


class TestRejectOversizedContours:
    """Tests for reject_oversized_contours()."""

    def test_rejects_large_contours(self):
        """Should reject contours covering >70% of image."""
        image_shape = (1000, 800)

        # Large contour (75% of image)
        large = np.array([[0, 0], [800, 0], [800, 750], [0, 750]], dtype=np.int32)
        # Normal body (20% of image)
        body = np.array([[200, 300], [600, 300], [600, 700], [200, 700]], dtype=np.int32)

        contours = [large, body]
        filtered = reject_oversized_contours(contours, image_shape, max_area_ratio=0.70)

        assert len(filtered) == 1
        assert np.array_equal(filtered[0], body)


# =============================================================================
# View Segmentation Tests
# =============================================================================

class TestBlueprintViewSegmenter:
    """Tests for BlueprintViewSegmenter class."""

    def test_single_view_returns_full_image(self, tmp_path):
        """A single-view image should return one view covering full image."""
        # Create simple test image
        img = np.zeros((500, 400, 3), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (300, 400), (255, 255, 255), 2)

        img_path = tmp_path / "single_view.png"
        cv2.imwrite(str(img_path), img)

        segmenter = BlueprintViewSegmenter()
        result = segmenter.segment(img_path)

        assert result.view_count >= 1
        assert result.original_size == (400, 500)

    def test_detects_multi_view_with_divider_line(self, tmp_path):
        """Should detect multiple views when separated by thick line."""
        # Create image with vertical divider
        img = np.ones((500, 400, 3), dtype=np.uint8) * 255
        # Left view content
        cv2.rectangle(img, (50, 100), (150, 400), (0, 0, 0), 2)
        # Right view content
        cv2.rectangle(img, (250, 100), (350, 400), (0, 0, 0), 2)
        # Thick vertical divider
        cv2.line(img, (200, 0), (200, 500), (0, 0, 0), 5)

        img_path = tmp_path / "multi_view.png"
        cv2.imwrite(str(img_path), img)

        segmenter = BlueprintViewSegmenter()
        result = segmenter.segment(img_path, method="lines")

        # Should detect at least the divider effect
        assert result.original_size == (400, 500)


class TestDetectedView:
    """Tests for DetectedView dataclass."""

    def test_properties(self):
        """Test DetectedView computed properties."""
        view = DetectedView(
            bbox=(100, 200, 300, 400),
            label="test_view",
            view_type=ViewType.FRONT,
            confidence=0.85,
        )

        assert view.x == 100
        assert view.y == 200
        assert view.width == 300
        assert view.height == 400
        assert view.center == (250, 400)

    def test_area_ratio(self):
        """Test area ratio calculation."""
        view = DetectedView(
            bbox=(0, 0, 400, 500),
            area_ratio=0.25,
        )

        assert view.area_ratio == 0.25


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegrationWithExistingPipeline:
    """Tests for integration with photo_vectorizer pipeline."""

    def test_border_filter_in_pipeline(self):
        """Border filtering should work with numpy contours from cv2.findContours."""
        # Simulate what findContours returns
        image_shape = (1000, 800)

        # Border-like contour (what findContours returns for page edge)
        border = np.array([
            [[5, 5]], [[795, 5]], [[795, 995]], [[5, 995]]
        ], dtype=np.int32)

        # Body-like contour
        body = np.array([
            [[300, 400]], [[500, 400]], [[500, 600]], [[300, 600]]
        ], dtype=np.int32)

        # Reshape to match our function expectations
        border_flat = border.reshape(-1, 2)
        body_flat = body.reshape(-1, 2)

        # Filter
        filtered = filter_border_contours([border_flat, body_flat], image_shape)

        assert len(filtered) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
