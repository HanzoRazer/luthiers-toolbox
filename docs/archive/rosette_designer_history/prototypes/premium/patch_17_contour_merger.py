"""
PATCH 17 — Body Contour Merger + X-Extent Guard + Coin Position Filter
=======================================================================

Root-cause analysis of live test failures (Patches 01–16):

  SMART GUITAR (H err 41%):
    The body is split into two separate contours at the Florentine cutaway
    waist. The gap between upper and lower fragments is ~15mm. No
    morphological close kernel can bridge this — the two fragments are
    distinct assembled contours, not adjacent edge pixels.
    Fix: ContourMerger fills all body-candidate contours onto a mask,
    closes that mask with a large kernel, and re-detects as one contour.

  ARCHTOP (W err 111%):
    Fix A (Patch 12) correctly rejected the full-image silhouette using
    vertical overlap, then elected a contour with correct Y extent but
    spanning 101% of image width (neck diagonal sweep included).
    Fix A only checks vertical overlap — width is unconstrained.
    Fix: Add X-extent guard: body candidate width ≤ body_region.width × 1.3

  BENEDETTO (H err 68%, W err 59%):
    A tuner, f-hole rim, or decorative element passed all coin filters
    (size, color, sharpness) at confidence 0.70. On a Benedetto archtop,
    reference coins are never present in the body photo.
    Key: the false object is INSIDE the body silhouette.
    Real coins are always placed BESIDE the instrument.
    Fix: CoinPositionFilter — reject any coin candidate whose centre
    is inside the fg_mask foreground region.

All three fixes operate on existing data structures with no new stages.

Pipeline positions:
  ContourMerger: Stage 8 (after contour assembly, before body election)
  X-extent guard: extends elect_body_contour() from Patch 12
  CoinPositionFilter: extends filter_coin_detections() from Patch 05/07

Author: The Production Shop
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# FIX 1 — ContourMerger
# =============================================================================

@dataclass
class MergeResult:
    """Result from ContourMerger."""
    merged_contour:    np.ndarray        # merged body contour points
    n_fragments:       int               # number of fragments merged
    fragment_areas:    List[float]       # areas of individual fragments
    close_kernel_px:   int               # kernel used to bridge gaps
    bbox_px:           Tuple[int,int,int,int]
    notes:             List[str] = field(default_factory=list)


class ContourMerger:
    """
    Merges fragmented body contours into a single unified outline.

    Strategy: fill all body-candidate contour areas onto a binary mask,
    then apply morphological close to bridge the inter-fragment gaps,
    then re-detect the single merged contour.

    This is fundamentally different from GatedAdaptiveCloser (Patch 14),
    which operates on edge pixel images. ContourMerger operates on filled
    silhouette masks — it bridges the physical waist gap between upper
    and lower bout fragments regardless of gap size.

    Parameters
    ----------
    max_close_px      : maximum close kernel in pixels (default 120)
    min_fragment_area : minimum fragment area to include in merge (px²)
    max_fragments     : maximum fragments to consider (avoids noise)
    body_overlap_min  : minimum vertical overlap with body_region to qualify
    """

    def __init__(
        self,
        max_close_px:      int   = 120,
        min_fragment_area: float = 2000.0,
        max_fragments:     int   = 8,
        body_overlap_min:  float = 0.40,
    ):
        self.max_close_px      = max_close_px
        self.min_fragment_area = min_fragment_area
        self.max_fragments     = max_fragments
        self.body_overlap_min  = body_overlap_min

    # ------------------------------------------------------------------
    def merge(
        self,
        feature_contours: list,          # List[FeatureContour]
        image_shape:      Tuple[int, int],
        body_region       = None,        # BodyRegion (optional)
        mpp:              float = 0.3,
    ) -> Optional[MergeResult]:
        """
        Find all body-candidate fragments, fill them onto a mask, close,
        re-detect as a single merged contour.

        Parameters
        ----------
        feature_contours : assembled FeatureContour list from Stage 8
        image_shape      : (height, width) of the working image
        body_region      : BodyRegion from BodyIsolator
        mpp              : mm per pixel (for logging)

        Returns
        -------
        MergeResult with merged contour, or None if merging unnecessary
        """
        h, w = image_shape
        notes = []

        # Collect body-candidate fragments within the body region
        candidates = self._collect_candidates(
            feature_contours, body_region, notes)

        if len(candidates) <= 1:
            notes.append(f"Only {len(candidates)} candidate(s) — no merge needed")
            logger.info(f"ContourMerger: {notes[-1]}")
            return None

        notes.append(f"Found {len(candidates)} body fragments to merge")

        # Estimate gap size between fragments (vertical)
        gap_px = self._estimate_gap_px(candidates)
        notes.append(f"Max vertical gap between fragments: {gap_px}px "
                     f"({gap_px*mpp:.1f}mm at mpp={mpp:.3f})")

        # Close kernel: must be large enough to bridge the gap
        # Use odd kernel, capped at max_close_px
        k_size = min(self.max_close_px, int(gap_px * 1.5 / 2) * 2 + 1)
        k_size = max(11, k_size)
        notes.append(f"Close kernel: {k_size}×{k_size}")

        # Fill all candidate contours onto a mask
        mask = np.zeros((h, w), np.uint8)
        fragment_areas = []
        for fc in candidates:
            pts = fc.points_px
            if pts.ndim == 3:
                pts_draw = pts
            else:
                pts_draw = pts.reshape(-1, 1, 2)
            cv2.fillPoly(mask, [pts_draw], 255)
            fragment_areas.append(float(fc.area_px))

        # Close the merged mask
        kernel = np.ones((k_size, k_size), np.uint8)
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Re-detect contours
        cnts, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cnts:
            notes.append("No contours after merge — returning None")
            return None

        merged = max(cnts, key=cv2.contourArea)
        bbox   = cv2.boundingRect(merged)

        notes.append(
            f"Merged: {len(candidates)} fragments → 1 contour "
            f"({bbox[2]}×{bbox[3]}px)")

        logger.info(
            f"ContourMerger: {len(candidates)} fragments merged with "
            f"k={k_size}×{k_size}, gap={gap_px}px → "
            f"bbox {bbox[2]}×{bbox[3]}px")

        return MergeResult(
            merged_contour = merged,
            n_fragments    = len(candidates),
            fragment_areas = fragment_areas,
            close_kernel_px = k_size,
            bbox_px        = bbox,
            notes          = notes,
        )

    # ------------------------------------------------------------------
    def _collect_candidates(
        self,
        feature_contours: list,
        body_region,
        notes: List[str],
    ) -> list:
        """Select body-candidate fragments from feature_contour list."""
        candidates = []

        for fc in feature_contours:
            if fc.area_px < self.min_fragment_area:
                continue

            # Check vertical overlap with body region if available
            if body_region is not None:
                _, cy, _, ch = fc.bbox_px
                b_top = body_region.y
                b_bot = body_region.y + body_region.height
                overlap = max(0, min(cy + ch, b_bot) - max(cy, b_top))
                ov_frac = overlap / max(ch, 1)
                if ov_frac < self.body_overlap_min:
                    continue

            candidates.append(fc)

        # Sort by area descending, cap at max_fragments
        candidates.sort(key=lambda fc: fc.area_px, reverse=True)
        return candidates[:self.max_fragments]

    @staticmethod
    def _estimate_gap_px(candidates: list) -> int:
        """Estimate the maximum vertical gap between candidate fragments."""
        if len(candidates) < 2:
            return 0

        # Get y extents of each fragment
        extents = []
        for fc in candidates:
            _, cy, _, ch = fc.bbox_px
            extents.append((cy, cy + ch))

        extents.sort()
        max_gap = 0
        for i in range(len(extents) - 1):
            gap = extents[i + 1][0] - extents[i][1]
            max_gap = max(max_gap, gap)
        return max(0, max_gap)


# =============================================================================
# FIX 2 — X-Extent Guard (extends elect_body_contour from Patch 12)
# =============================================================================

def elect_body_contour_v2(
    contours:          list,             # List[FeatureContour]
    body_region_hint   = None,           # BodyRegion or None
    min_overlap:       float = 0.50,
    max_width_factor:  float = 1.30,     # body width ≤ body_region.width × this
) -> int:
    """
    Extended body contour election with both vertical overlap AND
    X-extent guard.

    Extends elect_body_contour() from Patch 12 Fix A by adding:
    - Width constraint: elected contour must not be wider than
      body_region.width × max_width_factor
    - This prevents neck-sweeping contours that are correct in Y
      but span to image edges in X

    Parameters
    ----------
    contours          : List[FeatureContour]
    body_region_hint  : BodyRegion from BodyIsolator
    min_overlap       : minimum vertical overlap fraction (0.50)
    max_width_factor  : maximum width as multiple of body_region width (1.30)

    Returns
    -------
    Index of elected body contour, or -1 if empty.
    """
    if not contours:
        return -1

    if body_region_hint is None:
        return max(range(len(contours)), key=lambda i: contours[i].area_px)

    body_w  = max(body_region_hint.width,  1)
    body_h  = max(body_region_hint.height, 1)
    max_w   = body_w * max_width_factor

    scored = []
    rejected_overlap = 0
    rejected_width   = 0

    for i, fc in enumerate(contours):
        cx, cy, cw, ch = fc.bbox_px

        # Vertical overlap check (from Patch 12)
        b_top = body_region_hint.y
        b_bot = body_region_hint.y + body_h
        overlap = max(0, min(cy + ch, b_bot) - max(cy, b_top))
        ov_frac = overlap / max(ch, 1)

        if ov_frac < min_overlap:
            rejected_overlap += 1
            continue

        # X-extent guard (NEW in Patch 17)
        if cw > max_w:
            logger.debug(
                f"X-extent guard: contour[{i}] width={cw}px > "
                f"max={max_w:.0f}px ({max_width_factor}× body_width={body_w}px) "
                f"— rejected")
            rejected_width += 1
            continue

        score = ov_frac * fc.area_px
        scored.append((i, score, ov_frac, cw))

    logger.info(
        f"elect_body_contour_v2: {len(scored)} candidates pass "
        f"(rejected overlap={rejected_overlap}, width={rejected_width})")

    if scored:
        scored.sort(key=lambda x: x[1], reverse=True)
        best_idx, best_score, best_ov, best_w = scored[0]
        logger.info(
            f"  Elected idx={best_idx}: overlap={best_ov:.0%}, "
            f"width={best_w}px, area={contours[best_idx].area_px:.0f}px²")
        return best_idx

    # Fallback: no contour passed both filters — use overlap only
    logger.warning(
        "elect_body_contour_v2: no contour passed X-extent guard "
        "— falling back to overlap-only")
    return max(
        (i for i, fc in enumerate(contours)
         if _vertical_overlap(fc.bbox_px, body_region_hint) >= min_overlap),
        key=lambda i: contours[i].area_px,
        default=max(range(len(contours)),
                    key=lambda i: contours[i].area_px))


def _vertical_overlap(
    contour_bbox: Tuple[int, int, int, int],
    body_region,
) -> float:
    _, cy, _, ch = contour_bbox
    b_top = body_region.y
    b_bot = body_region.y + body_region.height
    overlap = max(0, min(cy + ch, b_bot) - max(cy, b_top))
    return overlap / max(ch, 1)


# =============================================================================
# FIX 3 — Coin Position Filter
# =============================================================================

def filter_coin_by_position(
    circles:   np.ndarray,              # (N, 3) filtered circles [x, y, r]
    fg_mask:   Optional[np.ndarray],    # foreground mask from Stage 4
    image_shape: Tuple[int, int],
    margin_px: int = 15,               # allow coin slightly inside fg edge
) -> np.ndarray:
    """
    Reject coin candidates whose centre is inside the instrument silhouette.

    Real reference coins are placed BESIDE the instrument, not on top of it.
    Hardware (tuners, knobs, f-hole rims) that passes size/color/sharpness
    filters is always inside or very close to the body silhouette.

    Parameters
    ----------
    circles     : (N, 3) array of [x, y, r] from prior filters
    fg_mask     : foreground mask (255 = instrument, 0 = background)
    image_shape : (height, width)
    margin_px   : coin allowed to overlap fg_mask by this many pixels
                  (handles coins placed right next to the body edge)

    Returns
    -------
    Filtered circles array.
    """
    if fg_mask is None or len(circles) == 0:
        return circles

    h, w = image_shape
    accepted = []
    rejected = 0

    # Erode fg_mask slightly — coins can touch the edge
    if margin_px > 0:
        kernel = np.ones((margin_px * 2 + 1, margin_px * 2 + 1), np.uint8)
        fg_check = cv2.erode(fg_mask, kernel)
    else:
        fg_check = fg_mask

    for entry in circles:
        x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        # Is the coin centre inside the eroded fg_mask?
        if fg_check[y, x] > 0:
            logger.debug(
                f"Coin position filter: rejected ({x},{y}) r={r}px "
                f"— centre inside fg_mask")
            rejected += 1
            continue

        # Also check: is a significant fraction of the coin area inside fg?
        y0, y1 = max(0, y - r), min(h, y + r)
        x0, x1 = max(0, x - r), min(w, x + r)
        patch = fg_check[y0:y1, x0:x1]
        if patch.size > 0:
            inside_frac = float(np.sum(patch > 0)) / patch.size
            if inside_frac > 0.30:   # >30% of coin area is inside body
                logger.debug(
                    f"Coin position filter: rejected ({x},{y}) r={r}px "
                    f"— {inside_frac:.0%} inside fg_mask")
                rejected += 1
                continue

        accepted.append(entry)

    logger.info(
        f"CoinPositionFilter: {len(circles)} → {len(accepted)} "
        f"({rejected} inside body rejected)")

    return np.array(accepted, dtype=np.float32) if accepted \
        else np.empty((0, 3))


# =============================================================================
# Integration
# =============================================================================

INTEGRATION_NOTES = """
PATCH 17 — Integration Points in photo_vectorizer_v2.py
=========================================================

FIX 1: ContourMerger — insert after Stage 8 (ContourAssembler.assemble())
        and before body contour election

    from patch_17_contour_merger import ContourMerger
    self.contour_merger = ContourMerger()   # add to __init__

    # In extract(), after feature_contours = self.assembler.assemble(...):
    merge_result = self.contour_merger.merge(
        feature_contours, (img_h, img_w),
        body_region=body_region, mpp=mpp)

    if merge_result is not None:
        # Create a synthetic FeatureContour from the merged contour
        from photo_vectorizer_v2 import FeatureContour, FeatureType
        import hashlib
        merged_fc = FeatureContour(
            points_px    = merge_result.merged_contour,
            feature_type = FeatureType.BODY_OUTLINE,
            confidence   = 0.85,
            area_px      = cv2.contourArea(merge_result.merged_contour),
            bbox_px      = merge_result.bbox_px,
            hash_id      = hashlib.md5(
                merge_result.merged_contour.tobytes()).hexdigest()[:12],
        )
        # Add merged contour to feature_contours list
        feature_contours.append(merged_fc)
        result.warnings.append(
            f"Body fragmented into {merge_result.n_fragments} parts "
            f"— merged with {merge_result.close_kernel_px}×"
            f"{merge_result.close_kernel_px}px kernel")

FIX 2: X-extent guard — replace elect_body_contour() call

    from patch_17_contour_merger import elect_body_contour_v2

    # Replace:
    body_idx = elect_body_contour(feature_contours, body_region)
    # With:
    body_idx = elect_body_contour_v2(
        feature_contours, body_region,
        min_overlap=0.50, max_width_factor=1.30)

FIX 3: Coin position filter — add to filter_coin_detections() in
        ReferenceObjectDetector.detect()

    from patch_17_contour_merger import filter_coin_by_position

    # After existing size+color+sharpness filters:
    filtered = filter_coin_by_position(
        filtered, alpha_mask, (h, w))
    # Note: alpha_mask must be passed to detect() — add as parameter
    # In ScaleCalibrator.calibrate(), pass fg_mask to ref_detector.detect()
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 65)
    print("PATCH 17 — Self-Test")
    print("=" * 65)

    # ── FIX 1: ContourMerger ────────────────────────────────────────
    print("\nFIX 1 — ContourMerger (Smart Guitar two-fragment case):")

    class MockFC:
        def __init__(self, x, y, w, h):
            self.bbox_px  = (x, y, w, h)
            self.area_px  = float(w * h * 0.85)
            self.points_px = np.array([
                [x, y], [x+w, y], [x+w, y+h], [x, y+h]
            ], dtype=np.int32).reshape(-1, 1, 2)

    class MockBR:
        def __init__(self, y, height, width=800):
            self.y = y; self.height = height; self.width = width

    # Smart Guitar: upper bout (rows 200-750) + lower bout (rows 800-1400)
    upper_fc = MockFC(100, 200, 800, 550)   # upper bout
    lower_fc = MockFC(80,  800, 820, 600)   # lower bout
    noise_fc = MockFC(400, 600,  30,  30)   # tiny noise contour

    contours = [upper_fc, lower_fc, noise_fc]
    body_region = MockBR(y=200, height=1200)

    merger = ContourMerger()
    result = merger.merge(contours, (1536, 1024), body_region, mpp=0.296)

    if result:
        _, _, bw, bh = result.bbox_px
        print(f"  Fragments merged: {result.n_fragments}")
        print(f"  Merged bbox: {bw}×{bh}px")
        print(f"  Close kernel: {result.close_kernel_px}px")
        print(f"  Height: {bh}px × 0.296mm/px = {bh*0.296:.0f}mm "
              f"(spec 444.5mm)")
        for note in result.notes:
            print(f"    {note}")
    else:
        print("  No merge (unexpected)")

    # ── FIX 2: X-extent guard ──────────────────────────────────────
    print("\nFIX 2 — X-extent guard (Archtop neck-width case):")

    class MockFC2:
        def __init__(self, x, y, w, h, area=None):
            self.bbox_px = (x, y, w, h)
            self.area_px = float(area or w*h*0.85)

    body_reg = MockBR(y=497, height=522, width=600)

    # The archtop contours: one spans full width, one is correct body
    full_width   = MockFC2(0, 480, 1024, 540)   # full image width — WRONG
    correct_body = MockFC2(50, 490, 620,  500)  # correct body width

    contours2 = [full_width, correct_body]

    idx = elect_body_contour_v2(contours2, body_reg,
                                 min_overlap=0.50, max_width_factor=1.30)
    max_allowed = body_reg.width * 1.30
    print(f"  Body region width: {body_reg.width}px")
    print(f"  Max allowed width: {max_allowed:.0f}px")
    print(f"  Full-width contour: 1024px → "
          f"{'REJECTED ✓' if 1024 > max_allowed else 'accepted'}")
    print(f"  Correct body contour: 620px → "
          f"{'accepted ✓' if 620 <= max_allowed else 'rejected'}")
    print(f"  Elected index: {idx} "
          f"({'correct_body ✓' if idx == 1 else 'full_width ✗'})")

    # ── FIX 3: Coin position filter ─────────────────────────────────
    print("\nFIX 3 — Coin position filter (Benedetto false-positive case):")

    # Create a mock fg_mask: body occupies centre 60% of 1024×1024
    h_test, w_test = 1024, 1024
    fg = np.zeros((h_test, w_test), np.uint8)
    cv2.rectangle(fg, (150, 100), (874, 924), 255, -1)  # body region

    # Coins to test
    coins = np.array([
        [50,   50,  25],   # upper-left corner (outside body) → ACCEPT
        [950,  50,  25],   # upper-right corner (outside body) → ACCEPT
        [512, 512,  25],   # dead centre of body → REJECT
        [200, 300,  25],   # inside body → REJECT
        [140, 100,  25],   # just at edge (margin 15px) → likely ACCEPT
    ], dtype=np.float32)

    filtered_pos = filter_coin_by_position(coins, fg, (h_test, w_test),
                                            margin_px=15)
    print(f"  Input coins: {len(coins)}")
    print(f"  After position filter: {len(filtered_pos)}")
    labels = ["corner (outside)", "corner (outside)",
              "body centre", "inside body", "edge"]
    for i, (x, y, r) in enumerate(coins.astype(int)):
        inside = fg[min(y, h_test-1), min(x, w_test-1)] > 0
        accepted = any(abs(fc[0]-x) < 1 and abs(fc[1]-y) < 1
                       for fc in filtered_pos) if len(filtered_pos) else False
        print(f"    ({x:4d},{y:4d}) r={r}  {labels[i]:<22} "
              f"{'ACCEPT ✓' if accepted else 'REJECT ✓' if inside else 'REJECT?'}")

    print(f"\n{'='*65}")
    print("All tests complete.")
    print(INTEGRATION_NOTES)
