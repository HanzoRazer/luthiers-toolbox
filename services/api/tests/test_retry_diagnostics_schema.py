from __future__ import annotations

import json
from pathlib import Path


REQUIRED_RETRY_ATTEMPT_KEYS = {
    "retry_reason",
    "retry_profile_used",
    "retry_iteration",
    "score_before",
    "score_after",
    "score_delta",
}


def _fixture_path() -> Path:
    return (
        Path(__file__).parent
        / "fixtures"
        / "serialized_extraction_with_retry.json"
    )


def test_retry_attempt_entries_have_required_keys():
    """
    Regression test:
    Every retry_attempt entry in the serialized replay fixture must contain
    the full required key set. This locks the replay contract.
    """
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))

    retry_attempts = (
        payload.get("contour_stage", {})
        .get("diagnostics", {})
        .get("retry_attempts", [])
    )

    assert retry_attempts, "Expected at least one retry_attempt entry in fixture"

    for idx, attempt in enumerate(retry_attempts):
        missing = REQUIRED_RETRY_ATTEMPT_KEYS - set(attempt.keys())
        assert not missing, (
            f"Retry attempt at index {idx} is missing required keys: {sorted(missing)}"
        )


def test_retry_attempt_entries_have_basic_value_types():
    """
    Light type sanity check to catch obvious schema drift in replay artifacts.
    """
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))
    attempt = payload["contour_stage"]["diagnostics"]["retry_attempts"][0]

    assert isinstance(attempt["retry_reason"], str)
    assert isinstance(attempt["retry_profile_used"], str)
    assert isinstance(attempt["retry_iteration"], int)
    assert isinstance(attempt["score_before"], (int, float))
    assert isinstance(attempt["score_after"], (int, float))
    assert isinstance(attempt["score_delta"], (int, float))
