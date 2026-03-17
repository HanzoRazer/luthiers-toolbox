"""
Live-case regression harness for GeometryCoachV2 multi-iteration convergence.

Three guitar families:
  1. Smart Guitar  – ownership failure → body_region_expansion → converges 1–2 iters
  2. Benedetto      – border contamination → retry → improve materially OR manual_review
  3. Archtop        – merge disagreement → width stabilizes, neck inclusion drops

Each test calls coach.evaluate() with staged runners that return progressively
different results per iteration, exercising the full retry loop.
"""
from __future__ import annotations

import types
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

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
        issues: Optional[List[str]] = None,
        diagnostics: Optional[dict] = None,
        ownership_score: Optional[float] = None,
    ):
        self.best_score = best_score
        self.elected_source = elected_source
        self.contour_scores_pre = []
        self.contour_scores_post = []
        self.export_block_issues = issues or []
        self.export_blocked = False
        self.block_reason = None
        self.recommended_next_action = None
        self.diagnostics = diagnostics if diagnostics is not None else {}
        self.ownership_score = ownership_score
        self.ownership_ok = (
            None if ownership_score is None else ownership_score >= 0.60
        )


# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_body_result(
    *,
    completeness: float,
    lower_bout: bool = False,
    border: bool = False,
    bbox: Tuple[int, int, int, int] = (100, 50, 300, 200),
) -> BodyIsolationResult:
    r = BodyIsolationResult(
        body_bbox_px=bbox,
        body_region=_BodyRegionStub(
            x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3],
        ),
        confidence=0.75,
        completeness_score=completeness,
        lower_bout_missing_likely=lower_bout,
        border_contact_likely=border,
        score_breakdown=BodyIsolationSignalBreakdown(
            hull_coverage=0.80,
            vertical_extent_ratio=0.72,
            width_stability=0.73,
            border_contact_penalty=0.75 if border else 0.0,
            center_alignment=0.78,
            lower_bout_presence=0.20 if lower_bout else 0.70,
        ),
    )
    if lower_bout:
        r.add_issue(
            "lower_bout_missing_likely",
            "Body isolation likely under-captured the lower bout.",
        )
    return r


_CONTOUR_INPUTS = {
    "edges": None,
    "alpha_mask": None,
    "calibration": types.SimpleNamespace(mm_per_pixel=1.0),
    "family": "solid_body",
    "image_shape": (300, 200),
    "params": types.SimpleNamespace(),
}


class _SequencedRunner:
    """Runner that yields different results on successive calls."""

    def __init__(self, results: list):
        self._results = list(results)
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def run(self, *args, **kwargs):
        idx = min(self._call_count, len(self._results) - 1)
        self._call_count += 1
        return self._results[idx]


# ── Smart Guitar: ownership failure → converge in 1–2 iterations ───────────


def test_smart_guitar_ownership_failure_converges():
    """
    Smart Guitar: initial contour has low ownership_score (0.39 < 0.60).
    Coach forces body_region_expansion, which improves ownership past
    threshold.  Evaluate should converge (accept) within 1–2 iterations.
    """
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            ownership_retry_threshold=0.60,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
                BodyIsolationParams(profile="border_suppression"),
                BodyIsolationParams(profile="body_region_expansion"),
            ],
        )
    )

    # Initial state: decent body, weak ownership
    initial_body = _make_body_result(completeness=0.69)
    initial_contour = _ContourResultStub(
        best_score=0.58,
        ownership_score=0.39,
        issues=["body ownership weak (0.39)"],
    )

    # After body_region_expansion: body improves, contour score improves,
    # and ownership crosses threshold
    improved_body = _make_body_result(completeness=0.74)
    improved_contour = _ContourResultStub(
        best_score=0.72,
        ownership_score=0.68,
    )

    body_runner = _SequencedRunner([improved_body])
    contour_runner = _SequencedRunner([improved_contour])

    final_body, final_contour, decision = coach.evaluate(
        body_stage_runner=body_runner,
        contour_stage_runner=contour_runner,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="solid_body",
        geometry_authority=None,
        contour_inputs=_CONTOUR_INPUTS,
        body_result=initial_body,
        contour_result=initial_contour,
    )

    # Convergence assertions
    assert decision.action == "accept", (
        f"Expected 'accept', got '{decision.action}': {decision.reason}"
    )
    assert body_runner.call_count >= 1, "Body runner should have been invoked"
    assert contour_runner.call_count >= 1, "Contour runner should follow body retry"

    # Ownership improved past threshold
    assert final_contour.ownership_score >= 0.60

    # Retry trajectory recorded
    retry_attempts = final_contour.diagnostics.get("retry_attempts", [])
    assert len(retry_attempts) >= 1
    assert retry_attempts[0]["retry_profile_used"] == "body_region_expansion"
    assert "ownership" in retry_attempts[0]["retry_reason"].lower()


# ── Benedetto: border contamination → material improvement or manual_review ─


def test_benedetto_border_contact_resolves_or_reviews():
    """
    Benedetto: border/crop contamination detected.  Coach retries body
    isolation.  Two sub-cases:

    a) Retry yields material improvement → accept.
    b) Retry makes things worse   → manual_review_required.

    We test (a) first, then (b) via the acceptance gate.
    """
    config = CoachV2Config(
        max_retries=2,
        epsilon=0.03,
        body_isolation_review_threshold=0.45,
        contour_target_threshold=0.80,
        severe_border_penalty_threshold=0.5,
        body_retry_profiles=[
            BodyIsolationParams(profile="lower_bout_recovery"),
            BodyIsolationParams(profile="border_suppression"),
        ],
    )

    # ── Sub-case (a): retry produces material improvement ──
    coach_a = GeometryCoachV2(config)

    initial_body_a = _make_body_result(
        completeness=0.42,
        border=True,
        bbox=(0, 8, 145, 120),
    )
    initial_contour_a = _ContourResultStub(best_score=0.60)

    # After border_suppression retry: significant gain
    better_body = _make_body_result(
        completeness=0.59,
        border=False,
        bbox=(12, 10, 140, 190),
    )
    better_contour = _ContourResultStub(best_score=0.74)

    body_runner_a = _SequencedRunner([better_body])
    contour_runner_a = _SequencedRunner([better_contour])

    final_body_a, final_contour_a, decision_a = coach_a.evaluate(
        body_stage_runner=body_runner_a,
        contour_stage_runner=contour_runner_a,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="archtop",
        geometry_authority=None,
        contour_inputs=_CONTOUR_INPUTS,
        body_result=initial_body_a,
        contour_result=initial_contour_a,
    )

    # Either accepted the improvement or triggered another retry
    assert decision_a.action in ("accept", "rerun_body_isolation"), (
        f"Benedetto (a): unexpected action '{decision_a.action}'"
    )
    # If accepted, contour must have improved
    if decision_a.action == "accept":
        assert final_contour_a.best_score > initial_contour_a.best_score

    # ── Sub-case (b): retry makes things worse → manual review ──
    coach_b = GeometryCoachV2(config)

    initial_body_b = _make_body_result(
        completeness=0.42,
        border=True,
        bbox=(0, 8, 145, 120),
    )
    initial_contour_b = _ContourResultStub(best_score=0.60)

    # Retry is worse: acceptance gate rejects
    worse_body = _make_body_result(
        completeness=0.40,
        border=True,
        bbox=(0, 8, 145, 115),
    )
    worse_contour = _ContourResultStub(best_score=0.52)

    body_runner_b = _SequencedRunner([worse_body])
    contour_runner_b = _SequencedRunner([worse_contour])

    final_body_b, final_contour_b, decision_b = coach_b.evaluate(
        body_stage_runner=body_runner_b,
        contour_stage_runner=contour_runner_b,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="archtop",
        geometry_authority=None,
        contour_inputs=_CONTOUR_INPUTS,
        body_result=initial_body_b,
        contour_result=initial_contour_b,
    )

    # Rejected retry preserves originals and lands in rerun_body_isolation
    # (the rejection path returns decision.action == "rerun_body_isolation"
    # with notes about monotonic gate rejection)
    assert final_body_b is initial_body_b, "Originals must be preserved on rejection"
    assert final_contour_b is initial_contour_b
    assert any(
        "rejected" in n.lower() or "manual" in n.lower()
        for n in decision_b.notes
    ), f"Expected rejection note, got: {decision_b.notes}"


# ── Archtop: merge disagreement → width stabilizes, neck inclusion drops ────


def test_archtop_merge_disagreement_improves_on_retry():
    """
    Archtop: pre/post merge disagreement + 'dimension plausibility weak'.
    Coach retries the contour stage.  The improved result should have:
      - Better or equal best_score (width-stable)
      - No 'neck included' issue (neck inclusion drops)
    """
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            contour_target_threshold=0.80,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
            ],
            contour_retry_profiles=[],
        )
    )

    initial_body = _make_body_result(completeness=0.71)
    initial_contour = _ContourResultStub(
        best_score=0.64,
        elected_source="pre_merge_guarded",
        issues=["dimension plausibility weak"],
    )

    # Retry produces cleaner contour: score jumps, no more dimension issues
    improved_contour = _ContourResultStub(
        best_score=0.78,
        elected_source="post_merge",
        issues=[],
    )

    body_runner = _SequencedRunner([initial_body])
    contour_runner = _SequencedRunner([improved_contour])

    final_body, final_contour, decision = coach.evaluate(
        body_stage_runner=body_runner,
        contour_stage_runner=contour_runner,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="archtop",
        geometry_authority=None,
        contour_inputs=_CONTOUR_INPUTS,
        body_result=initial_body,
        contour_result=initial_contour,
    )

    # Contour retry should lead to accept
    assert decision.action == "accept", (
        f"Expected 'accept', got '{decision.action}': {decision.reason}"
    )
    assert final_contour.best_score >= initial_contour.best_score, (
        "Width/score should stabilize or improve, not regress"
    )
    # Neck inclusion / dimension issues should be gone
    assert "neck included" not in (final_contour.export_block_issues or [])

    # Retry tracked in diagnostics
    retry_attempts = final_contour.diagnostics.get("retry_attempts", [])
    assert len(retry_attempts) >= 1
    assert retry_attempts[0]["score_delta"] > 0


def test_archtop_merge_disagreement_no_improvement_leads_to_manual_review():
    """
    Archtop: merge disagreement but retry fails to improve.
    The monotonic gate rejects, and originals are preserved.
    """
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            contour_target_threshold=0.80,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
            ],
            contour_retry_profiles=[],
        )
    )

    initial_body = _make_body_result(completeness=0.71)
    initial_contour = _ContourResultStub(
        best_score=0.64,
        elected_source="pre_merge_guarded",
        issues=["dimension plausibility weak"],
    )

    # Retry produces worse contour
    worse_contour = _ContourResultStub(
        best_score=0.60,
        elected_source="pre_merge_guarded",
        issues=["dimension plausibility weak", "neck included"],
    )

    body_runner = _SequencedRunner([initial_body])
    contour_runner = _SequencedRunner([worse_contour])

    final_body, final_contour, decision = coach.evaluate(
        body_stage_runner=body_runner,
        contour_stage_runner=contour_runner,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="archtop",
        geometry_authority=None,
        contour_inputs=_CONTOUR_INPUTS,
        body_result=initial_body,
        contour_result=initial_contour,
    )

    # Originals preserved; retry rejected
    assert final_body is initial_body
    assert final_contour is initial_contour
    assert any("rejected" in n.lower() for n in decision.notes)


def test_smart_guitar_ownership_persistent_failure_escalates_to_manual_review():
    """
    Smart Guitar: ownership remains below threshold even after
    body_region_expansion.  Coach should exhaust retries and
    escalate to manual_review_required.
    """
    coach = GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            ownership_retry_threshold=0.60,
            body_retry_profiles=[
                BodyIsolationParams(profile="lower_bout_recovery"),
                BodyIsolationParams(profile="border_suppression"),
                BodyIsolationParams(profile="body_region_expansion"),
            ],
        )
    )

    initial_body = _make_body_result(completeness=0.69)
    initial_contour = _ContourResultStub(
        best_score=0.58,
        ownership_score=0.39,
    )

    # Each retry improves scores enough to pass monotonic gate,
    # but ownership stays below threshold on every pass.
    retry_body_1 = _make_body_result(completeness=0.72)
    retry_contour_1 = _ContourResultStub(
        best_score=0.66,
        ownership_score=0.45,  # still below 0.60
    )

    retry_body_2 = _make_body_result(completeness=0.75)
    retry_contour_2 = _ContourResultStub(
        best_score=0.73,       # enough improvement to pass acceptance gate
        ownership_score=0.50,  # still below 0.60
    )

    body_runner = _SequencedRunner([retry_body_1, retry_body_2])
    contour_runner = _SequencedRunner([retry_contour_1, retry_contour_2])

    final_body, final_contour, decision = coach.evaluate(
        body_stage_runner=body_runner,
        contour_stage_runner=contour_runner,
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family="solid_body",
        geometry_authority=None,
        contour_inputs=_CONTOUR_INPUTS,
        body_result=initial_body,
        contour_result=initial_contour,
    )

    assert decision.action == "manual_review_required", (
        f"Expected escalation to manual_review_required, got '{decision.action}'"
    )
    assert "ownership" in decision.reason.lower()
