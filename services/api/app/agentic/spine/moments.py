"""
Agentic Moment Detection - Identifies significant moments from event streams.

Moments represent points in the user workflow where the system should
consider providing guidance. This module implements the same detection
logic as the frontend for consistency.

Moment Types (in priority order):
1. ERROR: Something failed (analysis_failed, system_error)
2. OVERLOAD: User overwhelmed (3+ undos, explicit too_much feedback)
3. DECISION_REQUIRED: User needs to choose (decision_required event)
4. FINDING: Significant result found (high-confidence artifact)
5. HESITATION: User appears stuck (idle_timeout, no parameter changes)
6. FIRST_SIGNAL: Initial engagement (view_rendered, analysis_completed)
"""

from __future__ import annotations

from typing import Any, Dict, List

from .schemas import DetectedMoment, MOMENT_PRIORITY

# Module is now implemented
IMPLEMENTED = True


def detect_moments(events: List[Dict[str, Any]]) -> List[DetectedMoment]:
    """
    Detect significant moments from a sequence of events.

    Args:
        events: List of event dictionaries (AgentEventV1 compatible)

    Returns:
        List of detected moments, sorted by priority (highest first)
    """
    if not events:
        return []

    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda e: e.get("occurred_at", ""))
    detected: List[tuple] = []

    # --- ERROR Detection ---
    for ev in sorted_events:
        event_type = ev.get("event_type", "")
        if event_type in ("analysis_failed", "system_error"):
            detected.append(("ERROR", 0.95, [ev.get("event_id", "")]))
            break

    # --- OVERLOAD Detection (explicit too_much feedback) ---
    if not _has_moment(detected, "ERROR"):
        for ev in sorted_events:
            if ev.get("event_type") == "user_feedback":
                payload = ev.get("payload", {})
                if payload.get("feedback") == "too_much":
                    detected.append(("OVERLOAD", 0.9, [ev.get("event_id", "")]))
                    break

    # --- OVERLOAD Detection (undo spike: 3+ undos) ---
    if not _has_moment(detected, "OVERLOAD"):
        undo_ids = [
            ev.get("event_id", "")
            for ev in sorted_events
            if ev.get("event_type") == "user_action"
            and ev.get("payload", {}).get("action") == "undo"
        ]
        if len(undo_ids) >= 3:
            detected.append(("OVERLOAD", 0.75, undo_ids[:3]))

    # --- DECISION_REQUIRED Detection ---
    if not _has_moment(detected, "ERROR") and not _has_moment(detected, "OVERLOAD"):
        for ev in sorted_events:
            if ev.get("event_type") == "decision_required":
                detected.append(("DECISION_REQUIRED", 0.9, [ev.get("event_id", "")]))
                break

    # --- FINDING Detection (high-confidence artifact) ---
    if not _has_any_moment(detected, ["ERROR", "OVERLOAD", "DECISION_REQUIRED"]):
        for ev in sorted_events:
            if ev.get("event_type") == "artifact_created":
                payload = ev.get("payload", {})
                schema = payload.get("schema", "")
                confidence = float(payload.get("confidence_max", 0))
                if schema == "wolf_candidates_v1" and confidence >= 0.6:
                    detected.append(("FINDING", 0.7, [ev.get("event_id", "")]))
                    break

    # --- HESITATION Detection (idle timeout, no param changes) ---
    if not _has_any_moment(detected, ["ERROR", "OVERLOAD", "DECISION_REQUIRED", "FINDING"]):
        has_param_change = any(
            ev.get("event_type") == "user_action"
            and ev.get("payload", {}).get("action") == "parameter_changed"
            for ev in sorted_events
        )
        if not has_param_change:
            idle_event = next(
                (ev for ev in sorted_events if ev.get("event_type") == "idle_timeout"),
                None,
            )
            if idle_event:
                detected.append(("HESITATION", 0.8, [idle_event.get("event_id", "")]))

    # --- FIRST_SIGNAL Detection (initial engagement) ---
    if not detected:
        view_event = next(
            (
                ev for ev in sorted_events
                if ev.get("event_type") == "user_action"
                and ev.get("payload", {}).get("action") == "view_rendered"
            ),
            None,
        )
        if view_event:
            detected.append(("FIRST_SIGNAL", 0.75, [view_event.get("event_id", "")]))
        else:
            comp_event = next(
                (ev for ev in sorted_events if ev.get("event_type") == "analysis_completed"),
                None,
            )
            if comp_event:
                detected.append(("FIRST_SIGNAL", 0.65, [comp_event.get("event_id", "")]))

    if not detected:
        return []

    # Sort by priority (lower number = higher priority)
    detected.sort(key=lambda x: MOMENT_PRIORITY.get(x[0], 999))

    # Return only the highest priority moment
    best = detected[0]
    return [
        DetectedMoment(
            moment=best[0],
            confidence=best[1],
            trigger_events=best[2],
        )
    ]


def _has_moment(detected: List[tuple], moment: str) -> bool:
    """Check if a specific moment type is in the detected list."""
    return any(d[0] == moment for d in detected)


def _has_any_moment(detected: List[tuple], moments: List[str]) -> bool:
    """Check if any of the specified moment types are in the detected list."""
    return any(d[0] in moments for d in detected)
