"""
Contour Scoring Module
======================

Intelligent contour selection for blueprint vectorization.

Instead of binary reject-only logic, this module:
- Scores candidate contours on multiple geometric signals
- Ranks candidates deterministically
- Returns the best contour even if imperfect
- Provides confidence scores and debug visibility

Integration:
    from app.services.contour_scoring import score_contours

    selection = score_contours(contours, width, height)
    if selection.selected_contour is not None:
        # Use selection.selected_contour
        # Check selection.confidence for quality

Author: Production Shop
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable, Iterable, List, Optional

import cv2
import numpy as np

# Type alias for ownership scoring callback
# Takes a contour (numpy array) and returns score 0.0-1.0
OwnershipFn = Optional[Callable[[np.ndarray], float]]


@dataclass
class ContourScore:
    """Score breakdown for a single contour candidate."""
    index: int
    area: float
    area_ratio: float
    perimeter: float
    closure_gap_px: float
    closure_score: float
    aspect_ratio: float
    aspect_score: float
    solidity: float
    solidity_score: float
    continuity_score: float
    ownership_score: float  # Body ownership score (0.0-1.0), 1.0 if not provided
    vertex_count: int
    score: float
    rejected: bool = False
    reject_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContourSelectionResult:
    """Result of contour scoring and selection."""
    selected_index: Optional[int]
    selected_contour: Optional[np.ndarray]
    confidence: float
    candidates: List[ContourScore]
    warnings: List[str]
    # Selection diagnostics for recommendation layer
    runner_up_score: float = 0.0
    winner_margin: float = 0.0

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "selected_index": self.selected_index,
            "confidence": round(self.confidence, 3),
            "runner_up_score": round(self.runner_up_score, 3),
            "winner_margin": round(self.winner_margin, 3),
            "candidate_count": len(self.candidates),
            "candidates": [c.to_dict() for c in self.candidates],
            "warnings": self.warnings,
        }


# ─── Scoring Helpers ─────────────────────────────────────────────────────────

def _safe_bbox_aspect(contour: np.ndarray) -> float:
    """Get aspect ratio from bounding box (always >= 1.0)."""
    x, y, w, h = cv2.boundingRect(contour)
    if h <= 0 or w <= 0:
        return 999.0
    ratio = max(w / h, h / w)
    return float(ratio)


def _closure_gap_px(contour: np.ndarray) -> float:
    """Distance in pixels between first and last contour point."""
    if contour is None or len(contour) < 2:
        return 9999.0
    start = contour[0][0].astype(np.float32)
    end = contour[-1][0].astype(np.float32)
    return float(np.linalg.norm(start - end))


def _closure_score(gap_px: float, perimeter: float) -> float:
    """
    Score how "closed" a contour is.

    0 gap → 1.0 (perfectly closed)
    Large gap relative to perimeter → 0.0
    """
    if perimeter <= 0:
        return 0.0
    normalized_gap = gap_px / max(perimeter, 1.0)
    # 0 gap -> 1.0, larger gaps decay smoothly
    return float(max(0.0, 1.0 - min(normalized_gap * 20.0, 1.0)))


def _solidity(contour: np.ndarray) -> float:
    """
    Ratio of contour area to convex hull area.

    1.0 = convex shape
    Lower = more concave/irregular
    """
    area = cv2.contourArea(contour)
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    if hull_area <= 0:
        return 0.0
    return float(area / hull_area)


def _solidity_score(solidity: float) -> float:
    """
    Score solidity - body shapes should be reasonably solid.

    Guitar bodies are typically 0.7-0.9 solidity.
    """
    if solidity <= 0:
        return 0.0
    # Map 0.4-0.9 solidity to 0.0-1.0 score
    return float(min(max((solidity - 0.4) / 0.5, 0.0), 1.0))


def _aspect_score(aspect_ratio: float) -> float:
    """
    Score aspect ratio - penalize very extreme skinny shapes.

    Most guitar bodies have aspect ratio 1.2-2.5.
    Allow up to 6.0 for neck-like shapes.
    """
    if aspect_ratio <= 0:
        return 0.0
    if aspect_ratio <= 2.5:
        return 1.0
    if aspect_ratio >= 6.0:
        return 0.0
    return float(1.0 - ((aspect_ratio - 2.5) / 3.5))


def _continuity_score(vertex_count: int, perimeter: float) -> float:
    """
    Score contour continuity - jagged/noisy contours have high vertex density.

    Clean contours have fewer vertices per unit perimeter.
    """
    if perimeter <= 0 or vertex_count <= 0:
        return 0.0
    density = vertex_count / perimeter
    # Too many vertices per unit perimeter often means jagged/noisy contour
    if density <= 0.15:
        return 1.0
    if density >= 1.5:
        return 0.0
    return float(1.0 - ((density - 0.15) / 1.35))


# ─── Main Scoring Function ───────────────────────────────────────────────────

def score_contours(
    contours: Iterable[np.ndarray],
    image_width: int,
    image_height: int,
    *,
    min_area_ratio: float = 0.01,
    max_area_ratio: float = 0.95,
    min_confidence: float = 0.45,
    ownership_fn: OwnershipFn = None,
    debug: bool = False,
) -> ContourSelectionResult:
    """
    Score candidate contours and return the best one.

    This is intentionally broad and forgiving:
    - Prefers large, closed, solid, non-extreme contours
    - Avoids tiny noise
    - Returns best candidate even if low confidence
    - Never returns empty if any contour exists

    Scoring weights (with ownership_fn provided):
    - 35% area ratio (body should be materially present)
    - 25% closure score (closed loops preferred)
    - 10% aspect ratio (reasonable proportions)
    - 15% solidity (convex-ish shapes)
    - 5% continuity (smooth, not jagged)
    - 10% ownership (body ownership from external scorer)

    Without ownership_fn, ownership defaults to 1.0 and weight
    is redistributed to geometric signals.

    Args:
        contours: Iterable of OpenCV contours (numpy arrays)
        image_width: Source image width in pixels
        image_height: Source image height in pixels
        min_area_ratio: Minimum contour area / image area (default 1%)
        max_area_ratio: Maximum contour area / image area (default 95%)
        min_confidence: Threshold for "low confidence" warning
        ownership_fn: Optional callback that takes a contour and returns
                      body ownership score 0.0-1.0. If None, ownership
                      defaults to 1.0 (no penalty).
        debug: If True, return all candidates; otherwise top 3

    Returns:
        ContourSelectionResult with selected contour, confidence, and debug info
    """
    image_area = float(max(image_width * image_height, 1))
    warnings: List[str] = []
    scored: List[ContourScore] = []

    # Convert to list to allow multiple passes
    contour_list = list(contours)

    for idx, contour in enumerate(contour_list):
        if contour is None or len(contour) < 3:
            scored.append(
                ContourScore(
                    index=idx,
                    area=0.0,
                    area_ratio=0.0,
                    perimeter=0.0,
                    closure_gap_px=9999.0,
                    closure_score=0.0,
                    aspect_ratio=999.0,
                    aspect_score=0.0,
                    solidity=0.0,
                    solidity_score=0.0,
                    continuity_score=0.0,
                    ownership_score=0.0,
                    vertex_count=0,
                    score=0.0,
                    rejected=True,
                    reject_reason="degenerate_contour",
                )
            )
            continue

        area = float(cv2.contourArea(contour))
        area_ratio = area / image_area
        perimeter = float(cv2.arcLength(contour, closed=False))
        gap_px = _closure_gap_px(contour)
        closure = _closure_score(gap_px, perimeter)
        aspect = _safe_bbox_aspect(contour)
        aspect_s = _aspect_score(aspect)
        solid = _solidity(contour)
        solid_s = _solidity_score(solid)
        continuity = _continuity_score(len(contour), perimeter)

        # Compute ownership score if callback provided, else default to 1.0
        ownership = 1.0
        if ownership_fn is not None:
            try:
                ownership = float(ownership_fn(contour))
                ownership = max(0.0, min(1.0, ownership))  # Clamp to [0, 1]
            except Exception:
                ownership = 0.5  # Fallback on error

        rejected = False
        reject_reason = ""

        if area_ratio < min_area_ratio:
            rejected = True
            reject_reason = "too_small"
        elif area_ratio > max_area_ratio:
            rejected = True
            reject_reason = "too_large"

        # Weighted score calculation
        # With ownership: geometric signals share 90%, ownership gets 10%
        # Without ownership (ownership=1.0): full geometric weight
        if ownership_fn is not None:
            # Weights with ownership signal
            score = (
                0.35 * min(area_ratio / 0.35, 1.0) +  # body should be ~35% of image
                0.25 * closure +
                0.10 * aspect_s +      # reduced from 0.15
                0.15 * solid_s +
                0.05 * continuity +    # reduced from 0.10
                0.10 * ownership       # new: ownership signal
            )
        else:
            # Original weights without ownership
            score = (
                0.35 * min(area_ratio / 0.35, 1.0) +
                0.25 * closure +
                0.15 * aspect_s +
                0.15 * solid_s +
                0.10 * continuity
            )

        # Penalize rejected contours heavily but don't zero them
        if rejected:
            score *= 0.1

        scored.append(
            ContourScore(
                index=idx,
                area=round(area, 1),
                area_ratio=round(area_ratio, 4),
                perimeter=round(perimeter, 1),
                closure_gap_px=round(gap_px, 2),
                closure_score=round(closure, 3),
                aspect_ratio=round(aspect, 2),
                aspect_score=round(aspect_s, 3),
                solidity=round(solid, 3),
                solidity_score=round(solid_s, 3),
                continuity_score=round(continuity, 3),
                ownership_score=round(ownership, 3),
                vertex_count=len(contour),
                score=round(float(score), 3),
                rejected=rejected,
                reject_reason=reject_reason,
            )
        )

    if not scored:
        return ContourSelectionResult(
            selected_index=None,
            selected_contour=None,
            confidence=0.0,
            candidates=[],
            warnings=["No contours available for scoring."],
            runner_up_score=0.0,
            winner_margin=0.0,
        )

    # Rank by score descending
    ranked = sorted(scored, key=lambda c: c.score, reverse=True)
    best = ranked[0]

    # Compute runner-up and margin for recommendation layer
    runner_up_score = ranked[1].score if len(ranked) > 1 else 0.0
    winner_margin = best.score - runner_up_score

    # Select contour
    selected_contour = None
    selected_index = None

    if not best.rejected:
        selected_index = best.index
        selected_contour = contour_list[best.index]

    confidence = float(best.score)

    # Generate warnings
    if selected_contour is None:
        warnings.append("No contour passed minimum geometric sanity checks.")
    elif confidence < min_confidence:
        warnings.append(
            f"Low confidence contour selection ({confidence:.2f}). Review output before fabrication."
        )

    # Fallback: if best was rejected but it's all we have, use it anyway
    if selected_contour is None and contour_list:
        fallback = ranked[0]
        selected_index = fallback.index
        selected_contour = contour_list[fallback.index]
        confidence = float(fallback.score)
        warnings.append(
            f"Falling back to best available contour despite rejection: {fallback.reject_reason}."
        )

    return ContourSelectionResult(
        selected_index=selected_index,
        selected_contour=selected_contour,
        confidence=confidence,
        candidates=ranked if debug else ranked[:3],
        warnings=warnings,
        runner_up_score=float(runner_up_score),
        winner_margin=float(winner_margin),
    )


# ─── Convenience Functions ───────────────────────────────────────────────────

def select_best_contour(
    contours: Iterable[np.ndarray],
    image_width: int,
    image_height: int,
) -> Optional[np.ndarray]:
    """
    Simple helper to get the best contour without full result object.

    Returns:
        Best contour numpy array, or None if no contours
    """
    result = score_contours(contours, image_width, image_height)
    return result.selected_contour


def get_contour_confidence(
    contours: Iterable[np.ndarray],
    image_width: int,
    image_height: int,
) -> float:
    """
    Get confidence score for the best contour.

    Returns:
        Confidence score 0.0-1.0
    """
    result = score_contours(contours, image_width, image_height)
    return result.confidence
