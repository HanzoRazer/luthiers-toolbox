from __future__ import annotations

import json
from pathlib import Path

from pytest import approx

from app.agentic.replay_summary import summarize_retry_attempts


def _fixture_path() -> Path:
    return (
        Path(__file__).parent
        / "fixtures"
        / "serialized_extraction_with_two_retries.json"
    )


def test_replay_summary_helper_computes_retry_metrics_from_serialized_payload():
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 2
    assert summary["final_score_delta"] == approx(0.22)
    assert summary["last_retry_profile_used"] == "lower_bout_recovery"
    assert summary["retry_profiles_used"] == ["lower_bout_recovery", "lower_bout_recovery"]


def test_replay_summary_helper_handles_empty_retry_list():
    payload = {
        "contour_stage": {
            "diagnostics": {
                "retry_attempts": []
            }
        }
    }

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 0
    assert summary["final_score_delta"] == 0.0
    assert summary["last_retry_profile_used"] is None
    assert summary["retry_profiles_used"] == []
