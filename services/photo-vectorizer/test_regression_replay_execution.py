from __future__ import annotations

import pytest

from body_isolation_result import ReplayBodyRegion, BodyRegionProtocol
from replay_execution import execute_regression_case
from replay_fixture_loader import (
    load_regression_case,
    load_regression_cases,
    make_serialized_body_result,
    make_serialized_contour_result,
)


@pytest.mark.parametrize(
    "case",
    load_regression_cases(["smart_guitar", "benedetto", "archtop"]),
    ids=lambda c: c.case_id,
)
def test_regression_fixture_executes_through_coach_loop_and_matches_summary(case):
    result = execute_regression_case(case.case_id)

    assert result.final_decision.action == case.payload["expected_final_action"]
    assert result.summary["retry_count"] == case.payload["expected_retry_count"]
    assert (
        result.summary["last_retry_profile_used"]
        == case.payload["expected_last_retry_profile_used"]
    )
    assert (
        result.summary["final_ownership_ok"]
        == case.payload["expected_final_ownership_ok"]
    )

    if case.payload["expected_final_ownership_ok"]:
        assert result.final_contour_result.ownership_ok is True
        assert result.case.manual_review_required is False
    else:
        assert result.final_contour_result.ownership_ok is False
        assert result.final_decision.action == "manual_review_required"
        assert result.case.manual_review_required is True


def test_smart_guitar_execution_clears_ownership_after_two_retries():
    result = execute_regression_case("smart_guitar")

    assert result.final_decision.action == "accept"
    assert result.summary["retry_count"] == 2
    assert result.summary["first_ownership_score_before"] == 0.39
    assert result.summary["final_ownership_score"] == 0.66
    assert result.summary["final_ownership_ok"] is True
    assert result.summary["ownership_score_delta"] == 0.27


def test_benedetto_execution_ends_in_manual_review_when_ownership_never_clears():
    result = execute_regression_case("benedetto")

    assert result.final_decision.action == "manual_review_required"
    assert result.summary["retry_count"] == 2
    assert result.summary["final_ownership_score"] == 0.47
    assert result.summary["final_ownership_ok"] is False
    assert result.summary["ownership_failures"] == 2


def test_archtop_execution_clears_ownership_in_single_retry():
    result = execute_regression_case("archtop")

    assert result.final_decision.action == "accept"
    assert result.summary["retry_count"] == 1
    assert result.summary["last_retry_profile_used"] == "body_region_expansion"
    assert result.summary["final_ownership_score"] == 0.63
    assert result.summary["final_ownership_ok"] is True


def test_execution_starts_from_concrete_serialized_contour_object():
    case = load_regression_case("smart_guitar")
    body = make_serialized_body_result(case.payload)
    serialized = make_serialized_contour_result(case.payload)
    result = execute_regression_case("smart_guitar")

    assert body.body_bbox_px == tuple(case.payload["body_result"]["body_bbox_px"])
    assert serialized.best_score == case.payload["contour_result"]["best_score"]
    assert serialized.ownership_score == 0.39
    assert serialized.ownership_ok is False
    assert result.summary["first_ownership_score_before"] == serialized.ownership_score
    assert isinstance(body.body_region, ReplayBodyRegion)
    assert isinstance(body.body_region, BodyRegionProtocol)
