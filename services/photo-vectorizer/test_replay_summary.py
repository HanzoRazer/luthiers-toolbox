from __future__ import annotations

import json
from pathlib import Path

from pytest import approx

from replay_summary import summarize_retry_attempts


def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "replay_retry_attempts_with_ownership.json"


def test_summarize_retry_attempts_fixture_preserves_ownership_trajectory():
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 2
    assert summary["final_score_delta"] == 0.16
    assert summary["last_retry_profile_used"] == "lower_bout_recovery"
    assert summary["retry_profiles_used"] == [
        "body_region_expansion",
        "lower_bout_recovery",
    ]
    assert summary["first_ownership_score_before"] == 0.39
    assert summary["final_ownership_score"] == 0.67
    assert summary["final_ownership_ok"] is True
    assert summary["ownership_score_delta"] == 0.28
    assert summary["ownership_failures"] == 1


def test_summarize_retry_attempts_counts_only_failed_post_retry_ownership_states():
    payload = {
        "diagnostics": {
            "retry_attempts": [
                {
                    "retry_profile_used": "body_region_expansion",
                    "score_delta": 0.05,
                    "ownership_score_before": 0.42,
                    "ownership_score_after": 0.58,
                    "ownership_ok_before": False,
                    "ownership_ok_after": False,
                },
                {
                    "retry_profile_used": "lower_bout_recovery",
                    "score_delta": 0.07,
                    "ownership_score_before": 0.58,
                    "ownership_score_after": 0.64,
                    "ownership_ok_before": False,
                    "ownership_ok_after": True,
                },
            ]
        }
    }

    summary = summarize_retry_attempts(payload)

    assert summary["ownership_failures"] == 1
    assert summary["final_ownership_ok"] is True


def test_summarize_retry_attempts_direct_unit_tolerates_malformed_ownership_fields():
    payload = {
        "diagnostics": {
            "retry_attempts": [
                {
                    "retry_reason": "ownership low",
                    "retry_profile_used": 123,
                    "retry_iteration": 1,
                    "score_before": "0.50",
                    "score_after": "0.61",
                    "score_delta": "0.11",
                    "ownership_score_before": "bad",
                    "ownership_score_after": "0.58",
                    "ownership_ok_before": "no",
                    "ownership_ok_after": "false",
                },
                {
                    "retry_reason": "ownership low again",
                    "retry_profile_used": "body_region_expansion",
                    "retry_iteration": 2,
                    "score_before": 0.61,
                    "score_after": 0.72,
                    "score_delta": 0.11,
                    "ownership_score_before": 0.58,
                    "ownership_score_after": 0.64,
                    "ownership_ok_before": False,
                    "ownership_ok_after": True,
                },
            ]
        }
    }

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 2
    assert summary["final_score_delta"] == approx(0.22)
    assert summary["last_retry_profile_used"] == "body_region_expansion"
    assert summary["retry_profiles_used"] == [None, "body_region_expansion"]
    assert summary["first_ownership_score_before"] == 0.58
    assert summary["final_ownership_score"] == 0.64
    assert summary["final_ownership_ok"] is True
    assert summary["ownership_score_delta"] == approx(0.06)
    assert summary["ownership_failures"] == 1


def test_summarize_retry_attempts_empty_payload():
    summary = summarize_retry_attempts({})

    assert summary == {
        "retry_count": 0,
        "final_score_delta": 0.0,
        "last_retry_profile_used": None,
        "retry_profiles_used": [],
        "first_ownership_score_before": None,
        "final_ownership_score": None,
        "final_ownership_ok": None,
        "ownership_score_delta": None,
        "ownership_failures": 0,
    }
