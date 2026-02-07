# tests/test_replay_smoke.py
"""
Replay smoke test — runs shadow-mode replay against a synthetic fixture.

This test validates that the entire spine pipeline works end-to-end:
- load_events() parses JSONL
- run_shadow_replay() processes events through moment detection, UWSM update, and policy
- Shadow mode (M0) produces a report with diagnostic but no emitted directive
"""

from __future__ import annotations

from pathlib import Path
import pytest


def test_replay_smoke_runs_and_returns_summary():
    replay = pytest.importorskip("app.agentic.spine.replay", reason="replay harness not implemented")
    fixture = Path(__file__).parent / "fixtures" / "smoke_session.jsonl"

    events = replay.load_events(fixture)
    report = replay.run_shadow_replay(events, replay.ReplayConfig(mode="M0", verbose=False))

    assert report["mode"] == "M0"
    assert report["summary"]["total_sessions"] >= 1
    assert "session_smoke" in report["sessions"]

    sess = report["sessions"]["session_smoke"]
    assert sess["event_count"] == 4
    assert "moment" in sess and "decision" in sess
    # Shadow mode: no directive emitted
    assert sess["decision"]["emit_directive"] is False
    assert sess["decision"]["diagnostic"].get("would_have_emitted") is not None
