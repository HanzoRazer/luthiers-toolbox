"""
Replay Harness — Replay recorded sessions for determinism testing.

The replay harness takes a JSONL file of AgentEventV1 events and replays
them through the moment detection and policy engines to verify determinism.

Key features:
- Deterministic: Same events always produce same moments and decisions
- Shadow mode: Compute decisions without emitting to UI
- Scoreboard: Track accuracy against expected outcomes
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
import json

from .moments import detect_moments
from .policy import decide, AgenticMode
from .uwsm_update import default_uwsm


@dataclass
class ReplayConfig:
    """Configuration for replay execution."""
    mode: AgenticMode = "M0"
    verbose: bool = False
    expected_outcomes: Optional[Dict[str, Dict[str, Any]]] = None


def load_events(path: Path) -> List[Dict[str, Any]]:
    """
    Load events from a JSONL file.
    
    Each line is a JSON object representing an AgentEventV1 event.
    """
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def group_by_session(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by session_id."""
    sessions: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        session_id = event.get("session", {}).get("session_id", "unknown")
        sessions.setdefault(session_id, []).append(event)
    return sessions


def run_shadow_replay(
    events: List[Dict[str, Any]],
    config: ReplayConfig,
) -> Dict[str, Any]:
    """
    Run shadow replay on a list of events.
    
    Returns a report with:
    - mode: The operating mode used
    - summary: Aggregate statistics
    - sessions: Per-session results
    """
    sessions = group_by_session(events)
    
    session_results: Dict[str, Dict[str, Any]] = {}
    total_moments = 0
    total_decisions = 0
    
    for session_id, session_events in sessions.items():
        # Detect moments
        moments = detect_moments(session_events)
        moment = moments[0] if moments else None
        
        # Make decision
        uwsm = default_uwsm()
        decision = None
        if moment:
            decision = decide(moment, uwsm, config.mode)
            total_decisions += 1
        
        total_moments += len(moments)
        
        session_results[session_id] = {
            "event_count": len(session_events),
            "moment": moment,
            "decision": decision,
        }
        
        if config.verbose:
            print(f"Session {session_id}: {len(session_events)} events")
            if moment:
                print(f"  Moment: {moment['moment']} (conf={moment['confidence']:.2f})")
            if decision:
                print(f"  Decision: {decision['attention_action']} (emit={decision['emit_directive']})")
    
    return {
        "mode": config.mode,
        "summary": {
            "total_sessions": len(sessions),
            "total_events": len(events),
            "total_moments": total_moments,
            "total_decisions": total_decisions,
        },
        "sessions": session_results,
    }


def run_determinism_check(
    events: List[Dict[str, Any]],
    runs: int = 10,
) -> Dict[str, Any]:
    """
    Run multiple replays and verify determinism.
    
    Returns a report with:
    - deterministic: Whether all runs produced the same results
    - runs: Number of runs performed
    - mismatches: List of session_ids with non-deterministic results
    """
    config = ReplayConfig(mode="M0", verbose=False)
    
    first_result = run_shadow_replay(events, config)
    mismatches: List[str] = []
    
    for _ in range(runs - 1):
        result = run_shadow_replay(events, config)
        
        # Compare session results
        for session_id, first_session in first_result["sessions"].items():
            current_session = result["sessions"].get(session_id)
            if current_session is None:
                mismatches.append(session_id)
                continue
            
            # Compare moments
            if first_session.get("moment") != current_session.get("moment"):
                if session_id not in mismatches:
                    mismatches.append(session_id)
            
            # Compare decisions
            first_decision = first_session.get("decision")
            current_decision = current_session.get("decision")
            if first_decision and current_decision:
                if first_decision.get("attention_action") != current_decision.get("attention_action"):
                    if session_id not in mismatches:
                        mismatches.append(session_id)
    
    return {
        "deterministic": len(mismatches) == 0,
        "runs": runs,
        "mismatches": mismatches,
    }
