"""
Tests for GeometryCoachV2 routing rules.

Verifies:
  - lower-bout missing  → rerun_body_isolation  (Rule A)
  - border contact       → rerun_body_isolation  (Rule B)
  - merge disagreement   → rerun_contour_stage   (Rule C)
  - retries exhausted    → manual_review_required
"""

import pytest
import types
from dataclasses import dataclass

from body_isolation_result import (
    BodyIsolationResult,
    BodyIsolationSignalBreakdown,
)
from geometry_coach_v2 import GeometryCoachV2, CoachV2Config


# ── Stubs ───────────────────────────────────────────────────────────────────


@dataclass
class _BodyRegionStub:
    """Mimics the real BodyRegion with the fields the coach touches."""
    x: int = 100
    y: int = 50
    width: int = 300
    height: int = 200
    confidence: float = 0.7
    height_px: int = 200
    width_px: int = 300
    height_mm: float = 0.0
    width_mm: float = 0.0


@dataclass
class _ScoreStub:
    """Mimics ContourScore — only .score is used by _contour_retry_worthwhile."""
    score: float = 0.0


class _ContourResultStub:
    """
    Minimal ContourStageResult-compatible stub.

    Only the fields inspected by GeometryCoachV2.decide() and
    _contour_retry_worthwhile() are populated.
    """

    def __init__(
        self,
        *,
        best_score=0.60,
        pre_scores=None,
        post_scores=None,
        issues=None,
    ):
        self.best_score = best_score
        self.contour_scores_pre = pre_scores or []
        self.contour_scores_post = post_scores or []
        self.export_block_issues = issues or []
        self.export_blocked = False
        self.block_reason = None


# ── Helpers ─────────────────────────────────────────────────────────────────


def make_body_result(
    *,
    completeness=0.50,
    lower_bout=False,
    border=False,
):
    r = BodyIsolationResult(
        body_bbox_px=(100, 50, 300, 200),
        body_region=_BodyRegionStub(),
        confidence=0.7,
        completeness_score=completeness,
        lower_bout_missing_likely=lower_bout,
        border_contact_likely=border,
        score_breakdown=BodyIsolationSignalBreakdown(
            hull_coverage=0.7,
            vertical_extent_ratio=0.7,
            width_stability=0.7,
            border_contact_penalty=0.6 if border else 0.0,
            center_alignment=0.8,
            lower_bout_presence=0.2 if lower_bout else 0.8,
        ),
    )
    if lower_bout:
        r.add_issue(
            "lower_bout_missing_likely",
            "Body isolation likely under-captured the lower bout.",
        )
    if border:
        r.add_issue(
            "border_contact_likely",
            "Body isolation touches image border; page edge or crop contamination possible.",
        )
    return r


def make_contour_result(
    *,
    best_score=0.60,
    pre_best=0.60,
    post_best=0.60,
    issues=None,
):
    return _ContourResultStub(
        best_score=best_score,
        pre_scores=[_ScoreStub(score=pre_best)],
        post_scores=[_ScoreStub(score=post_best)],
        issues=issues or [],
    )


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def coach():
    return GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            contour_target_threshold=0.80,
            body_isolation_review_threshold=0.45,
            severe_border_penalty_threshold=0.5,
        )
    )


# ── Rule A: lower bout missing → rerun_body_isolation ───────────────────────


def test_lower_bout_missing_requests_rerun_body_isolation(coach):
    body = make_body_result(completeness=0.40, lower_bout=True)
    contour = make_contour_result(best_score=0.58, pre_best=0.58, post_best=0.58)

    decision = coach.decide(
        body_result=body,
        contour_result=contour,
        retry_count=0,
    )

    assert decision.action == "rerun_body_isolation"
    assert "lower bout" in decision.reason.lower()
    assert decision.body_retry_params is not None


# ── Rule B: border contact → rerun_body_isolation ───────────────────────────


def test_border_contact_requests_rerun_body_isolation(coach):
    body = make_body_result(completeness=0.42, border=True)
    contour = make_contour_result(best_score=0.62, pre_best=0.62, post_best=0.62)

    decision = coach.decide(
        body_result=body,
        contour_result=contour,
        retry_count=0,
    )

    assert decision.action == "rerun_body_isolation"
    assert "border" in decision.reason.lower() or "crop" in decision.reason.lower()
    assert decision.body_retry_params is not None


# ── Rule C: merge disagreement → rerun_contour_stage ────────────────────────


def test_merge_disagreement_requests_rerun_contour_stage(coach):
    """Pre/post score gap > 0.08 triggers contour-only retry."""
    body = make_body_result(completeness=0.72)
    contour = make_contour_result(
        best_score=0.64,
        pre_best=0.74,
        post_best=0.61,
        issues=["dimension plausibility weak"],
    )

    decision = coach.decide(
        body_result=body,
        contour_result=contour,
        retry_count=0,
    )

    assert decision.action == "rerun_contour_stage"
    # contour_retry_params may be None if no profiles are configured
    assert decision.contour_retry_params is not None or coach.config.contour_retry_profiles == []


# ── Exhausted retries → manual_review_required ──────────────────────────────


def test_retries_exhaust_to_manual_review(coach):
    body = make_body_result(completeness=0.30, lower_bout=True)
    contour = make_contour_result(best_score=0.20, pre_best=0.20, post_best=0.20)

    decision = coach.decide(
        body_result=body,
        contour_result=contour,
        retry_count=coach.config.max_retries,
    )

    assert decision.action == "manual_review_required"


# ── Accept path (healthy scores) ────────────────────────────────────────────


def test_healthy_scores_accept(coach):
    body = make_body_result(completeness=0.88)
    contour = make_contour_result(best_score=0.85, pre_best=0.85, post_best=0.85)

    decision = coach.decide(
        body_result=body,
        contour_result=contour,
        retry_count=0,
    )

    assert decision.action == "accept"


def test_contour_retry_worthwhile_returns_false_when_only_best_score_present():
    """
    Regression: older ContourStageResult stubs may only expose best_score
    and omit contour_scores_pre, contour_scores_post, export_block_issues.
    _contour_retry_worthwhile() must fail closed and return False.
    """
    contour_result = types.SimpleNamespace(
        best_score=0.62,
        # intentionally missing:
        # contour_scores_pre
        # contour_scores_post
        # export_block_issues
    )

    assert GeometryCoachV2._contour_retry_worthwhile(contour_result) is False
