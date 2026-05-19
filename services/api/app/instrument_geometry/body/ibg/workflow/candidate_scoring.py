"""
Candidate Scoring — Body Evidence Candidate Ranking
====================================================

Scores contour candidates for plausibility as instrument body regions.

Scoring signals:
- Vertical body extent
- Horizontal mass distribution
- Waist narrowing evidence
- Upper/lower bout presence
- Centerline balance
- Offset/asymmetry visibility
- Not dominated by text/dimension strokes

DEV ORDER 1A-WORKFLOW: IBG Workflow Pipeline

Author: Production Shop
Date: 2026-05-18
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .topology_recovery import ContourCandidate


@dataclass
class ScoringSignals:
    """
    Individual scoring signals for a candidate.

    All signals normalized to 0.0-1.0 where higher is better.
    """
    vertical_extent: float = 0.0
    horizontal_distribution: float = 0.0
    waist_narrowing: float = 0.0
    bout_presence: float = 0.0
    centerline_balance: float = 0.0
    asymmetry_visibility: float = 0.0
    not_text_stroke: float = 0.0
    closure_quality: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "vertical_extent": self.vertical_extent,
            "horizontal_distribution": self.horizontal_distribution,
            "waist_narrowing": self.waist_narrowing,
            "bout_presence": self.bout_presence,
            "centerline_balance": self.centerline_balance,
            "asymmetry_visibility": self.asymmetry_visibility,
            "not_text_stroke": self.not_text_stroke,
            "closure_quality": self.closure_quality,
        }

    def composite_score(self) -> float:
        """Compute weighted composite score."""
        weights = {
            "vertical_extent": 0.15,
            "horizontal_distribution": 0.10,
            "waist_narrowing": 0.15,
            "bout_presence": 0.15,
            "centerline_balance": 0.10,
            "asymmetry_visibility": 0.05,
            "not_text_stroke": 0.15,
            "closure_quality": 0.15,
        }

        total = 0.0
        for signal, weight in weights.items():
            total += getattr(self, signal) * weight

        return total


@dataclass
class ScoredCandidate:
    """
    A scored body evidence candidate.

    Attributes:
        contour: Original contour candidate
        signals: Individual scoring signals
        rank_score: Composite ranking score (0.0-1.0)
        rejection_flags: List of rejection reasons
        rank: Position in ranking (1 = best)
    """
    contour: ContourCandidate
    signals: ScoringSignals
    rank_score: float
    rejection_flags: List[str] = field(default_factory=list)
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contour_id": self.contour.contour_id,
            "rank": self.rank,
            "rank_score": self.rank_score,
            "signals": self.signals.to_dict(),
            "rejection_flags": self.rejection_flags,
            "contour": self.contour.to_dict(),
        }


@dataclass
class ScoringResult:
    """
    Result of candidate scoring.

    Attributes:
        candidates: Scored candidates sorted by rank
        top_n: Number of top candidates returned
        total_evaluated: Total candidates evaluated
    """
    candidates: List[ScoredCandidate] = field(default_factory=list)
    top_n: int = 5
    total_evaluated: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "top_n": self.top_n,
            "total_evaluated": self.total_evaluated,
            "candidates": [c.to_dict() for c in self.candidates],
        }


def score_candidates(
    contours: List[ContourCandidate],
    top_n: int = 5,
    min_area_mm2: float = 1000.0,
    max_area_mm2: float = 500000.0,
    min_aspect_ratio: float = 0.5,
    max_aspect_ratio: float = 3.0,
) -> ScoringResult:
    """
    Score and rank contour candidates for body evidence.

    Args:
        contours: List of contour candidates
        top_n: Number of top candidates to return
        min_area_mm2: Minimum area for valid body
        max_area_mm2: Maximum area for valid body
        min_aspect_ratio: Minimum height/width ratio
        max_aspect_ratio: Maximum height/width ratio

    Returns:
        ScoringResult with ranked candidates
    """
    scored = []

    for contour in contours:
        signals = ScoringSignals()
        rejection_flags = []

        # Skip if not enough points
        if len(contour.points) < 10:
            rejection_flags.append("too_few_points")
            signals.not_text_stroke = 0.0
        else:
            signals.not_text_stroke = min(1.0, len(contour.points) / 50.0)

        # Compute dimensions
        min_x, min_y, max_x, max_y = contour.bounding_box
        width = max_x - min_x
        height = max_y - min_y

        # Vertical extent score
        if height > 0:
            # Prefer bodies with reasonable height (200-600mm typical)
            if 200 <= height <= 600:
                signals.vertical_extent = 1.0
            elif height > 600:
                signals.vertical_extent = max(0.5, 1.0 - (height - 600) / 400)
            else:
                signals.vertical_extent = height / 200.0
        else:
            rejection_flags.append("no_vertical_extent")

        # Aspect ratio check
        if width > 0 and height > 0:
            aspect = height / width
            if min_aspect_ratio <= aspect <= max_aspect_ratio:
                # Typical guitar body is 1.2-1.8 height/width
                if 1.2 <= aspect <= 1.8:
                    signals.horizontal_distribution = 1.0
                else:
                    signals.horizontal_distribution = 0.7
            else:
                signals.horizontal_distribution = 0.3
                rejection_flags.append("unusual_aspect_ratio")

        # Area check
        area = contour.area_mm2 if contour.is_closed else _estimate_area(contour.points)
        if area < min_area_mm2:
            rejection_flags.append("too_small")
            signals.bout_presence = 0.2
        elif area > max_area_mm2:
            rejection_flags.append("too_large")
            signals.bout_presence = 0.3
        else:
            signals.bout_presence = 0.8

        # Waist narrowing detection
        waist_score = _detect_waist_narrowing(contour.points)
        signals.waist_narrowing = waist_score

        # Centerline balance
        center_x = (min_x + max_x) / 2
        balance_score = _compute_centerline_balance(contour.points, center_x)
        signals.centerline_balance = balance_score

        # Asymmetry (guitars are mostly symmetric)
        asymmetry = _compute_asymmetry(contour.points, center_x)
        signals.asymmetry_visibility = 1.0 - min(1.0, asymmetry / 50.0)  # Penalize high asymmetry

        # Closure quality
        if contour.is_closed:
            signals.closure_quality = 1.0
        elif contour.gap_distance < 5.0:
            signals.closure_quality = 0.8
        elif contour.gap_distance < 20.0:
            signals.closure_quality = 0.5
        else:
            signals.closure_quality = 0.2
            rejection_flags.append("large_gap")

        # Compute composite score
        rank_score = signals.composite_score()

        # Penalize rejected candidates
        if rejection_flags:
            rank_score *= 0.5

        scored.append(ScoredCandidate(
            contour=contour,
            signals=signals,
            rank_score=rank_score,
            rejection_flags=rejection_flags,
        ))

    # Sort by score descending
    scored.sort(key=lambda c: c.rank_score, reverse=True)

    # Assign ranks
    for i, candidate in enumerate(scored):
        candidate.rank = i + 1

    # Return top N
    return ScoringResult(
        candidates=scored[:top_n],
        top_n=top_n,
        total_evaluated=len(contours),
    )


def _estimate_area(points: List[Tuple[float, float]]) -> float:
    """Estimate area of open contour using bounding box."""
    if len(points) < 3:
        return 0.0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (max(xs) - min(xs)) * (max(ys) - min(ys)) * 0.6  # Approximate


def _detect_waist_narrowing(points: List[Tuple[float, float]]) -> float:
    """
    Detect waist narrowing in contour.

    Guitar bodies typically have a waist that's narrower than bouts.
    Returns score 0.0-1.0 where 1.0 = clear waist detected.
    """
    if len(points) < 20:
        return 0.3

    # Sample width at different Y positions
    ys = [p[1] for p in points]
    min_y, max_y = min(ys), max(ys)
    height = max_y - min_y

    if height < 100:
        return 0.3

    # Compute width at 3 zones: lower (0-30%), middle (40-60%), upper (70-100%)
    lower_pts = [p for p in points if min_y <= p[1] <= min_y + 0.3 * height]
    middle_pts = [p for p in points if min_y + 0.4 * height <= p[1] <= min_y + 0.6 * height]
    upper_pts = [p for p in points if min_y + 0.7 * height <= p[1] <= max_y]

    def width_of(pts):
        if not pts:
            return 0.0
        xs = [p[0] for p in pts]
        return max(xs) - min(xs)

    lower_width = width_of(lower_pts)
    middle_width = width_of(middle_pts)
    upper_width = width_of(upper_pts)

    # Check for waist narrowing pattern
    if lower_width > 0 and upper_width > 0 and middle_width > 0:
        avg_bout = (lower_width + upper_width) / 2
        if middle_width < avg_bout * 0.9:
            # Clear waist narrowing
            narrowing_ratio = 1 - (middle_width / avg_bout)
            return min(1.0, 0.5 + narrowing_ratio)

    return 0.4


def _compute_centerline_balance(
    points: List[Tuple[float, float]],
    center_x: float,
) -> float:
    """
    Compute how well points are balanced around centerline.

    Returns 1.0 for perfect balance, lower for imbalanced.
    """
    if not points:
        return 0.0

    left_count = sum(1 for p in points if p[0] < center_x)
    right_count = sum(1 for p in points if p[0] > center_x)

    total = left_count + right_count
    if total == 0:
        return 0.5

    balance = min(left_count, right_count) / max(left_count, right_count) if max(left_count, right_count) > 0 else 0

    return balance


def _compute_asymmetry(
    points: List[Tuple[float, float]],
    center_x: float,
) -> float:
    """
    Compute asymmetry around centerline.

    Returns average deviation from mirror symmetry in mm.
    """
    if len(points) < 10:
        return 100.0  # High asymmetry for sparse points

    # Group points by Y and compare left/right X distances from center
    from collections import defaultdict

    y_buckets = defaultdict(list)
    ys = [p[1] for p in points]
    min_y, max_y = min(ys), max(ys)
    bucket_size = (max_y - min_y) / 10 if max_y > min_y else 1.0

    for p in points:
        bucket = int((p[1] - min_y) / bucket_size)
        y_buckets[bucket].append(p[0] - center_x)

    # For each bucket, compare left and right max extents
    asymmetries = []
    for bucket, x_offsets in y_buckets.items():
        if not x_offsets:
            continue
        left_max = abs(min(x_offsets)) if any(x < 0 for x in x_offsets) else 0
        right_max = abs(max(x_offsets)) if any(x > 0 for x in x_offsets) else 0

        if left_max > 0 or right_max > 0:
            asymmetries.append(abs(left_max - right_max))

    return sum(asymmetries) / len(asymmetries) if asymmetries else 0.0
