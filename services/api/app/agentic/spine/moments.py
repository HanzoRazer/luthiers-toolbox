"""
Moment Detection Engine — Detects user moments from event streams.

Moments are high-level abstractions that summarize what's happening:
- FIRST_SIGNAL: User just started or analysis completed
- HESITATION: User has been idle (not changing parameters)
- OVERLOAD: User gave "too_much" feedback or multiple undos
- FINDING: High-confidence artifact was created
- DECISION_REQUIRED: Explicit decision point reached
- ERROR: Analysis failed or system error occurred

Priority (highest to lowest):
ERROR > OVERLOAD > DECISION_REQUIRED > FINDING > HESITATION > FIRST_SIGNAL

Note: Returns ALL detected moments (sorted by priority) so that
the grace selector can prefer FIRST_SIGNAL over FINDING in FTUE.
"""

from __future__ import annotations

from typing import TypedDict, List, Dict, Any

# Priority order (lower = higher priority)
MOMENT_PRIORITY: Dict[str, int] = {
    "ERROR": 1,
    "OVERLOAD": 2,
    "DECISION_REQUIRED": 3,
    "FINDING": 4,
    "HESITATION": 5,
    "FIRST_SIGNAL": 6,
}


class DetectedMoment(TypedDict):
    moment: str
    confidence: float
    trigger_events: List[str]
    priority: int


def detect_moments(events: List[Dict[str, Any]]) -> List[DetectedMoment]:
    """
    Detect moments from a list of AgentEventV1 events.

    Returns a list of ALL detected moments, sorted by priority (highest first).
    The caller (replay harness or store) applies grace selection to choose
    which moment to act on.
    """
    if not events:
        return []

    # Sort by occurred_at
    evs = sorted(events, key=lambda e: e.get("occurred_at", ""))

    detected: List[tuple] = []  # (moment, confidence, trigger_events)

    # ERROR detection
    for e in evs:
        if e.get("event_type") in ("analysis_failed", "system_error"):
            detected.append(("ERROR", 0.95, [e["event_id"]]))
            break

    # OVERLOAD (explicit too_much feedback)
    for e in evs:
        if e.get("event_type") == "user_feedback":
            payload = e.get("payload", {})
            if payload.get("feedback") == "too_much":
                if not any(d[0] == "OVERLOAD" for d in detected):
                    detected.append(("OVERLOAD", 0.9, [e["event_id"]]))
                break

    # OVERLOAD (undo spike)
    if not any(d[0] == "OVERLOAD" for d in detected):
        undo_ids = [
            e["event_id"]
            for e in evs
            if e.get("event_type") == "user_action"
            and e.get("payload", {}).get("action") == "undo"
        ]
        if len(undo_ids) >= 3:
            detected.append(("OVERLOAD", 0.75, undo_ids[:3]))

    # DECISION_REQUIRED
    for e in evs:
        if e.get("event_type") == "decision_required":
            detected.append(("DECISION_REQUIRED", 0.9, [e["event_id"]]))
            break

    # FINDING (high-confidence artifact)
    for e in evs:
        if e.get("event_type") == "artifact_created":
            payload = e.get("payload", {})
            if (
                payload.get("schema") == "wolf_candidates_v1"
                and float(payload.get("confidence_max", 0)) >= 0.6
            ):
                detected.append(("FINDING", 0.7, [e["event_id"]]))
                break

    # HESITATION (idle timeout without parameter change)
    has_param_change = any(
        e.get("event_type") == "user_action"
        and e.get("payload", {}).get("action") == "parameter_changed"
        for e in evs
    )
    if not has_param_change:
        idle_event = next(
            (e for e in evs if e.get("event_type") == "idle_timeout"),
            None,
        )
        if idle_event:
            detected.append(("HESITATION", 0.8, [idle_event["event_id"]]))

    # FIRST_SIGNAL (view rendered or analysis completed)
    # Always check for view_rendered, regardless of other moments
    view_event = next(
        (
            e
            for e in evs
            if e.get("event_type") == "user_action"
            and e.get("payload", {}).get("action") == "view_rendered"
        ),
        None,
    )
    if view_event:
        detected.append(("FIRST_SIGNAL", 0.75, [view_event["event_id"]]))
    else:
        comp_event = next(
            (e for e in evs if e.get("event_type") == "analysis_completed"),
            None,
        )
        if comp_event:
            detected.append(("FIRST_SIGNAL", 0.65, [comp_event["event_id"]]))

    if not detected:
        return []

    # Sort by priority (highest first)
    detected.sort(key=lambda d: MOMENT_PRIORITY.get(d[0], 999))

    return [
        DetectedMoment(
            moment=d[0],
            confidence=d[1],
            trigger_events=d[2],
            priority=MOMENT_PRIORITY.get(d[0], 999),
        )
        for d in detected
    ]
