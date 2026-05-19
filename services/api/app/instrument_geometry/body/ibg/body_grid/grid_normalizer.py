"""
Grid Normalizer — Coordinate Normalization for Body Grid
=========================================================

Transforms raw coordinates (pixel or mm) to centerline-relative
normalized coordinates.

Coordinate System:
    y_norm: 0.0 at butt/tail, 1.0 at neck end
    x_norm: signed distance from centerline (negative=bass/left, positive=treble/right)

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .body_grid_schema import (
    BodyEvidence,
    CenterlineDescriptor,
    CoordinateSpace,
    ContourSegment,
    EvidenceSource,
    Landmark,
    NormalizedPoint,
    RawCoordinate,
)


@dataclass
class NormalizationTransform:
    """
    Transform parameters from raw to normalized coordinates.

    Stores all parameters needed to convert between coordinate spaces.
    """
    centerline_x: float         # Centerline X in source coordinates
    body_y_min: float           # Butt Y in source coordinates
    body_y_max: float           # Neck Y in source coordinates
    body_width: float           # Maximum body width (for X normalization)
    source_space: CoordinateSpace
    flip_y: bool = False        # True if source Y increases downward


class GridNormalizer:
    """
    Normalizes body evidence to centerline-relative coordinates.

    Handles coordinate transformation from raw pixel/mm coordinates
    to the normalized Body Grid coordinate system.
    """

    def __init__(self):
        self._transform: Optional[NormalizationTransform] = None

    def normalize_evidence(
        self,
        evidence: BodyEvidence,
        centerline_x: Optional[float] = None
    ) -> Tuple[BodyEvidence, CenterlineDescriptor]:
        """
        Normalize body evidence to centerline-relative coordinates.

        Args:
            evidence: Raw body evidence
            centerline_x: Optional declared centerline X (auto-detect if None)

        Returns:
            Tuple of (normalized BodyEvidence, CenterlineDescriptor)
        """
        # Compute transform parameters
        self._transform = self._compute_transform(evidence, centerline_x)

        # Normalize landmarks
        normalized_landmarks = [
            self._normalize_landmark(lm) for lm in evidence.landmarks
        ]

        # Normalize contour segments
        normalized_segments = [
            self._normalize_segment(seg) for seg in evidence.contour_segments
        ]

        # Normalize outline points
        normalized_outline = [
            self._normalize_point_tuple(pt) for pt in evidence.outline_points
        ]

        # Build centerline descriptor
        centerline = CenterlineDescriptor(
            x_mm=self._transform.centerline_x,
            source="declared" if centerline_x is not None else "detected",
            confidence=0.9 if centerline_x is not None else self._estimate_centerline_confidence(evidence),
            symmetry_score=self._compute_symmetry_score(evidence)
        )

        # Build normalized evidence
        normalized = BodyEvidence(
            outline_points=normalized_outline,
            contour_segments=normalized_segments,
            landmarks=normalized_landmarks,
            source_type=evidence.source_type,
            source_transform={
                "centerline_x": self._transform.centerline_x,
                "y_min": self._transform.body_y_min,
                "y_max": self._transform.body_y_max,
                "width": self._transform.body_width,
            },
            bounding_box_mm=evidence.bounding_box_mm,
            centerline_x_mm=self._transform.centerline_x,
        )

        return normalized, centerline

    def _compute_transform(
        self,
        evidence: BodyEvidence,
        declared_centerline: Optional[float]
    ) -> NormalizationTransform:
        """Compute normalization transform parameters."""

        # Collect all points
        all_points = list(evidence.outline_points)
        for seg in evidence.contour_segments:
            all_points.extend((p.raw.x, p.raw.y) if p.raw else (p.x_norm, p.y_norm) for p in seg.points)
        for lm in evidence.landmarks:
            if lm.point.raw:
                all_points.append((lm.point.raw.x, lm.point.raw.y))

        if not all_points:
            # Default transform for empty evidence
            return NormalizationTransform(
                centerline_x=0.0,
                body_y_min=0.0,
                body_y_max=1.0,
                body_width=1.0,
                source_space=CoordinateSpace.RAW_MM
            )

        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # Determine centerline
        if declared_centerline is not None:
            centerline_x = declared_centerline
        elif evidence.centerline_x_mm is not None:
            centerline_x = evidence.centerline_x_mm
        else:
            # Auto-detect: use midpoint of X range
            centerline_x = (x_min + x_max) / 2

            # Refine using landmarks if available
            butt_lm = evidence.get_landmark("butt_center")
            neck_lm = evidence.get_landmark("neck_center")
            if butt_lm and butt_lm.point.raw:
                centerline_x = butt_lm.point.raw.x
            elif neck_lm and neck_lm.point.raw:
                centerline_x = neck_lm.point.raw.x

        body_width = max(
            abs(x_max - centerline_x),
            abs(x_min - centerline_x)
        ) * 2

        return NormalizationTransform(
            centerline_x=centerline_x,
            body_y_min=y_min,
            body_y_max=y_max,
            body_width=body_width if body_width > 0 else 1.0,
            source_space=CoordinateSpace.RAW_MM
        )

    def _normalize_point_tuple(self, pt: Tuple[float, float]) -> Tuple[float, float]:
        """Normalize a (x, y) tuple to (x_norm, y_norm)."""
        x, y = pt
        t = self._transform

        # Compute normalized coordinates
        x_norm = (x - t.centerline_x) / (t.body_width / 2) if t.body_width > 0 else 0.0
        y_range = t.body_y_max - t.body_y_min
        y_norm = (y - t.body_y_min) / y_range if y_range > 0 else 0.0

        return (x_norm, y_norm)

    def _normalize_landmark(self, lm: Landmark) -> Landmark:
        """Normalize a landmark to centerline-relative coordinates."""
        if lm.point.raw:
            x, y = lm.point.raw.x, lm.point.raw.y
        else:
            # Already normalized or no raw
            return lm

        t = self._transform

        x_norm = (x - t.centerline_x) / (t.body_width / 2) if t.body_width > 0 else 0.0
        y_range = t.body_y_max - t.body_y_min
        y_norm = (y - t.body_y_min) / y_range if y_range > 0 else 0.0

        return Landmark(
            label=lm.label,
            point=NormalizedPoint(
                x_norm=x_norm,
                y_norm=y_norm,
                raw=lm.point.raw,
                confidence=lm.point.confidence
            ),
            source=lm.source,
            confidence=lm.confidence
        )

    def _normalize_segment(self, seg: ContourSegment) -> ContourSegment:
        """Normalize a contour segment to centerline-relative coordinates."""
        normalized_points = []
        t = self._transform

        for pt in seg.points:
            if pt.raw:
                x, y = pt.raw.x, pt.raw.y
            else:
                # Use existing normalized values
                normalized_points.append(pt)
                continue

            x_norm = (x - t.centerline_x) / (t.body_width / 2) if t.body_width > 0 else 0.0
            y_range = t.body_y_max - t.body_y_min
            y_norm = (y - t.body_y_min) / y_range if y_range > 0 else 0.0

            normalized_points.append(NormalizedPoint(
                x_norm=x_norm,
                y_norm=y_norm,
                raw=pt.raw,
                confidence=pt.confidence
            ))

        # Determine side based on average x_norm
        if normalized_points:
            avg_x = sum(p.x_norm for p in normalized_points) / len(normalized_points)
            if avg_x < -0.1:
                side = "left"
            elif avg_x > 0.1:
                side = "right"
            else:
                side = "centerline"
        else:
            side = seg.side

        return ContourSegment(
            points=normalized_points,
            is_closed=seg.is_closed,
            side=side,
            source=seg.source
        )

    def _estimate_centerline_confidence(self, evidence: BodyEvidence) -> float:
        """Estimate confidence in auto-detected centerline."""
        # Higher confidence if we have centerline landmarks
        if evidence.get_landmark("butt_center") or evidence.get_landmark("neck_center"):
            return 0.85

        # Lower confidence for pure bounding box detection
        return 0.6

    def _compute_symmetry_score(self, evidence: BodyEvidence) -> float:
        """
        Compute body symmetry score.

        Returns 1.0 for perfectly symmetric, 0.0 for highly asymmetric.
        """
        if not evidence.outline_points:
            return 0.5  # Unknown

        t = self._transform

        # Sample points at several Y positions
        y_samples = [0.2, 0.35, 0.5, 0.65, 0.8]
        symmetry_errors = []

        for y_target in y_samples:
            y_actual = t.body_y_min + y_target * (t.body_y_max - t.body_y_min)

            # Find points near this Y
            tolerance = (t.body_y_max - t.body_y_min) * 0.05
            nearby = [
                (x, y) for x, y in evidence.outline_points
                if abs(y - y_actual) < tolerance
            ]

            if len(nearby) < 2:
                continue

            xs = [x for x, y in nearby]
            left_extent = t.centerline_x - min(xs)
            right_extent = max(xs) - t.centerline_x

            if left_extent + right_extent > 0:
                error = abs(left_extent - right_extent) / (left_extent + right_extent)
                symmetry_errors.append(error)

        if not symmetry_errors:
            return 0.5

        avg_error = sum(symmetry_errors) / len(symmetry_errors)
        return max(0.0, 1.0 - avg_error * 2)

    def denormalize_point(self, pt: NormalizedPoint) -> Tuple[float, float]:
        """
        Convert normalized point back to source coordinates.

        Useful for overlay generation.
        """
        if self._transform is None:
            return (pt.x_norm, pt.y_norm)

        t = self._transform
        x = pt.x_norm * (t.body_width / 2) + t.centerline_x
        y = pt.y_norm * (t.body_y_max - t.body_y_min) + t.body_y_min

        return (x, y)


def normalize_from_landmarks(
    landmarks: List[Tuple[str, float, float]],
    source: EvidenceSource = EvidenceSource.CONSTRAINT_EXTRACTOR
) -> Tuple[BodyEvidence, CenterlineDescriptor]:
    """
    Convenience function to normalize from constraint_extractor landmarks.

    Args:
        landmarks: List of (label, x_mm, y_mm) tuples
        source: Evidence source type

    Returns:
        Tuple of (normalized BodyEvidence, CenterlineDescriptor)
    """
    evidence = BodyEvidence(source_type=source)

    for label, x, y in landmarks:
        evidence.landmarks.append(Landmark(
            label=label,
            point=NormalizedPoint(
                x_norm=0.0,  # Will be computed
                y_norm=0.0,
                raw=RawCoordinate(x, y, CoordinateSpace.RAW_MM)
            ),
            source=source
        ))

    normalizer = GridNormalizer()
    return normalizer.normalize_evidence(evidence)
