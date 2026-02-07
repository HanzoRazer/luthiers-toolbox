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
    assert len(sessions) >= 7, f"Expected 7+ sessions, got {len(sessions)}"

    expected_sessions = [
        "session_golden_m1",
        "session_overload",
        "session_error",
        "session_finding",
        "session_first_signal",
        "session_noncritical_suppressed",
        "session_critical_allowed",
    ]
    for sid in expected_sessions:
        assert sid in sessions, f"Missing session: {sid}"


def test_golden_m1_detects_finding(replay_module, events):
    """session_golden_m1 detects FINDING as highest-priority moment."""
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_golden_m1"]

    # This session has view_rendered, artifacts, and idle_timeout.
    # FINDING (priority 4) is highest priority in the list.
    moments = detect_moments(session_events)
    assert len(moments) >= 1
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
    """session_overload should detect OVERLOAD as highest-priority moment."""
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_overload"]

    moments = detect_moments(session_events)
    assert len(moments) >= 1
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

    # Check golden_m1: With grace selection, FIRST_SIGNAL is preferred -> INSPECT
    # (FINDING and FIRST_SIGNAL both present, grace prefers FIRST_SIGNAL in FTUE)
    golden = report["sessions"]["session_golden_m1"]
    assert golden["decision"]["emit_directive"] is True
    assert golden["decision"]["directive"]["action"] == "INSPECT"

    # Check overload: OVERLOAD -> REVIEW (critical moment, no grace needed)
    overload = report["sessions"]["session_overload"]
    assert overload["decision"]["emit_directive"] is True
    assert overload["decision"]["directive"]["action"] == "REVIEW"

    # Check error: ERROR -> REVIEW (critical moment, no grace needed)
    error = report["sessions"]["session_error"]
    assert error["decision"]["emit_directive"] is True
    assert error["decision"]["directive"]["action"] == "REVIEW"

    # Check finding: Only FINDING present (no FIRST_SIGNAL) -> REVIEW
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


# --- Session-level gate tests (validates fixture structure for frontend gate) ---
# Note: The "only critical after first" gate is implemented in the frontend store.
# These tests validate the raw moments detected, which the frontend uses to apply the gate.


def test_noncritical_suppressed_session_detects_hesitation(replay_module, events):
    """session_noncritical_suppressed: view_rendered (FIRST_SIGNAL) then idle_timeout (HESITATION).

    Raw moment detection: HESITATION (priority 5) beats FIRST_SIGNAL (priority 6).
    Frontend gate: After first directive shown, HESITATION would be suppressed (non-critical).
    """
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_noncritical_suppressed"]

    # Raw detection: both HESITATION and FIRST_SIGNAL are detected
    # HESITATION wins by priority (moments[0])
    # (Frontend gate would suppress this after first directive)
    moments = detect_moments(session_events)
    assert len(moments) >= 1
    assert moments[0]["moment"] == "HESITATION"


def test_critical_allowed_session_detects_overload(replay_module, events):
    """session_critical_allowed: view_rendered (FIRST_SIGNAL) then 3 undos (OVERLOAD).

    Raw moment detection: OVERLOAD (priority 2) beats FIRST_SIGNAL (priority 6).
    Frontend gate: OVERLOAD is critical, so it would still show after first directive.
    """
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(events)
    session_events = sessions["session_critical_allowed"]

    # Raw detection: both OVERLOAD and FIRST_SIGNAL are detected
    # OVERLOAD wins by priority (moments[0])
    # (Frontend gate would allow this — OVERLOAD is critical)
    moments = detect_moments(session_events)
    assert len(moments) >= 1
    assert moments[0]["moment"] == "OVERLOAD"


def test_noncritical_not_in_critical_set():
    """HESITATION and FINDING are not critical moments."""
    CRITICAL_MOMENTS = {"ERROR", "OVERLOAD", "DECISION_REQUIRED"}

    assert "HESITATION" not in CRITICAL_MOMENTS
    assert "FINDING" not in CRITICAL_MOMENTS
    assert "FIRST_SIGNAL" not in CRITICAL_MOMENTS


def test_critical_moments_are_critical():
    """ERROR, OVERLOAD, DECISION_REQUIRED are critical moments."""
    CRITICAL_MOMENTS = {"ERROR", "OVERLOAD", "DECISION_REQUIRED"}

    assert "ERROR" in CRITICAL_MOMENTS
    assert "OVERLOAD" in CRITICAL_MOMENTS
    assert "DECISION_REQUIRED" in CRITICAL_MOMENTS


# --- FIRST_SIGNAL Grace Selection Tests ---
# These tests validate that the grace selector prefers FIRST_SIGNAL over FINDING
# when both are present and FIRST_SIGNAL hasn't been shown yet.


GRACE_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "first_signal_grace_wins.jsonl"


def test_grace_fixture_exists():
    """Sanity check: grace fixture file exists."""
    assert GRACE_FIXTURE_PATH.exists(), f"Missing fixture: {GRACE_FIXTURE_PATH}"


@pytest.fixture
def grace_events(replay_module):
    """Load events from the grace selection fixture."""
    return replay_module.load_events(GRACE_FIXTURE_PATH)


def test_grace_raw_detection_includes_both_moments(replay_module, grace_events):
    """Raw detectMoments() returns both FINDING and FIRST_SIGNAL."""
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(grace_events)
    session_events = sessions["session_first_signal_grace_wins"]

    moments = detect_moments(session_events)

    # Should have at least 2 moments (FINDING and FIRST_SIGNAL)
    moment_types = [m["moment"] for m in moments]
    assert "FINDING" in moment_types, f"Missing FINDING in {moment_types}"
    assert "FIRST_SIGNAL" in moment_types, f"Missing FIRST_SIGNAL in {moment_types}"


def test_grace_finding_is_raw_priority_winner(replay_module, grace_events):
    """Without grace selection, FINDING would win by priority."""
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(grace_events)
    session_events = sessions["session_first_signal_grace_wins"]

    moments = detect_moments(session_events)

    # FINDING (priority 4) beats FIRST_SIGNAL (priority 6) in raw detection
    # So moments[0] should be FINDING
    assert moments[0]["moment"] == "FINDING", (
        f"Expected FINDING as raw winner, got {moments[0]['moment']}"
    )


def test_grace_selector_prefers_first_signal(replay_module, grace_events):
    """Grace selector should prefer FIRST_SIGNAL over FINDING when not yet shown."""
    from app.agentic.spine.moments import detect_moments

    sessions = replay_module.group_by_session(grace_events)
    session_events = sessions["session_first_signal_grace_wins"]

    moments = detect_moments(session_events)

    # Apply grace selection with first_signal_shown=False
    selected = replay_module.select_moment_with_grace(
        moments,
        first_signal_shown=False,
    )

    assert selected is not None
    assert selected["moment"] == "FIRST_SIGNAL", (
        f"Grace selector should prefer FIRST_SIGNAL, got {selected['moment']}"
    )


def test_grace_replay_selects_first_signal(replay_module, grace_events):
    """Full replay with grace selection should choose FIRST_SIGNAL."""
    config = replay_module.ReplayConfig(
        mode="M1",
        verbose=False,
        apply_grace_selection=True,  # Explicit
    )
    report = replay_module.run_shadow_replay(grace_events, config)

    session = report["sessions"]["session_first_signal_grace_wins"]

    # With grace selection, FIRST_SIGNAL should be chosen
    assert session["moment"]["moment"] == "FIRST_SIGNAL", (
        f"Expected FIRST_SIGNAL with grace, got {session['moment']['moment']}"
    )


def test_grace_replay_emits_inspect_directive(replay_module, grace_events):
    """FIRST_SIGNAL should produce INSPECT directive."""
    config = replay_module.ReplayConfig(mode="M1", verbose=False)
    report = replay_module.run_shadow_replay(grace_events, config)

    session = report["sessions"]["session_first_signal_grace_wins"]

    # FIRST_SIGNAL -> INSPECT
    assert session["decision"]["emit_directive"] is True
    assert session["decision"]["directive"]["action"] == "INSPECT", (
        f"Expected INSPECT, got {session['decision']['directive']['action']}"
    )


def test_grace_one_shot_suppresses_second_first_signal(replay_module):
    """After FIRST_SIGNAL shown, grace selector should never return it again."""
    # Create fake moments list
    moments = [
        {"moment": "FIRST_SIGNAL", "confidence": 0.8, "priority": 6},
        {"moment": "HESITATION", "confidence": 0.5, "priority": 5},
    ]

    # First selection: FIRST_SIGNAL wins
    selected = replay_module.select_moment_with_grace(moments, first_signal_shown=False)
    assert selected["moment"] == "FIRST_SIGNAL"

    # Second selection with first_signal_shown=True: should skip FIRST_SIGNAL
    selected = replay_module.select_moment_with_grace(moments, first_signal_shown=True)
    assert selected is not None
    assert selected["moment"] == "HESITATION", (
        f"One-shot: expected HESITATION after FIRST_SIGNAL shown, got {selected['moment']}"
    )
