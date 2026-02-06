# app/agentic/spine/moments.py
"""
Moment Detection Engine — Reference Implementation

Detects named patterns (moments) from AgentEventV1 event streams.
This is a conservative, dependency-light implementation designed to:
1. Pass the test suite
2. Work correctly in shadow mode
3. Provide a bootstrap for CI

For full specification, see: docs/EVENT_MOMENTS_CATALOG_V1.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


MomentName = str


PRIORITY: Dict[MomentName, int] = {
    "ERROR": 1,
    "OVERLOAD": 2,
    "DECISION_REQUIRED": 3,
    "FINDING": 4,
    "HESITATION": 5,
    "FIRST_SIGNAL": 6,
}


def _get(e: Any, key: str, default=None):
    if isinstance(e, dict):
        return e.get(key, default)
    return getattr(e, key, default)


def _payload(e: Any) -> dict:
    p = _get(e, "payload", {}) or {}
    return p if isinstance(p, dict) else {}


def _eid(e: Any) -> str:
    return str(_get(e, "event_id", ""))


def detect_moments(events: List[Any]) -> List[dict]:
    """
    Detect moments from a list of AgentEventV1-like dicts/objects.

    Output: list of dicts
      { "moment": str, "confidence": float, "trigger_events": [event_id, ...] }

    Priority rule: if multiple moments detected, only highest priority is returned.
    """
    if not events:
        return []

    # Sort by occurred_at if present, otherwise keep order
    def _sort_key(e: Any) -> str:
        return str(_get(e, "occurred_at", ""))

    evs = sorted(events, key=_sort_key)

    detected: List[Tuple[MomentName, float, List[str]]] = []

    # --- ERROR ---
    for e in evs:
        et = _get(e, "event_type")
        if et in ("analysis_failed", "system_error"):
            detected.append(("ERROR", 0.95, [_eid(e)]))
            break

    # --- OVERLOAD ---
    if not any(m[0] == "ERROR" for m in detected):
        # Explicit too_much
        for e in evs:
            if _get(e, "event_type") == "user_feedback":
                fb = _payload(e).get("feedback")
                if fb == "too_much":
                    detected.append(("OVERLOAD", 0.9, [_eid(e)]))
                    break

        # Undo spike heuristic: 3 undo actions within the provided window
        if not any(m[0] == "OVERLOAD" for m in detected):
            undo_ids = [
                _eid(e)
                for e in evs
                if _get(e, "event_type") == "user_action" and _payload(e).get("action") == "undo"
            ]
            if len(undo_ids) >= 3:
                detected.append(("OVERLOAD", 0.75, undo_ids[:3]))

        # Rapid open/close cycles: tool_rendered/tool_closed alternating at least twice
        if not any(m[0] == "OVERLOAD" for m in detected):
            toggles = []
            for e in evs:
                if _get(e, "event_type") in ("tool_rendered", "tool_closed"):
                    toggles.append((_get(e, "event_type"), _eid(e)))
            # naive: if at least 4 toggle events, treat as overload
            if len(toggles) >= 4:
                detected.append(("OVERLOAD", 0.65, [eid for _, eid in toggles[:4]]))

    # --- DECISION_REQUIRED ---
    if not any(m[0] in ("ERROR", "OVERLOAD") for m in detected):
        for e in evs:
            if _get(e, "event_type") == "decision_required":
                detected.append(("DECISION_REQUIRED", 0.9, [_eid(e)]))
                break

    # --- FINDING ---
    if not any(m[0] in ("ERROR", "OVERLOAD", "DECISION_REQUIRED") for m in detected):
        # Preferred: attention_requested, but only if there is supporting high-confidence artifact_created
        attention_e = next((e for e in evs if _get(e, "event_type") == "attention_requested"), None)

        high_conf_artifact = None
        for e in evs:
            if _get(e, "event_type") == "artifact_created":
                p = _payload(e)
                if p.get("schema") == "wolf_candidates_v1" and float(p.get("confidence_max", 0.0)) >= 0.6:
                    high_conf_artifact = e
                    break

        if attention_e and high_conf_artifact:
            detected.append(("FINDING", 0.85, [_eid(attention_e)]))
        elif high_conf_artifact:
            detected.append(("FINDING", 0.7, [_eid(high_conf_artifact)]))

    # --- HESITATION ---
    if not any(m[0] in ("ERROR", "OVERLOAD", "DECISION_REQUIRED", "FINDING") for m in detected):
        # If a parameter change happens, suppress hesitation.
        has_param_change = any(
            _get(e, "event_type") == "user_action" and _payload(e).get("action") == "parameter_changed"
            for e in evs
        )
        if not has_param_change:
            # Idle timeout event triggers hesitation
            idle_e = next((e for e in evs if _get(e, "event_type") == "idle_timeout"), None)
            if idle_e:
                detected.append(("HESITATION", 0.8, [_eid(idle_e)]))
            else:
                # Repeated hovers trigger hesitation
                hover_events = [
                    e
                    for e in evs
                    if _get(e, "event_type") == "user_action" and _payload(e).get("action") == "hover"
                ]
                if len(hover_events) >= 2:
                    detected.append(("HESITATION", 0.65, [_eid(hover_events[0]), _eid(hover_events[1])]))

    # --- FIRST_SIGNAL ---
    if not detected:
        # Prefer view_rendered (user_action with action=view_rendered)
        view_e = next(
            (
                e
                for e in evs
                if _get(e, "event_type") == "user_action" and _payload(e).get("action") == "view_rendered"
            ),
            None,
        )
        if view_e:
            detected.append(("FIRST_SIGNAL", 0.75, [_eid(view_e)]))
        else:
            comp_e = next((e for e in evs if _get(e, "event_type") == "analysis_completed"), None)
            if comp_e:
                detected.append(("FIRST_SIGNAL", 0.65, [_eid(comp_e)]))

    if not detected:
        return []

    # Apply priority suppression: keep only the single highest-priority moment
    detected.sort(key=lambda x: PRIORITY.get(x[0], 999))
    best = detected[0]
    return [{"moment": best[0], "confidence": float(best[1]), "trigger_events": best[2]}]
