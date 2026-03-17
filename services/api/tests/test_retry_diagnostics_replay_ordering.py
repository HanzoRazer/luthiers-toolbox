from __future__ import annotations

import json
from pathlib import Path


def _fixture_path() -> Path:
    return (
        Path(__file__).parent
        / "fixtures"
        / "serialized_extraction_with_two_retries.json"
    )


def test_retry_attempts_preserve_order_in_replay_fixture():
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))

    retry_attempts = (
        payload.get("contour_stage", {})
        .get("diagnostics", {})
        .get("retry_attempts", [])
    )

    assert len(retry_attempts) == 2

    iterations = [attempt["retry_iteration"] for attempt in retry_attempts]
    assert iterations == [1, 2]


def test_retry_attempts_preserve_profile_name_in_replay_fixture():
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))

    retry_attempts = payload["contour_stage"]["diagnostics"]["retry_attempts"]

    assert retry_attempts[0]["retry_profile_used"] == "lower_bout_recovery"
    assert retry_attempts[1]["retry_profile_used"] == "lower_bout_recovery"
    assert retry_attempts[0]["score_delta"] > 0
    assert retry_attempts[1]["score_delta"] > 0
