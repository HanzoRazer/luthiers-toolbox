"""
Contour Recommendation Module
=============================

Decides whether a selected contour is trustworthy enough for product success.

Architecture:
    contour_scoring.py  -> which candidate is best (selection)
    contour_recommendation.py -> can the product trust that winner (recommendation)

The same selected contour can be:
    - acceptable in blueprint mode
    - review in permissive mode
    - reject in photo mode

Recommendation consumes:
    - selected candidate + score
    - runner-up / margin
    - mode (blueprint vs photo)
    - warnings
    - artifact validation state
    - scale reliability
    - mode-specific signals (ownership for photo)

Author: Production Shop
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class RecommendationAction(str, Enum):
    """Product acceptance decision."""
    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"


class ProcessingMode(str, Enum):
    """Pipeline mode affects recommendation thresholds."""
    BLUEPRINT = "blueprint"
    PHOTO = "photo"


@dataclass
class SelectionResult:
    """Output from contour selection (scoring layer)."""
    candidate_count: int = 0
    selected_index: Optional[int] = None
    selection_score: float = 0.0
    runner_up_score: float = 0.0
    winner_margin: float = 0.0
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_count": self.candidate_count,
            "selected_index": self.selected_index,
            "selection_score": round(self.selection_score, 3),
            "runner_up_score": round(self.runner_up_score, 3),
            "winner_margin": round(self.winner_margin, 3),
            "reasons": self.reasons,
        }


@dataclass
class Recommendation:
    """Product acceptance recommendation."""
    action: RecommendationAction = RecommendationAction.REJECT
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
        }


@dataclass
class RecommendationInput:
    """All signals consumed by the recommendation layer."""
    # Selection results
    selection: SelectionResult

    # Mode
    mode: ProcessingMode = ProcessingMode.BLUEPRINT

    # Artifact validation
    svg_valid: bool = False
    dxf_valid: bool = False

    # Warnings from pipeline
    warnings: List[str] = field(default_factory=list)

    # Photo-specific: ownership score (0.0-1.0)
    ownership_score: Optional[float] = None

    # Scale reliability
    scale_source: str = "estimated"  # "spec", "calibration", "estimated"

    # Structural signals
    aspect_ratio: float = 1.0  # width/height of selected contour
    expected_aspect_range: tuple[float, float] = (0.5, 2.5)  # for instrument bodies

    # Hard-fail detection flags
    page_span_detected: bool = False
    extreme_fragmentation: bool = False
    multi_path_ambiguity: bool = False
    spec_forced_rescue: bool = False
    mode_classifier_mismatch: bool = False


# ─── Threshold Configuration ────────────────────────────────────────────────

# Blueprint thresholds (more permissive)
BLUEPRINT_ACCEPT_SCORE = 0.70
BLUEPRINT_ACCEPT_MARGIN = 0.12
BLUEPRINT_REVIEW_SCORE = 0.45

# Photo thresholds (stricter)
PHOTO_ACCEPT_SCORE = 0.75
PHOTO_ACCEPT_MARGIN = 0.15
PHOTO_ACCEPT_OWNERSHIP = 0.75
PHOTO_REVIEW_SCORE = 0.55
PHOTO_REVIEW_OWNERSHIP = 0.60
PHOTO_REJECT_OWNERSHIP = 0.60  # Hard gate

# Aspect ratio bounds (instrument bodies)
ASPECT_ERROR_THRESHOLD = 2.0  # ratio outside expected range by this factor


# ─── Hard-Fail Detection ────────────────────────────────────────────────────

def _detect_hard_fails(inp: RecommendationInput) -> List[str]:
    """
    Detect conditions that override score and force rejection.

    These are structural failures that mean the geometry is wrong,
    regardless of how "good" the selection score looks.
    """
    fails: List[str] = []

    # Artifact invalidity
    if not inp.svg_valid and not inp.dxf_valid:
        fails.append("No valid artifacts produced")

    # Page-span / page-border capture
    if inp.page_span_detected:
        fails.append("Page-span contour detected (likely captured page border)")

    # Extreme aspect mismatch
    min_aspect, max_aspect = inp.expected_aspect_range
    if inp.aspect_ratio < min_aspect / ASPECT_ERROR_THRESHOLD:
        fails.append(f"Extreme aspect mismatch: {inp.aspect_ratio:.2f} (expected {min_aspect}-{max_aspect})")
    elif inp.aspect_ratio > max_aspect * ASPECT_ERROR_THRESHOLD:
        fails.append(f"Extreme aspect mismatch: {inp.aspect_ratio:.2f} (expected {min_aspect}-{max_aspect})")

    # Fragmentation at structural boundaries
    if inp.extreme_fragmentation:
        fails.append("Contour fragmentation detected at structural boundary")

    # Multi-path ambiguity when single outline expected
    if inp.multi_path_ambiguity:
        fails.append("Multiple peer contours with similar scores (ambiguous selection)")

    # Spec-forced rescue with low quality
    if inp.spec_forced_rescue and inp.selection.selection_score < 0.50:
        fails.append("Spec-forced rescue required with low shape quality")

    # Mode classifier mismatch
    if inp.mode_classifier_mismatch:
        fails.append("Selected contour inconsistent with input mode classifier")

    return fails


def _check_severe_warnings(warnings: List[str]) -> bool:
    """Check if warnings contain severe structural issues."""
    severe_patterns = [
        "no contour",
        "too_small",
        "too_large",
        "page border",
        "fragmentation",
        "invalid",
        "failed",
    ]
    for w in warnings:
        w_lower = w.lower()
        for pattern in severe_patterns:
            if pattern in w_lower:
                return True
    return False


# ─── Recommendation Logic ───────────────────────────────────────────────────

def recommend_blueprint(inp: RecommendationInput) -> Recommendation:
    """
    Recommendation policy for blueprint mode.

    More permissive than photo mode because blueprints are cleaner
    and users can work with low-confidence results.
    """
    reasons: List[str] = []

    # Check hard-fails first
    hard_fails = _detect_hard_fails(inp)
    if hard_fails:
        return Recommendation(
            action=RecommendationAction.REJECT,
            confidence=0.0,
            reasons=hard_fails,
        )

    sel = inp.selection
    has_severe_warnings = _check_severe_warnings(inp.warnings)
    artifacts_valid = inp.svg_valid or inp.dxf_valid

    # Accept criteria
    if (
        sel.selection_score >= BLUEPRINT_ACCEPT_SCORE
        and sel.winner_margin >= BLUEPRINT_ACCEPT_MARGIN
        and not has_severe_warnings
        and artifacts_valid
    ):
        confidence = min(sel.selection_score, sel.winner_margin * 5)  # margin contributes
        return Recommendation(
            action=RecommendationAction.ACCEPT,
            confidence=confidence,
            reasons=["Strong selection with clear margin"],
        )

    # Review criteria
    if (
        sel.selection_score >= BLUEPRINT_REVIEW_SCORE
        and artifacts_valid
    ):
        reasons.append("Selection score below accept threshold")
        if sel.winner_margin < BLUEPRINT_ACCEPT_MARGIN:
            reasons.append(f"Winner margin weak ({sel.winner_margin:.2f} < {BLUEPRINT_ACCEPT_MARGIN})")
        if has_severe_warnings:
            reasons.append("Severe warnings present")

        confidence = sel.selection_score * 0.7  # Discount for review
        return Recommendation(
            action=RecommendationAction.REVIEW,
            confidence=confidence,
            reasons=reasons,
        )

    # Reject
    reasons.append(f"Selection score below review threshold ({sel.selection_score:.2f} < {BLUEPRINT_REVIEW_SCORE})")
    if not artifacts_valid:
        reasons.append("No valid artifacts")

    return Recommendation(
        action=RecommendationAction.REJECT,
        confidence=0.0,
        reasons=reasons,
    )


def recommend_photo(inp: RecommendationInput) -> Recommendation:
    """
    Recommendation policy for photo/AI mode.

    Stricter than blueprint mode because photos have more noise
    and incorrect exports are more harmful.
    """
    reasons: List[str] = []

    # Check hard-fails first
    hard_fails = _detect_hard_fails(inp)
    if hard_fails:
        return Recommendation(
            action=RecommendationAction.REJECT,
            confidence=0.0,
            reasons=hard_fails,
        )

    sel = inp.selection
    ownership = inp.ownership_score or 0.0
    has_severe_warnings = _check_severe_warnings(inp.warnings)
    artifacts_valid = inp.svg_valid or inp.dxf_valid

    # Ownership hard gate (photo mode's defining constraint)
    if ownership < PHOTO_REJECT_OWNERSHIP:
        return Recommendation(
            action=RecommendationAction.REJECT,
            confidence=0.0,
            reasons=[f"Ownership score below threshold ({ownership:.2f} < {PHOTO_REJECT_OWNERSHIP})"],
        )

    # Accept criteria (strict)
    if (
        sel.selection_score >= PHOTO_ACCEPT_SCORE
        and sel.winner_margin >= PHOTO_ACCEPT_MARGIN
        and ownership >= PHOTO_ACCEPT_OWNERSHIP
        and not has_severe_warnings
        and artifacts_valid
    ):
        # Confidence combines selection and ownership
        confidence = (sel.selection_score * 0.6) + (ownership * 0.4)
        return Recommendation(
            action=RecommendationAction.ACCEPT,
            confidence=confidence,
            reasons=["Strong selection with high ownership confidence"],
        )

    # Review criteria
    if (
        sel.selection_score >= PHOTO_REVIEW_SCORE
        and ownership >= PHOTO_REVIEW_OWNERSHIP
        and artifacts_valid
    ):
        if sel.selection_score < PHOTO_ACCEPT_SCORE:
            reasons.append(f"Selection score below accept threshold ({sel.selection_score:.2f} < {PHOTO_ACCEPT_SCORE})")
        if sel.winner_margin < PHOTO_ACCEPT_MARGIN:
            reasons.append(f"Winner margin weak ({sel.winner_margin:.2f} < {PHOTO_ACCEPT_MARGIN})")
        if ownership < PHOTO_ACCEPT_OWNERSHIP:
            reasons.append(f"Ownership below accept threshold ({ownership:.2f} < {PHOTO_ACCEPT_OWNERSHIP})")
        if has_severe_warnings:
            reasons.append("Severe warnings present")

        confidence = (sel.selection_score * 0.5) + (ownership * 0.3)
        return Recommendation(
            action=RecommendationAction.REVIEW,
            confidence=confidence,
            reasons=reasons,
        )

    # Reject
    if sel.selection_score < PHOTO_REVIEW_SCORE:
        reasons.append(f"Selection score below review threshold ({sel.selection_score:.2f} < {PHOTO_REVIEW_SCORE})")
    if not artifacts_valid:
        reasons.append("No valid artifacts")

    return Recommendation(
        action=RecommendationAction.REJECT,
        confidence=0.0,
        reasons=reasons,
    )


# ─── Public API ─────────────────────────────────────────────────────────────

def recommend(inp: RecommendationInput) -> Recommendation:
    """
    Main entry point for recommendation.

    Routes to mode-specific policy based on input.mode.
    """
    if inp.mode == ProcessingMode.PHOTO:
        return recommend_photo(inp)
    else:
        return recommend_blueprint(inp)


def build_selection_result(
    candidates: List[Any],
    selected_index: Optional[int],
    scores: List[float],
    reasons: Optional[List[str]] = None,
) -> SelectionResult:
    """
    Build SelectionResult from scoring output.

    Helper for orchestrators to construct the selection block
    from contour_scoring results.
    """
    if not scores:
        return SelectionResult(
            candidate_count=len(candidates),
            selected_index=None,
            selection_score=0.0,
            runner_up_score=0.0,
            winner_margin=0.0,
            reasons=reasons or ["No candidates scored"],
        )

    sorted_scores = sorted(scores, reverse=True)
    best_score = sorted_scores[0] if sorted_scores else 0.0
    runner_up = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
    margin = best_score - runner_up

    return SelectionResult(
        candidate_count=len(candidates),
        selected_index=selected_index,
        selection_score=best_score,
        runner_up_score=runner_up,
        winner_margin=margin,
        reasons=reasons or [],
    )
