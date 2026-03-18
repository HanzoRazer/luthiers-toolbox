from __future__ import annotations

import json
from pathlib import Path

from pytest import approx

from replay_summary import summarize_retry_attempts


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_smart_guitar_replay_asserts_ownership_failure_then_clearance():
    payload = _load_fixture("regression_replay_smart_guitar.json")

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
    assert payload["manual_review_required"] is False


def test_benedetto_replay_asserts_ownership_failure_persists_into_manual_review():
    payload = _load_fixture("regression_replay_benedetto.json")

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
    assert payload["manual_review_required"] is True


def test_archtop_replay_asserts_single_retry_clears_ownership_gate():
    payload = _load_fixture("regression_replay_archtop.json")

    summary = summarize_retry_attempts(payload)

    assert summary["retry_count"] == 1
    assert summary["retry_profiles_used"] == ["body_region_expansion"]
    assert summary["first_ownership_score_before"] == 0.46
    assert summary["final_ownership_score"] == 0.63
    assert summary["ownership_score_delta"] == approx(0.17)
    assert summary["final_ownership_ok"] is True
    assert summary["ownership_failures"] == 0
    assert payload["manual_review_required"] is False
