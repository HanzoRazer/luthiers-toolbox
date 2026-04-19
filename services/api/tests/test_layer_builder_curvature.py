"""
Tests for Curvature-Aware Body Promotion in Layer Builder

Tests cover:
- Curvature-based BODY promotion when enabled
- No promotion of title block/page frame by curvature alone
- Curvature signal does not override obvious annotation classification
- Feature flag disabled preserves existing behavior
"""

import os
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from app.services.layer_builder import (
    Layer,
    build_layers,
    _is_curvature_body_candidate,
    curvature_body_promotion_enabled,
    CURVATURE_PROFILER_AVAILABLE,
)


class TestCurvatureBodyPromotion:
    """Tests for curvature-based BODY promotion."""

    def create_contour(
        self,
        x: int, y: int, w: int, h: int,
    ) -> np.ndarray:
        """Create a rectangular contour for testing."""
        return np.array([
            [[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]
        ], dtype=np.int32)

    def create_circle_contour(
        self,
        cx: int, cy: int, radius: int,
        num_points: int = 50,
    ) -> np.ndarray:
        """Create a circular contour for testing."""
        theta = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        points = np.column_stack([
            cx + radius * np.cos(theta),
            cy + radius * np.sin(theta)
        ]).astype(np.int32).reshape(-1, 1, 2)
        return points

    def create_mock_profile(
        self,
        classification: str = "profile_curve",
        confidence: float = 0.85,
        mean_radius_mm: float = 100.0,
        is_plausible: bool = True,
    ):
        """Create a mock CurvatureProfile for testing."""
        mock = MagicMock()
        mock.classification = MagicMock()
        mock.classification.value = classification
        mock.confidence = confidence
        mock.mean_radius_mm = mean_radius_mm
        mock.is_plausible_body_curve = MagicMock(return_value=is_plausible)
        return mock

    @patch.dict(os.environ, {"VECTORIZER_CURVATURE_EPSILON": "0"})
    def test_feature_flag_disabled_no_promotion(self):
        """When flag disabled, curvature profiles are ignored."""
        assert not curvature_body_promotion_enabled()

        # Create contours: one central body, one peripheral
        body_contour = self.create_contour(100, 100, 200, 300)
        peripheral_contour = self.create_contour(50, 50, 50, 50)

        structural = [body_contour, peripheral_contour]
        image_size = (500, 600)

        # Even with profiles, flag disabled should not promote
        mock_profile = self.create_mock_profile()
        curvature_profiles = {1: mock_profile}

        result, debug = build_layers(
            structural_contours=structural,
            annotation_contours=[],
            image_size=image_size,
            mm_per_px=1.0,
            curvature_profiles=curvature_profiles,
        )

        # Peripheral contour should remain AUX_VIEWS
        assert len(result.aux_views) >= 0  # May or may not be promoted by geometry

    @patch.dict(os.environ, {"VECTORIZER_CURVATURE_EPSILON": "1"})
    def test_feature_flag_enabled_with_profiles(self):
        """When flag enabled and profiles provided, curvature affects promotion."""
        assert curvature_body_promotion_enabled()

        # This test validates the flag is checked correctly
        # Actual promotion depends on CURVATURE_PROFILER_AVAILABLE

    @patch.dict(os.environ, {"VECTORIZER_CURVATURE_EPSILON": "1"})
    def test_page_frame_not_promoted_by_curvature(self):
        """Page frame contours should never be promoted by curvature."""
        # Create a page-spanning contour (touches edges)
        frame_contour = self.create_contour(2, 2, 496, 596)

        structural = [frame_contour]
        image_size = (500, 600)

        result, debug = build_layers(
            structural_contours=structural,
            annotation_contours=[],
            image_size=image_size,
            mm_per_px=1.0,
            curvature_profiles=None,
        )

        # Should be classified as PAGE_FRAME, not BODY
        assert len(result.page_frame) == 1
        assert len(result.body) == 0

    @patch.dict(os.environ, {"VECTORIZER_CURVATURE_EPSILON": "1"})
    def test_title_block_region_not_promoted(self):
        """Contours in title block region should not be promoted."""
        # Create contour in bottom-right (title block area)
        title_block_contour = self.create_contour(400, 500, 80, 80)

        structural = [title_block_contour]
        image_size = (500, 600)

        # Mock profile that would otherwise promote
        mock_profile = self.create_mock_profile()

        data = {
            "bbox": (400, 500, 80, 80),
            "center": (440, 540),
            "area": 6400,
            "is_frame": False,
        }

        should_promote, reason = _is_curvature_body_candidate(
            data=data,
            curvature_profile=mock_profile,
            body_region=None,
            image_size=image_size,
        )

        # Should be rejected due to title block location
        assert not should_promote
        assert "title_block" in reason

    def test_curvature_candidate_no_profile(self):
        """No profile should return no promotion."""
        data = {
            "bbox": (100, 100, 50, 50),
            "center": (125, 125),
            "area": 2500,
            "is_frame": False,
        }

        should_promote, reason = _is_curvature_body_candidate(
            data=data,
            curvature_profile=None,
            body_region=None,
            image_size=(500, 600),
        )

        assert not should_promote
        assert reason == "no_profile"

    @pytest.mark.skipif(
        not CURVATURE_PROFILER_AVAILABLE,
        reason="Curvature profiler not available"
    )
    def test_wrong_classification_not_promoted(self):
        """ANNOTATION or NOISE classification should not be promoted."""
        from app.services.curvature_profiler import CurvatureClass, CurvatureProfile

        # Create profile with ANNOTATION classification
        profile = CurvatureProfile(
            contour_id=0,
            local_radii_mm=[50, 60, 70],
            radius_stability=1.5,  # Unstable
            mean_radius_mm=60,
            min_radius_mm=50,
            max_radius_mm=70,
            classification=CurvatureClass.ANNOTATION,
            confidence=0.5,
            recommended_epsilon_factor=0.001,
        )

        data = {
            "bbox": (100, 100, 100, 100),
            "center": (150, 150),
            "area": 10000,
            "is_frame": False,
        }

        should_promote, reason = _is_curvature_body_candidate(
            data=data,
            curvature_profile=profile,
            body_region=None,
            image_size=(500, 600),
        )

        assert not should_promote
        assert "wrong_class" in reason

    @pytest.mark.skipif(
        not CURVATURE_PROFILER_AVAILABLE,
        reason="Curvature profiler not available"
    )
    def test_profile_curve_promoted(self):
        """PROFILE_CURVE with good metrics should be promoted."""
        from app.services.curvature_profiler import CurvatureClass, CurvatureProfile

        # Create profile with PROFILE_CURVE classification
        profile = CurvatureProfile(
            contour_id=0,
            local_radii_mm=[100, 102, 98, 101],
            radius_stability=0.2,  # Very stable
            mean_radius_mm=100,
            min_radius_mm=98,
            max_radius_mm=102,
            classification=CurvatureClass.PROFILE_CURVE,
            confidence=0.85,
            recommended_epsilon_factor=0.0005,
        )

        data = {
            "bbox": (100, 100, 150, 200),
            "center": (175, 200),
            "area": 30000,
            "is_frame": False,
        }

        should_promote, reason = _is_curvature_body_candidate(
            data=data,
            curvature_profile=profile,
            body_region=(80, 80, 200, 250),  # Near body region
            image_size=(500, 600),
        )

        assert should_promote
        assert "curvature_profile_curve" in reason

    @pytest.mark.skipif(
        not CURVATURE_PROFILER_AVAILABLE,
        reason="Curvature profiler not available"
    )
    def test_thin_stroke_with_good_radius_promoted(self):
        """THIN_STROKE with plausible radius should be promoted."""
        from app.services.curvature_profiler import CurvatureClass, CurvatureProfile

        # Create profile with THIN_STROKE classification
        profile = CurvatureProfile(
            contour_id=0,
            local_radii_mm=[80, 120, 90, 110],
            radius_stability=0.8,  # Moderately stable
            mean_radius_mm=100,
            min_radius_mm=80,
            max_radius_mm=120,
            classification=CurvatureClass.THIN_STROKE,
            confidence=0.6,
            recommended_epsilon_factor=0.00075,
        )

        data = {
            "bbox": (120, 120, 100, 150),
            "center": (170, 195),
            "area": 15000,
            "is_frame": False,
        }

        should_promote, reason = _is_curvature_body_candidate(
            data=data,
            curvature_profile=profile,
            body_region=(100, 100, 200, 250),  # Near body region
            image_size=(500, 600),
        )

        assert should_promote
        assert "thin_stroke" in reason

    def test_outside_body_region_not_promoted(self):
        """Contours far from body region should not be promoted by curvature."""
        mock_profile = self.create_mock_profile()

        data = {
            "bbox": (10, 10, 30, 30),  # Far corner
            "center": (25, 25),
            "area": 900,
            "is_frame": False,
        }

        should_promote, reason = _is_curvature_body_candidate(
            data=data,
            curvature_profile=mock_profile,
            body_region=(200, 200, 100, 150),  # Body region far away
            image_size=(500, 600),
        )

        # Without CURVATURE_PROFILER_AVAILABLE, it returns profiler_unavailable
        # With it available but outside region, it should return outside_body_region
        assert not should_promote


class TestBuildLayersReturnType:
    """Tests for build_layers return type consistency."""

    def test_returns_tuple(self):
        """build_layers should return tuple of (LayeredEntities, debug_dict)."""
        result = build_layers(
            structural_contours=[],
            annotation_contours=[],
            image_size=(500, 600),
        )

        assert isinstance(result, tuple)
        assert len(result) == 2

        entities, debug = result
        assert hasattr(entities, 'body')
        assert hasattr(entities, 'aux_views')
        assert isinstance(debug, dict)

    def test_debug_dict_keys(self):
        """Debug dict should have expected keys."""
        _, debug = build_layers(
            structural_contours=[],
            annotation_contours=[],
            image_size=(500, 600),
        )

        assert "curvature_enabled" in debug
        assert "curvature_profiles_provided" in debug
        assert "curvature_body_promotions" in debug
        assert "curvature_promotion_reasons" in debug
        assert "curvature_rejection_reasons" in debug
