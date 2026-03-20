from __future__ import annotations

from pytest import approx

from replay_summary import summarize_retry_attempts
from replay_fixture_loader import load_regression_case


def test_smart_guitar_replay_asserts_ownership_failure_then_clearance():
    case = load_regression_case("smart_guitar")
    payload = case.payload

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 2
    assert summary["retry_profiles_used"] == [
        "body_region_expansion",
        "lower_bout_recovery",
    ]
    assert summary["first_ownership_score_before"] == 0.39
    assert summary["final_ownership_score"] == 0.66
    assert summary["ownership_score_delta"] == approx(0.27)
    assert summary["final_ownership_ok"] is True
    assert summary["ownership_failures"] >= 1
    assert case.manual_review_required is False
    assert summary["last_retry_profile_used"] == payload["expected_last_retry_profile_used"]


def test_benedetto_replay_asserts_ownership_failure_persists_into_manual_review():
    case = load_regression_case("benedetto")
    payload = case.payload

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 2
    assert summary["retry_profiles_used"] == [
        "body_region_expansion",
        "lower_bout_recovery",
    ]
    assert summary["first_ownership_score_before"] == 0.28
    assert summary["final_ownership_score"] == 0.47
    assert summary["ownership_score_delta"] == approx(0.19)
    assert summary["final_ownership_ok"] is False
    assert summary["ownership_failures"] == 2
    assert case.manual_review_required is True
    assert summary["last_retry_profile_used"] == payload["expected_last_retry_profile_used"]


def test_archtop_replay_asserts_single_retry_clears_ownership_gate():
    case = load_regression_case("archtop")
    payload = case.payload

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 1
    assert summary["retry_profiles_used"] == ["body_region_expansion"]
    assert summary["first_ownership_score_before"] == 0.46
    assert summary["final_ownership_score"] == 0.63
    assert summary["ownership_score_delta"] == approx(0.17)
    assert summary["final_ownership_ok"] is True
    assert summary["ownership_failures"] == 0
    assert case.manual_review_required is False
    assert summary["last_retry_profile_used"] == payload["expected_last_retry_profile_used"]


def test_summary_loader_and_execution_loader_share_same_retry_attempt_payload():
    case = load_regression_case("benedetto")
    payload = case.payload

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == len(payload["diagnostics"]["retry_attempts"])
    assert summary["first_ownership_score_before"] == payload["diagnostics"]["retry_attempts"][0]["ownership_score_before"]
