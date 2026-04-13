"""
Blueprint Cleanup Service
=========================

Shared cleanup logic for blueprint DXF processing.
Extracted from vectorize_router.py to enable reuse by:
- Sync /api/blueprint/vectorize route
- Future async job runner
- Legacy clean_router.py (if refactored)

Integrates contour_scoring for ranked selection instead of binary reject.

Note: This scoring-based approach applies to blueprint pipeline only.
Photo vectorizer still uses ownership-threshold hard gate (0.60).

Multi-Mode Architecture (2026-04-13):
=====================================
Two cleanup modes are available via the `mode` parameter:

- BASELINE: Last useful end-to-end behavior before grouping/refinement.
            Bypasses border removal, 5-tier fallback ladder, and newer penalties.
            Use for stability and regression comparison.

- REFINED:  Current logic with border removal, fallback ladder, and all
            newer selection intelligence. Default for new processing.

The mode is propagated from API → orchestrator → cleanup.
Both modes produce the same response shape; only internal behavior differs.

Author: Production Shop
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from .contour_scoring import score_contours, ContourSelectionResult

logger = logging.getLogger(__name__)


# ─── Cleanup Mode ────────────────────────────────────────────────────────────

class CleanupMode(str, Enum):
    """
    Blueprint cleanup behavior mode.

    BASELINE: Simpler pre-grouping logic for stability/regression.
              - No border removal at cleanup stage
              - No 5-tier fallback ladder
              - Simple 2-pass fallback (length/closure, then any)

    REFINED:  Current logic with all improvements.
              - Surgical border removal before scoring
              - 5-tier fallback priority ladder
              - Body-likeness checks for fallback candidates
    """
    BASELINE = "baseline"
    REFINED = "refined"


@dataclass
class CleanResult:
    """Result from DXF cleanup."""
    success: bool
    svg_preview: str = ""
    dxf_path: str = ""
    original_entity_count: int = 0
    cleaned_entity_count: int = 0
    contours_found: int = 0
    chains_found: int = 0
    discarded_short: int = 0
    discarded_open: int = 0
    discarded_low_score: int = 0
    best_confidence: float = 0.0
    # Selection diagnostics for recommendation layer
    runner_up_score: float = 0.0
    winner_margin: float = 0.0
    candidate_count: int = 0
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    # Fallback diagnostics (for debug)
    fallback_used: bool = False
    fallback_tier: int = 0  # 1-5, 0 if no fallback
    fallback_reason: str = ""
    fallback_reject_reason: str = ""
    fallback_is_page_border: bool = False


# ─── Ownership Adapter ───────────────────────────────────────────────────────

def _create_ownership_fn(canvas_width: int, canvas_height: int):
    """
    Create an ownership scoring callback for contour scoring.

    Wraps body_ownership_score() from contour_plausibility.py as a weighted
    signal instead of a hard gate.

    Args:
        canvas_width: Virtual canvas width (for border contact estimation)
        canvas_height: Virtual canvas height (for border contact estimation)

    Returns:
        Callable that takes a contour and returns ownership score 0.0-1.0
    """
    try:
        # Import from photo-vectorizer service
        import sys
        from pathlib import Path as P
        vectorizer_path = P(__file__).parents[3] / "photo-vectorizer"
        if vectorizer_path.exists() and str(vectorizer_path) not in sys.path:
            sys.path.insert(0, str(vectorizer_path))

        from contour_plausibility import ContourPlausibilityScorer
        scorer = ContourPlausibilityScorer(ownership_threshold=0.0)  # No threshold, just score

        def ownership_fn(contour: np.ndarray) -> float:
            """Compute body ownership score for a contour."""
            if contour is None or len(contour) < 3:
                return 0.0

            breakdown = scorer.score_candidate(
                contour,
                image_shape=(canvas_height, canvas_width),
            )
            return breakdown.ownership_score

        return ownership_fn

    except ImportError:
        # Fallback: return None to skip ownership scoring
        logger.debug("ContourPlausibilityScorer not available, skipping ownership scoring")
        return None


# ─── Fallback Priority Ladder ───────────────────────────────────────────────

# Fallback tiers (lower = better):
# Tier 1: Non-rejected, non-border
# Tier 2: Rejected-for-score, non-border, structurally plausible
# Tier 3: Rejected-for-geometry, non-border, not strip-like
# Tier 4: Rejected non-border, weak structural plausibility
# Tier 5: Page border (LAST RESORT)


def _classify_fallback_tier(candidate) -> int:
    """
    Classify a candidate into a fallback tier.

    Returns tier 1-5, where lower is better.
    """
    # Tier 1: Not rejected, not page border
    if not candidate.rejected and not candidate.is_page_border:
        return 1

    # Page border is always Tier 5
    if candidate.is_page_border:
        return 5

    # Non-border rejected candidates: tiers 2-4 based on reject reason
    reject_reason = candidate.reject_reason

    # Tier 2: Rejected for score/confidence reasons, but structurally valid
    if reject_reason in ("low_score", "low_confidence", ""):
        # Check structural plausibility: decent area, not too extreme aspect
        if candidate.area_ratio >= 0.01 and candidate.aspect_ratio <= 4.0:
            return 2

    # Tier 3: Rejected for geometric reasons, but not strip-like
    if reject_reason in ("too_small", "degenerate_contour"):
        # Still might be a valid body if aspect is reasonable
        if candidate.aspect_ratio <= 6.0:
            return 3

    # Tier 4: All other non-border rejected candidates
    return 4


def _is_body_like(candidate, min_contour_length_mm: float, is_closed: bool, keep_open_chains: bool) -> bool:
    """
    Check if a candidate is body-like enough for fallback consideration.

    More permissive than primary selection but still filters obvious junk.
    """
    # Must pass basic length/closure requirements or be closed
    if not (is_closed or keep_open_chains):
        return False

    # Body-like aspect ratio (not a thin strip)
    if candidate.aspect_ratio > 8.0:
        return False

    # Not too small (more permissive than primary)
    if candidate.area_ratio < 0.002:
        return False

    return True


def _select_fallback_candidate(
    scoring_result,
    chains: list,
    min_contour_length_mm: float,
    close_gaps_mm: float,
    keep_open_chains: bool,
) -> tuple:
    """
    Select the best fallback candidate using priority ladder.

    Returns:
        (chain, score, tier, candidate) or (None, 0.0, 0, None) if no fallback
    """
    if not scoring_result.candidates or not chains:
        return None, 0.0, 0, None

    # Build list of (tier, score, idx, candidate, chain) for sorting
    candidates_with_tiers = []

    for candidate in scoring_result.candidates:
        idx = candidate.index
        if idx >= len(chains):
            continue

        chain = chains[idx]
        chain_len = chain.length()
        is_closed = chain.is_closed(close_gaps_mm)

        # Skip if doesn't meet minimum length
        if chain_len < min_contour_length_mm * 0.5:  # More permissive for fallback
            continue

        tier = _classify_fallback_tier(candidate)

        # Check body-likeness for tiers 2-4
        if tier >= 2:
            if not _is_body_like(candidate, min_contour_length_mm, is_closed, keep_open_chains):
                # Demote to next tier
                tier = min(tier + 1, 5)

        candidates_with_tiers.append((tier, -candidate.score, idx, candidate, chain))

    if not candidates_with_tiers:
        return None, 0.0, 0, None

    # Sort by tier (ascending), then by score (descending via negation)
    candidates_with_tiers.sort(key=lambda x: (x[0], x[1]))

    best = candidates_with_tiers[0]
    tier, neg_score, idx, candidate, chain = best

    return chain, candidate.score, tier, candidate


# ─── Scoring Integration Helpers ─────────────────────────────────────────────

def _chain_to_contour(chain) -> np.ndarray:
    """Convert a Chain object to numpy contour array for scoring."""
    points = [(p.x, p.y) for p in chain.points]
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def _compute_chain_bounds(chains: list, polyline_pts: list) -> Tuple[float, float, float, float]:
    """Compute bounding box of all chains and polylines."""
    all_x, all_y = [], []

    for chain in chains:
        for p in chain.points:
            all_x.append(p.x)
            all_y.append(p.y)

    for pts in polyline_pts:
        for x, y in pts:
            all_x.append(x)
            all_y.append(y)

    if not all_x:
        return 0.0, 0.0, 1000.0, 1000.0

    return min(all_x), min(all_y), max(all_x), max(all_y)


def _estimate_canvas_size(chains: list, polyline_pts: list) -> Tuple[int, int]:
    """Estimate virtual canvas size from chain bounds (in mm units)."""
    min_x, min_y, max_x, max_y = _compute_chain_bounds(chains, polyline_pts)
    width = max(int(max_x - min_x), 100)
    height = max(int(max_y - min_y), 100)
    return width, height


# ─── Surgical Border Removal (Cleanup Stage) ────────────────────────────────
#
# This mirrors the extraction-stage border removal in edge_to_dxf.py.
# The cleanup stage can re-detect page borders from chain geometry,
# so we need to remove them BEFORE scoring to prevent fallback selection.
#
# Author: Production Shop
# Date: 2026-04-13


def _is_chain_page_border(
    chain_contour: np.ndarray,
    canvas_width: int,
    canvas_height: int,
    margin_ratio: float = 0.02,
    area_threshold: float = 0.70,
) -> bool:
    """
    Detect if a chain contour is likely a page border.

    Uses the same logic as contour_scoring._is_page_border but adapted
    for DXF chain coordinates (which may be in mm units).

    Args:
        chain_contour: Numpy array of chain points
        canvas_width, canvas_height: Estimated canvas size
        margin_ratio: How close to edge counts as "touching" (default 2%)
        area_threshold: Area ratio for border detection

    Returns:
        True if this looks like a page border
    """
    if chain_contour is None or len(chain_contour) < 3:
        return False

    # Flatten if needed
    points = chain_contour.reshape(-1, 2)

    # Get bounding box
    x_coords = points[:, 0]
    y_coords = points[:, 1]
    min_x, max_x = x_coords.min(), x_coords.max()
    min_y, max_y = y_coords.min(), y_coords.max()

    # Calculate margins
    margin_x = canvas_width * margin_ratio
    margin_y = canvas_height * margin_ratio

    # Check which edges are touched
    touches_left = min_x <= margin_x
    touches_right = max_x >= canvas_width - margin_x
    touches_top = min_y <= margin_y
    touches_bottom = max_y >= canvas_height - margin_y

    edge_count = sum([touches_left, touches_right, touches_top, touches_bottom])

    # Calculate area ratio
    area = float(cv2.contourArea(chain_contour.astype(np.float32)))
    canvas_area = float(canvas_width * canvas_height)
    area_ratio = area / canvas_area if canvas_area > 0 else 0.0

    # Page border detection (same criteria as contour_scoring)
    if edge_count >= 3:
        return True
    if edge_count >= 2 and area_ratio > area_threshold:
        return True

    return False


def _remove_page_border_chains(
    chains: list,
    contours: list,
    canvas_width: int,
    canvas_height: int,
) -> Tuple[list, list, int, list, list]:
    """
    Remove page border chains BEFORE scoring, but KEEP them if they're
    the only option (for best-effort output).

    This is the cleanup-stage equivalent of _remove_page_borders_early()
    in edge_to_dxf.py. It ensures page borders don't win when better
    candidates exist, but still returns SOMETHING if border is all we have.

    Args:
        chains: List of Chain objects
        contours: List of numpy contour arrays (parallel to chains)
        canvas_width, canvas_height: Estimated canvas size

    Returns:
        (filtered_chains, filtered_contours, removed_count, border_chains, border_contours)
        If filtered_chains is empty but border_chains exists, caller should
        fall back to border_chains with appropriate warning.
    """
    if not chains or not contours:
        return chains, contours, 0, [], []

    filtered_chains = []
    filtered_contours = []
    border_chains = []
    border_contours = []
    removed_count = 0

    for chain, contour in zip(chains, contours):
        if _is_chain_page_border(contour, canvas_width, canvas_height):
            removed_count += 1
            border_chains.append(chain)
            border_contours.append(contour)
            logger.info(
                f"BORDER_REMOVAL_CLEAN | Identified page border chain with {len(contour)} points"
            )
        else:
            filtered_chains.append(chain)
            filtered_contours.append(contour)

    if removed_count > 0:
        logger.info(
            f"BORDER_REMOVAL_CLEAN | Found {removed_count} page border chain(s), "
            f"{len(filtered_chains)} non-border chains for scoring"
        )

    return filtered_chains, filtered_contours, removed_count, border_chains, border_contours


# ─── Main Cleanup Function ───────────────────────────────────────────────────

# Scoring thresholds (soft, not hard gates)
MIN_SCORE_TO_KEEP = 0.20  # Below this, chain is discarded
MIN_CONFIDENCE_WARNING = 0.45  # Below this, add low-confidence warning


def clean_blueprint_dxf(
    input_path: str,
    output_path: str,
    min_contour_length_mm: float = 50.0,
    close_gaps_mm: float = 1.0,
    keep_open_chains: bool = False,
    mode: CleanupMode = CleanupMode.REFINED,
) -> CleanResult:
    """
    Clean raw edge-to-dxf output to isolate body outline.

    Uses scoring-based selection instead of binary reject:
    - Scores all candidate chains on geometric signals
    - Keeps chains above MIN_SCORE_TO_KEEP threshold
    - Always returns best candidate even if low confidence
    - Warns on low confidence rather than failing

    Args:
        input_path: Path to raw DXF from extraction
        output_path: Path for cleaned DXF output
        min_contour_length_mm: Minimum contour length to keep
        close_gaps_mm: Maximum gap to close between endpoints
        keep_open_chains: Whether to keep open chains (not just closed loops)
        mode: CleanupMode.BASELINE for stable pre-grouping behavior,
              CleanupMode.REFINED for current logic with all improvements

    Returns:
        CleanResult with success status, SVG preview, and metrics
    """
    # Dispatch to appropriate implementation based on mode
    if mode == CleanupMode.BASELINE:
        return _clean_blueprint_baseline(
            input_path, output_path, min_contour_length_mm,
            close_gaps_mm, keep_open_chains
        )
    # Default: REFINED mode (current behavior)
    return _clean_blueprint_refined(
        input_path, output_path, min_contour_length_mm,
        close_gaps_mm, keep_open_chains
    )


def _clean_blueprint_refined(
    input_path: str,
    output_path: str,
    min_contour_length_mm: float,
    close_gaps_mm: float,
    keep_open_chains: bool,
) -> CleanResult:
    """
    REFINED mode: Current cleanup logic with all improvements.

    Features:
    - Surgical border removal before scoring
    - 5-tier fallback priority ladder
    - Body-likeness checks for fallback candidates
    """
    warnings: List[str] = []

    try:
        from ..cam.unified_dxf_cleaner import DXFCleaner, Chain, Point

        cleaner = DXFCleaner(
            min_contour_length_mm=0.0,  # Don't filter by length yet
            closure_tolerance=close_gaps_mm,
            keep_open_chains=True,  # Get all chains, filter by score
        )

        # Step 1: Extract raw chains without filtering
        chains, polyline_pts, original_count = cleaner.extract_chains(Path(input_path))
        total_chains = len(chains)

        logger.info(f"BLUEPRINT_CLEAN | extracted {total_chains} chains, {len(polyline_pts)} polylines")

        if total_chains == 0 and len(polyline_pts) == 0:
            return CleanResult(
                success=False,
                error="No chains or polylines found in DXF",
                original_entity_count=original_count,
                chains_found=0,
            )

        # Step 2: Convert chains to contours for scoring
        contours = [_chain_to_contour(c) for c in chains]

        # Also convert polylines to contours
        for pts in polyline_pts:
            arr = np.array(pts, dtype=np.float32).reshape(-1, 1, 2)
            contours.append(arr)
            # Create dummy chain for polylines (for writing later)
            dummy_chain = Chain(points=[Point(x, y) for x, y in pts])
            chains.append(dummy_chain)

        # Step 2.5: BORDER IDENTIFICATION (not removal)
        # Identify page borders but DON'T remove them yet.
        # If they're the ONLY option, we still need to return SOMETHING.
        # Border removal only happens if better candidates exist.
        canvas_w, canvas_h = _estimate_canvas_size(chains, [])
        non_border_chains, non_border_contours, border_count, border_chains, border_contours = \
            _remove_page_border_chains(chains, contours, canvas_w, canvas_h)

        # Decision: use non-border chains if available, else fall back to borders
        use_border_fallback = False
        if non_border_chains:
            # Good: we have non-border candidates
            scoring_chains = non_border_chains
            scoring_contours = non_border_contours
            # Re-estimate canvas without borders for better scoring
            canvas_w, canvas_h = _estimate_canvas_size(scoring_chains, [])
            logger.info(f"Using {len(scoring_chains)} non-border chains for scoring")
        elif border_chains:
            # Fallback: only borders exist, use them but warn
            scoring_chains = border_chains
            scoring_contours = border_contours
            use_border_fallback = True
            warnings.append(
                "Only page-border geometry found. Using border as best-effort fallback. "
                "This is likely not the instrument body."
            )
            logger.warning(
                f"BORDER_FALLBACK | No non-border chains found, using {len(border_chains)} "
                f"border chain(s) as fallback"
            )
        else:
            # No chains at all
            return CleanResult(
                success=False,
                error="No chains found in DXF",
                original_entity_count=original_count,
                chains_found=total_chains,
                warnings=warnings,
            )

        # Update chains/contours for scoring
        chains = scoring_chains
        contours = scoring_contours

        # Step 3: Score all contours (with ownership as weighted signal)
        ownership_fn = _create_ownership_fn(canvas_w, canvas_h)

        scoring_result = score_contours(
            contours,
            image_width=canvas_w,
            image_height=canvas_h,
            min_area_ratio=0.005,  # Very permissive for DXF (already filtered by edge detection)
            max_area_ratio=0.99,
            ownership_fn=ownership_fn,  # Body ownership as weighted signal
            debug=True,  # Get all candidates for selection
        )

        # Step 4: Select chains based on scores
        selected_chains: List = []
        discarded_short = 0
        discarded_open = 0
        discarded_low_score = 0

        # Build index mapping: scored candidate index → chain
        for candidate in scoring_result.candidates:
            idx = candidate.index
            if idx >= len(chains):
                continue

            chain = chains[idx]
            chain_len = chain.length()
            is_closed = chain.is_closed(close_gaps_mm)

            # Apply minimum length filter (still useful)
            if chain_len < min_contour_length_mm:
                discarded_short += 1
                continue

            # Apply closure filter unless keep_open_chains
            if not is_closed and not keep_open_chains:
                discarded_open += 1
                continue

            # Apply score threshold (soft, not hard)
            if candidate.score < MIN_SCORE_TO_KEEP:
                discarded_low_score += 1
                continue

            selected_chains.append((chain, candidate.score))

        # Sort by score descending
        selected_chains.sort(key=lambda x: x[1], reverse=True)

        # Step 5: Fallback - if nothing selected, use priority ladder
        # CRITICAL: Always return best-effort output if ANY chain exists
        # Selection confidence controls recommendation, NOT artifact existence
        # Page border is LAST RESORT - never pick it if any other candidate exists
        best_confidence = scoring_result.confidence
        fallback_used = False
        fallback_tier = 0
        fallback_reason = ""
        fallback_reject_reason = ""
        fallback_is_page_border = False

        if not selected_chains and chains:
            # Use priority ladder to select fallback
            fb_chain, fb_score, fb_tier, fb_candidate = _select_fallback_candidate(
                scoring_result,
                chains,
                min_contour_length_mm,
                close_gaps_mm,
                keep_open_chains,
            )

            if fb_chain is not None:
                selected_chains.append((fb_chain, fb_score))
                best_confidence = fb_score
                fallback_used = True
                fallback_tier = fb_tier
                fallback_reject_reason = fb_candidate.reject_reason if fb_candidate else ""
                fallback_is_page_border = fb_candidate.is_page_border if fb_candidate else False

                # Generate appropriate warning based on tier
                if fb_tier == 1:
                    fallback_reason = "non-rejected candidate selected via fallback"
                    warnings.append(
                        f"Falling back to best available contour (score={fb_score:.2f}) "
                        f"despite low confidence."
                    )
                elif fb_tier == 2:
                    fallback_reason = "rejected-for-score but structurally plausible"
                    warnings.append(
                        f"Falling back to structurally plausible contour (score={fb_score:.2f}, "
                        f"tier 2) despite rejection."
                    )
                elif fb_tier == 3:
                    fallback_reason = "rejected-for-geometry but not strip-like"
                    warnings.append(
                        f"Falling back to non-strip contour (score={fb_score:.2f}, tier 3) "
                        f"despite geometric rejection: {fallback_reject_reason}."
                    )
                elif fb_tier == 4:
                    fallback_reason = "weak structural plausibility, non-border"
                    warnings.append(
                        f"Falling back to weak but non-border contour (score={fb_score:.2f}, tier 4) "
                        f"despite rejection: {fallback_reject_reason}."
                    )
                elif fb_tier == 5:
                    fallback_reason = "page_border as last resort"
                    warnings.append(
                        "No contour passed minimum geometric sanity checks."
                    )
                    warnings.append(
                        f"Falling back to best available contour despite rejection: page_border."
                    )

        # Add scoring warnings
        warnings.extend(scoring_result.warnings)

        if best_confidence < MIN_CONFIDENCE_WARNING and selected_chains:
            warnings.append(
                f"Low confidence contour selection ({best_confidence:.2f}). "
                f"Review output before fabrication."
            )

        # Step 6: Write selected chains to output
        final_chains = [c for c, _ in selected_chains]
        contours_written = 0

        if final_chains:
            contours_written = cleaner.write_selected_chains(
                Path(output_path),
                final_chains,
                polyline_pts=None,  # Already included in chains
            )

        # Step 7: Generate SVG preview
        svg_preview = ""
        if final_chains:
            svg_preview = cleaner.generate_svg_preview(final_chains)

        logger.info(
            f"BLUEPRINT_CLEAN | scored {len(scoring_result.candidates)} candidates, "
            f"selected {len(final_chains)}, confidence={best_confidence:.2f}, "
            f"margin={scoring_result.winner_margin:.2f}"
        )

        return CleanResult(
            success=True,
            svg_preview=svg_preview,
            dxf_path=output_path,
            original_entity_count=original_count,
            cleaned_entity_count=contours_written,
            contours_found=contours_written,
            chains_found=total_chains,
            discarded_short=discarded_short,
            discarded_open=discarded_open,
            discarded_low_score=discarded_low_score,
            best_confidence=best_confidence,
            runner_up_score=scoring_result.runner_up_score,
            winner_margin=scoring_result.winner_margin,
            candidate_count=len(scoring_result.candidates),
            warnings=warnings,
            fallback_used=fallback_used,
            fallback_tier=fallback_tier,
            fallback_reason=fallback_reason,
            fallback_reject_reason=fallback_reject_reason,
            fallback_is_page_border=fallback_is_page_border,
        )

    except ImportError as e:
        logger.error(f"DXFCleaner not available: {e}")
        return CleanResult(success=False, error=f"DXFCleaner not available: {e}")
    except Exception as e:
        logger.exception(f"DXF cleanup failed: {e}")
        return CleanResult(success=False, error=str(e))


def _clean_blueprint_baseline(
    input_path: str,
    output_path: str,
    min_contour_length_mm: float,
    close_gaps_mm: float,
    keep_open_chains: bool,
) -> CleanResult:
    """
    BASELINE mode: Simpler pre-grouping behavior for stability/regression.

    This is the last useful end-to-end blueprint cleanup before:
    - Border removal at cleanup stage
    - 5-tier fallback priority ladder
    - Body-likeness penalties

    Behavior:
    - Scores ALL chains (no border removal)
    - Simple 2-pass fallback:
      1. Try chains passing length/closure filters
      2. Fallback to best regardless of filters
    - Returns same CleanResult shape as refined mode

    This mode exists for:
    - Regression comparison
    - Safe fallback when refined mode causes issues
    - Benchmark validation
    """
    warnings: List[str] = []
    warnings.append("Using BASELINE cleanup mode (pre-grouping behavior)")

    try:
        from ..cam.unified_dxf_cleaner import DXFCleaner, Chain, Point

        cleaner = DXFCleaner(
            min_contour_length_mm=0.0,
            closure_tolerance=close_gaps_mm,
            keep_open_chains=True,
        )

        # Step 1: Extract raw chains without filtering
        chains, polyline_pts, original_count = cleaner.extract_chains(Path(input_path))
        total_chains = len(chains)

        logger.info(f"BLUEPRINT_CLEAN_BASELINE | extracted {total_chains} chains, {len(polyline_pts)} polylines")

        if total_chains == 0 and len(polyline_pts) == 0:
            return CleanResult(
                success=False,
                error="No chains or polylines found in DXF",
                original_entity_count=original_count,
                chains_found=0,
                warnings=warnings,
            )

        # Step 2: Convert chains to contours for scoring
        contours = [_chain_to_contour(c) for c in chains]

        # Also convert polylines to contours
        for pts in polyline_pts:
            arr = np.array(pts, dtype=np.float32).reshape(-1, 1, 2)
            contours.append(arr)
            dummy_chain = Chain(points=[Point(x, y) for x, y in pts])
            chains.append(dummy_chain)

        # Step 3: Score ALL contours (NO border removal in baseline)
        canvas_w, canvas_h = _estimate_canvas_size(chains, [])
        ownership_fn = _create_ownership_fn(canvas_w, canvas_h)

        scoring_result = score_contours(
            contours,
            image_width=canvas_w,
            image_height=canvas_h,
            min_area_ratio=0.005,
            max_area_ratio=0.99,
            ownership_fn=ownership_fn,
            debug=True,
        )

        # Step 4: Select chains based on scores (simple thresholding)
        selected_chains: List = []
        discarded_short = 0
        discarded_open = 0
        discarded_low_score = 0

        for candidate in scoring_result.candidates:
            idx = candidate.index
            if idx >= len(chains):
                continue

            chain = chains[idx]
            chain_len = chain.length()
            is_closed = chain.is_closed(close_gaps_mm)

            if chain_len < min_contour_length_mm:
                discarded_short += 1
                continue

            if not is_closed and not keep_open_chains:
                discarded_open += 1
                continue

            if candidate.score < MIN_SCORE_TO_KEEP:
                discarded_low_score += 1
                continue

            selected_chains.append((chain, candidate.score))

        selected_chains.sort(key=lambda x: x[1], reverse=True)

        # Step 5: BASELINE FALLBACK - simple 2-pass, no tier system
        best_confidence = scoring_result.confidence
        fallback_used = False

        if not selected_chains and chains:
            # Pass 1: Try to find chain that passes length/closure filters
            for candidate in scoring_result.candidates:
                idx = candidate.index
                if idx >= len(chains):
                    continue
                chain = chains[idx]
                chain_len = chain.length()
                is_closed = chain.is_closed(close_gaps_mm)

                if chain_len >= min_contour_length_mm and (is_closed or keep_open_chains):
                    selected_chains.append((chain, candidate.score))
                    best_confidence = candidate.score
                    fallback_used = True
                    warnings.append(
                        f"Falling back to best available contour (score={candidate.score:.2f}) "
                        f"despite low confidence."
                    )
                    break

            # Pass 2: If still nothing, use absolute best regardless of filters
            if not selected_chains and scoring_result.candidates:
                best_candidate = scoring_result.candidates[0]
                idx = best_candidate.index
                if idx < len(chains):
                    chain = chains[idx]
                    selected_chains.append((chain, best_candidate.score))
                    best_confidence = best_candidate.score
                    fallback_used = True
                    warnings.append(
                        f"Using best available contour (score={best_candidate.score:.2f}) "
                        f"bypassing length/closure filters for review."
                    )

        # Add scoring warnings
        warnings.extend(scoring_result.warnings)

        if best_confidence < MIN_CONFIDENCE_WARNING and selected_chains:
            warnings.append(
                f"Low confidence contour selection ({best_confidence:.2f}). "
                f"Review output before fabrication."
            )

        # Step 6: Write selected chains to output
        final_chains = [c for c, _ in selected_chains]
        contours_written = 0

        if final_chains:
            contours_written = cleaner.write_selected_chains(
                Path(output_path),
                final_chains,
                polyline_pts=None,
            )

        # Step 7: Generate SVG preview
        svg_preview = ""
        if final_chains:
            svg_preview = cleaner.generate_svg_preview(final_chains)

        logger.info(
            f"BLUEPRINT_CLEAN_BASELINE | scored {len(scoring_result.candidates)} candidates, "
            f"selected {len(final_chains)}, confidence={best_confidence:.2f}, "
            f"margin={scoring_result.winner_margin:.2f}"
        )

        return CleanResult(
            success=True,
            svg_preview=svg_preview,
            dxf_path=output_path,
            original_entity_count=original_count,
            cleaned_entity_count=contours_written,
            contours_found=contours_written,
            chains_found=total_chains,
            discarded_short=discarded_short,
            discarded_open=discarded_open,
            discarded_low_score=discarded_low_score,
            best_confidence=best_confidence,
            runner_up_score=scoring_result.runner_up_score,
            winner_margin=scoring_result.winner_margin,
            candidate_count=len(scoring_result.candidates),
            warnings=warnings,
            # Baseline mode doesn't use the tier system
            fallback_used=fallback_used,
            fallback_tier=0,
            fallback_reason="baseline_simple_fallback" if fallback_used else "",
            fallback_reject_reason="",
            fallback_is_page_border=False,
        )

    except ImportError as e:
        logger.error(f"DXFCleaner not available: {e}")
        return CleanResult(success=False, error=f"DXFCleaner not available: {e}", warnings=warnings)
    except Exception as e:
        logger.exception(f"DXF cleanup failed: {e}")
        return CleanResult(success=False, error=str(e), warnings=warnings)


def _generate_svg_preview(dxf_path: str, cleaner) -> str:
    """
    Generate SVG preview from cleaned DXF file.

    Args:
        dxf_path: Path to cleaned DXF file
        cleaner: DXFCleaner instance for SVG generation

    Returns:
        SVG string or empty string on failure
    """
    try:
        import ezdxf
        from ..cam.unified_dxf_cleaner import Chain, Point

        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        chains = []
        for e in msp:
            if e.dxftype() == "LWPOLYLINE":
                points = [Point(x, y) for x, y in e.get_points("xy")]
                if points:
                    chains.append(Chain(points=points))

        if chains:
            return cleaner.generate_svg_preview(chains)

    except Exception as e:
        logger.warning(f"SVG preview generation failed: {e}")

    return ""


def validate_cleanup_result(result: CleanResult) -> tuple[bool, list[str]]:
    """
    Validate cleanup result for downstream use.

    Follows tolerance philosophy:
    - FAIL only when no contours at all
    - WARN + return for low confidence results
    - RETURN silently for good confidence

    Args:
        result: CleanResult from clean_blueprint_dxf

    Returns:
        (is_valid, warnings) tuple
    """
    warnings = list(result.warnings)  # Include any warnings from scoring

    if not result.success:
        return False, [result.error or "Cleanup failed"]

    if result.contours_found == 0:
        # Build detailed failure message
        discard_details = []
        if result.discarded_short > 0:
            discard_details.append(f"{result.discarded_short} too short")
        if result.discarded_open > 0:
            discard_details.append(f"{result.discarded_open} open")
        if result.discarded_low_score > 0:
            discard_details.append(f"{result.discarded_low_score} low score")

        discard_msg = ", ".join(discard_details) if discard_details else "unknown reason"
        warnings.append(
            f"No contours survived filtering. "
            f"Found {result.chains_found} chains but 0 passed "
            f"(discarded: {discard_msg})."
        )
        return False, warnings

    if not result.svg_preview or len(result.svg_preview) < 50:
        warnings.append("SVG preview is missing or too small")

    if result.cleaned_entity_count == 0:
        warnings.append("No entities in cleaned output")
        return False, warnings

    # Low confidence is a warning, not a failure
    if result.best_confidence < MIN_CONFIDENCE_WARNING:
        # Warning already added during cleanup, don't duplicate
        pass

    return True, warnings
