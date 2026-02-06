# app/agentic/spine/uwsm_update.py
"""
UWSM Update Engine — Reference Implementation

Applies deterministic preference updates from event streams.
Produces auditable update records per UWSM_UPDATE_RULES_V1.md.

This is a conservative, dependency-light implementation designed to:
1. Apply explicit and behavioral evidence
2. Respect hysteresis rules (no oscillation)
3. Emit audit records for every update

For full specification, see: docs/UWSM_UPDATE_RULES_V1.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone


# ----------------------------
# Utilities
# ----------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get(e: Any, key: str, default=None):
    if isinstance(e, dict):
        return e.get(key, default)
    return getattr(e, key, default)


def _payload(e: Any) -> dict:
    p = _get(e, "payload", {}) or {}
    return p if isinstance(p, dict) else {}


def _eid(e: Any) -> str:
    return str(_get(e, "event_id", ""))


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ----------------------------
# UWSM Defaults
# ----------------------------

DEFAULT_HALF_LIFE_DAYS = {
    "cognitive_load_sensitivity": 7,
    "guidance_density": 14,
    "initiative_tolerance": 21,
    "exploration_style": 10,
    "risk_posture": 10,
    "feedback_style": 21,
    "representation_preference": 14,
}

DEFAULT_FLOOR = 0.20

UWSM_DEFAULTS = {
    "guidance_density": ("medium", 0.20),
    "initiative_tolerance": ("shared_control", 0.20),
    "cognitive_load_sensitivity": ("medium", 0.20),
    "exploration_style": ("iterative", 0.20),
    "risk_posture": ("balanced", 0.20),
    "feedback_style": ("neutral", 0.20),
    "representation_preference": ("mixed", 0.20),
}

# Evidence deltas (v1)
DELTA_EXPLICIT = 0.20
DELTA_BEHAVIORAL = 0.05
DELTA_CONTRADICTION = -0.15

CAP_EXPLICIT = 0.90
CAP_BEHAVIORAL = 0.80


# ----------------------------
# Public API
# ----------------------------

def ensure_uwsm(uwsm: Optional[dict] = None) -> dict:
    """
    Ensure UWSM has required shape + defaults.
    """
    uwsm = uwsm or {}
    uwsm_version = uwsm.get("uwsm_version", "1.1")
    dims = uwsm.get("dimensions", {}) or {}

    for dim, (default_value, default_conf) in UWSM_DEFAULTS.items():
        if dim not in dims:
            dims[dim] = {
                "value": default_value,
                "confidence": float(default_conf),
                "decay": {
                    "half_life_days": DEFAULT_HALF_LIFE_DAYS[dim],
                    "floor": DEFAULT_FLOOR,
                },
            }
        else:
            d = dims[dim]
            d.setdefault("value", default_value)
            d.setdefault("confidence", float(default_conf))
            d.setdefault(
                "decay",
                {"half_life_days": DEFAULT_HALF_LIFE_DAYS[dim], "floor": DEFAULT_FLOOR},
            )
            d["decay"].setdefault("half_life_days", DEFAULT_HALF_LIFE_DAYS[dim])
            d["decay"].setdefault("floor", DEFAULT_FLOOR)

    uwsm["uwsm_version"] = uwsm_version
    uwsm["updated_at"] = uwsm.get("updated_at") or _now_iso()
    uwsm["dimensions"] = dims
    # Internal scratchpad for hysteresis: last evidence streaks
    uwsm.setdefault("_state", {})
    uwsm["_state"].setdefault("streaks", {})  # dim -> {"candidate": value, "count": int}
    return uwsm


def apply_uwsm_updates(
    *,
    events: List[Any],
    uwsm: Optional[dict] = None,
) -> Tuple[dict, List[dict]]:
    """
    Apply deterministic UWSM updates from an event list.
    Returns (updated_uwsm, audit_records).

    This is intentionally minimal and conservative:
    - Explicit evidence overrides quickly
    - Behavioral evidence nudges confidence slowly
    - Contradictions reduce confidence rather than flipping
    - Value flips require hysteresis (2 consecutive evidence windows)
    """
    uwsm = ensure_uwsm(uwsm)
    audits: List[dict] = []

    # 1) Extract evidence signals from events (deterministic)
    evidences = _extract_evidence(events)

    # 2) Apply evidence in order
    for ev in evidences:
        dim = ev["dimension"]
        audits.extend(_apply_evidence(uwsm, ev))

    uwsm["updated_at"] = _now_iso()
    return uwsm, audits


# ----------------------------
# Evidence Extraction
# ----------------------------

def _extract_evidence(events: List[Any]) -> List[dict]:
    """
    Convert raw events into a list of evidence dicts:
      {
        "dimension": str,
        "type": "explicit"|"behavioral"|"contradiction",
        "value": <candidate value>,
        "event_id": str,
        "signal_strength": float
      }
    """
    evidence: List[dict] = []

    # --- Explicit: user feedback "too_much" ---
    for e in events:
        if _get(e, "event_type") == "user_feedback":
            fb = _payload(e).get("feedback")
            if fb == "too_much":
                evidence.append(
                    {
                        "dimension": "cognitive_load_sensitivity",
                        "type": "explicit",
                        "value": "very_high",
                        "event_id": _eid(e),
                        "signal_strength": 1.0,
                        "rule_id": "UWSM_CLS_EXPLICIT_TOO_MUCH_v1",
                    }
                )

    # --- Behavioral: idle_timeout => higher cognitive load sensitivity ---
    for e in events:
        if _get(e, "event_type") == "idle_timeout":
            idle_s = float(_payload(e).get("idle_seconds", 0) or 0)
            if idle_s >= 8:
                evidence.append(
                    {
                        "dimension": "cognitive_load_sensitivity",
                        "type": "behavioral",
                        "value": "high",
                        "event_id": _eid(e),
                        "signal_strength": _clamp(idle_s / 15.0, 0.3, 1.0),
                        "rule_id": "UWSM_CLS_IDLE_NUDGE_UP_v1",
                    }
                )

    # --- Behavioral: undo spike => cautious risk posture ---
    undo_events = [
        e for e in events if _get(e, "event_type") == "user_action" and _payload(e).get("action") == "undo"
    ]
    if len(undo_events) >= 3:
        evidence.append(
            {
                "dimension": "risk_posture",
                "type": "behavioral",
                "value": "cautious",
                "event_id": _eid(undo_events[0]),
                "signal_strength": _clamp(len(undo_events) / 5.0, 0.6, 1.0),
                "rule_id": "UWSM_RISK_UNDO_SPIKE_v1",
            }
        )

    # --- Behavioral: representation preference from view switching ---
    # table_view => numeric; zoom/isolate => visual; open_explanation => narrative; many switches => mixed
    rep_votes = {"visual": 0, "numeric": 0, "narrative": 0}
    view_switch_count = 0

    for e in events:
        if _get(e, "event_type") != "user_action":
            continue
        p = _payload(e)
        action = p.get("action")
        if action == "view_rendered":
            # doesn't imply preference alone
            continue
        if action == "view_changed":
            view_switch_count += 1
            view = p.get("view")
            if view == "table":
                rep_votes["numeric"] += 1
            if view == "graph":
                rep_votes["visual"] += 1
        if action in ("zoom", "isolate_trace"):
            rep_votes["visual"] += 1
        if action in ("open_explanation", "why_clicked"):
            rep_votes["narrative"] += 1

    # If lots of switching, lean mixed
    if view_switch_count >= 3:
        evidence.append(
            {
                "dimension": "representation_preference",
                "type": "behavioral",
                "value": "mixed",
                "event_id": _eid(events[0]) if events else "",
                "signal_strength": _clamp(view_switch_count / 6.0, 0.5, 1.0),
                "rule_id": "UWSM_REP_SWITCHING_v1",
            }
        )
    else:
        # Pick highest vote if any
        best = max(rep_votes.items(), key=lambda kv: kv[1])[0]
        if rep_votes[best] > 0:
            evidence.append(
                {
                    "dimension": "representation_preference",
                    "type": "behavioral",
                    "value": best,
                    "event_id": _eid(events[0]) if events else "",
                    "signal_strength": _clamp(rep_votes[best] / 3.0, 0.4, 1.0),
                    "rule_id": f"UWSM_REP_{best.upper()}_VOTE_v1",
                }
            )

    # --- Exploration style: dabble vs iterative vs deep_focus (minimal heuristic) ---
    # Many tool render/close events => dabble; repeated parameter_changed => iterative
    tool_toggles = sum(1 for e in events if _get(e, "event_type") in ("tool_rendered", "tool_closed"))
    param_changes = sum(
        1
        for e in events
        if _get(e, "event_type") == "user_action" and _payload(e).get("action") == "parameter_changed"
    )

    if tool_toggles >= 4 and param_changes <= 1:
        evidence.append(
            {
                "dimension": "exploration_style",
                "type": "behavioral",
                "value": "dabble",
                "event_id": _eid(events[0]) if events else "",
                "signal_strength": 0.7,
                "rule_id": "UWSM_EXP_DABBLE_TOOL_TOGGLES_v1",
            }
        )
    elif param_changes >= 2:
        evidence.append(
            {
                "dimension": "exploration_style",
                "type": "behavioral",
                "value": "iterative",
                "event_id": _eid(events[0]) if events else "",
                "signal_strength": _clamp(param_changes / 5.0, 0.5, 1.0),
                "rule_id": "UWSM_EXP_ITERATIVE_PARAM_CHANGES_v1",
            }
        )

    return evidence


# ----------------------------
# Evidence Application + Audit
# ----------------------------

def _apply_evidence(uwsm: dict, ev: dict) -> List[dict]:
    dim = ev["dimension"]
    e_type = ev["type"]
    candidate = ev["value"]
    eid = ev.get("event_id", "")
    strength = float(ev.get("signal_strength", 1.0))
    rule_id = ev.get("rule_id", "UWSM_RULE_UNKNOWN")

    d = uwsm["dimensions"][dim]
    prev_value = d["value"]
    prev_conf = float(d["confidence"])

    # Contradiction: reduce confidence only (do not flip)
    if e_type == "contradiction" and candidate != prev_value:
        new_conf = _clamp(prev_conf + DELTA_CONTRADICTION * strength, DEFAULT_FLOOR, 1.0)
        d["confidence"] = new_conf
        return [
            _audit(dim, prev_value, prev_conf, candidate, new_conf, eid, e_type, rule_id, changed=(prev_value != d["value"]))
        ]

    # Explicit and behavioral: increase confidence; potential value change gated by hysteresis
    if e_type == "explicit":
        cap = CAP_EXPLICIT
        delta = DELTA_EXPLICIT
    else:
        cap = CAP_BEHAVIORAL
        delta = DELTA_BEHAVIORAL

    new_conf = _clamp(prev_conf + delta * strength, DEFAULT_FLOOR, cap)
    d["confidence"] = new_conf

    # Hysteresis: require confidence>=0.60 and 2 consecutive windows supporting same candidate
    streaks = uwsm["_state"]["streaks"]
    st = streaks.get(dim, {"candidate": None, "count": 0})

    if candidate == st.get("candidate"):
        st["count"] = int(st.get("count", 0)) + 1
    else:
        st = {"candidate": candidate, "count": 1}

    streaks[dim] = st

    changed_value = False
    if new_conf >= 0.60 and st["count"] >= 2 and candidate != prev_value:
        # flip to candidate
        d["value"] = candidate
        changed_value = True
        # reset streak after a flip so we don't oscillate instantly
        streaks[dim] = {"candidate": candidate, "count": 0}

    return [
        _audit(dim, prev_value, prev_conf, candidate, new_conf, eid, e_type, rule_id, changed=changed_value)
    ]


def _audit(
    dim: str,
    prev_value: str,
    prev_conf: float,
    candidate: str,
    new_conf: float,
    event_id: str,
    e_type: str,
    rule_id: str,
    changed: bool,
) -> dict:
    return {
        "dimension": dim,
        "previous": {"value": prev_value, "confidence": float(prev_conf)},
        "evidence": {"event_id": event_id, "type": e_type, "candidate": candidate},
        "next": {"value": prev_value if not changed else candidate, "confidence": float(new_conf)},
        "changed": bool(changed),
        "rule_id": rule_id,
        "timestamp": _now_iso(),
    }
