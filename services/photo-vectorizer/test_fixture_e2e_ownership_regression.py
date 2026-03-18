"""
Fixture-backed end-to-end regression: ownership-triggered body retries.

Unlike test_geometry_coach_v2_real_routing.py (decide-only) and
test_coaching_convergence.py (mocked runners), these tests verify that
fixture-defined cases route through the full evaluate() loop and produce
retry annotations with ownership provenance — not just generic retry routing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from body_isolation_result import (
    BodyIsolationIssue,
    BodyIsolationResult,
    BodyIsolationSignalBreakdown,
)
from geometry_coach_v2 import CoachV2Config, GeometryCoachV2


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _BodyRegionStub:
    def __init__(self, *, x_px, y_px, width_px, height_px, confidence):
        self.x = self.x_px = x_px
        self.y = self.y_px = y_px
        self.width = self.width_px = width_px
        self.height = self.height_px = height_px
        self.confidence = confidence
        self.height_mm = self.width_mm = None


class _ContourStageResultStub:
    def __init__(
        self,
        *,
        best_score: float,
        export_block_issues: list,
        ownership_score: Optional[float] = None,
        ownership_ok: Optional[bool] = None,
        diagnostics: Optional[dict] = None,
    ):
        self.best_score = best_score
        self.export_block_issues = list(export_block_issues)
        self.export_blocked = False
        self.export_block_reason = None
        self.recommended_next_action = None
        self.ownership_score = ownership_score
        self.ownership_ok = ownership_ok
        self.diagnostics = diagnostics if diagnostics is not None else {}
        self.contour_scores_pre = []
        self.contour_scores_post = []
        self.feature_contours_post_grid = []
        self.body_contour_final = None


class _StageRunnerStub:
    """Stage runner that returns an improved result with ownership recovery."""

    def __init__(
        self,
        *,
        improved_body: BodyIsolationResult,
        improved_contour: _ContourStageResultStub,
    ):
        self._improved_body = improved_body
        self._improved_contour = improved_contour

    def run(self, *args, **kwargs):
        return self._improved_body if hasattr(self._improved_body, "body_bbox_px") else self._improved_contour


class _BodyStageRunner:
    def __init__(self, improved_body: BodyIsolationResult):
        self._result = improved_body

    def run(self, *args, **kwargs):
        return self._result


class _ContourStageRunner:
    def __init__(self, improved_contour: _ContourStageResultStub):
        self._result = improved_contour

    def run(self, *args, **kwargs):
        return self._result


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------

def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "body_ownership_routing_cases.json"


def _load_cases() -> list:
    return json.loads(_fixture_path().read_text(encoding="utf-8"))["cases"]


def _make_body_result(case: dict) -> BodyIsolationResult:
    b = case["body_result"]
    bbox = tuple(b["body_bbox_px"])
    result = BodyIsolationResult(
        body_bbox_px=bbox,
        body_region=_BodyRegionStub(
            x_px=bbox[0], y_px=bbox[1],
            width_px=bbox[2], height_px=bbox[3],
            confidence=b["confidence"],
        ),
        confidence=b["confidence"],
        completeness_score=b["completeness_score"],
        review_required=b["review_required"],
        lower_bout_missing_likely=b["lower_bout_missing_likely"],
        border_contact_likely=b["border_contact_likely"],
        score_breakdown=BodyIsolationSignalBreakdown(**b["score_breakdown"]),
    )
    for issue in b["issues"]:
        result.issues.append(
            BodyIsolationIssue(
                code=issue["code"],
                message=issue["message"],
                severity=issue.get("severity", "warning"),
            )
        )
    return result


def _make_contour_result(case: dict) -> _ContourStageResultStub:
    c = case["contour_result"]
    return _ContourStageResultStub(
        best_score=c["best_score"],
        export_block_issues=c["export_block_issues"],
        ownership_score=c.get("ownership_score"),
        ownership_ok=c.get("ownership_ok"),
    )


# ---------------------------------------------------------------------------
# Coach fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def coach() -> GeometryCoachV2:
    return GeometryCoachV2(
        CoachV2Config(
            max_retries=2,
            epsilon=0.03,
            contour_target_threshold=0.80,
            body_isolation_review_threshold=0.45,
            severe_border_penalty_threshold=0.5,
            ownership_retry_threshold=0.60,
        )
    )


# ---------------------------------------------------------------------------
# Smart Guitar: ownership failure → body retry with ownership provenance
# ---------------------------------------------------------------------------

def test_smart_guitar_ownership_triggers_body_retry_with_provenance(coach):
    """
    The Smart Guitar fixture has ownership_score=0.39 (<0.60).
    Evaluate() must route to body retry AND the resulting retry_attempts
    must carry ownership_score_before / ownership_score_after — proving the retry was
    specifically ownership-triggered, not generic.
    """
    cases = {c["id"]: c for c in _load_cases()}
    case = cases["smart_guitar_body_ownership_failure"]

    original_body = _make_body_result(case)
    original_contour = _make_contour_result(case)

    # Improved results after body retry — ownership recovers above threshold
    improved_body = _make_body_result(case)
    improved_body.completeness_score = 0.72

    improved_contour = _ContourStageResultStub(
        best_score=0.70,
        export_block_issues=[],
        ownership_score=0.74,
        ownership_ok=True,
    )

    body, contour, decision = coach.evaluate(
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family=None,
        geometry_authority=None,
        body_stage_runner=_BodyStageRunner(improved_body),
        contour_stage_runner=_ContourStageRunner(improved_contour),
        contour_inputs={
            "edges": None, "alpha_mask": None,
            "body_region": original_body.body_region,
            "calibration": None, "family": None, "image_shape": (400, 300),
        },
        body_result=original_body,
        contour_result=original_contour,
    )

    assert decision.action == "accept"

    # The retry attempt must carry ownership trajectory
    retry_attempts = contour.diagnostics.get("retry_attempts", [])
    assert len(retry_attempts) >= 1, "Expected at least one retry attempt"

    attempt = retry_attempts[0]
    assert attempt.get("ownership_score_before") == 0.39, (
        "Retry must record initial ownership_score as ownership_score_before"
    )
    assert attempt.get("ownership_score_after") == 0.74, (
        "Retry must record recovered ownership_score as ownership_score_after"
    )
    assert attempt.get("ownership_ok_before") is False
    assert attempt.get("ownership_ok_after") is True
    assert "ownership" in attempt["retry_reason"].lower(), (
        "Retry reason must mention ownership to distinguish from generic retries"
    )


# ---------------------------------------------------------------------------
# Benedetto: border contact → body retry (NOT ownership-driven)
# ---------------------------------------------------------------------------

def test_benedetto_border_contact_retry_has_no_ownership_trajectory(coach):
    """
    The Benedetto fixture has border_contact_likely=True but no ownership failure.
    The retry should NOT carry ownership_score_before/ownership_score_after fields,
    proving the system distinguishes ownership retries from border-contact retries.
    """
    cases = {c["id"]: c for c in _load_cases()}
    case = cases["benedetto_border_contact"]

    original_body = _make_body_result(case)
    original_contour = _make_contour_result(case)

    improved_body = _make_body_result(case)
    improved_body.completeness_score = 0.58
    improved_body.border_contact_likely = False

    improved_contour = _ContourStageResultStub(
        best_score=0.71,
        export_block_issues=[],
        ownership_score=None,
        ownership_ok=None,
    )

    body, contour, decision = coach.evaluate(
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family=None,
        geometry_authority=None,
        body_stage_runner=_BodyStageRunner(improved_body),
        contour_stage_runner=_ContourStageRunner(improved_contour),
        contour_inputs={
            "edges": None, "alpha_mask": None,
            "body_region": original_body.body_region,
            "calibration": None, "family": None, "image_shape": (400, 300),
        },
        body_result=original_body,
        contour_result=original_contour,
    )

    assert decision.action == "accept"

    retry_attempts = contour.diagnostics.get("retry_attempts", [])
    assert len(retry_attempts) >= 1

    attempt = retry_attempts[0]
    # Border contact retries should not have ownership data
    assert attempt["ownership_score_before"] is None
    assert attempt["ownership_score_after"] is None
    assert attempt["ownership_ok_before"] is None
    assert attempt["ownership_ok_after"] is None


# ---------------------------------------------------------------------------
# Archtop: merge disagreement → contour retry (NOT ownership-driven)
# ---------------------------------------------------------------------------

def test_archtop_merge_disagreement_retry_is_contour_not_ownership(coach):
    """
    The Archtop fixture has dimension plausibility issues but no ownership failure.
    Retry should route to contour stage, and retry_attempts should NOT carry
    ownership trajectory — proving ownership retries are distinct.
    """
    cases = {c["id"]: c for c in _load_cases()}
    case = cases["archtop_merge_disagreement"]

    original_body = _make_body_result(case)
    original_contour = _make_contour_result(case)

    improved_contour = _ContourStageResultStub(
        best_score=0.75,
        export_block_issues=[],
        ownership_score=None,
        ownership_ok=None,
    )

    body, contour, decision = coach.evaluate(
        image=None,
        fg_mask=None,
        original_image=None,
        instrument_family=None,
        geometry_authority=None,
        body_stage_runner=_BodyStageRunner(_make_body_result(case)),
        contour_stage_runner=_ContourStageRunner(improved_contour),
        contour_inputs={
            "edges": None, "alpha_mask": None,
            "body_region": original_body.body_region,
            "calibration": None, "family": None, "image_shape": (400, 300),
        },
        body_result=original_body,
        contour_result=original_contour,
    )

    assert decision.action == "accept"

    retry_attempts = contour.diagnostics.get("retry_attempts", [])
    assert len(retry_attempts) >= 1

    attempt = retry_attempts[0]
    # Contour-stage retries for merge disagreement should not have ownership data
    assert attempt["ownership_score_before"] is None
    assert attempt["ownership_score_after"] is None
    assert attempt["ownership_ok_before"] is None
    assert attempt["ownership_ok_after"] is None
    assert "ownership" not in attempt.get("retry_reason", "").lower(), (
        "Merge disagreement retry reason should not mention ownership"
    )
