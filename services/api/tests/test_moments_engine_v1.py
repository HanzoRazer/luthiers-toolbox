# tests/test_moments_engine_v1.py
"""
Moment Detection Engine Tests — validates detect_moments() behavior.

Tests ensure:
1. Priority suppression works (ERROR > OVERLOAD > DECISION_REQUIRED > ...)
2. Moment detection is deterministic
3. Confidence scores are in expected ranges
4. Trigger events are tracked correctly
"""

from __future__ import annotations

import pytest


def test_detect_moments_import():
    """Smoke test: moments module is importable."""
    from app.agentic.spine.moments import detect_moments
    assert callable(detect_moments)


def test_empty_events_returns_empty():
    from app.agentic.spine.moments import detect_moments
    assert detect_moments([]) == []


def test_first_signal_from_analysis_completed():
    """analysis_completed alone triggers FIRST_SIGNAL."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": "e1", "event_type": "analysis_completed", "occurred_at": "2026-01-01T00:00:00Z"}
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "FIRST_SIGNAL"
    assert result[0]["confidence"] >= 0.5
    assert "e1" in result[0]["trigger_events"]


def test_first_signal_from_view_rendered():
    """user_action with action=view_rendered triggers FIRST_SIGNAL with higher confidence."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {
            "event_id": "e1",
            "event_type": "user_action",
            "payload": {"action": "view_rendered"},
            "occurred_at": "2026-01-01T00:00:00Z",
        }
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "FIRST_SIGNAL"
    assert result[0]["confidence"] >= 0.7


def test_hesitation_from_idle_timeout():
    """idle_timeout triggers HESITATION (if no parameter change)."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": "e1", "event_type": "idle_timeout", "payload": {"idle_seconds": 10}, "occurred_at": "2026-01-01T00:00:01Z"}
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "HESITATION"


def test_hesitation_suppressed_by_parameter_change():
    """Parameter change suppresses HESITATION detection."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": "e1", "event_type": "idle_timeout", "payload": {"idle_seconds": 10}, "occurred_at": "2026-01-01T00:00:01Z"},
        {"event_id": "e2", "event_type": "user_action", "payload": {"action": "parameter_changed"}, "occurred_at": "2026-01-01T00:00:02Z"},
    ]
    result = detect_moments(events)

    # No hesitation; may get FIRST_SIGNAL or nothing
    moments = [r["moment"] for r in result]
    assert "HESITATION" not in moments


def test_overload_from_explicit_too_much():
    """user_feedback with feedback=too_much triggers OVERLOAD."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {
            "event_id": "e1",
            "event_type": "user_feedback",
            "payload": {"feedback": "too_much"},
            "occurred_at": "2026-01-01T00:00:01Z",
        }
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "OVERLOAD"
    assert result[0]["confidence"] >= 0.8


def test_overload_from_undo_spike():
    """3+ undo actions triggers OVERLOAD."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": f"e{i}", "event_type": "user_action", "payload": {"action": "undo"}, "occurred_at": f"2026-01-01T00:00:0{i}Z"}
        for i in range(1, 5)
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "OVERLOAD"


def test_error_has_highest_priority():
    """ERROR should suppress all other moments."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": "e1", "event_type": "analysis_failed", "occurred_at": "2026-01-01T00:00:01Z"},
        {"event_id": "e2", "event_type": "user_feedback", "payload": {"feedback": "too_much"}, "occurred_at": "2026-01-01T00:00:02Z"},
        {"event_id": "e3", "event_type": "idle_timeout", "payload": {"idle_seconds": 10}, "occurred_at": "2026-01-01T00:00:03Z"},
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "ERROR"


def test_decision_required_moment():
    """decision_required event triggers DECISION_REQUIRED moment."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": "e1", "event_type": "decision_required", "occurred_at": "2026-01-01T00:00:01Z"}
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "DECISION_REQUIRED"


def test_priority_overload_beats_decision_required():
    """OVERLOAD has higher priority than DECISION_REQUIRED."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": "e1", "event_type": "decision_required", "occurred_at": "2026-01-01T00:00:01Z"},
        {"event_id": "e2", "event_type": "user_feedback", "payload": {"feedback": "too_much"}, "occurred_at": "2026-01-01T00:00:02Z"},
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "OVERLOAD"


def test_finding_from_high_confidence_artifact():
    """High-confidence wolf_candidates artifact triggers FINDING."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {
            "event_id": "e1",
            "event_type": "artifact_created",
            "payload": {"schema": "wolf_candidates_v1", "confidence_max": 0.85},
            "occurred_at": "2026-01-01T00:00:01Z",
        }
    ]
    result = detect_moments(events)

    assert len(result) == 1
    assert result[0]["moment"] == "FINDING"


def test_determinism_same_input_same_output():
    """Same events should always produce the same moments."""
    from app.agentic.spine.moments import detect_moments

    events = [
        {"event_id": "e1", "event_type": "analysis_completed", "occurred_at": "2026-01-01T00:00:00Z"},
        {"event_id": "e2", "event_type": "idle_timeout", "payload": {"idle_seconds": 5}, "occurred_at": "2026-01-01T00:00:05Z"},
    ]

    result1 = detect_moments(events)
    result2 = detect_moments(events)

    assert result1 == result2
