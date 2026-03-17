"""
Test: GeometryCoachV2 real-world routing — body-ownership correction harness.

Loads named failure-class fixtures and verifies the coach routes each to
the expected action (rerun_body_isolation, rerun_contour_stage, etc.).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from body_isolation_result import (
    BodyIsolationResult,
    BodyIsolationIssue,
    BodyIsolationSignalBreakdown,
)
from geometry_coach_v2 import GeometryCoachV2, CoachV2Config


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _BodyRegionStub:
    def __init__(
        self,
        *,
        x_px: int,
        y_px: int,
        width_px: int,
        height_px: int,
        confidence: float,
    ):
        self.x_px = x_px
        self.y_px = y_px
        self.width_px = width_px
        self.height_px = height_px
        # Dual naming convention for downstream compatibility
        self.x = x_px
        self.y = y_px
        self.width = width_px
        self.height = height_px
        self.confidence = confidence
        self.height_mm = None
        self.width_mm = None


class _ContourStageResultStub:
    def __init__(
        self,
        *,
        best_score: float,
        export_block_issues: list,
        ownership_score=None,
        diagnostics=None,
    ):
        self.best_score = best_score
        self.export_block_issues = export_block_issues
        self.export_blocked = False
        self.export_block_reason = None
        self.recommended_next_action = None
        self.ownership_score = ownership_score
        self.diagnostics = diagnostics if diagnostics is not None else {}
        # _contour_retry_worthwhile reads these; empty = rely on export_block_issues
        self.contour_scores_pre = []
        self.contour_scores_post = []
        self.feature_contours_post_grid = []
        self.body_contour_final = None


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------

def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "body_ownership_routing_cases.json"


def _load_cases():
    data = json.loads(_fixture_path().read_text(encoding="utf-8"))
    return data["cases"]


def _make_body_result(case: dict) -> BodyIsolationResult:
    b = case["body_result"]
    bbox = tuple(b["body_bbox_px"])

    result = BodyIsolationResult(
        body_bbox_px=bbox,
        body_region=_BodyRegionStub(
            x_px=bbox[0],
            y_px=bbox[1],
            width_px=bbox[2],
            height_px=bbox[3],
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


def _make_contour_result(case: dict):
    c = case["contour_result"]
    return _ContourStageResultStub(
        best_score=c["best_score"],
        export_block_issues=c["export_block_issues"],
        ownership_score=c.get("ownership_score"),
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
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_geometry_coach_v2_routes_real_body_ownership_cases(case, coach: GeometryCoachV2):
    body_result = _make_body_result(case)
    contour_result = _make_contour_result(case)

    decision = coach.decide(
        body_result=body_result,
        contour_result=contour_result,
        retry_count=0,
    )

    assert decision.action == case["expected_action"], (
        f"Case {case['id']} expected {case['expected_action']} "
        f"but got {decision.action}. Reason: {decision.reason}"
    )


def test_geometry_coach_v2_fixture_is_nonempty():
    cases = _load_cases()
    assert len(cases) >= 3


def test_geometry_coach_v2_real_cases_cover_all_first_rules():
    cases = _load_cases()
    actions = {c["expected_action"] for c in cases}
    assert "rerun_body_isolation" in actions
    assert "rerun_contour_stage" in actions
