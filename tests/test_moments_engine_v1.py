# tests/test_moments_engine_v1.py
"""
Executable tests for moment detection.

These assume you implement a moment detector in luthiers-toolbox, e.g.:

    from app.agentic.spine.moments import detect_moments

with a signature like:
    detect_moments(events: list[AgentEventV1 | dict]) -> list[dict]

Where each emitted moment dict includes:
    - "moment": str
    - "confidence": float
    - "trigger_events": list[str]

Until that module exists, these tests will be SKIPPED.

If you prefer a different module path, update MOMENTS_IMPORT_PATH below.
"""

from __future__ import annotations

import pytest

MOMENTS_IMPORT_PATH = "app.agentic.spine.moments"


def _import_detector():
    mod = pytest.importorskip(MOMENTS_IMPORT_PATH, reason=f"{MOMENTS_IMPORT_PATH} not implemented yet")
    detect_moments = getattr(mod, "detect_moments", None)
    assert callable(detect_moments), "Expected a callable detect_moments(events) in spine.moments"
    return detect_moments


def _moment_names(moments):
    return {m["moment"] for m in moments}


def test_first_signal_from_analysis_completed(ev_analysis_started, ev_analysis_completed_basic):
    detect_moments = _import_detector()

    moments = detect_moments([ev_analysis_started, ev_analysis_completed_basic])
    assert "FIRST_SIGNAL" in _moment_names(moments)
    first = next(m for m in moments if m["moment"] == "FIRST_SIGNAL")
    assert ev_analysis_completed_basic["event_id"] in first.get("trigger_events", [])


def test_first_signal_prefers_view_rendered(ev_analysis_completed_basic, ev_view_rendered_spectrum):
    detect_moments = _import_detector()

    moments = detect_moments([ev_analysis_completed_basic, ev_view_rendered_spectrum])
    first = next(m for m in moments if m["moment"] == "FIRST_SIGNAL")
    # Prefer view_rendered as trigger if your implementation supports it
    assert ev_view_rendered_spectrum["event_id"] in first.get("trigger_events", []) or \
           ev_analysis_completed_basic["event_id"] in first.get("trigger_events", [])


def test_hesitation_idle_timeout(ev_view_rendered_spectrum, ev_idle_timeout_9s):
    detect_moments = _import_detector()

    moments = detect_moments([ev_view_rendered_spectrum, ev_idle_timeout_9s])
    assert "HESITATION" in _moment_names(moments)


def test_hesitation_repeated_hover(ev_hover_1, ev_hover_2):
    detect_moments = _import_detector()

    moments = detect_moments([ev_hover_1, ev_hover_2])
    assert "HESITATION" in _moment_names(moments)


def test_no_hesitation_if_param_changed(ev_view_rendered_spectrum, ev_parameter_changed):
    detect_moments = _import_detector()

    moments = detect_moments([ev_view_rendered_spectrum, ev_parameter_changed])
    assert "HESITATION" not in _moment_names(moments)


def test_overload_explicit(ev_user_feedback_too_much):
    detect_moments = _import_detector()

    moments = detect_moments([ev_user_feedback_too_much])
    assert "OVERLOAD" in _moment_names(moments)


def test_overload_undo_spike(ev_undo_1, ev_undo_2, ev_undo_3):
    detect_moments = _import_detector()

    moments = detect_moments([ev_undo_1, ev_undo_2, ev_undo_3])
    assert "OVERLOAD" in _moment_names(moments)


def test_decision_required(ev_decision_required):
    detect_moments = _import_detector()

    moments = detect_moments([ev_decision_required])
    assert "DECISION_REQUIRED" in _moment_names(moments)


def test_finding_high_conf(ev_artifact_created_high_conf, ev_attention_requested):
    detect_moments = _import_detector()

    moments = detect_moments([ev_artifact_created_high_conf, ev_attention_requested])
    assert "FINDING" in _moment_names(moments)


def test_no_finding_low_conf(ev_artifact_created_low_conf):
    detect_moments = _import_detector()

    moments = detect_moments([ev_artifact_created_low_conf])
    assert "FINDING" not in _moment_names(moments)


def test_error_analysis_failed(ev_analysis_failed):
    detect_moments = _import_detector()

    moments = detect_moments([ev_analysis_failed])
    assert "ERROR" in _moment_names(moments)


def test_priority_error_suppresses_overload(ev_user_feedback_too_much, ev_analysis_failed):
    detect_moments = _import_detector()

    moments = detect_moments([ev_user_feedback_too_much, ev_analysis_failed])
    names = _moment_names(moments)
    assert "ERROR" in names
    # Priority spec: ERROR suppresses OVERLOAD
    assert "OVERLOAD" not in names
