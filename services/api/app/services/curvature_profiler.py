"""
Curvature Profiler — Phase 1 Structural Parsing Service
========================================================

Analyzes contour curvature stability to classify contours BEFORE simplification.

This service answers:
- Is this contour a smooth profile curve (body, neck, bout)?
- Is this contour a thin, potentially fragmented stroke?
- Is this contour annotation text or dimension lines?
- What epsilon should be used for simplification?

Integration point: Called during Phase 1 (structural parsing) after contour
extraction but before simplification and layer classification.

Feature flag: VECTORIZER_CURVATURE_EPSILON=1

Author: Production Shop
Date: 2026-04-14
"""

from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# Import profile for instrument-specific thresholds
try:
    from ..instrument_geometry.curvature_correction import (
        InstrumentCurvatureProfile,
        get_instrument_profile,
        ZONE_DEFAULT,
    )
    PROFILE_AVAILABLE = True
except ImportError:
    PROFILE_AVAILABLE = False
    InstrumentCurvatureProfile = None
    get_instrument_profile = None
    ZONE_DEFAULT = "default"

logger = logging.getLogger(__name__)


# Feature flag
def curvature_epsilon_enabled() -> bool:
    """Check if curvature-based epsilon is enabled."""
    return os.environ.get("VECTORIZER_CURVATURE_EPSILON", "0") == "1"


class CurvatureClass(str, Enum):
    """Semantic class of contour based on curvature analysis."""
    PROFILE_CURVE = "profile_curve"      # Smooth body/bout curves
    PROFILE_CURVE_FRAGMENT = "profile_curve_fragment"  # Short fragment of profile curve
    THIN_STROKE = "thin_stroke"          # Fragmented thin strokes
    ANNOTATION = "annotation"            # Text, dimension lines
    STRAIGHT_LINE = "straight_line"      # Ruler, grid lines
    NOISE = "noise"                      # Small irregular fragments
    MICRO_FRAGMENT = "micro_fragment"    # <8mm, needs spatial promotion in layer_builder
    UNKNOWN = "unknown"


@dataclass
class CurvatureProfile:
    """Per-contour curvature analysis result."""
    contour_id: int
    local_radii_mm: List[float]
    radius_stability: float               # std(radii) / mean(radii), lower = more stable
    mean_radius_mm: float
    min_radius_mm: float
    max_radius_mm: float
    classification: CurvatureClass
    confidence: float                     # 0.0-1.0
    recommended_epsilon_factor: float     # For approxPolyDP
    notes: List[str] = field(default_factory=list)

    def is_stable_curve(self, stability_threshold: float = 0.5) -> bool:
        """True if curvature is stable enough to be a smooth profile."""
        return self.radius_stability < stability_threshold

    def is_plausible_body_curve(
        self,
        min_radius: float = 30.0,
        max_radius: float = 800.0,
    ) -> bool:
        """True if radius range matches typical guitar body curves."""
        return (
            self.is_stable_curve() and
            min_radius <= self.mean_radius_mm <= max_radius
        )


@dataclass
class CurvatureAnalysisResult:
    """Aggregate result from profiling all contours."""
    profiles: Dict[int, CurvatureProfile]
    profile_curves: List[int]            # Contour IDs classified as PROFILE_CURVE
    profile_fragments: List[int]         # Contour IDs classified as PROFILE_CURVE_FRAGMENT
    micro_fragments: List[int]           # Contour IDs classified as MICRO_FRAGMENT (<8mm)
    thin_strokes: List[int]              # Contour IDs classified as THIN_STROKE
    annotations: List[int]               # Contour IDs classified as ANNOTATION
    straight_lines: List[int]            # Contour IDs classified as STRAIGHT_LINE
    noise: List[int]                     # Contour IDs classified as NOISE
    unknown: List[int]                   # Contour IDs classified as UNKNOWN

    def get_profile_confidence(self, contour_id: int) -> float:
        """Get confidence that a contour is a profile curve."""
        profile = self.profiles.get(contour_id)
        return profile.confidence if profile else 0.0

    def get_recommended_epsilon(self, contour_id: int, default: float = 0.001) -> float:
        """Get recommended epsilon factor for simplification."""
        profile = self.profiles.get(contour_id)
        return profile.recommended_epsilon_factor if profile else default

    def get_class_counts(self) -> Dict[str, int]:
        """Get counts by classification."""
        return {
            "profile_curve": len(self.profile_curves),
            "profile_fragment": len(self.profile_fragments),
            "micro_fragment": len(self.micro_fragments),
            "thin_stroke": len(self.thin_strokes),
            "annotation": len(self.annotations),
            "straight_line": len(self.straight_lines),
            "noise": len(self.noise),
            "unknown": len(self.unknown),
        }

    def summary(self) -> Dict:
        """Summary dict for debug payload."""
        return {
            "total_profiled": len(self.profiles),
            "class_counts": self.get_class_counts(),
            "profile_curve_ids": self.profile_curves[:10],  # First 10 for debug
            "thin_stroke_ids": self.thin_strokes[:10],
        }


class CurvatureProfiler:
    """
    Phase 1 service: Analyze contour curvature for classification and optimization.

    This service should be called during structural parsing, after contour
    extraction but before simplification and layer classification.

    Usage:
        profiler = CurvatureProfiler()
        result = profiler.analyze_contours(contours, mm_per_px, image_shape)

        for contour_id, profile in result.profiles.items():
            if profile.is_plausible_body_curve():
                epsilon = profile.recommended_epsilon_factor * perimeter
                simplified = cv2.approxPolyDP(contour, epsilon, closed=True)

    With instrument profile (Commit 2):
        from body_curvature_correction import get_instrument_profile
        profile = get_instrument_profile("gibson_explorer")
        profiler = CurvatureProfiler(instrument_profile=profile)
        # Uses Explorer-specific stability thresholds and epsilon values
    """

    # Fallback classification thresholds (used when no profile provided)
    _DEFAULT_STABILITY_PROFILE = 0.5      # Below this = stable curve
    _DEFAULT_STABILITY_THIN = 1.0         # Between 0.5-1.0 = thin stroke
    _DEFAULT_MIN_RADIUS_MM = 30.0         # Smallest plausible body curve (mm)
    _DEFAULT_MAX_RADIUS_MM = 800.0        # Largest plausible body curve (mm)

    # Fallback epsilon factors (used when no profile provided)
    _DEFAULT_EPSILON_PROFILE = 0.0005     # Smooth curves: preserve detail
    _DEFAULT_EPSILON_THIN = 0.00075       # Thin strokes: moderate simplification
    _DEFAULT_EPSILON_ANNOTATION = 0.001   # Text/lines: standard simplification
    _DEFAULT_EPSILON_STRAIGHT = 0.002     # Straight lines: aggressive
    _DEFAULT_EPSILON_NOISE = 0.01         # Noise: extreme simplification

    def __init__(
        self,
        window_size: int = 5,
        min_points_for_analysis: int = 10,
        min_area_px: float = 100,
        resample_target: int = 200,
        instrument_profile: Optional["InstrumentCurvatureProfile"] = None,
        spec_name: Optional[str] = None,
    ):
        """
        Args:
            window_size: Number of points for local curvature calculation
            min_points_for_analysis: Minimum contour points to analyze
            min_area_px: Skip contours smaller than this
            resample_target: Target point count after resampling
            instrument_profile: Pre-built InstrumentCurvatureProfile (takes precedence)
            spec_name: Instrument spec name to load profile for (if profile not provided)
        """
        self.window_size = window_size
        self.min_points = min_points_for_analysis
        self.min_area_px = min_area_px
        self.resample_target = resample_target

        # Load or use provided instrument profile
        if instrument_profile is not None:
            self.profile = instrument_profile
        elif spec_name is not None and PROFILE_AVAILABLE and get_instrument_profile:
            self.profile = get_instrument_profile(spec_name)
        else:
            self.profile = None

        # Resolve thresholds from profile or defaults
        if self.profile is not None:
            self._stability_threshold_profile = self.profile.stability_threshold
            self._min_profile_radius_mm = self.profile.min_profile_radius_mm
            self._max_profile_radius_mm = self.profile.max_profile_radius_mm
            self._epsilon_profile_curve = self.profile.epsilon_profile_curve
            self._epsilon_thin_stroke = self.profile.epsilon_thin_stroke
            self._epsilon_annotation = self.profile.epsilon_annotation
            self._epsilon_straight_line = self.profile.epsilon_straight_line
            self._epsilon_noise = self.profile.epsilon_noise
        else:
            self._stability_threshold_profile = self._DEFAULT_STABILITY_PROFILE
            self._min_profile_radius_mm = self._DEFAULT_MIN_RADIUS_MM
            self._max_profile_radius_mm = self._DEFAULT_MAX_RADIUS_MM
            self._epsilon_profile_curve = self._DEFAULT_EPSILON_PROFILE
            self._epsilon_thin_stroke = self._DEFAULT_EPSILON_THIN
            self._epsilon_annotation = self._DEFAULT_EPSILON_ANNOTATION
            self._epsilon_straight_line = self._DEFAULT_EPSILON_STRAIGHT
            self._epsilon_noise = self._DEFAULT_EPSILON_NOISE

        # Thin stroke threshold (not currently zone-specific)
        self._stability_threshold_thin = self._DEFAULT_STABILITY_THIN

    def analyze_contours(
        self,
        contours: List[np.ndarray],
        mm_per_px: float,
        image_shape: Tuple[int, int],
        contour_ids: Optional[List[int]] = None,
    ) -> CurvatureAnalysisResult:
        """
        Analyze all contours and return curvature profiles.

        Args:
            contours: List of OpenCV contours
            mm_per_px: Conversion factor from pixels to mm
            image_shape: (height, width) of source image
            contour_ids: Optional IDs for each contour (defaults to indices)

        Returns:
            CurvatureAnalysisResult with profiles and classifications
        """
        if contour_ids is None:
            contour_ids = list(range(len(contours)))

        profiles: Dict[int, CurvatureProfile] = {}
        profile_curves: List[int] = []
        profile_fragments: List[int] = []
        micro_fragments: List[int] = []
        thin_strokes: List[int] = []
        annotations: List[int] = []
        straight_lines: List[int] = []
        noise_ids: List[int] = []
        unknown_ids: List[int] = []

        for contour, cid in zip(contours, contour_ids):
            if len(contour) < self.min_points:
                continue

            # cv2.contourArea requires int32, but we may have float64 for testing
            # Note: Lines have area=0 and small arcs have tiny areas - these are
            # legitimate geometry, so we check arc length instead of area for
            # contours with near-zero area (could be lines or open curves)
            contour_for_area = contour
            if contour.dtype != np.int32:
                contour_for_area = contour.astype(np.int32)
            area = cv2.contourArea(contour_for_area)

            # For near-zero area (lines, thin curves), check arc length instead
            # Note: _compute_profile handles short arcs via the MICRO_FRAGMENT gate,
            # so we only skip truly degenerate contours here
            if area < self.min_area_px:
                arc_length = cv2.arcLength(contour_for_area, closed=False)
                # Skip only if BOTH area and arc length are negligible
                if arc_length < 3:  # Less than 3px = degenerate
                    continue

            profile = self._compute_profile(contour, cid, mm_per_px)
            profiles[cid] = profile

            # Classify based on curvature stability and radius range
            if profile.classification == CurvatureClass.PROFILE_CURVE:
                profile_curves.append(cid)
            elif profile.classification == CurvatureClass.PROFILE_CURVE_FRAGMENT:
                profile_fragments.append(cid)
            elif profile.classification == CurvatureClass.MICRO_FRAGMENT:
                micro_fragments.append(cid)
            elif profile.classification == CurvatureClass.THIN_STROKE:
                thin_strokes.append(cid)
            elif profile.classification == CurvatureClass.ANNOTATION:
                annotations.append(cid)
            elif profile.classification == CurvatureClass.STRAIGHT_LINE:
                straight_lines.append(cid)
            elif profile.classification == CurvatureClass.NOISE:
                noise_ids.append(cid)
            else:
                unknown_ids.append(cid)

        logger.info(
            f"Curvature analysis complete: "
            f"{len(profile_curves)} profile, "
            f"{len(profile_fragments)} profile_frag, "
            f"{len(micro_fragments)} micro_frag, "
            f"{len(thin_strokes)} thin, "
            f"{len(annotations)} annotation, "
            f"{len(straight_lines)} straight, "
            f"{len(noise_ids)} noise"
        )

        return CurvatureAnalysisResult(
            profiles=profiles,
            profile_curves=profile_curves,
            profile_fragments=profile_fragments,
            micro_fragments=micro_fragments,
            thin_strokes=thin_strokes,
            annotations=annotations,
            straight_lines=straight_lines,
            noise=noise_ids,
            unknown=unknown_ids,
        )

    # Minimum arc length thresholds (mm)
    MIN_ARC_LENGTH_FULL_ANALYSIS = 15.0   # Full curvature analysis
    MIN_ARC_LENGTH_FRAGMENT = 8.0          # Below this = MICRO_FRAGMENT

    def _compute_profile(
        self,
        contour: np.ndarray,
        contour_id: int,
        mm_per_px: float,
    ) -> CurvatureProfile:
        """
        Compute curvature profile for a single contour.

        Algorithm:
        0. Compute arc length - short fragments get special handling
        1. Resample contour to ensure consistent point spacing
        2. For each vertex, fit circle through neighboring points
        3. Compute local radius from fitted circle
        4. Calculate stability metric (std/mean of radii)
        5. Classify based on stability and radius range
        """
        points = contour.reshape(-1, 2).astype(np.float64)
        n = len(points)

        if n < self.window_size:
            return self._default_profile(contour_id, "insufficient_points")

        # Stage 0: Compute arc length for length-based pre-classification
        diffs = np.diff(points, axis=0)
        seg_lengths_px = np.sqrt(np.sum(diffs ** 2, axis=1))
        arc_length_px = float(np.sum(seg_lengths_px))
        arc_length_mm = arc_length_px * mm_per_px

        # Short fragment gate: < 8mm gets MICRO_FRAGMENT classification
        # These will be spatially promoted in layer_builder.py if near BODY_CORE
        if arc_length_mm < self.MIN_ARC_LENGTH_FRAGMENT:
            return CurvatureProfile(
                contour_id=contour_id,
                local_radii_mm=[],
                radius_stability=float('inf'),
                mean_radius_mm=0,
                min_radius_mm=0,
                max_radius_mm=0,
                classification=CurvatureClass.MICRO_FRAGMENT,
                confidence=0.0,
                recommended_epsilon_factor=0.0,  # NO simplification - preserve all points
                notes=[f"arc_length={arc_length_mm:.1f}mm < 8mm threshold"],
            )

        # Resample to ensure even spacing
        points = self._resample_contour(
            points,
            target_points=min(n, self.resample_target)
        )
        n = len(points)

        if n < self.window_size:
            return self._default_profile(contour_id, "insufficient_after_resample")

        half_w = self.window_size // 2
        local_radii_mm: List[float] = []
        infinite_count = 0
        total_samples = 0

        for i in range(half_w, n - half_w):
            # Get points for circle fitting
            p1 = points[i - half_w] * mm_per_px
            p2 = points[i] * mm_per_px
            p3 = points[i + half_w] * mm_per_px

            radius = fit_circle_radius(p1, p2, p3)
            total_samples += 1
            if radius < 10000:  # Filter near-infinite (collinear)
                local_radii_mm.append(radius)
            else:
                infinite_count += 1

        # If ALL radii are infinite, this is a straight line
        if len(local_radii_mm) == 0:
            if infinite_count > 0 and infinite_count == total_samples:
                return CurvatureProfile(
                    contour_id=contour_id,
                    local_radii_mm=[],
                    radius_stability=0.0,
                    mean_radius_mm=float('inf'),
                    min_radius_mm=float('inf'),
                    max_radius_mm=float('inf'),
                    classification=CurvatureClass.STRAIGHT_LINE,
                    confidence=0.9,
                    recommended_epsilon_factor=self._epsilon_straight_line,
                    notes=["all points collinear - straight line"],
                )
            return self._default_profile(contour_id, "no_valid_radii")

        radii_array = np.array(local_radii_mm)
        mean_radius = float(np.mean(radii_array))
        std_radius = float(np.std(radii_array))
        stability = std_radius / mean_radius if mean_radius > 0 else float('inf')

        min_radius = float(np.min(radii_array))
        max_radius = float(np.max(radii_array))

        # Classify based on stability and radius range
        classification, confidence, epsilon_factor, notes = self._classify(
            stability, mean_radius, min_radius, max_radius
        )

        return CurvatureProfile(
            contour_id=contour_id,
            local_radii_mm=local_radii_mm,
            radius_stability=stability,
            mean_radius_mm=mean_radius,
            min_radius_mm=min_radius,
            max_radius_mm=max_radius,
            classification=classification,
            confidence=confidence,
            recommended_epsilon_factor=epsilon_factor,
            notes=notes,
        )

    def _classify(
        self,
        stability: float,
        mean_radius: float,
        min_radius: float,
        max_radius: float,
        zone: str = "default",
    ) -> Tuple[CurvatureClass, float, float, List[str]]:
        """
        Classify contour based on curvature metrics.

        Decision tree:
        1. Very stable curvature + radius in body range -> PROFILE_CURVE
        2. Moderately stable -> THIN_STROKE
        3. Unstable + erratic -> NOISE
        4. Very low curvature variation + large radii -> STRAIGHT_LINE
        5. Everything else -> ANNOTATION

        Args:
            zone: Body zone for zone-specific thresholds (waist, bout, horn_tip, etc.)
        """
        notes = []

        # Get zone-specific stability threshold if profile available
        if self.profile is not None:
            stability_threshold = self.profile.get_stability(zone)
        else:
            stability_threshold = self._stability_threshold_profile

        # Check for profile curve (smooth, body-like radii)
        if (stability < stability_threshold and
                self._min_profile_radius_mm <= mean_radius <= self._max_profile_radius_mm):
            confidence = min(
                0.9,
                0.7 + (1 - stability / stability_threshold) * 0.2
            )
            notes.append(f"stable curvature (stability={stability:.3f})")
            notes.append(f"radius {mean_radius:.0f}mm in body range")
            if zone != "default":
                notes.append(f"zone={zone} threshold={stability_threshold:.2f}")
            return (
                CurvatureClass.PROFILE_CURVE,
                confidence,
                self._epsilon_profile_curve,
                notes
            )

        # Check for straight line (very large, consistent radii)
        if mean_radius > 5000 or (max_radius > 0 and (max_radius - min_radius) / max_radius < 0.1):
            confidence = 0.7
            notes.append("very low curvature variation")
            notes.append(f"mean radius {mean_radius:.0f}mm")
            return (
                CurvatureClass.STRAIGHT_LINE,
                confidence,
                self._epsilon_straight_line,
                notes
            )

        # Check for thin stroke (moderately stable)
        if stability < self._stability_threshold_thin:
            confidence = 0.6
            notes.append(f"moderately stable (stability={stability:.3f})")
            notes.append("likely thin stroke")
            return (
                CurvatureClass.THIN_STROKE,
                confidence,
                self._epsilon_thin_stroke,
                notes
            )

        # Check for noise (very unstable)
        if stability > 2.0:
            confidence = 0.5
            notes.append(f"unstable curvature (stability={stability:.3f})")
            notes.append("likely noise")
            return (
                CurvatureClass.NOISE,
                confidence,
                self._epsilon_noise,
                notes
            )

        # Default: annotation
        notes.append(f"default classification (stability={stability:.3f})")
        return (
            CurvatureClass.ANNOTATION,
            0.5,
            self._epsilon_annotation,
            notes
        )

    def _resample_contour(
        self,
        points: np.ndarray,
        target_points: int = 200,
    ) -> np.ndarray:
        """
        Resample contour to have evenly spaced points.

        This improves curvature stability by ensuring consistent
        point spacing along the contour.
        """
        if len(points) < 3:
            return points

        # Calculate cumulative arc length
        diffs = np.diff(points, axis=0)
        seg_lengths = np.sqrt(np.sum(diffs ** 2, axis=1))
        cumulative = np.concatenate([[0], np.cumsum(seg_lengths)])
        total_length = cumulative[-1]

        if total_length < 1e-6:
            return points

        # Generate evenly spaced samples
        target_distances = np.linspace(0, total_length, target_points)

        resampled = []
        idx = 0
        for t in target_distances:
            while idx < len(cumulative) - 1 and cumulative[idx + 1] < t:
                idx += 1

            if idx >= len(cumulative) - 1:
                resampled.append(points[-1])
            else:
                # Linear interpolation
                t0 = cumulative[idx]
                t1 = cumulative[idx + 1]
                if t1 - t0 < 1e-9:
                    resampled.append(points[idx])
                else:
                    alpha = (t - t0) / (t1 - t0)
                    interp = points[idx] * (1 - alpha) + points[idx + 1] * alpha
                    resampled.append(interp)

        return np.array(resampled)

    def _default_profile(self, contour_id: int, reason: str) -> CurvatureProfile:
        """Return default profile for contours that couldn't be analyzed."""
        return CurvatureProfile(
            contour_id=contour_id,
            local_radii_mm=[],
            radius_stability=float('inf'),
            mean_radius_mm=0,
            min_radius_mm=0,
            max_radius_mm=0,
            classification=CurvatureClass.UNKNOWN,
            confidence=0.0,
            recommended_epsilon_factor=self._epsilon_annotation,
            notes=[f"default: {reason}"],
        )


def fit_circle_radius(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
) -> float:
    """
    Fit circle through three points, return radius.

    Uses circumradius formula: R = (a*b*c) / (4*area)

    This is the same mathematics used in radius_profiles.py for
    fretboard and brace calculations, adapted for contour points.
    """
    # Convert to tuples if numpy arrays
    if hasattr(p1, '__len__'):
        p1 = (float(p1[0]), float(p1[1]))
        p2 = (float(p2[0]), float(p2[1]))
        p3 = (float(p3[0]), float(p3[1]))

    # Side lengths
    a = math.hypot(p2[0] - p3[0], p2[1] - p3[1])
    b = math.hypot(p1[0] - p3[0], p1[1] - p3[1])
    c = math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    # Triangle area via cross product
    area = abs(
        (p2[0] - p1[0]) * (p3[1] - p1[1]) -
        (p3[0] - p1[0]) * (p2[1] - p1[1])
    ) / 2.0

    if area < 1e-9:
        return float('inf')  # Collinear points = infinite radius

    return (a * b * c) / (4.0 * area)


def compute_contour_curvature_profile(
    contour: np.ndarray,
    mm_per_px: float,
    contour_id: int = 0,
    window_size: int = 5,
    spec_name: Optional[str] = None,
) -> CurvatureProfile:
    """
    Convenience function to compute curvature profile for a single contour.

    Args:
        contour: OpenCV contour
        mm_per_px: Conversion factor from pixels to mm
        contour_id: Optional ID for the contour
        window_size: Points for local radius calculation
        spec_name: Optional instrument spec name for instrument-specific thresholds

    Returns:
        CurvatureProfile with classification and recommended epsilon
    """
    profiler = CurvatureProfiler(window_size=window_size, spec_name=spec_name)
    return profiler._compute_profile(contour, contour_id, mm_per_px)
