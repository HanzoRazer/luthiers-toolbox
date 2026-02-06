# app/agentic/spine/replay.py
"""
Shadow Replay Harness — Reference Implementation

Replays recorded event sessions through the agentic spine:
- Detects moments from events
- Updates UWSM deterministically
- Runs policy decisions in chosen mode (M0/M1/M2)

Supports JSON array or JSONL input formats.

Usage:
    python -m app.agentic.spine.replay recordings/session.jsonl
    python -m app.agentic.spine.replay recordings/session.jsonl --mode M1 --verbose
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .moments import detect_moments
from .policy import decide
from .uwsm_update import apply_uwsm_updates, ensure_uwsm


@dataclass
class ReplayConfig:
    mode: str = "M0"  # M0 Shadow by default
    capability: dict = None
    # Context used by policy for FIRST_SIGNAL onboarding (safe defaults)
    context: dict = None
    # Output verbosity
    verbose: bool = False


def load_events(path: str | Path) -> List[dict]:
    """
    Load recorded sessions from:
      - JSON array file: [ {...}, {...} ]
      - JSONL file: one JSON object per line

    Returns list of event dicts.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8").strip()
    if not text:
        return []

    # JSON array
    if text.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON file must be an array of event objects")
        return data

    # JSONL fallback
    events: List[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events


def group_by_session(events: List[dict]) -> Dict[str, List[dict]]:
    """
    Group events by session_id if present; otherwise return a single session.
    """
    by: Dict[str, List[dict]] = {}
    for e in events:
        sid = (e.get("session") or {}).get("session_id")
        sid = sid or "session_unknown"
        by.setdefault(sid, []).append(e)

    # Sort events per session by occurred_at when present
    for sid, evs in by.items():
        evs.sort(key=lambda x: str(x.get("occurred_at", "")))
    return by


def run_shadow_replay(
    events: List[dict],
    config: Optional[ReplayConfig] = None,
) -> Dict[str, Any]:
    """
    Run shadow-mode replay across sessions.

    For each session:
      - detect moments from all events
      - update UWSM from all events (deterministic)
      - run policy decide(...) for the top moment in M0 (shadow)
      - return per-session summary + audit details

    This is a minimal harness intended for:
      - CI smoke tests
      - offline evaluation
      - quick debugging
    """
    config = config or ReplayConfig()
    capability = config.capability or {"automation_limits": {"agent_can_adjust_view": False}}
    context = config.context or {"first_time_user": True, "primary_panel": "spectrum", "primary_trace": "main"}

    sessions = group_by_session(events)
    report: Dict[str, Any] = {"mode": config.mode, "sessions": {}, "summary": {}}

    total_sessions = 0
    moment_counts: Dict[str, int] = {}
    action_counts: Dict[str, int] = {}

    for sid, evs in sessions.items():
        total_sessions += 1

        # UWSM update + audit
        uwsm0 = ensure_uwsm(None)
        uwsm1, audits = apply_uwsm_updates(events=evs, uwsm=uwsm0)

        # Moment detection (highest priority only)
        moments = detect_moments(evs)
        moment = moments[0] if moments else {"moment": "NONE", "confidence": 0.0, "trigger_events": []}

        # Policy decision in chosen mode (default: shadow)
        decision = decide(moment=moment, uwsm=uwsm1, mode=config.mode, capability=capability, context=context)

        mname = moment.get("moment", "NONE")
        aname = decision.get("attention_action", "NONE")

        moment_counts[mname] = moment_counts.get(mname, 0) + 1
        action_counts[aname] = action_counts.get(aname, 0) + 1

        report["sessions"][sid] = {
            "moment": moment,
            "decision": decision,
            "uwsm": _strip_internal_state(uwsm1),
            "audits": audits if config.verbose else audits[-5:],  # keep last few by default
            "event_count": len(evs),
        }

    report["summary"] = {
        "total_sessions": total_sessions,
        "moment_counts": moment_counts,
        "action_counts": action_counts,
    }
    return report


def _strip_internal_state(uwsm: dict) -> dict:
    uwsm = dict(uwsm)
    uwsm.pop("_state", None)
    return uwsm


def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI entry:
      python -m app.agentic.spine.replay path/to/events.jsonl --verbose

    Outputs JSON report to stdout.
    """
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Shadow replay harness for agentic spine")
    ap.add_argument("path", help="Path to events JSON or JSONL")
    ap.add_argument("--mode", default="M0", choices=["M0", "M1", "M2"], help="Replay mode")
    ap.add_argument("--verbose", action="store_true", help="Include full audit logs")
    args = ap.parse_args(argv)

    events = load_events(args.path)
    cfg = ReplayConfig(mode=args.mode, verbose=args.verbose)
    report = run_shadow_replay(events, cfg)

    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
