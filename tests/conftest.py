# tests/conftest.py
"""
Shared fixtures for agentic contract + spine tests.

These are designed to work in BOTH repos:
- luthiers-toolbox (pydantic models)
- tap_tone_pi (dataclasses)

They provide sample AgentEventV1 payloads that mirror the Markdown test cases.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def mk_source(repo: str, component: str = "test_component", version: str = "1.0.0") -> dict:
    return {"repo": repo, "component": component, "version": version}


def mk_event(
    *,
    event_type: str,
    repo: str = "tap_tone_pi",
    component: str = "wolf_detector",
    occurred_at: str | None = None,
    payload: dict | None = None,
    privacy_layer: int = 2,
    schema_version: str = "1.0.0",
    event_id: str | None = None,
) -> dict:
    return {
        "event_id": event_id or f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "source": mk_source(repo=repo, component=component, version="2.0.0"),
        "payload": payload or {},
        "privacy_layer": privacy_layer,
        "occurred_at": occurred_at or iso_now(),
        "schema_version": schema_version,
    }


# --- Moment-case fixtures (mirror markdown examples) ---

@pytest.fixture
def ev_analysis_started():
    return mk_event(event_type="analysis_started", occurred_at="2026-02-06T12:00:01Z")


@pytest.fixture
def ev_analysis_completed_basic():
    return mk_event(
        event_type="analysis_completed",
        occurred_at="2026-02-06T12:00:30Z",
        payload={"artifacts_created": ["ods_snapshot_v1"]},
    )


@pytest.fixture
def ev_view_rendered_spectrum():
    # If you add a dedicated EventType VIEW_RENDERED later, update this fixture accordingly.
    # For now, we treat it as USER_ACTION with structured payload.
    return mk_event(
        event_type="user_action",
        occurred_at="2026-02-06T12:00:12Z",
        payload={"action": "view_rendered", "panel_id": "spectrum", "trace_id": "main"},
    )


@pytest.fixture
def ev_idle_timeout_9s():
    return mk_event(
        event_type="idle_timeout",
        occurred_at="2026-02-06T12:00:14Z",
        payload={"idle_seconds": 9},
    )


@pytest.fixture
def ev_hover_1():
    return mk_event(
        event_type="user_action",
        occurred_at="2026-02-06T12:00:05Z",
        payload={"action": "hover", "target": "trace_panel", "duration_ms": 3200},
    )


@pytest.fixture
def ev_hover_2():
    return mk_event(
        event_type="user_action",
        occurred_at="2026-02-06T12:00:09Z",
        payload={"action": "hover", "target": "trace_panel", "duration_ms": 3400},
    )


@pytest.fixture
def ev_parameter_changed():
    return mk_event(
        event_type="user_action",
        occurred_at="2026-02-06T12:00:07Z",
        payload={"action": "parameter_changed", "param": "brightness", "value": 0.6},
    )


@pytest.fixture
def ev_user_feedback_too_much():
    return mk_event(
        event_type="user_feedback",
        occurred_at="2026-02-06T12:00:20Z",
        payload={"feedback": "too_much"},
    )


@pytest.fixture
def ev_undo_1():
    return mk_event(
        event_type="user_action",
        occurred_at="2026-02-06T12:00:21Z",
        payload={"action": "undo"},
    )


@pytest.fixture
def ev_undo_2():
    return mk_event(
        event_type="user_action",
        occurred_at="2026-02-06T12:00:22Z",
        payload={"action": "undo"},
    )


@pytest.fixture
def ev_undo_3():
    return mk_event(
        event_type="user_action",
        occurred_at="2026-02-06T12:00:23Z",
        payload={"action": "undo"},
    )


@pytest.fixture
def ev_tool_rendered():
    return mk_event(
        event_type="tool_rendered",
        occurred_at="2026-02-06T12:00:05Z",
        payload={"tool_id": "tap_tone_analyzer"},
    )


@pytest.fixture
def ev_tool_closed():
    return mk_event(
        event_type="tool_closed",
        occurred_at="2026-02-06T12:00:07Z",
        payload={"tool_id": "tap_tone_analyzer"},
    )


@pytest.fixture
def ev_decision_required():
    return mk_event(
        event_type="decision_required",
        occurred_at="2026-02-06T12:00:40Z",
        payload={"decision_id": "d1", "options": ["A", "B"]},
    )


@pytest.fixture
def ev_artifact_created_high_conf():
    return mk_event(
        event_type="artifact_created",
        occurred_at="2026-02-06T12:00:35Z",
        payload={"schema": "wolf_candidates_v1", "confidence_max": 0.87},
    )


@pytest.fixture
def ev_artifact_created_low_conf():
    return mk_event(
        event_type="artifact_created",
        occurred_at="2026-02-06T12:00:35Z",
        payload={"schema": "wolf_candidates_v1", "confidence_max": 0.42},
    )


@pytest.fixture
def ev_attention_requested():
    return mk_event(
        event_type="attention_requested",
        occurred_at="2026-02-06T12:00:36Z",
        payload={"directive_id": "attn_1"},
    )


@pytest.fixture
def ev_analysis_failed():
    return mk_event(
        event_type="analysis_failed",
        occurred_at="2026-02-06T12:00:25Z",
        payload={"message": "file not found"},
    )


@pytest.fixture
def ev_system_error():
    return mk_event(
        event_type="system_error",
        occurred_at="2026-02-06T12:00:25Z",
        payload={"code": "E_TIMEOUT"},
    )
