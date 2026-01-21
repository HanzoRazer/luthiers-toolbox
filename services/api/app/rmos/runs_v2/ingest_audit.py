"""
Ingest Audit Log - append-only event store for /import-zip traceability.

Store location (consistent with runs_v2):
    {runs_root}/ingest_events/{YYYY-MM-DD}/{event_id}.json
    {runs_root}/ingest_events/_recent.json   # small recency index

Event schema: acoustics_ingest_event_v1
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------


class IngestEventError(TypedDict, total=False):
    """Error payload for 4xx/5xx outcomes."""
    code: str
    message: str
    detail: Any


class IngestEventValidation(TypedDict, total=False):
    """Validation summary from viewer_pack."""
    passed: Optional[bool]
    errors_count: Optional[int]
    warnings_count: Optional[int]
    reason: Optional[str]


class IngestEvent(TypedDict, total=False):
    """
    Ingest event schema v1.

    All fields except schema_id, event_id, created_at_utc, outcome are optional.
    """
    schema_id: str
    event_id: str
    created_at_utc: str
    outcome: str  # "accepted" | "rejected" | "quarantined"
    session_id: Optional[str]
    batch_label: Optional[str]
    uploader_filename: Optional[str]
    zip_sha256: Optional[str]
    zip_size_bytes: Optional[int]
    http_status: Optional[int]
    error: Optional[IngestEventError]
    validation: Optional[IngestEventValidation]
    run_id: Optional[str]
    bundle_id: Optional[str]
    bundle_sha256: Optional[str]


class IngestEventSummary(TypedDict, total=False):
    """Compact summary for recency index."""
    event_id: str
    created_at_utc: str
    outcome: str
    session_id: Optional[str]
    batch_label: Optional[str]
    uploader_filename: Optional[str]
    zip_sha256: Optional[str]
    zip_size_bytes: Optional[int]
    http_status: Optional[int]
    run_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]


class ListEventsResult(TypedDict):
    """Result from list_events_recent."""
    count: int
    entries: List[IngestEventSummary]
    next_cursor: Optional[str]


# ---------------------------------------------------------------------------
# Default paths (consistent with store.py)
# ---------------------------------------------------------------------------

from .store import _get_store_root

INGEST_EVENTS_SUBDIR = "ingest_events"
RECENT_INDEX_FILENAME = "_recent.json"
MAX_RECENT_ENTRIES = 500


def _get_runs_root() -> Path:
    """Get runs_v2 root directory from canonical store resolver."""
    return Path(_get_store_root()).expanduser().resolve()


def _utc_now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_partition(iso_utc: str) -> str:
    """Extract YYYY-MM-DD from ISO timestamp."""
    return iso_utc.split("T", 1)[0]


def _json_dump(path: Path, obj: Any) -> None:
    """Write JSON atomically (tmp + replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _json_load(path: Path) -> Any:
    """Read JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Event creation helpers
# ---------------------------------------------------------------------------


def create_event_id() -> str:
    """Generate a unique event ID."""
    return f"ingest_{uuid.uuid4().hex}"


def build_event(
    *,
    outcome: str,
    event_id: Optional[str] = None,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    uploader_filename: Optional[str] = None,
    zip_sha256: Optional[str] = None,
    zip_size_bytes: Optional[int] = None,
    http_status: Optional[int] = None,
    error: Optional[IngestEventError] = None,
    validation: Optional[IngestEventValidation] = None,
    run_id: Optional[str] = None,
    bundle_id: Optional[str] = None,
    bundle_sha256: Optional[str] = None,
) -> IngestEvent:
    """
    Build a complete IngestEvent dict.

    Timestamps event_id and created_at_utc automatically if not provided.
    """
    evt: IngestEvent = {
        "schema_id": "acoustics_ingest_event_v1",
        "event_id": event_id or create_event_id(),
        "created_at_utc": _utc_now_iso(),
        "outcome": outcome,
    }

    if session_id:
        evt["session_id"] = session_id
    if batch_label:
        evt["batch_label"] = batch_label
    if uploader_filename:
        evt["uploader_filename"] = uploader_filename
    if zip_sha256:
        evt["zip_sha256"] = zip_sha256
    if zip_size_bytes is not None:
        evt["zip_size_bytes"] = zip_size_bytes
    if http_status is not None:
        evt["http_status"] = http_status
    if error is not None:
        evt["error"] = error
    if validation is not None:
        evt["validation"] = validation
    if run_id:
        evt["run_id"] = run_id
    if bundle_id:
        evt["bundle_id"] = bundle_id
    if bundle_sha256:
        evt["bundle_sha256"] = bundle_sha256

    return evt


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def append_event(root: Optional[Path], event: IngestEvent) -> Path:
    """
    Append an ingest event to the store (atomic write).

    Args:
        root: runs_v2 root directory (defaults to env/default if None)
        event: IngestEvent dict to persist

    Returns:
        Path to the written event JSON file
    """
    if root is None:
        root = _get_runs_root()

    event_id = event.get("event_id") or create_event_id()
    created_at = event.get("created_at_utc") or _utc_now_iso()

    # Ensure required fields
    event["event_id"] = event_id
    event["created_at_utc"] = created_at
    if "schema_id" not in event:
        event["schema_id"] = "acoustics_ingest_event_v1"

    date_part = _date_partition(created_at)
    events_dir = root / INGEST_EVENTS_SUBDIR / date_part
    event_path = events_dir / f"{event_id}.json"

    _json_dump(event_path, event)

    # Best-effort update recency index
    try:
        summary = _event_to_summary(event)
        update_recent_index(root, summary)
    except Exception:
        pass  # Non-blocking

    return event_path


def _event_to_summary(event: IngestEvent) -> IngestEventSummary:
    """Convert full event to compact summary for recency index."""
    error = event.get("error") or {}
    return IngestEventSummary(
        event_id=event.get("event_id", ""),
        created_at_utc=event.get("created_at_utc", ""),
        outcome=event.get("outcome", ""),
        session_id=event.get("session_id"),
        batch_label=event.get("batch_label"),
        uploader_filename=event.get("uploader_filename"),
        zip_sha256=event.get("zip_sha256"),
        zip_size_bytes=event.get("zip_size_bytes"),
        http_status=event.get("http_status"),
        run_id=event.get("run_id"),
        error_code=error.get("code") if error else None,
        error_message=error.get("message") if error else None,
    )


def update_recent_index(root: Path, event_summary: IngestEventSummary) -> None:
    """
    Update the _recent.json index with a new event summary.

    Maintains a list sorted by created_at_utc DESC, capped at MAX_RECENT_ENTRIES.
    """
    events_dir = root / INGEST_EVENTS_SUBDIR
    recent_path = events_dir / RECENT_INDEX_FILENAME

    entries: List[IngestEventSummary] = []
    if recent_path.exists():
        try:
            data = _json_load(recent_path)
            entries = data.get("entries", []) if isinstance(data, dict) else []
        except Exception:
            entries = []

    # Remove duplicate if present
    event_id = event_summary.get("event_id")
    entries = [e for e in entries if e.get("event_id") != event_id]

    # Prepend new entry (most recent first)
    entries.insert(0, event_summary)

    # Cap size
    entries = entries[:MAX_RECENT_ENTRIES]

    # Write atomically
    _json_dump(recent_path, {
        "schema_id": "acoustics_ingest_recent_v1",
        "updated_at_utc": _utc_now_iso(),
        "count": len(entries),
        "entries": entries,
    })


def list_events_recent(
    root: Optional[Path] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
    outcome: Optional[str] = None,
) -> ListEventsResult:
    """
    List recent ingest events from the _recent.json index.

    Args:
        root: runs_v2 root directory
        limit: max entries to return
        cursor: opaque pagination cursor (event_id of last returned)
        outcome: filter by outcome (accepted|rejected|quarantined)

    Returns:
        ListEventsResult with count, entries, next_cursor
    """
    if root is None:
        root = _get_runs_root()

    events_dir = root / INGEST_EVENTS_SUBDIR
    recent_path = events_dir / RECENT_INDEX_FILENAME

    entries: List[IngestEventSummary] = []
    if recent_path.exists():
        try:
            data = _json_load(recent_path)
            entries = data.get("entries", []) if isinstance(data, dict) else []
        except Exception:
            entries = []

    # Filter by outcome
    if outcome:
        outcome_lower = outcome.lower().strip()
        entries = [e for e in entries if (e.get("outcome") or "").lower() == outcome_lower]

    # Cursor pagination: skip until we find cursor, then take entries after
    if cursor:
        found_idx = None
        for i, e in enumerate(entries):
            if e.get("event_id") == cursor:
                found_idx = i
                break
        if found_idx is not None:
            entries = entries[found_idx + 1:]

    # Apply limit
    page = entries[:limit]
    next_cursor = page[-1]["event_id"] if len(entries) > limit and page else None

    return ListEventsResult(
        count=len(page),
        entries=page,
        next_cursor=next_cursor,
    )


def get_event(root: Optional[Path], event_id: str) -> Optional[IngestEvent]:
    """
    Load a single ingest event by ID.

    Searches the date-partitioned directories for the event file.
    """
    if root is None:
        root = _get_runs_root()

    events_base = root / INGEST_EVENTS_SUBDIR
    if not events_base.exists():
        return None

    # First try recency index for date hint (faster)
    recent_path = events_base / RECENT_INDEX_FILENAME
    date_hint = None
    if recent_path.exists():
        try:
            data = _json_load(recent_path)
            for e in data.get("entries", []):
                if e.get("event_id") == event_id:
                    ts = e.get("created_at_utc", "")
                    if ts:
                        date_hint = _date_partition(ts)
                    break
        except Exception:
            pass

    # Try date hint first
    if date_hint:
        p = events_base / date_hint / f"{event_id}.json"
        if p.exists():
            try:
                return _json_load(p)
            except Exception:
                pass

    # Fallback: scan date directories (newest first)
    for date_dir in sorted(events_base.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        name = date_dir.name
        # Check if YYYY-MM-DD pattern
        if len(name) != 10 or name[4] != "-" or name[7] != "-":
            continue
        p = date_dir / f"{event_id}.json"
        if p.exists():
            try:
                return _json_load(p)
            except Exception:
                continue

    return None
