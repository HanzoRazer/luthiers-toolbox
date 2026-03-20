from __future__ import annotations

from body_isolation_result import ReplayBodyRegion, BodyRegionProtocol
from replay_fixture_loader import (
    load_regression_case,
    load_regression_cases,
    make_serialized_body_result,
    make_serialized_contour_result,
)


def test_load_regression_case_exposes_both_replay_and_execution_payloads():
    case = load_regression_case("smart_guitar")

    assert case.case_id == "smart_guitar"
    assert case.expected_action == "rerun_body_isolation"
    assert case.manual_review_required is False
    assert case.payload["expected_final_action"] == "accept"
    assert case.payload["expected_retry_count"] == 2
    assert case.payload["expected_last_retry_profile_used"] == "lower_bout_recovery"
    assert case.payload["expected_final_ownership_ok"] is True
    assert "body_result" in case.payload
    assert "contour_result" in case.payload
    assert "diagnostics" in case.payload
    assert "retry_attempts" in case.payload["diagnostics"]


def test_fixture_loader_uses_native_from_payload_path_only():
    case = load_regression_case("benedetto")

    body_result = make_serialized_body_result(case.payload)
    contour_result = make_serialized_contour_result(case.payload)

    assert body_result.to_payload()["completeness_score"] == case.payload["body_result"]["completeness_score"]
    assert contour_result.to_payload()["best_score"] == case.payload["contour_result"]["best_score"]
    assert contour_result.to_payload()["ownership_ok"] == case.payload["contour_result"]["ownership_ok"]


def test_make_serialized_body_and_contour_results_from_same_fixture():
    case = load_regression_case("archtop")

    body_result = make_serialized_body_result(case.payload)
    contour_result = make_serialized_contour_result(case.payload)

    assert body_result.completeness_score == case.payload["body_result"]["completeness_score"]
    assert contour_result.best_score == case.payload["contour_result"]["best_score"]
    assert contour_result.ownership_score == case.payload["contour_result"]["ownership_score"]
    assert contour_result.diagnostics["ownership_score"] == case.payload["contour_result"]["ownership_score"]


def test_make_serialized_results_builds_concrete_replay_objects():
    case = load_regression_case("smart_guitar")

    body_result = make_serialized_body_result(case.payload)
    contour_result = make_serialized_contour_result(case.payload)

    assert body_result.body_bbox_px == tuple(case.payload["body_result"]["body_bbox_px"])
    assert contour_result.best_score == case.payload["contour_result"]["best_score"]
    assert contour_result.ownership_score == case.payload["contour_result"]["ownership_score"]
    assert contour_result.ownership_ok is False
    assert "retry_attempts" in contour_result.diagnostics
    assert len(contour_result.diagnostics["retry_attempts"]) == 2
    assert body_result.body_bbox_px == tuple(case.payload["body_result"]["body_bbox_px"])
    assert body_result.to_payload()["body_bbox_px"] == case.payload["body_result"]["body_bbox_px"]
    assert contour_result.to_payload()["ownership_score"] == case.payload["contour_result"]["ownership_score"]
    assert isinstance(body_result.body_region, ReplayBodyRegion)
    assert isinstance(body_result.body_region, BodyRegionProtocol)


def test_load_regression_cases_returns_all_three_checkpoint_cases():
    cases = load_regression_cases(["smart_guitar", "benedetto", "archtop"])
    ids = [c.case_id for c in cases]
    assert ids == ["archtop", "benedetto", "smart_guitar"] or sorted(ids) == ["archtop", "benedetto", "smart_guitar"]
