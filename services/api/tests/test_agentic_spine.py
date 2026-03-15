"""
Tests for Agentic Spine - moment detection and policy decisions.
"""

import pytest
from app.agentic.spine import (
    detect_moments,
    decide,
    group_by_session,
    select_moment_with_grace,
    DetectedMoment,
    UWSMSnapshot,
    IMPLEMENTED,
)


class TestMomentDetection:
    """Tests for moment detection."""

    def test_implemented_flag(self):
        """Verify IMPLEMENTED flag is True."""
        assert IMPLEMENTED is True

    def test_empty_events_returns_empty(self):
        """Empty event list returns no moments."""
        moments = detect_moments([])
        assert moments == []

    def test_first_signal_view_rendered(self):
        """view_rendered triggers FIRST_SIGNAL."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "user_action",
                "payload": {"action": "view_rendered"},
                "occurred_at": "2025-01-01T00:00:00Z",
            }
        ]
        moments = detect_moments(events)
        assert len(moments) == 1
        assert moments[0].moment == "FIRST_SIGNAL"
        assert moments[0].confidence == 0.75

    def test_first_signal_analysis_completed(self):
        """analysis_completed triggers FIRST_SIGNAL."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "analysis_completed",
                "payload": {},
                "occurred_at": "2025-01-01T00:00:00Z",
            }
        ]
        moments = detect_moments(events)
        assert len(moments) == 1
        assert moments[0].moment == "FIRST_SIGNAL"
        assert moments[0].confidence == 0.65

    def test_error_moment_highest_priority(self):
        """ERROR moment has highest priority (coexists with FIRST_SIGNAL)."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "user_action",
                "payload": {"action": "view_rendered"},
                "occurred_at": "2025-01-01T00:00:00Z",
            },
            {
                "event_id": "evt_2",
                "event_type": "analysis_failed",
                "payload": {"error": "test error"},
                "occurred_at": "2025-01-01T00:00:01Z",
            },
        ]
        moments = detect_moments(events)
        # detect_moments returns all moments; FIRST_SIGNAL can coexist
        assert len(moments) >= 1
        assert moments[0].moment == "ERROR"  # ERROR has highest priority
        assert moments[0].confidence == 0.95

    def test_overload_too_much_feedback(self):
        """too_much feedback triggers OVERLOAD."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "user_feedback",
                "payload": {"feedback": "too_much"},
                "occurred_at": "2025-01-01T00:00:00Z",
            }
        ]
        moments = detect_moments(events)
        assert len(moments) == 1
        assert moments[0].moment == "OVERLOAD"

    def test_overload_undo_spike(self):
        """3+ undos triggers OVERLOAD."""
        events = [
            {
                "event_id": f"evt_{i}",
                "event_type": "user_action",
                "payload": {"action": "undo"},
                "occurred_at": f"2025-01-01T00:00:0{i}Z",
            }
            for i in range(3)
        ]
        moments = detect_moments(events)
        assert len(moments) == 1
        assert moments[0].moment == "OVERLOAD"
        assert len(moments[0].trigger_events) == 3

    def test_hesitation_idle_timeout(self):
        """idle_timeout without param change triggers HESITATION."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "idle_timeout",
                "payload": {"idle_seconds": 8},
                "occurred_at": "2025-01-01T00:00:00Z",
            }
        ]
        moments = detect_moments(events)
        assert len(moments) == 1
        assert moments[0].moment == "HESITATION"

    def test_hesitation_suppressed_by_param_change(self):
        """HESITATION suppressed when parameter_changed present."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "idle_timeout",
                "payload": {"idle_seconds": 8},
                "occurred_at": "2025-01-01T00:00:00Z",
            },
            {
                "event_id": "evt_2",
                "event_type": "user_action",
                "payload": {"action": "parameter_changed"},
                "occurred_at": "2025-01-01T00:00:01Z",
            },
        ]
        moments = detect_moments(events)
        # No HESITATION because param changed
        assert len(moments) == 0 or moments[0].moment != "HESITATION"

    def test_decision_required(self):
        """decision_required event triggers DECISION_REQUIRED."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "decision_required",
                "payload": {"decision_type": "approve", "options": ["yes", "no"]},
                "occurred_at": "2025-01-01T00:00:00Z",
            }
        ]
        moments = detect_moments(events)
        assert len(moments) == 1
        assert moments[0].moment == "DECISION_REQUIRED"


class TestPolicyDecision:
    """Tests for policy decisions."""

    def test_first_signal_inspect(self):
        """FIRST_SIGNAL generates INSPECT directive."""
        moment = DetectedMoment(
            moment="FIRST_SIGNAL",
            confidence=0.75,
            trigger_events=["evt_1"],
        )
        decision = decide(moment)
        assert decision.emit_directive is True
        assert decision.directive.action == "INSPECT"
        assert decision.directive.title == "Inspect this"

    def test_error_review(self):
        """ERROR generates REVIEW directive."""
        moment = DetectedMoment(
            moment="ERROR",
            confidence=0.95,
            trigger_events=["evt_1"],
        )
        decision = decide(moment)
        assert decision.emit_directive is True
        assert decision.directive.action == "REVIEW"

    def test_shadow_mode_no_emit(self):
        """M0 shadow mode does not emit directives."""
        moment = DetectedMoment(
            moment="FIRST_SIGNAL",
            confidence=0.75,
            trigger_events=["evt_1"],
        )
        decision = decide(moment, mode="M0")
        assert decision.emit_directive is False
        assert decision.directive.action == "NONE"
        # But would_have_emitted is tracked
        assert decision.diagnostic.would_have_emitted is not None
        assert decision.diagnostic.would_have_emitted.action == "INSPECT"


class TestSessionGrouping:
    """Tests for session grouping."""

    def test_group_by_session(self):
        """Events are grouped by session_id."""
        events = [
            {
                "event_id": "evt_1",
                "event_type": "user_action",
                "session": {"session_id": "session_a"},
                "occurred_at": "2025-01-01T00:00:00Z",
            },
            {
                "event_id": "evt_2",
                "event_type": "user_action",
                "session": {"session_id": "session_b"},
                "occurred_at": "2025-01-01T00:00:01Z",
            },
            {
                "event_id": "evt_3",
                "event_type": "user_action",
                "session": {"session_id": "session_a"},
                "occurred_at": "2025-01-01T00:00:02Z",
            },
        ]
        sessions = group_by_session(events)
        assert len(sessions) == 2
        assert len(sessions["session_a"]) == 2
        assert len(sessions["session_b"]) == 1


class TestMomentSelection:
    """Tests for moment selection with grace period."""

    def test_first_signal_one_shot(self):
        """FIRST_SIGNAL is not returned if already shown."""
        moments = [
            DetectedMoment(moment="FIRST_SIGNAL", confidence=0.75, trigger_events=["e1"]),
            DetectedMoment(moment="FINDING", confidence=0.7, trigger_events=["e2"]),
        ]
        result = select_moment_with_grace(moments, first_signal_shown=True)
        assert result is not None
        assert result.moment == "FINDING"

    def test_prefer_first_signal_over_finding(self):
        """FIRST_SIGNAL preferred over FINDING when not yet shown."""
        moments = [
            DetectedMoment(moment="FINDING", confidence=0.7, trigger_events=["e1"]),
            DetectedMoment(moment="FIRST_SIGNAL", confidence=0.75, trigger_events=["e2"]),
        ]
        result = select_moment_with_grace(moments, first_signal_shown=False)
        assert result is not None
        assert result.moment == "FIRST_SIGNAL"
