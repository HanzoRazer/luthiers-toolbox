# services/api/app/api/deps/rmos_stores.py
"""
RMOS Stores Dependency Injection.

DEPRECATED: Use app.core.store_registry or app.api.deps directly.

This module now delegates to the centralized StoreRegistry for singleton management.
The old module-level globals have been removed to support horizontal scaling.

Migration:
    # Old (still works for backward compatibility)
    from app.api.deps.rmos_stores import get_pattern_store
    store = get_pattern_store()

    # New (preferred)
    from fastapi import Depends
    from app.api.deps import get_pattern_store

    @router.get("/patterns")
    def list_patterns(store = Depends(get_pattern_store)):
        return store.list_all()
"""

from __future__ import annotations

# Re-export from centralized registry for backward compatibility
from app.core.store_registry import (
    get_pattern_store,
    get_joblog_store,
    get_strip_family_store,
)

# Type hints for IDE support
from app.stores.sqlite_pattern_store import SQLitePatternStore
from app.stores.sqlite_joblog_store import SQLiteJobLogStore
from app.stores.sqlite_strip_family_store import SQLiteStripFamilyStore

__all__ = [
    "get_pattern_store",
    "get_joblog_store",
    "get_strip_family_store",
]
