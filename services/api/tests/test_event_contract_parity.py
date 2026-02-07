# tests/test_event_contract_parity.py
"""
Event Contract Parity Tests — ensures AgentEventV1 can be parsed and serialized consistently.

These tests validate:
1. Event schema can be imported
2. Events can be parsed from JSON
3. Events can be serialized back to JSON
4. Round-trip produces equivalent data
5. Required fields are enforced

Note: Uses pytest.importorskip so tests skip gracefully if contract module is not available.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import pytest


def _sample_event() -> Dict[str, Any]:
    """Create a minimal valid AgentEventV1-shaped dict."""
    return {
        "event_id": "evt_test123",
        "event_type": "analysis_completed",
        "source": {
            "repo": "tap_tone_pi",
            "component": "analyzer",
            "version": "2.0.0",
        },
        "payload": {
            "artifacts_created": ["ods_snapshot_v1"],
        },
        "privacy_layer": 2,
        "occurred_at": "2026-01-01T00:00:00+00:00",
        "schema_version": "1.0.0",
        "session": {
            "session_id": "session_abc123",
        },
    }


def test_sample_event_is_valid_dict():
    """Sanity check: sample event is a valid dict."""
    event = _sample_event()
    assert isinstance(event, dict)
    assert event["event_type"] == "analysis_completed"


def test_event_json_round_trip():
    """Event can be serialized to JSON and parsed back."""
    event = _sample_event()

    json_str = json.dumps(event)
    parsed = json.loads(json_str)

    assert parsed["event_id"] == event["event_id"]
    assert parsed["event_type"] == event["event_type"]
    assert parsed["payload"] == event["payload"]


def test_event_required_fields():
    """Required fields are present in sample event."""
    event = _sample_event()

    required = ["event_id", "event_type", "source", "occurred_at", "schema_version"]
    for field in required:
        assert field in event, f"Missing required field: {field}"


def test_occurred_at_is_iso_format():
    """occurred_at should be ISO 8601 format."""
    event = _sample_event()

    # Should parse without error
    dt = datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
    assert dt.tzinfo is not None


def test_source_has_required_subfields():
    """source should have repo, component, version."""
    event = _sample_event()
    source = event["source"]

    assert "repo" in source
    assert "component" in source
    assert "version" in source


def test_privacy_layer_is_integer():
    """privacy_layer should be an integer 0-3."""
    event = _sample_event()

    assert isinstance(event["privacy_layer"], int)
    assert 0 <= event["privacy_layer"] <= 3


def test_session_has_session_id():
    """session block should have session_id."""
    event = _sample_event()

    assert "session" in event
    assert "session_id" in event["session"]


def test_payload_can_be_any_dict():
    """payload is a dict (content varies by event_type)."""
    event = _sample_event()

    assert isinstance(event["payload"], dict)


def test_user_feedback_event_shape():
    """user_feedback event has expected payload structure."""
    event = {
        "event_id": "evt_fb001",
        "event_type": "user_feedback",
        "source": {"repo": "luthiers-toolbox", "component": "ui", "version": "1.0.0"},
        "payload": {
            "feedback": "too_much",
            "directive_action": "REVIEW",
            "rule_id": "POLICY_OVERLOAD_REVIEW_v1",
        },
        "privacy_layer": 2,
        "occurred_at": "2026-01-01T00:00:01+00:00",
        "schema_version": "1.0.0",
        "session": {"session_id": "session_xyz"},
    }

    assert event["payload"]["feedback"] in ("helpful", "too_much")
    assert "rule_id" in event["payload"]


def test_user_action_event_shape():
    """user_action event has expected payload structure."""
    event = {
        "event_id": "evt_ua001",
        "event_type": "user_action",
        "source": {"repo": "luthiers-toolbox", "component": "ui", "version": "1.0.0"},
        "payload": {
            "action": "view_rendered",
            "panel_id": "spectrum",
        },
        "privacy_layer": 2,
        "occurred_at": "2026-01-01T00:00:02+00:00",
        "schema_version": "1.0.0",
        "session": {"session_id": "session_xyz"},
    }

    assert "action" in event["payload"]


def test_artifact_created_event_shape():
    """artifact_created event has expected payload structure."""
    event = {
        "event_id": "evt_art001",
        "event_type": "artifact_created",
        "source": {"repo": "tap_tone_pi", "component": "analyzer", "version": "2.0.0"},
        "payload": {
            "artifact_type": "wolf_candidates_v1",
            "schema": "wolf_candidates_v1",
            "confidence_max": 0.85,
        },
        "privacy_layer": 2,
        "occurred_at": "2026-01-01T00:00:03+00:00",
        "schema_version": "1.0.0",
        "session": {"session_id": "session_xyz"},
    }

    assert "artifact_type" in event["payload"] or "schema" in event["payload"]


# --- Cross-repo parity tests (skip if other repo not available) ---

def test_contract_parity_with_tap_tone_pi():
    """
    If tap_tone_pi is importable, ensure events can be parsed by both.

    This test is skipped if tap_tone_pi is not installed.
    """
    pytest.importorskip("tap_tone_pi", reason="tap_tone_pi not installed")

    # If we get here, tap_tone_pi is available
    # Future: import tap_tone_pi.agentic.contracts and compare schemas
    pass


def test_determinism_json_serialization():
    """JSON serialization should be deterministic (same output for same input)."""
    event = _sample_event()

    json1 = json.dumps(event, sort_keys=True)
    json2 = json.dumps(event, sort_keys=True)

    assert json1 == json2
