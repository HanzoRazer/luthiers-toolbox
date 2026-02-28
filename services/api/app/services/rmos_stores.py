"""
RMOS Store Implementations for Rosette Design Sheet API.

Provides PatternStore and JobLogStore for RMOS pattern management
and job logging functionality.
"""

from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class PatternRecord:
    """Represents a stored rosette pattern."""
    pattern_id: str
    name: str
    spec: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class JobLogRecord:
    """Represents a job execution log entry."""
    log_id: str
    job_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PatternStore:
    """
    In-memory pattern store for RMOS rosette patterns.
    
    Production implementations should back this with a database.
    """
    
    def __init__(self):
        self._patterns: Dict[str, PatternRecord] = {}
    
    def save(self, name: str, spec: Dict[str, Any], tags: Optional[List[str]] = None) -> str:
        """Save a pattern and return its ID."""
        pattern_id = str(uuid.uuid4())
        self._patterns[pattern_id] = PatternRecord(
            pattern_id=pattern_id,
            name=name,
            spec=spec,
            tags=tags or []
        )
        return pattern_id
    
    def get(self, pattern_id: str) -> Optional[PatternRecord]:
        """Get a pattern by ID."""
        return self._patterns.get(pattern_id)
    
    def list_all(self) -> List[PatternRecord]:
        """List all patterns."""
        return list(self._patterns.values())
    
    def delete(self, pattern_id: str) -> bool:
        """Delete a pattern. Returns True if deleted."""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False
    
    def search_by_tag(self, tag: str) -> List[PatternRecord]:
        """Find patterns with a specific tag."""
        return [p for p in self._patterns.values() if tag in p.tags]


class JobLogStore:
    """
    In-memory job log store for RMOS job execution history.
    
    Production implementations should back this with a database.
    """
    
    def __init__(self):
        self._logs: List[JobLogRecord] = []
    
    def append(self, job_id: str, event_type: str, payload: Optional[Dict[str, Any]] = None) -> str:
        """Append a log entry and return its ID."""
        log_id = str(uuid.uuid4())
        self._logs.append(JobLogRecord(
            log_id=log_id,
            job_id=job_id,
            event_type=event_type,
            payload=payload or {}
        ))
        return log_id
    
    def get_by_job(self, job_id: str) -> List[JobLogRecord]:
        """Get all log entries for a job."""
        return [log for log in self._logs if log.job_id == job_id]
    
    def get_recent(self, limit: int = 100) -> List[JobLogRecord]:
        """Get most recent log entries."""
        return sorted(self._logs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def clear_job_logs(self, job_id: str) -> int:
        """Clear all logs for a job. Returns count deleted."""
        before = len(self._logs)
        self._logs = [log for log in self._logs if log.job_id != job_id]
        return before - len(self._logs)


# Singleton instances for dependency injection
_pattern_store: Optional[PatternStore] = None
_joblog_store: Optional[JobLogStore] = None


def get_pattern_store() -> PatternStore:
    """Get the singleton PatternStore instance."""
    global _pattern_store
    if _pattern_store is None:
        _pattern_store = PatternStore()
    return _pattern_store


def get_joblog_store() -> JobLogStore:
    """Get the singleton JobLogStore instance."""
    global _joblog_store
    if _joblog_store is None:
        _joblog_store = JobLogStore()
    return _joblog_store
