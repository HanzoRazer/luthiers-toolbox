"""
Ingest Audit Log for Acoustics Import Operations.

Bundle 1 of Evidence QA Gate + Quarantine Workflow:
- Logs every /import-zip attempt with outcome
- Provides query APIs for "Ingest Events" UI panel
- Enables operational traceability

Storage: JSONL append-only log (simple, auditable, grep-friendly)
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class IngestOutcome(str, Enum):
    """Possible outcomes for an ingest attempt."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    ERROR = "error"


@dataclass
class IngestAuditRecord:
    """
    Immutable audit record for a single import attempt.
    
    All fields are logged regardless of outcome for complete traceability.
    """
    # Identity
    event_id: str  # UUID for this audit event
    timestamp: str  # ISO 8601 UTC
    
    # Request context
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    filename: Optional[str] = None  # Original upload filename
    
    # Bundle identity (if extractable)
    bundle_sha256: Optional[str] = None
    bundle_id: Optional[str] = None
    manifest_event_type: Optional[str] = None
    manifest_tool_id: Optional[str] = None
    
    # Outcome
    outcome: str = "error"  # accepted, rejected, quarantined, error
    
    # Rejection/error details
    rejection_reason: Optional[str] = None  # missing_validation_report, passed_false, invalid_zip, etc.
    rejection_message: Optional[str] = None  # Human-readable message
    errors_count: Optional[int] = None  # From validation_report.json
    warnings_count: Optional[int] = None
    error_excerpt: List[str] = field(default_factory=list)  # First few validation errors
    
    # Success details (if accepted)
    run_id: Optional[str] = None  # Created run ID
    attachments_written: Optional[int] = None
    attachments_deduped: Optional[int] = None
    
    # Request metadata
    request_id: Optional[str] = None  # X-Request-Id if available
    client_ip: Optional[str] = None  # For rate limiting / abuse detection
    
    # Bundle metadata (for future quarantine review)
    bundle_size_bytes: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        d = asdict(self)
        # Ensure lists serialize properly
        if not d.get("error_excerpt"):
            d["error_excerpt"] = []
        return d


# Default storage path (configurable via env)
INGEST_AUDIT_LOG_PATH = os.environ.get(
    "ACOUSTICS_INGEST_AUDIT_LOG",
    "services/api/data/ingest_audit.jsonl"
)

# Thread lock for append operations
_write_lock = threading.Lock()


def _get_audit_log_path() -> Path:
    """Get the audit log file path, creating parent dirs if needed."""
    path = Path(INGEST_AUDIT_LOG_PATH)
    if not path.is_absolute():
        # Relative to repo root
        repo_root = Path(__file__).resolve().parents[5]  # app/rmos/acoustics -> repo root
        path = repo_root / path
    return path


def _ensure_log_dir() -> None:
    """Lazily create the log directory (Docker-safe pattern)."""
    path = _get_audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)


def compute_bundle_sha256(data: bytes) -> str:
    """Compute SHA256 of the bundle bytes."""
    return hashlib.sha256(data).hexdigest()


def generate_event_id() -> str:
    """Generate a unique event ID for audit records."""
    import uuid
    return str(uuid.uuid4())


def log_ingest_event(record: IngestAuditRecord) -> None:
    """
    Append an ingest audit record to the log file.
    
    Thread-safe, atomic append via file locking.
    """
    _ensure_log_dir()
    path = _get_audit_log_path()
    
    line = json.dumps(record.to_dict(), separators=(",", ":"), sort_keys=True) + "\n"
    
    with _write_lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)


def query_ingest_events(
    *,
    outcome: Optional[str] = None,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    since: Optional[str] = None,  # ISO 8601 timestamp
    until: Optional[str] = None,  # ISO 8601 timestamp
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Query ingest audit events with optional filters.
    
    Returns events in reverse chronological order (newest first).
    """
    path = _get_audit_log_path()
    if not path.exists():
        return []
    
    events: List[Dict[str, Any]] = []
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # Apply filters
            if outcome and record.get("outcome") != outcome:
                continue
            if session_id and record.get("session_id") != session_id:
                continue
            if batch_label and record.get("batch_label") != batch_label:
                continue
            if since and record.get("timestamp", "") < since:
                continue
            if until and record.get("timestamp", "") > until:
                continue
            
            events.append(record)
    
    # Sort by timestamp descending (newest first)
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    
    # Apply pagination
    return events[offset : offset + limit]


def get_ingest_event(event_id: str) -> Optional[Dict[str, Any]]:
    """Get a single ingest event by ID."""
    path = _get_audit_log_path()
    if not path.exists():
        return None
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("event_id") == event_id:
                    return record
            except json.JSONDecodeError:
                continue
    
    return None


def count_ingest_events(
    *,
    outcome: Optional[str] = None,
    since: Optional[str] = None,
) -> Dict[str, int]:
    """
    Get counts of ingest events by outcome.
    
    Returns: {"accepted": N, "rejected": N, "quarantined": N, "error": N, "total": N}
    """
    path = _get_audit_log_path()
    if not path.exists():
        return {"accepted": 0, "rejected": 0, "quarantined": 0, "error": 0, "total": 0}
    
    counts: Dict[str, int] = {"accepted": 0, "rejected": 0, "quarantined": 0, "error": 0, "total": 0}
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # Apply filters
            if outcome and record.get("outcome") != outcome:
                continue
            if since and record.get("timestamp", "") < since:
                continue
            
            event_outcome = record.get("outcome", "error")
            if event_outcome in counts:
                counts[event_outcome] += 1
            else:
                counts["error"] += 1
            counts["total"] += 1
    
    return counts


# Convenience functions for creating audit records

def create_accepted_record(
    *,
    event_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    filename: Optional[str] = None,
    bundle_sha256: Optional[str] = None,
    bundle_id: Optional[str] = None,
    manifest_event_type: Optional[str] = None,
    manifest_tool_id: Optional[str] = None,
    run_id: str,
    attachments_written: int = 0,
    attachments_deduped: int = 0,
    bundle_size_bytes: Optional[int] = None,
    request_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> IngestAuditRecord:
    """Create an audit record for a successful import."""
    return IngestAuditRecord(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        batch_label=batch_label,
        filename=filename,
        bundle_sha256=bundle_sha256,
        bundle_id=bundle_id,
        manifest_event_type=manifest_event_type,
        manifest_tool_id=manifest_tool_id,
        outcome=IngestOutcome.ACCEPTED.value,
        run_id=run_id,
        attachments_written=attachments_written,
        attachments_deduped=attachments_deduped,
        bundle_size_bytes=bundle_size_bytes,
        request_id=request_id,
        client_ip=client_ip,
    )


def create_rejected_record(
    *,
    event_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    filename: Optional[str] = None,
    bundle_sha256: Optional[str] = None,
    rejection_reason: str,
    rejection_message: str,
    errors_count: Optional[int] = None,
    warnings_count: Optional[int] = None,
    error_excerpt: Optional[List[str]] = None,
    bundle_size_bytes: Optional[int] = None,
    request_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> IngestAuditRecord:
    """Create an audit record for a rejected import."""
    return IngestAuditRecord(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        batch_label=batch_label,
        filename=filename,
        bundle_sha256=bundle_sha256,
        outcome=IngestOutcome.REJECTED.value,
        rejection_reason=rejection_reason,
        rejection_message=rejection_message,
        errors_count=errors_count,
        warnings_count=warnings_count,
        error_excerpt=error_excerpt or [],
        bundle_size_bytes=bundle_size_bytes,
        request_id=request_id,
        client_ip=client_ip,
    )


def create_error_record(
    *,
    event_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    filename: Optional[str] = None,
    bundle_sha256: Optional[str] = None,
    rejection_reason: str,
    rejection_message: str,
    bundle_size_bytes: Optional[int] = None,
    request_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> IngestAuditRecord:
    """Create an audit record for an error during import."""
    return IngestAuditRecord(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        batch_label=batch_label,
        filename=filename,
        bundle_sha256=bundle_sha256,
        outcome=IngestOutcome.ERROR.value,
        rejection_reason=rejection_reason,
        rejection_message=rejection_message,
        bundle_size_bytes=bundle_size_bytes,
        request_id=request_id,
        client_ip=client_ip,
    )
