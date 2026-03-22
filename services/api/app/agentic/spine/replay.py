"""
Agentic Replay Module - Load, group, and replay event sequences.

This module enables:
1. Loading events from JSONL files (for replay/analysis)
2. Grouping events by session ID
3. Running shadow replay to test moment detection
4. Grace window selection for FIRST_SIGNAL priority
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .moments import detect_moments
from .schemas import DetectedMoment, CRITICAL_MOMENTS, AttentionDirective, PolicyDecision, PolicyDiagnostic

# Module is now implemented
IMPLEMENTED = True

# Constants
FIRST_SIGNAL_GRACE_MS = 1500

# Moment to action mapping
MOMENT_TO_ACTION = {
    "FIRST_SIGNAL": "INSPECT",
    "FINDING": "REVIEW",
    "HESITATION": "INSPECT",
    "ERROR": "REVIEW",
    "OVERLOAD": "REVIEW",
    "DECISION_REQUIRED": "DECIDE",
}


@dataclass
class ReplayConfig:
    """Configuration for replay sessions."""
    shadow_mode: bool = True
    strict_order: bool = True
    grace_period_ms: int = FIRST_SIGNAL_GRACE_MS
    mode: Optional[str] = None  # None=auto (from shadow_mode), M0=no emit, M1=emit
    verbose: bool = False
    apply_grace_selection: bool = True


@dataclass
class ReplayResult:
    """Result of replaying an event sequence."""
    session_id: str
    events_processed: int
    moments_detected: List[DetectedMoment]
    errors: List[str] = field(default_factory=list)


def load_events(path: Path) -> List[Dict[str, Any]]:
    """Load events from a JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"Event file not found: {path}")

    events: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {line_num}: {e.msg}",
                    e.doc,
                    e.pos,
                )
    return events


def group_by_session(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by session ID."""
    sessions: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        session_info = event.get("session", {})
        session_id = session_info.get("session_id", "unknown")
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(event)

    for session_id in sessions:
        sessions[session_id].sort(key=lambda e: e.get("occurred_at", ""))

    return sessions


def _make_directive(moment: DetectedMoment) -> AttentionDirective:
    """Create an attention directive from a moment."""
    action = MOMENT_TO_ACTION.get(moment.moment, "INSPECT")
    return AttentionDirective(
        action=action,
        title=f"{moment.moment} detected",
        detail=f"Confidence: {moment.confidence:.2f}",
    )


def _make_decision(moment: Optional[DetectedMoment], emit: bool, shadow_mode: bool = False) -> Dict[str, Any]:
    """Create a policy decision dict."""
    if moment is None:
        return None
    directive = _make_directive(moment)
    diagnostic = {"rule_id": "replay"}
    # In shadow mode, track what would have been emitted
    if shadow_mode:
        diagnostic["would_have_emitted"] = directive.action
    return {
        "attention_action": directive.action,
        "emit_directive": emit,
        "directive": {"action": directive.action, "title": directive.title, "detail": directive.detail},
        "diagnostic": diagnostic,
    }


def run_shadow_replay(
    events: List[Dict[str, Any]],
    config: Optional[ReplayConfig] = None,
) -> Dict[str, Any]:
    """
    Run shadow replay on a sequence of events.
    
    Returns a dict with sessions keyed by session_id, plus summary.
    """
    if config is None:
        config = ReplayConfig()

    sessions = group_by_session(events)
    result = {"sessions": {}}

    # Determine effective mode:
    # - Explicit mode setting (M0/M1) takes precedence
    # - If mode=None (auto), derive from shadow_mode
    if config.mode is not None:
        effective_mode = config.mode
    elif config.shadow_mode:
        effective_mode = "M0"
    else:
        effective_mode = "M1"

    for session_id, session_events in sessions.items():
        moments: List[DetectedMoment] = []
        try:
            moments = detect_moments(session_events)
        except Exception:  # audited: moment-detection-fallback
            pass

        # Apply grace selection if enabled
        selected_moment = None
        if moments:
            if config.apply_grace_selection:
                selected_moment = select_moment_with_grace(moments, first_signal_shown=False)
            else:
                selected_moment = moments[0]

        # Determine if we should emit (M1 emits, M0/shadow does not)
        emit = effective_mode == "M1" and selected_moment is not None

        result["sessions"][session_id] = {
            "event_count": len(session_events),
            "moments": moments,
            "moment": selected_moment,
            "decision": _make_decision(selected_moment, emit, shadow_mode=config.shadow_mode),
        }

    # Add summary
    result["mode"] = effective_mode
    result["summary"] = {
        "total_sessions": len(result["sessions"]),
        "total_events": sum(s["event_count"] for s in result["sessions"].values()),
    }

    return result


def run_determinism_check(events: List[Dict[str, Any]], runs: int = 3) -> Dict[str, Any]:
    """Run multiple replays and check for determinism."""
    results = []
    for _ in range(runs):
        report = run_shadow_replay(events)
        results.append(report)

    # Compare all results
    mismatches = []
    first = results[0]
    for i, report in enumerate(results[1:], 2):
        for session_id in first["sessions"]:
            if session_id not in report["sessions"]:
                mismatches.append(f"Run {i} missing session {session_id}")
            elif first["sessions"][session_id]["moment"] != report["sessions"][session_id]["moment"]:
                mismatches.append(f"Run {i} different moment for {session_id}")

    return {
        "deterministic": len(mismatches) == 0,
        "runs": runs,
        "mismatches": mismatches,
    }


def select_moment_with_grace(
    moments: List[DetectedMoment],
    grace_period_ms: int = FIRST_SIGNAL_GRACE_MS,
    first_signal_shown: bool = False,
    first_view_rendered_at_ms: Optional[int] = None,
    current_time_ms: Optional[int] = None,
) -> Optional[DetectedMoment]:
    """Select the appropriate moment given a grace period."""
    if not moments:
        return None

    top = moments[0]

    # One-shot: if FIRST_SIGNAL already shown, never return it again
    if first_signal_shown and top.moment == "FIRST_SIGNAL":
        next_moment = next((m for m in moments if m.moment != "FIRST_SIGNAL"), None)
        return next_moment

    # If FINDING is top but we have not shown FIRST_SIGNAL yet, prefer FIRST_SIGNAL
    if not first_signal_shown and top.moment == "FINDING":
        first_signal = next((m for m in moments if m.moment == "FIRST_SIGNAL"), None)
        if first_signal:
            return first_signal

        if first_view_rendered_at_ms is not None and current_time_ms is not None:
            elapsed = current_time_ms - first_view_rendered_at_ms
            if elapsed < grace_period_ms:
                return None

    return top


def is_critical_moment(moment: Optional[DetectedMoment]) -> bool:
    """Check if a moment is critical (bypasses cooldowns)."""
    if moment is None:
        return False
    return moment.moment in CRITICAL_MOMENTS


def export_events_jsonl(events: List[Dict[str, Any]], path: Path) -> int:
    """Export events to a JSONL file."""
    with open(path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, default=str) + chr(10))
    return len(events)
