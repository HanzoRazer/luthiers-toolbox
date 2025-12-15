# services/api/app/rmos/logging_core.py
"""
RMOS Logging Core - Central event logging infrastructure.
Provides log_rmos_event and query_rmos_events functions.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import threading


# Thread-safe storage for log events
_LOG_LOCK = threading.Lock()
_LOG_BUFFER: deque = deque(maxlen=10000)  # Ring buffer


class RmosLogEntry:
    """Internal log entry structure."""
    __slots__ = ("event_type", "timestamp", "payload")
    
    def __init__(self, event_type: str, payload: Dict[str, Any]):
        self.event_type = event_type
        self.timestamp = datetime.now(timezone.utc)
        self.payload = payload
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            **self.payload
        }


def log_rmos_event(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Log an RMOS event to the central buffer.
    
    Args:
        event_type: Type of event (e.g., 'ai_constraint_attempt', 'feasibility_check')
        payload: Event data as a dictionary
    """
    entry = RmosLogEntry(event_type, payload)
    with _LOG_LOCK:
        _LOG_BUFFER.append(entry)


def query_rmos_events(
    event_type: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    order: str = "desc"
) -> List[Dict[str, Any]]:
    """
    Query logged RMOS events with optional filtering.
    
    Args:
        event_type: Filter by event type
        filters: Optional dict of field -> value filters
        limit: Maximum results to return
        order: 'desc' (newest first) or 'asc' (oldest first)
        
    Returns:
        List of matching event payloads
    """
    filters = filters or {}
    
    with _LOG_LOCK:
        # Get a snapshot of the buffer
        entries = list(_LOG_BUFFER)
    
    # Filter by event type
    matching = [e for e in entries if e.event_type == event_type]
    
    # Apply additional filters
    for key, value in filters.items():
        matching = [
            e for e in matching 
            if e.payload.get(key) == value
        ]
    
    # Sort by timestamp
    matching.sort(
        key=lambda e: e.timestamp,
        reverse=(order == "desc")
    )
    
    # Limit results
    matching = matching[:limit]
    
    # Convert to dicts
    return [e.to_dict() for e in matching]


def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Get the most recent log entries regardless of type."""
    with _LOG_LOCK:
        entries = list(_LOG_BUFFER)
    
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return [e.to_dict() for e in entries[:limit]]


def clear_logs() -> int:
    """Clear all logs and return count of cleared entries."""
    with _LOG_LOCK:
        count = len(_LOG_BUFFER)
        _LOG_BUFFER.clear()
    return count


def logs_to_csv() -> str:
    """Export all logs to CSV format."""
    import csv
    from io import StringIO
    
    with _LOG_LOCK:
        entries = list(_LOG_BUFFER)
    
    if not entries:
        return "event_type,timestamp\n"
    
    # Collect all unique keys
    all_keys = {"event_type", "timestamp"}
    for e in entries:
        all_keys.update(e.payload.keys())
    
    all_keys = sorted(all_keys)
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys)
    writer.writeheader()
    
    for e in entries:
        row = {"event_type": e.event_type, "timestamp": e.timestamp.isoformat()}
        row.update(e.payload)
        writer.writerow(row)
    
    return output.getvalue()
