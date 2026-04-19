"""
Tests for Curvature Profiler — Phase 1 Structural Parsing Service

Tests cover:
- Circle-like contour classified as PROFILE_CURVE
- Straight line classified as STRAIGHT_LINE
- Noisy contour classified as NOISE or THIN_STROKE
- Recommended epsilon selection
- Edge cases (insufficient points, collinear points)
"""

import math
import numpy as np
import pytest

from app.services.curvature_profiler import (
    CurvatureClass,
    CurvatureProfile,
    CurvatureProfiler,
    CurvatureAnalysisResult,
    fit_circle_radius,
    compute_contour_curvature_profile,
)


class TestFitCircleRadius:
    """Unit tests for the circle fitting function."""

    def test_equilateral_triangle(self):
        """Equilateral triangle with side 2 has circumradius 2/sqrt(3)."""
        p1 = (0, 0)
        p2 = (2, 0)
        p3 = (1, math.sqrt(3))

        radius = fit_circle_radius(p1, p2, p3)
        expected = 2 / math.sqrt(3)

        assert abs(radius - expected) < 0.01

    def test_right_triangle(self):
        """Right triangle: circumradius = hypotenuse / 2."""
        p1 = (0, 0)
        p2 = (3, 0)
        p3 = (0, 4)

        radius = fit_circle_radius(p1, p2, p3)
        expected = 5 / 2  # hypotenuse = 5

        assert abs(radius - expected) < 0.01

    def test_collinear_points(self):
        """Collinear points should return infinite radius."""
        p1 = (0, 0)
        p2 = (1, 0)
        p3 = (2, 0)

        radius = fit_circle_radius(p1, p2, p3)

        assert radius == float('inf')

    def test_numpy_array_input(self):
        """Should handle numpy array input."""
        p1 = np.array([0, 0])
        p2 = np.array([2, 0])
        p3 = np.array([1, math.sqrt(3)])

        radius = fit_circle_radius(p1, p2, p3)
        expected = 2 / math.sqrt(3)

        assert abs(radius - expected) < 0.01


class TestCurvatureProfiler:
    """Tests for the CurvatureProfiler class."""

    def create_circle_contour(
        self,
        center: tuple = (100, 100),
        radius: float = 50,
        num_points: int = 100,
        use_float: bool = True,
    ) -> np.ndarray:
        """Create a circular contour for testing.

        Args:
            use_float: If True, use float64 to avoid integer quantization artifacts
                       that make consecutive points nearly collinear on small circles.
                       If False, use int32 (matches real OpenCV contour format).
        """
        theta = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        points = np.column_stack([
            center[0] + radius * np.cos(theta),
            center[1] + radius * np.sin(theta)
        ])
        if use_float:
            return points.astype(np.float64).reshape(-1, 1, 2)
        else:
            return points.astype(np.int32).reshape(-1, 1, 2)

    def create_straight_line_contour(
        self,
        start: tuple = (0, 0),
        end: tuple = (200, 0),
        num_points: int = 50,
        use_float: bool = True,
    ) -> np.ndarray:
        """Create a straight line contour for testing."""
        t = np.linspace(0, 1, num_points)
        points = np.column_stack([
            start[0] + t * (end[0] - start[0]),
            start[1] + t * (end[1] - start[1])
        ])
        if use_float:
            return points.astype(np.float64).reshape(-1, 1, 2)
        else:
            return points.astype(np.int32).reshape(-1, 1, 2)

    def create_noisy_circle_contour(
        self,
        center: tuple = (100, 100),
        radius: float = 50,
        num_points: int = 100,
        noise_std: float = 10,
        use_float: bool = True,
    ) -> np.ndarray:
        """Create a noisy circular contour for testing."""
        np.random.seed(42)  # Reproducible
        theta = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        points = np.column_stack([
            center[0] + radius * np.cos(theta) + np.random.normal(0, noise_std, num_points),
            center[1] + radius * np.sin(theta) + np.random.normal(0, noise_std, num_points)
        ])
        if use_float:
            return points.astype(np.float64).reshape(-1, 1, 2)
        else:
            return points.astype(np.int32).reshape(-1, 1, 2)

    def test_circle_classified_as_profile_curve(self):
        """A clean circle should be classified as PROFILE_CURVE."""
        contour = self.create_circle_contour(radius=50)
        mm_per_px = 1.0  # 1mm per pixel for easy calculation

        profile = compute_contour_curvature_profile(contour, mm_per_px)

        assert profile.classification == CurvatureClass.PROFILE_CURVE
        assert profile.radius_stability < 0.5
        # Mean radius should be close to 50mm (50px * 1mm/px)
        assert abs(profile.mean_radius_mm - 50) < 10

    def test_straight_line_classified_correctly(self):
        """A straight line should be classified as STRAIGHT_LINE."""
        contour = self.create_straight_line_contour()
        mm_per_px = 1.0

        profile = compute_contour_curvature_profile(contour, mm_per_px)

        assert profile.classification == CurvatureClass.STRAIGHT_LINE
        assert profile.mean_radius_mm > 5000 or len(profile.local_radii_mm) == 0

    def test_noisy_contour_not_profile_curve(self):
        """A noisy contour should NOT be classified as PROFILE_CURVE."""
        contour = self.create_noisy_circle_contour(noise_std=15)
        mm_per_px = 1.0

        profile = compute_contour_curvature_profile(contour, mm_per_px)

        # Should be THIN_STROKE, NOISE, or ANNOTATION - not PROFILE_CURVE
        assert profile.classification != CurvatureClass.PROFILE_CURVE
        assert profile.radius_stability > 0.5

    def test_recommended_epsilon_varies_by_class(self):
        """Different classifications should have different epsilon recommendations."""
        profiler = CurvatureProfiler()

        circle = self.create_circle_contour(radius=50)
        line = self.create_straight_line_contour()
        noisy = self.create_noisy_circle_contour(noise_std=20)

        profile_circle = profiler._compute_profile(circle, 0, 1.0)
        profile_line = profiler._compute_profile(line, 1, 1.0)
        profile_noisy = profiler._compute_profile(noisy, 2, 1.0)

        # Profile curve should have lowest epsilon (preserve detail)
        # Straight line should have high epsilon
        # These should differ
        assert profile_circle.recommended_epsilon_factor < profile_line.recommended_epsilon_factor
        assert profile_circle.recommended_epsilon_factor <= 0.001

    def test_insufficient_points_returns_unknown(self):
        """Contours with too few points should return UNKNOWN."""
        # Only 3 points - less than minimum
        contour = np.array([[[0, 0]], [[10, 0]], [[5, 10]]], dtype=np.int32)
        mm_per_px = 1.0

        profiler = CurvatureProfiler(min_points_for_analysis=10)
        profile = profiler._compute_profile(contour, 0, mm_per_px)

        assert profile.classification == CurvatureClass.UNKNOWN

    def test_short_arc_returns_micro_fragment(self):
        """Contours with arc length < 8mm should return MICRO_FRAGMENT."""
        # Create a small contour: 10 points in a 5mm arc (at 1mm/px)
        # Arc length = perimeter of small shape
        theta = np.linspace(0, np.pi / 4, 10)  # 45 degree arc
        radius_px = 5  # 5px radius at 1mm/px = 5mm
        points = np.column_stack([
            50 + radius_px * np.cos(theta),
            50 + radius_px * np.sin(theta)
        ]).astype(np.int32).reshape(-1, 1, 2)

        mm_per_px = 1.0  # 1mm per pixel
        # Arc length ~ radius * angle = 5 * (pi/4) ~ 3.9mm < 8mm threshold

        profiler = CurvatureProfiler()
        profile = profiler._compute_profile(points, 0, mm_per_px)

        assert profile.classification == CurvatureClass.MICRO_FRAGMENT
        assert profile.recommended_epsilon_factor == 0.0  # No simplification

    def test_micro_fragment_epsilon_zero(self):
        """MICRO_FRAGMENT should have epsilon=0 to preserve all points."""
        # Create short contour
        contour = np.array([
            [[0, 0]], [[2, 0]], [[4, 1]], [[6, 0]], [[8, 0]]
        ], dtype=np.int32)
        mm_per_px = 0.5  # 0.5mm/px -> arc length ~ 4mm < 8mm

        profiler = CurvatureProfiler()
        profile = profiler._compute_profile(contour, 0, mm_per_px)

        if profile.classification == CurvatureClass.MICRO_FRAGMENT:
            assert profile.recommended_epsilon_factor == 0.0

    def test_analyze_multiple_contours(self):
        """analyze_contours should process multiple contours correctly."""
        contours = [
            self.create_circle_contour(radius=50),
            self.create_straight_line_contour(),
            self.create_noisy_circle_contour(noise_std=15),
        ]
        mm_per_px = 1.0

        profiler = CurvatureProfiler()
        result = profiler.analyze_contours(contours, mm_per_px, (200, 200))

        assert len(result.profiles) == 3
        assert 0 in result.profiles
        assert 1 in result.profiles
        assert 2 in result.profiles

        # Check class distribution makes sense
        counts = result.get_class_counts()
        assert counts["profile_curve"] >= 1  # The circle
        assert counts["straight_line"] >= 1  # The line

    def test_custom_contour_ids(self):
        """Should use custom contour IDs when provided."""
        contours = [
            self.create_circle_contour(radius=50),
            self.create_straight_line_contour(),
        ]
        custom_ids = [100, 200]
        mm_per_px = 1.0

        profiler = CurvatureProfiler()
        result = profiler.analyze_contours(
            contours, mm_per_px, (200, 200), contour_ids=custom_ids
        )

        assert 100 in result.profiles
        assert 200 in result.profiles
        assert 0 not in result.profiles
        assert 1 not in result.profiles

    def test_mm_per_px_scaling(self):
        """Radius should scale with mm_per_px."""
        contour = self.create_circle_contour(radius=50)

        profile_1mm = compute_contour_curvature_profile(contour, mm_per_px=1.0)
        profile_05mm = compute_contour_curvature_profile(contour, mm_per_px=0.5)

        # At 0.5 mm/px, radius should be half
        assert abs(profile_05mm.mean_radius_mm - profile_1mm.mean_radius_mm / 2) < 5

    def test_resampling_improves_stability(self):
        """Resampling should produce consistent point spacing."""
        profiler = CurvatureProfiler()

        # Create unevenly spaced points
        theta = np.array([0, 0.1, 0.15, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0])
        radius = 50
        points = np.column_stack([
            100 + radius * np.cos(theta),
            100 + radius * np.sin(theta)
        ])

        resampled = profiler._resample_contour(points, target_points=20)

        # Should have target number of points
        assert len(resampled) == 20

        # Points should be more evenly spaced after resampling
        diffs = np.diff(resampled, axis=0)
        distances = np.sqrt(np.sum(diffs ** 2, axis=1))

        # Standard deviation of distances should be low
        assert np.std(distances) < np.mean(distances) * 0.5


class TestCurvatureAnalysisResult:
    """Tests for CurvatureAnalysisResult methods."""

    def test_summary(self):
        """summary() should return a dict with expected keys."""
        result = CurvatureAnalysisResult(
            profiles={
                0: CurvatureProfile(
                    contour_id=0,
                    local_radii_mm=[50],
                    radius_stability=0.1,
                    mean_radius_mm=50,
                    min_radius_mm=45,
                    max_radius_mm=55,
                    classification=CurvatureClass.PROFILE_CURVE,
                    confidence=0.85,
                    recommended_epsilon_factor=0.0005,
                ),
            },
            profile_curves=[0],
            profile_fragments=[],
            micro_fragments=[],
            thin_strokes=[],
            annotations=[],
            straight_lines=[],
            noise=[],
            unknown=[],
        )

        summary = result.summary()

        assert "total_profiled" in summary
        assert "class_counts" in summary
        assert summary["total_profiled"] == 1
        assert summary["class_counts"]["profile_curve"] == 1

    def test_get_recommended_epsilon_default(self):
        """get_recommended_epsilon should return default for unknown contours."""
        result = CurvatureAnalysisResult(
            profiles={},
            profile_curves=[],
            profile_fragments=[],
            micro_fragments=[],
            thin_strokes=[],
            annotations=[],
            straight_lines=[],
            noise=[],
            unknown=[],
        )

        epsilon = result.get_recommended_epsilon(999, default=0.001)

        assert epsilon == 0.001


class TestCurvatureProfile:
    """Tests for CurvatureProfile methods."""

    def test_is_stable_curve(self):
        """is_stable_curve should use stability threshold."""
        stable = CurvatureProfile(
            contour_id=0,
            local_radii_mm=[50, 51, 49],
            radius_stability=0.3,
            mean_radius_mm=50,
            min_radius_mm=49,
            max_radius_mm=51,
            classification=CurvatureClass.PROFILE_CURVE,
            confidence=0.8,
            recommended_epsilon_factor=0.0005,
        )

        unstable = CurvatureProfile(
            contour_id=1,
            local_radii_mm=[10, 100, 50],
            radius_stability=1.5,
            mean_radius_mm=50,
            min_radius_mm=10,
            max_radius_mm=100,
            classification=CurvatureClass.NOISE,
            confidence=0.5,
            recommended_epsilon_factor=0.01,
        )

        assert stable.is_stable_curve() is True
        assert unstable.is_stable_curve() is False

    def test_is_plausible_body_curve(self):
        """is_plausible_body_curve should check stability AND radius range."""
        # Stable and in range
        good = CurvatureProfile(
            contour_id=0,
            local_radii_mm=[100, 105, 95],
            radius_stability=0.3,
            mean_radius_mm=100,
            min_radius_mm=95,
            max_radius_mm=105,
            classification=CurvatureClass.PROFILE_CURVE,
            confidence=0.8,
            recommended_epsilon_factor=0.0005,
        )

        # Stable but radius too small
        too_small = CurvatureProfile(
            contour_id=1,
            local_radii_mm=[10, 11, 9],
            radius_stability=0.3,
            mean_radius_mm=10,
            min_radius_mm=9,
            max_radius_mm=11,
            classification=CurvatureClass.PROFILE_CURVE,
            confidence=0.8,
            recommended_epsilon_factor=0.0005,
        )

        # Radius in range but unstable
        unstable = CurvatureProfile(
            contour_id=2,
            local_radii_mm=[100, 200, 50],
            radius_stability=0.8,
            mean_radius_mm=100,
            min_radius_mm=50,
            max_radius_mm=200,
            classification=CurvatureClass.THIN_STROKE,
            confidence=0.6,
            recommended_epsilon_factor=0.00075,
        )

        assert good.is_plausible_body_curve() is True
        assert too_small.is_plausible_body_curve() is False
        assert unstable.is_plausible_body_curve() is False
