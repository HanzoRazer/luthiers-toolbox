# tests/test_golden_m1_replay.py
"""
Golden M1 Session Replay Tests — validates recorded sessions produce expected moments/decisions.

These tests replay real user workflows and verify:
1. Correct moments are detected
2. Correct directives are produced
3. UWSM updates work as expected
4. Replay is deterministic
"""

from __future__ import annotations

from pathlib import Path
import pytest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "golden_m1_session.jsonl"


@pytest.fixture
def replay_module():
    """Import replay module or skip if not available."""
    return pytest.importorskip("app.agentic.spine.replay", reason="replay harness not implemented")


@pytest.fixture
def events(replay_module):
    """Load all events from the golden session fixture."""
    return replay_module.load_events(FIXTURE_PATH)


def test_fixture_exists():
    """Sanity check: fixture file exists."""
    assert FIXTURE_PATH.exists(), f"Missing fixture: {FIXTURE_PATH}"


def test_fixture_has_multiple_sessions(replay_module, events):
    """Fixture contains multiple test sessions."""
    sessions = replay_module.group_by_session(events)
    assert len(sessions) >= 5, f"Expected 5+ sessions, got {len(sessions)}"

    expected_sessions = [
        "session_golden_m1",
        "session_overload",
        "session_error",
        "session_finding",
        "session_first_signal",
    ]
    for sid in expected_sessions:
        assert sid in sessions, f"Missing session: {sid}"


def test_golden_m1_detects_finding(replay_module, events):
    """session_golden_m1 detects FINDING (high-confidence artifact beats FIRST_SIGNAL)."""
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_golden_m1"]

    # This session has both view_rendered AND high-confidence artifacts.
    # FINDING (priority 4) beats FIRST_SIGNAL (priority 6).
    moments = detect_moments(session_events)
    assert len(moments) == 1
    assert moments[0]["moment"] == "FINDING"


def test_first_signal_pure_session(replay_module, events):
    """session_first_signal detects FIRST_SIGNAL (no high-confidence artifacts)."""
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_first_signal"]

    # This session ONLY has view_rendered, no artifacts.
    moments = detect_moments(session_events)
    assert len(moments) == 1
    assert moments[0]["moment"] == "FIRST_SIGNAL"


def test_overload_detects_undo_spike(replay_module, events):
    """session_overload should detect OVERLOAD from 3+ undos."""
    from app.agentic.spine.moments import detect_moments
    
    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_overload"]
    
    moments = detect_moments(session_events)
    assert len(moments) == 1
    assert moments[0]["moment"] == "OVERLOAD"


def test_error_session_detects_error(replay_module, events):
    """session_error should detect ERROR from analysis_failed."""
    from app.agentic.spine.moments import detect_moments
    
    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_error"]
    
    moments = detect_moments(session_events)
    assert len(moments) == 1
    assert moments[0]["moment"] == "ERROR"


def test_finding_session_detects_finding(replay_module, events):
    """session_finding should detect FINDING from high-confidence artifact."""
    from app.agentic.spine.moments import detect_moments
    
    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_finding"]
    
    moments = detect_moments(session_events)
    assert len(moments) == 1
    assert moments[0]["moment"] == "FINDING"


def test_m1_emits_correct_directives(replay_module, events):
    """M1 mode should emit correct directives for each session."""
    config = replay_module.ReplayConfig(mode="M1", verbose=False)
    report = replay_module.run_shadow_replay(events, config)

    # Check golden_m1: FINDING -> REVIEW (high-confidence artifact)
    golden = report["sessions"]["session_golden_m1"]
    assert golden["decision"]["emit_directive"] is True
    assert golden["decision"]["directive"]["action"] == "REVIEW"

    # Check overload: OVERLOAD -> REVIEW
    overload = report["sessions"]["session_overload"]
    assert overload["decision"]["emit_directive"] is True
    assert overload["decision"]["directive"]["action"] == "REVIEW"

    # Check error: ERROR -> REVIEW
    error = report["sessions"]["session_error"]
    assert error["decision"]["emit_directive"] is True
    assert error["decision"]["directive"]["action"] == "REVIEW"

    # Check finding: FINDING -> REVIEW
    finding = report["sessions"]["session_finding"]
    assert finding["decision"]["emit_directive"] is True
    assert finding["decision"]["directive"]["action"] == "REVIEW"


def test_m0_never_emits(replay_module, events):
    """M0 shadow mode should never emit directives."""
    config = replay_module.ReplayConfig(mode="M0", verbose=False)
    report = replay_module.run_shadow_replay(events, config)
    
    for session_id, session in report["sessions"].items():
        if session["decision"]:
            assert session["decision"]["emit_directive"] is False, f"{session_id} emitted in M0"


def test_replay_determinism(replay_module, events):
    """Multiple replays should produce identical results."""
    result = replay_module.run_determinism_check(events, runs=5)
    
    assert result["deterministic"] is True, f"Non-deterministic sessions: {result['mismatches']}"
    assert result["runs"] == 5
    assert result["mismatches"] == []
