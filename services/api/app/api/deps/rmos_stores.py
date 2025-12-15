# services/api/app/api/deps/rmos_stores.py
"""
RMOS Stores Dependency Injection.
Provides access to pattern, job log, and strip family stores.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class PatternStore:
    """
    Pattern store stub for RMOS pattern management.
    TODO: Implement actual SQLite/JSON store when ready.
    """
    
    def get(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get pattern by ID."""
        return None
    
    def list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all patterns with pagination."""
        return []
    
    def save(self, pattern: Dict[str, Any]) -> str:
        """Save pattern and return ID."""
        return pattern.get("id", "stub-id")
    
    def delete(self, pattern_id: str) -> bool:
        """Delete pattern by ID."""
        return False


class JobLogStore:
    """
    Job log store stub for RMOS job tracking.
    TODO: Implement actual SQLite store when ready.
    """
    
    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job log by ID."""
        return None
    
    def list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all job logs with pagination."""
        return []
    
    def create(self, job: Dict[str, Any]) -> str:
        """Create job log entry and return ID."""
        return job.get("id", "stub-job-id")
    
    def update(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job log entry."""
        return False


class StripFamilyStore:
    """
    Strip family store stub for material management.
    TODO: Implement actual store when ready.
    """
    
    def get(self, family_id: str) -> Optional[Dict[str, Any]]:
        """Get strip family by ID."""
        return None
    
    def list(self) -> List[Dict[str, Any]]:
        """List all strip families."""
        return []
    
    def save(self, family: Dict[str, Any]) -> str:
        """Save strip family and return ID."""
        return family.get("id", "stub-family-id")


# Singleton instances
_pattern_store: Optional[PatternStore] = None
_joblog_store: Optional[JobLogStore] = None
_strip_family_store: Optional[StripFamilyStore] = None


def get_pattern_store() -> PatternStore:
    """Get singleton pattern store instance."""
    global _pattern_store
    if _pattern_store is None:
        _pattern_store = PatternStore()
    return _pattern_store


def get_joblog_store() -> JobLogStore:
    """Get singleton job log store instance."""
    global _joblog_store
    if _joblog_store is None:
        _joblog_store = JobLogStore()
    return _joblog_store


def get_strip_family_store() -> StripFamilyStore:
    """Get singleton strip family store instance."""
    global _strip_family_store
    if _strip_family_store is None:
        _strip_family_store = StripFamilyStore()
    return _strip_family_store
