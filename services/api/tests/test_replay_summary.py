from __future__ import annotations

from pytest import approx

from app.agentic.replay_summary import summarize_retry_attempts


def test_summarize_retry_attempts_returns_correct_metrics():
    payload = {
        "contour_stage": {
            "diagnostics": {
                "retry_attempts": [
                    {
                        "retry_reason": "low_score",
                        "retry_profile_used": "lower_bout_recovery",
                        "retry_iteration": 1,
                        "score_before": 0.50,
                        "score_after": 0.60,
                        "score_delta": 0.10,
                    },
                    {
                        "retry_reason": "low_score",
                        "retry_profile_used": "border_suppression",
                        "retry_iteration": 2,
                        "score_before": 0.60,
                        "score_after": 0.72,
                        "score_delta": 0.12,
                    },
                ]
            }
        }
    }

    result = summarize_retry_attempts(payload)

    assert result["retry_count"] == 2
    assert result["final_score_delta"] == approx(0.22)
    assert result["last_retry_profile_used"] == "border_suppression"
    assert result["retry_profiles_used"] == ["lower_bout_recovery", "border_suppression"]
    assert result["ownership_score"] is None
    assert result["ownership_ok"] is None
    assert result["ownership_trajectory"] == []


def test_summarize_retry_attempts_returns_defaults_for_empty_payload():
    payload = {"contour_stage": {"diagnostics": {"retry_attempts": []}}}

    result = summarize_retry_attempts(payload)

    assert result["retry_count"] == 0
    assert result["final_score_delta"] == 0.0
    assert result["last_retry_profile_used"] is None
    assert result["retry_profiles_used"] == []
    assert result["ownership_score"] is None
    assert result["ownership_ok"] is None
    assert result["ownership_trajectory"] == []


def test_summarize_retry_attempts_ownership_trajectory():
    payload = {
        "contour_stage": {
            "ownership_score": 0.72,
            "ownership_ok": True,
            "diagnostics": {
                "retry_attempts": [
                    {
                        "retry_reason": "ownership too low",
                        "retry_profile_used": "body_region_expansion",
                        "retry_iteration": 1,
                        "score_before": 0.58,
                        "score_after": 0.66,
                        "score_delta": 0.08,
                        "ownership_before": 0.39,
                        "ownership_after": 0.72,
                    }
                ]
            },
        }
    }

    result = summarize_retry_attempts(payload)

    assert result["retry_count"] == 1
    assert result["ownership_score"] == 0.72
    assert result["ownership_ok"] is True
    assert len(result["ownership_trajectory"]) == 1
    assert result["ownership_trajectory"][0]["ownership_before"] == 0.39
    assert result["ownership_trajectory"][0]["ownership_after"] == 0.72
