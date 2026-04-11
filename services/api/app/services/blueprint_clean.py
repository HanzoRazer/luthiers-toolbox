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

Author: Production Shop
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from .contour_scoring import score_contours, ContourSelectionResult

logger = logging.getLogger(__name__)


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
    error: str = ""
    warnings: list[str] = field(default_factory=list)


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

    Returns:
        CleanResult with success status, SVG preview, and metrics
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

        # Step 3: Score all contours (with ownership as weighted signal)
        canvas_w, canvas_h = _estimate_canvas_size(chains, [])
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

        # Step 5: Fallback - if nothing selected, use best available
        best_confidence = scoring_result.confidence
        if not selected_chains and chains:
            # Find best chain that passes length/closure filters
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
                    warnings.append(
                        f"Falling back to best available contour (score={candidate.score:.2f}) "
                        f"despite low confidence."
                    )
                    break

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
            f"selected {len(final_chains)}, confidence={best_confidence:.2f}"
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
            warnings=warnings,
        )

    except ImportError as e:
        logger.error(f"DXFCleaner not available: {e}")
        return CleanResult(success=False, error=f"DXFCleaner not available: {e}")
    except Exception as e:
        logger.exception(f"DXF cleanup failed: {e}")
        return CleanResult(success=False, error=str(e))


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
