"""
Tests for GeometryCoachV2 retry diagnostics instrumentation.

Verifies:
  - Accepted retry appends one retry_attempts entry with positive score_delta
  - Baseline-elected contour skips retry (stable election guard)
"""
from __future__ import annotations

import types
from dataclasses import dataclass

from body_isolation_result import (
    BodyIsolationResult,
    BodyIsolationSignalBreakdown,
)
from body_isolation_stage import BodyIsolationParams
from geometry_coach_v2 import GeometryCoachV2, CoachV2Config


# ── Stubs ───────────────────────────────────────────────────────────────────


@dataclass
class _BodyRegionStub:
    x: int = 100
    y: int = 50
    width: int = 300
    height: int = 200
    confidence: float = 0.7
    height_px: int = 200
    width_px: int = 300
    height_mm: float = 0.0
    width_mm: float = 0.0


class _ContourResultStub:
    def __init__(
        self,
        *,
        best_score: float,
        elected_source: str = "pre_merge_guarded",
        pre_scores=None,
        post_scores=None,
        issues=None,
        diagnostics=None,
        ownership_score=None,
        ownership_ok=None,
    ):
        self.best_score = best_score
        self.elected_source = elected_source
        self.contour_scores_pre = pre_scores or []
        self.contour_scores_post = post_scores or []
        self.export_block_issues = issues or []
        self.export_blocked = False
        self.block_reason = None
        self.recommended_next_action = None
        self.ownership_score = ownership_score
        self.ownership_ok = ownership_ok
        self.diagnostics = diagnostics if diagnostics is not None else {}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_body_result(
    *,
    completeness: float,
    lower_bout: bool = False,
    border: bool = False,
) -> BodyIsolationResult:
    r = BodyIsolationResult(
        body_bbox_px=(100, 50, 300, 200),
        body_region=_BodyRegionStub(),
        confidence=0.75,
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
    return r


# ── Stable-election guard ───────────────────────────────────────────────────


def test_stable_post_merge_election_skips_retry():
    """When elected_source is 'post_merge' (stable baseline), no retry."""
    contour = _ContourResultStub(
        best_score=0.55,
        elected_source="post_merge",
        issues=["dimension plausibility weak"],
    )
    assert GeometryCoachV2._contour_retry_worthwhile(contour) is False


def test_stable_pre_merge_election_skips_retry():
    """When elected_source is 'pre_merge' (stable baseline), no retry."""
    contour = _ContourResultStub(
        best_score=0.55,
        elected_source="pre_merge",
        issues=["dimension plausibility weak"],
    )
    assert GeometryCoachV2._contour_retry_worthwhile(contour) is False


def test_guarded_election_allows_retry():
    """When elected_source is 'pre_merge_guarded', retry logic proceeds."""
    contour = _ContourResultStub(
        best_score=0.55,
        elected_source="pre_merge_guarded",
        issues=["dimension plausibility weak"],
    )
    assert GeometryCoachV2._contour_retry_worthwhile(contour) is True


def test_missing_elected_source_allows_retry():
    """Older stubs without elected_source do not short-circuit."""
    contour = types.SimpleNamespace(
        best_score=0.55,
        contour_scores_pre=[],
        contour_scores_post=[],
        export_block_issues=["dimension plausibility weak"],
    )
    assert GeometryCoachV2._contour_retry_worthwhile(contour) is True


# ── Retry diagnostics instrumentation ───────────────────────────────────────


def test_accepted_retry_records_retry_attempt_with_positive_score_delta():
    """An accepted body-isolation retry records one retry_attempts entry."""
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            body_isolation_review_threshold=0.45,
            contour_target_threshold=0.80,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
            ],
            contour_retry_profiles=[],
        )
    )

    original_body = _make_body_result(completeness=0.40, lower_bout=True)
    original_contour = _ContourResultStub(
        best_score=0.56,
        ownership_score=0.39,
        ownership_ok=False,
    )

    improved_body = _make_body_result(completeness=0.62, lower_bout=False)
    improved_contour = _ContourResultStub(
        best_score=0.71,
        ownership_score=0.66,
        ownership_ok=True,
    )

    body_stage_runner = types.SimpleNamespace(
        run=lambda *args, **kwargs: improved_body,
    )
    contour_stage_runner = types.SimpleNamespace(
        run=lambda *args, **kwargs: improved_contour,
    )

    current_body, current_contour, decision = coach.evaluate(
        body_stage_runner=body_stage_runner,
        contour_stage_runner=contour_stage_runner,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="solid_body",
        geometry_authority=None,
        contour_inputs={
            "edges": None,
            "alpha_mask": None,
            "calibration": types.SimpleNamespace(mm_per_pixel=1.0),
            "family": "solid_body",
            "image_shape": (300, 200),
            "params": types.SimpleNamespace(),
        },
        body_result=original_body,
        contour_result=original_contour,
    )

    assert current_body is improved_body
    assert current_contour is improved_contour
    assert decision.action in ("accept", "rerun_body_isolation")

    retry_attempts = current_contour.diagnostics.get("retry_attempts", [])
    assert len(retry_attempts) == 1

    attempt = retry_attempts[0]
    assert attempt["retry_reason"]
    assert attempt["retry_profile_used"] == "lower_bout_recovery"
    assert attempt["retry_iteration"] == 1
    assert attempt["score_before"] == 0.56
    assert attempt["score_after"] == 0.71
    assert attempt["score_delta"] > 0
    assert attempt["ownership_score_before"] == 0.39
    assert attempt["ownership_score_after"] == 0.66
    assert attempt["ownership_score_delta"] > 0
    assert attempt["ownership_ok_before"] is False
    assert attempt["ownership_ok_after"] is True


def test_rejected_retry_records_retry_attempt_with_negative_score_delta_and_preserves_original():
    """A rejected body-isolation retry records one entry and preserves originals."""
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            body_isolation_review_threshold=0.45,
            contour_target_threshold=0.80,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
            ],
            contour_retry_profiles=[],
        )
    )

    original_body = _make_body_result(completeness=0.40, lower_bout=True)
    original_contour = _ContourResultStub(
        best_score=0.56,
        ownership_score=0.44,
        ownership_ok=False,
    )

    # Retry makes things worse: should be rejected by monotonic improvement gate
    worse_body = _make_body_result(completeness=0.43, lower_bout=False)
    worse_contour = _ContourResultStub(
        best_score=0.50,
        ownership_score=0.41,
        ownership_ok=False,
    )

    body_stage_runner = types.SimpleNamespace(
        run=lambda *args, **kwargs: worse_body,
    )
    contour_stage_runner = types.SimpleNamespace(
        run=lambda *args, **kwargs: worse_contour,
    )

    current_body, current_contour, decision = coach.evaluate(
        body_stage_runner=body_stage_runner,
        contour_stage_runner=contour_stage_runner,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="solid_body",
        geometry_authority=None,
        contour_inputs={
            "edges": None,
            "alpha_mask": None,
            "calibration": types.SimpleNamespace(mm_per_pixel=1.0),
            "family": "solid_body",
            "image_shape": (300, 200),
            "params": types.SimpleNamespace(),
        },
        body_result=original_body,
        contour_result=original_contour,
    )

    # Original results must be preserved
    assert current_body is original_body
    assert current_contour is original_contour
    assert decision.action == "rerun_body_isolation"
    assert any("rejected by monotonic improvement gate" in note.lower() for note in decision.notes)

    retry_attempts = current_contour.diagnostics.get("retry_attempts", [])
    assert len(retry_attempts) == 1

    attempt = retry_attempts[0]
    assert attempt["retry_reason"]
    assert attempt["retry_profile_used"] == "lower_bout_recovery"
    assert attempt["retry_iteration"] == 1
    assert attempt["score_before"] == 0.56
    assert attempt["score_after"] == 0.50
    assert attempt["score_delta"] < 0
    assert attempt["ownership_score_before"] == 0.44
    assert attempt["ownership_score_after"] == 0.41
    assert attempt["ownership_score_delta"] < 0
    assert attempt["ownership_ok_before"] is False
    assert attempt["ownership_ok_after"] is False


# ── Ownership failure → body_region_expansion profile ───────────────────────


def test_ownership_failure_prefers_body_region_expansion_profile():
    """
    When ownership_score < threshold, decide() should select the
    body_region_expansion profile for the body-isolation retry.
    """
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            body_isolation_review_threshold=0.45,
            contour_target_threshold=0.80,
            ownership_retry_threshold=0.60,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
                BodyIsolationParams(profile="body_region_expansion"),
            ],
            contour_retry_profiles=[],
        )
    )

    body = _make_body_result(completeness=0.70)
    contour = _ContourResultStub(
        best_score=0.82,
        ownership_score=0.40,  # below threshold
    )

    decision = coach.decide(
        body_result=body,
        contour_result=contour,
        retry_count=0,
    )

    assert decision.action == "rerun_body_isolation"
    assert "ownership" in decision.reason.lower()
    assert decision.body_retry_params is not None
    assert decision.body_retry_params.profile == "body_region_expansion"
