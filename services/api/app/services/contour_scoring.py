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
    centrality_score: float  # How centered in image (0.0-1.0)
    touches_border: bool  # Contour touches image edge
    edge_count: int  # Number of edges touched (0-4)
    is_page_border: bool  # Detected as page border
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


# ─── Bounding Box Helpers ───────────────────────────────────────────────────


def _bbox_intersection(bbox1: tuple, bbox2: tuple) -> float:
    """Compute intersection area of two bounding boxes."""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    # Compute intersection rectangle
    ix1 = max(x1, x2)
    iy1 = max(y1, y2)
    ix2 = min(x1 + w1, x2 + w2)
    iy2 = min(y1 + h1, y2 + h2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    return float((ix2 - ix1) * (iy2 - iy1))


def _bbox_iou(bbox1: tuple, bbox2: tuple) -> float:
    """Compute Intersection over Union of two bounding boxes."""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    area1 = w1 * h1
    area2 = w2 * h2

    if area1 <= 0 or area2 <= 0:
        return 0.0

    intersection = _bbox_intersection(bbox1, bbox2)
    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return float(intersection / union)


def _bbox_containment(inner_bbox: tuple, outer_bbox: tuple) -> float:
    """
    Compute how much of inner_bbox is contained within outer_bbox.

    Returns intersection / inner_area (0.0 to 1.0).
    """
    _, _, w, h = inner_bbox
    inner_area = w * h

    if inner_area <= 0:
        return 0.0

    intersection = _bbox_intersection(inner_bbox, outer_bbox)
    return float(intersection / inner_area)


def _bbox_center(bbox: tuple) -> tuple:
    """Get center point of bounding box."""
    x, y, w, h = bbox
    return (x + w / 2, y + h / 2)


def _bbox_aspect_ratio(bbox: tuple) -> float:
    """Get aspect ratio of bounding box (always >= 1.0)."""
    _, _, w, h = bbox
    if h <= 0 or w <= 0:
        return 999.0
    return float(max(w / h, h / w))


# ─── Duplicate Detection ────────────────────────────────────────────────────


def _is_nested_duplicate(
    inner_contour: np.ndarray,
    outer_contour: np.ndarray,
    image_width: int,
    image_height: int,
) -> bool:
    """
    Detect if inner_contour is a nested duplicate of outer_contour.

    A nested duplicate is "same shape, offset inward" - like a binding line
    inside a body outline.

    Criteria (all must be true):
    - inner bbox substantially contained in outer bbox (≥90%)
    - aspect ratios within 15%
    - area ratio 0.70-0.98 (inner is smaller but similar)
    """
    if inner_contour is None or outer_contour is None:
        return False
    if len(inner_contour) < 3 or len(outer_contour) < 3:
        return False

    inner_bbox = cv2.boundingRect(inner_contour)
    outer_bbox = cv2.boundingRect(outer_contour)

    inner_area = float(cv2.contourArea(inner_contour))
    outer_area = float(cv2.contourArea(outer_contour))

    if outer_area <= 0 or inner_area <= 0:
        return False

    # Check containment (inner must be mostly inside outer)
    containment = _bbox_containment(inner_bbox, outer_bbox)
    if containment < 0.90:
        return False

    # Check aspect ratio similarity
    inner_aspect = _bbox_aspect_ratio(inner_bbox)
    outer_aspect = _bbox_aspect_ratio(outer_bbox)
    aspect_diff = abs(inner_aspect - outer_aspect) / max(outer_aspect, 0.01)
    if aspect_diff > 0.15:
        return False

    # Check area ratio (inner should be 70-98% of outer)
    area_ratio = inner_area / outer_area
    if not (0.70 <= area_ratio <= 0.98):
        return False

    return True


def _is_parallel_duplicate(
    contour1: np.ndarray,
    contour2: np.ndarray,
    image_width: int,
    image_height: int,
) -> bool:
    """
    Detect if two contours are parallel duplicates (same outline, offset).

    Parallel duplicates are nearly identical outlines offset by a small amount,
    like doubled construction lines from blueprint printing.

    Criteria:
    - bbox IoU ≥ 0.80
    - center distance ≤ 3% of max(image_w, image_h)
    - aspect ratio difference ≤ 10%
    - area ratio 0.80-1.20
    """
    if contour1 is None or contour2 is None:
        return False
    if len(contour1) < 3 or len(contour2) < 3:
        return False

    bbox1 = cv2.boundingRect(contour1)
    bbox2 = cv2.boundingRect(contour2)

    area1 = float(cv2.contourArea(contour1))
    area2 = float(cv2.contourArea(contour2))

    if area1 <= 0 or area2 <= 0:
        return False

    # Check bbox IoU
    iou = _bbox_iou(bbox1, bbox2)
    if iou < 0.80:
        return False

    # Check center distance
    c1 = _bbox_center(bbox1)
    c2 = _bbox_center(bbox2)
    max_dim = max(image_width, image_height)
    center_dist = ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5
    normalized_dist = center_dist / max(max_dim, 1)
    if normalized_dist > 0.03:
        return False

    # Check aspect ratio similarity
    aspect1 = _bbox_aspect_ratio(bbox1)
    aspect2 = _bbox_aspect_ratio(bbox2)
    aspect_diff = abs(aspect1 - aspect2) / max(aspect1, aspect2, 0.01)
    if aspect_diff > 0.10:
        return False

    # Check area ratio
    area_ratio = min(area1, area2) / max(area1, area2)
    if area_ratio < 0.80:
        return False

    return True


# ─── Thin Strip Detection ───────────────────────────────────────────────────


def _is_thin_strip(
    contour: np.ndarray,
    image_width: int,
    image_height: int,
) -> tuple:
    """
    Detect if contour is a thin strip (dimension line, border fragment).

    A thin strip is:
    - aspect ratio > 8.0
    - OR aspect ratio > 6.0 AND touches 2 opposite edges
    - OR minor axis < 1% of image short side

    Returns:
        (is_strip: bool, severity: float 0.0-1.0)
    """
    if contour is None or len(contour) < 3:
        return False, 0.0

    bbox = cv2.boundingRect(contour)
    x, y, w, h = bbox

    aspect = _bbox_aspect_ratio(bbox)
    minor_axis = min(w, h)
    image_short_side = min(image_width, image_height)

    # Check minor axis relative to image
    minor_ratio = minor_axis / max(image_short_side, 1)

    # Strong strip: aspect > 8
    if aspect > 8.0:
        severity = min(1.0, (aspect - 8.0) / 4.0 + 0.5)
        return True, severity

    # Moderate strip: aspect > 6 with edge contact
    if aspect > 6.0:
        # Check if touches opposite edges
        touches_left = x <= 3
        touches_right = x + w >= image_width - 3
        touches_top = y <= 3
        touches_bottom = y + h >= image_height - 3

        touches_horizontal_pair = touches_left and touches_right
        touches_vertical_pair = touches_top and touches_bottom

        if touches_horizontal_pair or touches_vertical_pair:
            severity = min(1.0, (aspect - 6.0) / 4.0 + 0.3)
            return True, severity

    # Very thin: minor axis < 1% of image
    if minor_ratio < 0.01:
        severity = min(1.0, (0.01 - minor_ratio) / 0.01 + 0.3)
        return True, severity

    return False, 0.0


# ─── Page Border Detection ──────────────────────────────────────────────────

def _touches_border(
    contour: np.ndarray,
    image_width: int,
    image_height: int,
    margin_px: int = 3,
) -> tuple[bool, int]:
    """
    Check if contour touches image border.

    Returns:
        (touches_any_edge, edge_count) where edge_count is 0-4
    """
    if contour is None or len(contour) < 3:
        return False, 0

    x, y, w, h = cv2.boundingRect(contour)

    edges_touched = 0
    if x <= margin_px:
        edges_touched += 1  # left
    if y <= margin_px:
        edges_touched += 1  # top
    if x + w >= image_width - margin_px:
        edges_touched += 1  # right
    if y + h >= image_height - margin_px:
        edges_touched += 1  # bottom

    return edges_touched > 0, edges_touched


def _is_page_border(
    contour: np.ndarray,
    image_width: int,
    image_height: int,
    area_ratio: float,
) -> bool:
    """
    Detect if contour is likely a page border.

    Page borders:
    - Touch 3+ edges
    - OR touch 2+ edges AND area > 70% of image
    """
    touches, edge_count = _touches_border(contour, image_width, image_height)
    if not touches:
        return False

    # Strong signal: touches 3+ edges
    if edge_count >= 3:
        return True

    # Moderate signal: touches 2+ edges AND large area
    if edge_count >= 2 and area_ratio > 0.70:
        return True

    return False


def _centrality_score(
    contour: np.ndarray,
    image_width: int,
    image_height: int,
) -> float:
    """
    Score how centered the contour is in the image.

    Guitar bodies in blueprints are typically centered.
    Page borders and annotations are often off-center.

    Returns:
        0.0 (edge-hugging) to 1.0 (perfectly centered)
    """
    if contour is None or len(contour) < 3:
        return 0.0

    x, y, w, h = cv2.boundingRect(contour)

    # Contour center
    cx = x + w / 2
    cy = y + h / 2

    # Image center
    img_cx = image_width / 2
    img_cy = image_height / 2

    # Distance from center, normalized by image diagonal
    dx = abs(cx - img_cx) / (image_width / 2)
    dy = abs(cy - img_cy) / (image_height / 2)
    offset = (dx + dy) / 2  # 0 = centered, 1 = corner

    # Convert to score (inverted)
    return float(max(0.0, 1.0 - offset))


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


# ─── In-Group Refinement ────────────────────────────────────────────────────


def _compute_duplicate_penalties(
    contours: List[np.ndarray],
    base_scores: List[float],
    image_width: int,
    image_height: int,
) -> List[float]:
    """
    Compute duplicate penalties for each contour.

    When contour A is a duplicate (nested or parallel) of higher-scoring contour B,
    A gets penalized. This prevents near-identical binding lines from competing
    with the actual body outline.

    Returns:
        List of penalty multipliers (0.0-1.0), where 1.0 means no penalty
    """
    n = len(contours)
    penalties = [1.0] * n

    # Sort indices by score descending to process higher-scoring first
    sorted_indices = sorted(range(n), key=lambda i: base_scores[i], reverse=True)

    # Track which contours are "dominant" (not yet penalized as duplicates)
    dominant = set(sorted_indices)

    for i, idx in enumerate(sorted_indices):
        contour = contours[idx]
        if contour is None or len(contour) < 3:
            continue

        # Compare against all higher-scoring contours
        for higher_idx in sorted_indices[:i]:
            if higher_idx not in dominant:
                continue

            higher_contour = contours[higher_idx]
            if higher_contour is None or len(higher_contour) < 3:
                continue

            # Check if current is a nested duplicate of higher
            if _is_nested_duplicate(contour, higher_contour, image_width, image_height):
                # Nested duplicate: moderate penalty
                penalties[idx] *= 0.6
                dominant.discard(idx)
                break

            # Check if current is a parallel duplicate of higher
            if _is_parallel_duplicate(contour, higher_contour, image_width, image_height):
                # Parallel duplicate: strong penalty (nearly same shape)
                penalties[idx] *= 0.5
                dominant.discard(idx)
                break

    return penalties


def _compute_thin_strip_penalties(
    contours: List[np.ndarray],
    image_width: int,
    image_height: int,
) -> List[float]:
    """
    Compute thin strip penalties for each contour.

    Returns:
        List of penalty multipliers (0.0-1.0), where 1.0 means no penalty
    """
    penalties = []
    for contour in contours:
        is_strip, severity = _is_thin_strip(contour, image_width, image_height)
        if is_strip:
            # Penalty scales with severity: 0.3 severity -> 0.7 multiplier
            penalty = max(0.3, 1.0 - severity * 0.7)
            penalties.append(penalty)
        else:
            penalties.append(1.0)
    return penalties


def _compute_outer_body_preference(
    contours: List[np.ndarray],
    base_scores: List[float],
    image_width: int,
    image_height: int,
    page_border_flags: List[bool],
) -> List[float]:
    """
    Compute outer-body preference bonus for each contour.

    The largest plausible non-border closed contour gets a bonus.
    This helps the "Body mould" win over smaller template pieces.

    Returns:
        List of bonus multipliers (1.0-1.15), where 1.0 means no bonus
    """
    n = len(contours)
    bonuses = [1.0] * n

    if n == 0:
        return bonuses

    image_area = float(image_width * image_height)

    # Find candidates: non-border, reasonable size, decent base score
    candidates = []
    for i, contour in enumerate(contours):
        if contour is None or len(contour) < 3:
            continue
        if page_border_flags[i]:
            continue

        area = float(cv2.contourArea(contour))
        area_ratio = area / max(image_area, 1)

        # Must be reasonably sized (5-80% of image)
        if not (0.05 <= area_ratio <= 0.80):
            continue

        # Must have decent base score (not rejected-level)
        if base_scores[i] < 0.15:
            continue

        # Must have body-like aspect ratio (not a strip)
        bbox = cv2.boundingRect(contour)
        aspect = _bbox_aspect_ratio(bbox)
        if aspect > 4.0:  # Too elongated to be a body
            continue

        candidates.append((i, area, area_ratio))

    if not candidates:
        return bonuses

    # Sort by area descending
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Top candidate gets the largest bonus
    # Second gets smaller bonus, etc.
    for rank, (idx, area, area_ratio) in enumerate(candidates[:3]):
        if rank == 0:
            # Largest: 10-15% bonus based on how dominant it is
            if len(candidates) > 1:
                second_area = candidates[1][1]
                dominance = area / max(second_area, 1)
                bonus = 1.0 + min(0.15, (dominance - 1.0) * 0.05 + 0.10)
            else:
                bonus = 1.15  # Only candidate gets full bonus
            bonuses[idx] = bonus
        elif rank == 1:
            bonuses[idx] = 1.03  # Small bonus for runner-up
        # Third and beyond get no bonus

    return bonuses


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
                    centrality_score=0.0,
                    touches_border=False,
                    edge_count=0,
                    is_page_border=False,
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

        # Page border detection (critical for blueprints)
        touches, edge_count = _touches_border(contour, image_width, image_height)
        page_border = _is_page_border(contour, image_width, image_height, area_ratio)
        centrality = _centrality_score(contour, image_width, image_height)

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

        # Hard rejection filters (order matters for reject_reason)
        if page_border:
            rejected = True
            reject_reason = "page_border"
        elif area_ratio < min_area_ratio:
            rejected = True
            reject_reason = "too_small"
        elif area_ratio > max_area_ratio:
            rejected = True
            reject_reason = "too_large"

        # Weighted score calculation
        # Updated weights: added centrality (5%), reduced area weight
        # With ownership: geometric signals share 85%, ownership 10%, centrality 5%
        # Without ownership: geometric + centrality
        if ownership_fn is not None:
            # Weights with ownership signal
            score = (
                0.30 * min(area_ratio / 0.35, 1.0) +  # body should be ~35% of image
                0.25 * closure +
                0.10 * aspect_s +
                0.10 * solid_s +
                0.05 * continuity +
                0.10 * ownership +
                0.10 * centrality  # new: centered bodies score higher
            )
        else:
            # Weights without ownership
            score = (
                0.30 * min(area_ratio / 0.35, 1.0) +
                0.25 * closure +
                0.10 * aspect_s +
                0.10 * solid_s +
                0.10 * continuity +
                0.15 * centrality  # higher weight when no ownership signal
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
                centrality_score=round(centrality, 3),
                touches_border=touches,
                edge_count=edge_count,
                is_page_border=page_border,
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

    # ─── In-Group Refinement Pass ───────────────────────────────────────────
    # Apply duplicate penalties, thin strip penalties, and outer body bonus
    # to improve winner margin and prevent near-duplicates from competing.

    # Extract data needed for refinement
    base_scores = [s.score for s in scored]
    page_border_flags = [s.is_page_border for s in scored]

    # Compute refinement adjustments
    duplicate_penalties = _compute_duplicate_penalties(
        contour_list, base_scores, image_width, image_height
    )
    strip_penalties = _compute_thin_strip_penalties(
        contour_list, image_width, image_height
    )
    outer_body_bonuses = _compute_outer_body_preference(
        contour_list, base_scores, image_width, image_height, page_border_flags
    )

    # Apply adjustments to scores
    for i, s in enumerate(scored):
        adjusted_score = s.score
        adjusted_score *= duplicate_penalties[i]
        adjusted_score *= strip_penalties[i]
        adjusted_score *= outer_body_bonuses[i]
        # Update the score in place (ContourScore is a dataclass)
        scored[i] = ContourScore(
            index=s.index,
            area=s.area,
            area_ratio=s.area_ratio,
            perimeter=s.perimeter,
            closure_gap_px=s.closure_gap_px,
            closure_score=s.closure_score,
            aspect_ratio=s.aspect_ratio,
            aspect_score=s.aspect_score,
            solidity=s.solidity,
            solidity_score=s.solidity_score,
            continuity_score=s.continuity_score,
            ownership_score=s.ownership_score,
            centrality_score=s.centrality_score,
            touches_border=s.touches_border,
            edge_count=s.edge_count,
            is_page_border=s.is_page_border,
            vertex_count=s.vertex_count,
            score=round(float(adjusted_score), 3),
            rejected=s.rejected,
            reject_reason=s.reject_reason,
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


# ─── Hierarchy-Aware Scoring ────────────────────────────────────────────────

# Import here to avoid circular dependency
# BodyCandidate is imported at function call time

def score_body_candidates(
    candidates: List[Any],  # List[BodyCandidate] - avoid circular import
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
    Score body candidates with hierarchy-aware metrics.

    This is the hierarchy-aware alternative to score_contours().
    It receives BodyCandidate objects that already have:
    - Isolated top-level contours only (no children competing)
    - Child area metrics for adjusted scoring

    Key differences from score_contours():
    - Uses child-aware fill ratio (outer + children) for solidity
    - Adds small capped bonus for plausible internal structure
    - Candidates have already been filtered by hierarchy isolation

    Scoring weights:
    - 30% area ratio (body should be materially present)
    - 25% closure score (closed loops preferred)
    - 10% aspect ratio (reasonable proportions)
    - 10% solidity (child-aware fill ratio)
    - 10% continuity (smooth, not jagged)
    - 10% centrality (centered in image)
    - 5% child bonus (plausible internal structure)

    Args:
        candidates: List of BodyCandidate from isolate_body_candidates()
        image_width: Source image width in pixels
        image_height: Source image height in pixels
        min_area_ratio: Minimum contour area / image area
        max_area_ratio: Maximum contour area / image area
        min_confidence: Threshold for "low confidence" warning
        ownership_fn: Optional callback for body ownership score
        debug: If True, return all candidates; otherwise top 3

    Returns:
        ContourSelectionResult with selected contour, confidence, and debug info
    """
    image_area = float(max(image_width * image_height, 1))
    warnings: List[str] = []
    scored: List[ContourScore] = []

    for cand in candidates:
        contour = cand.contour
        if contour is None or len(contour) < 3:
            continue

        area = cand.area
        area_ratio = area / image_area

        # Basic geometric metrics
        perimeter = float(cv2.arcLength(contour, closed=False))
        gap_px = _closure_gap_px(contour)
        closure = _closure_score(gap_px, perimeter)
        aspect = _safe_bbox_aspect(contour)
        aspect_s = _aspect_score(aspect)
        continuity = _continuity_score(len(contour), perimeter)

        # Child-aware solidity (key fix: don't penalize holes)
        # Use effective fill = (outer_area + child_area) / hull_area
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            effective_fill = min(1.0, (area + cand.child_area_sum) / hull_area)
        else:
            effective_fill = 0.0
        solid_s = _solidity_score(effective_fill)

        # Centrality
        centrality = _centrality_score(contour, image_width, image_height)

        # Page border detection (should already be filtered, but double-check)
        touches, edge_count = _touches_border(contour, image_width, image_height)
        page_border = _is_page_border(contour, image_width, image_height, area_ratio)

        # Ownership score
        ownership = 1.0
        if ownership_fn is not None:
            try:
                ownership = float(ownership_fn(contour))
                ownership = max(0.0, min(1.0, ownership))
            except Exception:
                ownership = 0.5

        # Child bonus (small, capped)
        # Only applies if 1-6 children and child_area_ratio in [0.01, 0.25]
        child_count = len(cand.child_nodes)
        child_bonus = 0.0
        if cand.has_internal_structure:
            # Bonus = child_area_ratio * 0.25, capped at 0.08
            child_bonus = min(0.08, cand.child_area_ratio * 0.25)

        # Rejection filters
        rejected = False
        reject_reason = ""

        if page_border:
            rejected = True
            reject_reason = "page_border"
        elif area_ratio < min_area_ratio:
            rejected = True
            reject_reason = "too_small"
        elif area_ratio > max_area_ratio:
            rejected = True
            reject_reason = "too_large"

        # Weighted score calculation (hierarchy-aware)
        # Note: child_bonus is additive, not weighted
        score = (
            0.30 * min(area_ratio / 0.35, 1.0) +  # area
            0.25 * closure +                       # closure
            0.10 * aspect_s +                      # aspect
            0.10 * solid_s +                       # child-aware solidity
            0.10 * continuity +                    # continuity
            0.10 * centrality +                    # centrality
            child_bonus                            # small bonus for internal structure
        )

        # Add ownership if provided
        if ownership_fn is not None:
            # Redistribute: reduce other weights slightly, add ownership
            score = score * 0.90 + 0.10 * ownership

        # Penalize rejected contours
        if rejected:
            score *= 0.1

        scored.append(
            ContourScore(
                index=cand.node.idx,
                area=round(area, 1),
                area_ratio=round(area_ratio, 4),
                perimeter=round(perimeter, 1),
                closure_gap_px=round(gap_px, 2),
                closure_score=round(closure, 3),
                aspect_ratio=round(aspect, 2),
                aspect_score=round(aspect_s, 3),
                solidity=round(effective_fill, 3),  # Using effective fill
                solidity_score=round(solid_s, 3),
                continuity_score=round(continuity, 3),
                ownership_score=round(ownership, 3),
                centrality_score=round(centrality, 3),
                touches_border=touches,
                edge_count=edge_count,
                is_page_border=page_border,
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
            warnings=["No body candidates available for scoring."],
            runner_up_score=0.0,
            winner_margin=0.0,
        )

    # Rank by score descending
    ranked = sorted(scored, key=lambda c: c.score, reverse=True)
    best = ranked[0]

    # Compute runner-up and margin
    runner_up_score = ranked[1].score if len(ranked) > 1 else 0.0
    winner_margin = best.score - runner_up_score

    # Select best non-rejected candidate
    selected_contour = None
    selected_index = None

    for cand_score in ranked:
        if not cand_score.rejected:
            selected_index = cand_score.index
            # Find the contour from candidates list
            for cand in candidates:
                if cand.node.idx == selected_index:
                    selected_contour = cand.contour
                    break
            break

    confidence = float(best.score)

    # Generate warnings
    if selected_contour is None:
        warnings.append("No body candidate passed geometric sanity checks.")
    elif confidence < min_confidence:
        warnings.append(
            f"Low confidence selection ({confidence:.2f}). Review output before fabrication."
        )

    # Fallback: if all rejected but candidates exist, use best anyway
    if selected_contour is None and candidates:
        fallback = ranked[0]
        selected_index = fallback.index
        for cand in candidates:
            if cand.node.idx == selected_index:
                selected_contour = cand.contour
                break
        confidence = float(fallback.score)
        warnings.append(
            f"Falling back to best available candidate despite rejection: {fallback.reject_reason}."
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
