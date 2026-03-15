"""
Geometry Coach V1 — Guarded Contour-Stage Rerun Coach
=====================================================

First agentic loop: decides whether to rerun contour assembly/merge
parameters based on ContourStageResult diagnostics.

Scope (v1 — narrow):
  - Only contour assembly + merge parameter adjustment
  - NOT body isolation, calibration, or background removal

Guardrails:
  - max_retries = 2
  - Monotonic improvement required (ε = 0.03)
  - No silent downgrade — worse reruns discarded
  - Terminal review state if still below export threshold

Usage:
    from geometry_coach import GeometryCoachV1
    from contour_stage import ContourStage, StageParams

    coach = GeometryCoachV1()
    stage = ContourStage()
    result = stage.run(edges, alpha_mask, body_region, calibration, family, shape)
    final = coach.evaluate(result, stage, edges, alpha_mask, body_region,
                           calibration, family, shape)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from photo_vectorizer_v2 import (
    BodyRegion,
    CalibrationResult,
    ContourStageResult,
)
from contour_stage import ContourStage, StageParams

logger = logging.getLogger(__name__)


# ── Coach configuration ────────────────────────────────────────────────────

@dataclass
class CoachConfig:
    """Tunable coach parameters."""
    target_threshold: float = 0.65
    max_retries: int = 2
    improvement_epsilon: float = 0.03
    # Merge profile variants to try on rerun
    merge_profiles: List[StageParams] = field(default_factory=list)

    def __post_init__(self):
        if not self.merge_profiles:
            self.merge_profiles = _default_merge_profiles()


def _default_merge_profiles() -> List[StageParams]:
    """Alternative merge profiles for rerun attempts."""
    return [
        # Profile 1: smaller close kernel, tighter fragment filter
        StageParams(
            merge_max_close_px=60,
            merge_min_fragment_area=3000.0,
            merge_body_overlap_min=0.50,
        ),
        # Profile 2: larger kernel, relaxed overlap
        StageParams(
            merge_max_close_px=180,
            merge_min_fragment_area=1500.0,
            merge_body_overlap_min=0.35,
        ),
    ]


# ── Coach decision record ─────────────────────────────────────────────────

@dataclass
class CoachDecision:
    """Record of a coaching evaluation."""
    action_taken: str  # "accepted_original", "accepted_rerun", "review_required"
    original_score: float
    final_score: float
    retries_attempted: int
    retry_scores: List[float] = field(default_factory=list)
    retry_profiles_used: List[int] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


# ── The coach ──────────────────────────────────────────────────────────────

class GeometryCoachV1:
    """
    First-generation geometry coach.

    Inspects ContourStageResult, decides whether to request a rerun
    of the contour stage with alternate merge parameters.
    """

    def __init__(self, config: Optional[CoachConfig] = None):
        self.config = config or CoachConfig()

    def should_retry(self, result: ContourStageResult) -> bool:
        """
        Decide whether a rerun is worth attempting.

        Triggers when:
          - best_score < target_threshold
          - AND merge occurred (merge_result is not None)
          - AND pre/post candidates disagree materially (score diff > 0.05)
        """
        if result.best_score >= self.config.target_threshold:
            return False

        if result.merge_result is None:
            return False

        # Check if pre/post merge scoring disagrees
        if not result.contour_scores_pre or not result.contour_scores_post:
            return False

        best_pre = max(s.score for s in result.contour_scores_pre)
        best_post = max(s.score for s in result.contour_scores_post)

        if abs(best_pre - best_post) > 0.05:
            return True

        # Also trigger if merge worsened dimension plausibility
        best_pre_cs = max(result.contour_scores_pre, key=lambda s: s.score)
        best_post_cs = max(result.contour_scores_post, key=lambda s: s.score)

        completeness_improved = (
            best_post_cs.completeness > best_pre_cs.completeness)
        dims_worsened = (
            best_post_cs.dimension_plausibility
            < best_pre_cs.dimension_plausibility - 0.05)
        aspect_worsened = (
            best_pre_cs.aspect_ratio_ok and not best_post_cs.aspect_ratio_ok)

        if completeness_improved and (dims_worsened or aspect_worsened):
            return True

        return False

    def evaluate(
        self,
        initial_result: ContourStageResult,
        stage: ContourStage,
        edges: np.ndarray,
        alpha_mask: np.ndarray,
        body_region: Optional[BodyRegion],
        calibration: CalibrationResult,
        family: str,
        image_shape: Tuple[int, int],
    ) -> Tuple[ContourStageResult, CoachDecision]:
        """
        Evaluate a stage result and optionally rerun with alternate params.

        Returns the best ContourStageResult and a CoachDecision record.
        """
        cfg = self.config
        decision_notes: List[str] = []
        retry_scores: List[float] = []
        retry_profiles: List[int] = []

        if not self.should_retry(initial_result):
            action = "accepted_original"
            if initial_result.best_score >= cfg.target_threshold:
                decision_notes.append(
                    f"Score {initial_result.best_score:.3f} meets "
                    f"target {cfg.target_threshold}")
            else:
                decision_notes.append(
                    "Below target but no rerun trigger (no merge or "
                    "pre/post agreement)")

            return initial_result, CoachDecision(
                action_taken=action,
                original_score=initial_result.best_score,
                final_score=initial_result.best_score,
                retries_attempted=0,
                notes=decision_notes,
            )

        decision_notes.append(
            f"Score {initial_result.best_score:.3f} below target "
            f"{cfg.target_threshold} — attempting reruns")

        best_result = initial_result
        best_score = initial_result.best_score
        retries = 0

        for i, profile in enumerate(cfg.merge_profiles[:cfg.max_retries]):
            retries += 1
            logger.info(
                f"GeometryCoachV1: retry {retries}/{cfg.max_retries} "
                f"with profile {i}")

            rerun_result = stage.run(
                edges=edges,
                alpha_mask=alpha_mask,
                body_region=body_region,
                calibration=calibration,
                family=family,
                image_shape=image_shape,
                params=profile,
            )

            new_score = rerun_result.best_score
            retry_scores.append(new_score)
            retry_profiles.append(i)

            # Guard 2: monotonic improvement
            if new_score > best_score + cfg.improvement_epsilon:
                decision_notes.append(
                    f"Retry {retries} improved: "
                    f"{best_score:.3f} -> {new_score:.3f} "
                    f"(+{new_score - best_score:.3f})")
                best_result = rerun_result
                best_score = new_score
            else:
                # Guard 3: no silent downgrade
                decision_notes.append(
                    f"Retry {retries} not better: "
                    f"{new_score:.3f} vs {best_score:.3f} — discarded")

        # Determine final action
        if best_score > initial_result.best_score + cfg.improvement_epsilon:
            action = "accepted_rerun"
            decision_notes.append(
                f"Rerun accepted: {initial_result.best_score:.3f} -> "
                f"{best_score:.3f}")
        else:
            # Guard 4: terminal review state
            action = "review_required" if best_score < cfg.target_threshold \
                else "accepted_original"
            if action == "review_required":
                best_result.recommended_next_action = "manual_review_required"
                decision_notes.append(
                    f"After {retries} retries, best score "
                    f"{best_score:.3f} still below target — "
                    f"review required")
            else:
                decision_notes.append("Original result retained")

        return best_result, CoachDecision(
            action_taken=action,
            original_score=initial_result.best_score,
            final_score=best_score,
            retries_attempted=retries,
            retry_scores=retry_scores,
            retry_profiles_used=retry_profiles,
            notes=decision_notes,
        )
