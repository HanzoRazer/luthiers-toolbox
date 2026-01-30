# services/api/app/api/deps/rmos_stores.py
"""
RMOS Stores Dependency Injection.
Provides access to pattern, job log, and strip family stores.

Wired to real SQLite stores for production run tracking.
"""

from __future__ import annotations

from typing import Optional

# Import real SQLite store implementations
from app.stores.sqlite_pattern_store import SQLitePatternStore
from app.stores.sqlite_joblog_store import SQLiteJobLogStore
from app.stores.sqlite_strip_family_store import SQLiteStripFamilyStore


# Singleton instances
_pattern_store: Optional[SQLitePatternStore] = None
_joblog_store: Optional[SQLiteJobLogStore] = None
_strip_family_store: Optional[SQLiteStripFamilyStore] = None


def get_pattern_store() -> SQLitePatternStore:
    """Get singleton pattern store instance."""
    global _pattern_store
    if _pattern_store is None:
        _pattern_store = SQLitePatternStore()
    return _pattern_store


def get_joblog_store() -> SQLiteJobLogStore:
    """Get singleton job log store instance."""
    global _joblog_store
    if _joblog_store is None:
        _joblog_store = SQLiteJobLogStore()
    return _joblog_store


def get_strip_family_store() -> SQLiteStripFamilyStore:
    """Get singleton strip family store instance."""
    global _strip_family_store
    if _strip_family_store is None:
        _strip_family_store = SQLiteStripFamilyStore()
    return _strip_family_store
