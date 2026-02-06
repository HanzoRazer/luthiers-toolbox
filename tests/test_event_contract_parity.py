# tests/test_event_contract_parity.py
"""
Executable tests for AgentEventV1 parsing/serialization in BOTH repos.

- luthiers-toolbox: pydantic BaseModel (AgentEventV1)
- tap_tone_pi: dataclasses (AgentEventV1)

These tests ensure both implementations can parse identical JSON payloads and
serialize to a JSON-serializable dict with expected keys.

If a repo doesn't have the other repo installed/importable, that section is skipped.
"""

from __future__ import annotations

import json
import pytest


EXPECTED_EVENT_KEYS = {
    "event_id",
    "event_type",
    "source",
    "payload",
    "privacy_layer",
    "occurred_at",
    "schema_version",
}


def _assert_event_dict_shape(d: dict):
    assert isinstance(d, dict)
    missing = EXPECTED_EVENT_KEYS - set(d.keys())
    assert not missing, f"Missing keys: {missing}"
    # Ensure JSON serializable
    json.dumps(d)


@pytest.fixture
def sample_events(
    ev_analysis_started,
    ev_analysis_completed_basic,
    ev_view_rendered_spectrum,
    ev_user_feedback_too_much,
    ev_decision_required,
    ev_analysis_failed,
):
    return [
        ev_analysis_started,
        ev_analysis_completed_basic,
        ev_view_rendered_spectrum,
        ev_user_feedback_too_much,
        ev_decision_required,
        ev_analysis_failed,
    ]


def test_tap_tone_pi_agent_event_parses_and_serializes(sample_events):
    tt = pytest.importorskip("tap_tone_pi.agentic.contracts", reason="tap_tone_pi not importable")
    AgentEventV1 = getattr(tt, "AgentEventV1")

    for e in sample_events:
        obj = AgentEventV1(**e)  # dataclass may accept kwargs via __init__
        # Prefer .to_dict() if provided, else fallback to __dict__
        if hasattr(obj, "to_dict"):
            d = obj.to_dict()
        else:
            d = obj.__dict__
        _assert_event_dict_shape(d)


def test_luthiers_toolbox_agent_event_parses_and_serializes(sample_events):
    lb = pytest.importorskip("app.agentic.contracts", reason="luthiers-toolbox contracts not importable")
    AgentEventV1 = getattr(lb, "AgentEventV1")

    for e in sample_events:
        obj = AgentEventV1(**e)
        # Prefer pydantic v2 .model_dump(); fallback to .dict() (v1)
        if hasattr(obj, "model_dump"):
            d = obj.model_dump()
        else:
            d = obj.dict()
        _assert_event_dict_shape(d)


def test_cross_repo_serialization_key_parity(sample_events):
    """
    If both repos are importable in the same environment, ensure that the serialized
    dicts share the same top-level keys (forward/back compat baseline).
    """
    tt_mod = pytest.importorskip("tap_tone_pi.agentic.contracts", reason="tap_tone_pi not importable")
    lb_mod = pytest.importorskip("app.agentic.contracts", reason="luthiers-toolbox not importable")

    TTEvent = getattr(tt_mod, "AgentEventV1")
    LBEvent = getattr(lb_mod, "AgentEventV1")

    for e in sample_events:
        tt_obj = TTEvent(**e)
        lb_obj = LBEvent(**e)

        tt_d = tt_obj.to_dict() if hasattr(tt_obj, "to_dict") else tt_obj.__dict__
        lb_d = lb_obj.model_dump() if hasattr(lb_obj, "model_dump") else lb_obj.dict()

        assert set(tt_d.keys()) == set(lb_d.keys()), (
            f"Key mismatch:\n"
            f"tap_tone_pi={set(tt_d.keys())}\n"
            f"luthiers-toolbox={set(lb_d.keys())}"
        )
