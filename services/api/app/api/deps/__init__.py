# services/api/app/api/deps/__init__.py
"""
API Dependencies - FastAPI dependency injection helpers.
Provides database sessions, authentication, store access, and common dependencies.

Store Dependencies (use with Depends()):
    - get_pattern_store() -> SQLitePatternStore
    - get_joblog_store() -> SQLiteJobLogStore
    - get_strip_family_store() -> SQLiteStripFamilyStore
    - get_profile_store() -> ProfileStore
    - get_advisory_store() -> AdvisoryAssetStore
    - get_prompt_history_store() -> PromptHistoryStore
    - get_budget_tracker() -> BudgetTracker
    - get_request_record_store() -> RequestRecordStore
    - get_learned_overrides_store() -> LearnedOverridesStore

Example:
    from fastapi import Depends
    from app.api.deps import get_pattern_store

    @router.get("/patterns")
    def list_patterns(store = Depends(get_pattern_store)):
        return store.list_all()
"""

from __future__ import annotations

from typing import Any, Generator, Optional

# Re-export store dependencies from centralized registry
from app.core.store_registry import (
    get_pattern_store,
    get_joblog_store,
    get_strip_family_store,
    get_profile_store,
    get_advisory_store,
    get_prompt_history_store,
    get_budget_tracker,
    get_request_record_store,
    get_learned_overrides_store,
    reset_all_stores,
    reset_store,
    StoreKeys,
)

__all__ = [
    # Database
    "get_db_session",
    # Auth
    "get_current_user",
    "get_optional_user",
    # Pagination
    "Pagination",
    "get_pagination",
    # Stores
    "get_pattern_store",
    "get_joblog_store",
    "get_strip_family_store",
    "get_profile_store",
    "get_advisory_store",
    "get_prompt_history_store",
    "get_budget_tracker",
    "get_request_record_store",
    "get_learned_overrides_store",
    # Testing utilities
    "reset_all_stores",
    "reset_store",
    "StoreKeys",
]


def get_db_session() -> Generator[Any, None, None]:
    """
    Dependency that provides a database session.
    
    Currently a stub - returns None until database is configured.
    
    Usage::

        # router.get("/items")
        def list_items(db = Depends(get_db_session)):
            ...
    """
    # TODO: Implement actual database session when SQLAlchemy is configured
    yield None


def get_current_user() -> Optional[dict]:
    """
    Dependency that returns the current authenticated user.
    
    Currently a stub - returns None (anonymous) until auth is configured.
    
    Usage::

        # router.get("/profile")
        def get_profile(user = Depends(get_current_user)):
            ...
    """
    # TODO: Implement actual auth when user system is configured
    return None


def get_optional_user() -> Optional[dict]:
    """
    Dependency for optional authentication.
    Returns user if authenticated, None otherwise.
    """
    return None


class Pagination:
    """Pagination parameters dependency."""
    
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = max(0, skip)
        self.limit = min(1000, max(1, limit))


def get_pagination(skip: int = 0, limit: int = 100) -> Pagination:
    """Dependency for pagination parameters."""
    return Pagination(skip=skip, limit=limit)
