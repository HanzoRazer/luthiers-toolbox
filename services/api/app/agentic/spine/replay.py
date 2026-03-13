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
from .schemas import DetectedMoment, CRITICAL_MOMENTS

# Module is now implemented
IMPLEMENTED = True

# Constants
FIRST_SIGNAL_GRACE_MS = 1500


@dataclass
class ReplayConfig:
    """Configuration for replay sessions."""
    shadow_mode: bool = True
    strict_order: bool = True
    grace_period_ms: int = FIRST_SIGNAL_GRACE_MS


@dataclass
class ReplayResult:
    """Result of replaying an event sequence."""
    session_id: str
    events_processed: int
    moments_detected: List[DetectedMoment]
    errors: List[str] = field(default_factory=list)


def load_events(path: Path) -> List[Dict[str, Any]]:
    """
    Load events from a JSONL file.

    Args:
        path: Path to JSONL file (one JSON object per line)

    Returns:
        List of event dictionaries

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If line is not valid JSON
    """
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
    """
    Group events by session ID.

    Args:
        events: List of event dictionaries

    Returns:
        Dictionary mapping session_id to list of events
    """
    sessions: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        session_info = event.get("session", {})
        session_id = session_info.get("session_id", "unknown")
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(event)

    # Sort events within each session by timestamp
    for session_id in sessions:
        sessions[session_id].sort(key=lambda e: e.get("occurred_at", ""))

    return sessions


def run_shadow_replay(
    events: List[Dict[str, Any]],
    config: Optional[ReplayConfig] = None,
) -> Iterator[ReplayResult]:
    """
    Run shadow replay on a sequence of events.

    Groups events by session and runs moment detection on each session.
    Yields results as each session is processed.

    Args:
        events: List of event dictionaries
        config: Optional replay configuration

    Yields:
        ReplayResult for each session
    """
    if config is None:
        config = ReplayConfig()

    sessions = group_by_session(events)

    for session_id, session_events in sessions.items():
        errors: List[str] = []
        moments: List[DetectedMoment] = []

        try:
            moments = detect_moments(session_events)
        except Exception as e:
            errors.append(f"Moment detection error: {str(e)}")

        yield ReplayResult(
            session_id=session_id,
            events_processed=len(session_events),
            moments_detected=moments,
            errors=errors,
        )


def select_moment_with_grace(
    moments: List[DetectedMoment],
    grace_period_ms: int = FIRST_SIGNAL_GRACE_MS,
    first_signal_shown: bool = False,
    first_view_rendered_at_ms: Optional[int] = None,
    current_time_ms: Optional[int] = None,
) -> Optional[DetectedMoment]:
    """
    Select the appropriate moment given a grace period.

    Implements FIRST_SIGNAL priority logic:
    1. FIRST_SIGNAL is one-shot: if already shown, skip it
    2. If FINDING is top but FIRST_SIGNAL not yet shown, prefer FIRST_SIGNAL
    3. During grace window, suppress non-critical if FIRST_SIGNAL not yet shown

    Args:
        moments: List of detected moments (sorted by priority)
        grace_period_ms: Grace window duration in milliseconds
        first_signal_shown: Whether FIRST_SIGNAL has been shown this session
        first_view_rendered_at_ms: Timestamp when first view was rendered
        current_time_ms: Current time (for grace window calculation)

    Returns:
        Selected moment or None if all should be suppressed
    """
    if not moments:
        return None

    top = moments[0]

    # One-shot: if FIRST_SIGNAL already shown, never return it again
    if first_signal_shown and top.moment == "FIRST_SIGNAL":
        # Skip to next moment if available, otherwise None
        next_moment = next((m for m in moments if m.moment != "FIRST_SIGNAL"), None)
        return next_moment

    # If FINDING is top but we haven't shown FIRST_SIGNAL yet,
    # prefer FIRST_SIGNAL if present in moments list
    if not first_signal_shown and top.moment == "FINDING":
        first_signal = next((m for m in moments if m.moment == "FIRST_SIGNAL"), None)
        if first_signal:
            return first_signal

        # Grace window suppression: if FIRST_SIGNAL not present yet,
        # show nothing briefly rather than jumping straight to FINDING
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
    """
    Export events to a JSONL file.

    Args:
        events: List of event dictionaries
        path: Output file path

    Returns:
        Number of events written
    """
    with open(path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, default=str) + chr(10))
    return len(events)
