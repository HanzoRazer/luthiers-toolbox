from __future__ import annotations

import json
from pathlib import Path


def _fixture_path() -> Path:
    return (
        Path(__file__).parent
        / "fixtures"
        / "serialized_extraction_with_retry.json"
    )


def test_retry_profile_survives_replay_fixture_load():
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))

    retry_attempts = (
        payload.get("contour_stage", {})
        .get("diagnostics", {})
        .get("retry_attempts", [])
    )

    assert len(retry_attempts) == 1
    assert retry_attempts[0]["retry_profile_used"] == "lower_bout_recovery"


def test_replay_fixture_has_expected_coach_action():
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))
    assert payload["geometry_coach_v2"]["action"] == "rerun_body_isolation"
