# services/api/app/core/store_registry.py
"""
Store Registry — Dependency Injection for Data Stores.

This module provides FastAPI-compatible dependency injection for all data stores.
It solves the singleton scaling problem: module-level globals break horizontal scaling
because each process gets its own copy.

Architecture:
- StoreRegistry holds store instances per-process (compatible with current file storage)
- get_*() functions are FastAPI dependencies via Depends()
- For horizontal scaling, stores can be backed by shared storage (Redis/PostgreSQL)

Usage:
    from fastapi import Depends
    from app.core.store_registry import get_pattern_store

    @router.get("/patterns")
    def list_patterns(store: SQLitePatternStore = Depends(get_pattern_store)):
        return store.list_all()

Migration Path:
1. CURRENT: File-based stores with process-local instances
2. FUTURE: Same interface, shared backend (Redis/PostgreSQL)

Note: The stores themselves are NOT request-scoped (they're shared within a process).
This is intentional — we want connection reuse. For true horizontal scaling,
the stores' backends need to be shared (database, Redis).
"""
from __future__ import annotations

import logging
import threading
from typing import Optional, TypeVar, Type, Dict, Any, Callable

logger = logging.getLogger(__name__)

T = TypeVar("T")


class StoreRegistry:
    """
    Centralized registry for data store instances.

    Thread-safe singleton that manages store lifecycle.
    Supports dependency injection via FastAPI Depends().
    """

    _instance: Optional["StoreRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "StoreRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._stores: Dict[str, Any] = {}
                    cls._instance._factories: Dict[str, Callable[[], Any]] = {}
                    cls._instance._factories_registered = False
        return cls._instance

    def _ensure_factories_registered(self) -> None:
        """Ensure default factories are registered (lazy initialization)."""
        if not self._factories_registered:
            _register_default_factories_impl(self)
            self._factories_registered = True

    def register_factory(self, key: str, factory: Callable[[], T]) -> None:
        """Register a factory function for lazy store creation."""
        self._factories[key] = factory

    def get(self, key: str) -> Any:
        """Get or create a store instance by key."""
        self._ensure_factories_registered()
        if key not in self._stores:
            with self._lock:
                if key not in self._stores:
                    if key not in self._factories:
                        raise KeyError(f"No factory registered for store: {key}")
                    self._stores[key] = self._factories[key]()
                    logger.debug("Created store instance: %s", key)
        return self._stores[key]

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset store instance(s). Primarily for testing.

        Args:
            key: Specific store to reset, or None to reset all.
        """
        with self._lock:
            if key is not None:
                self._stores.pop(key, None)
            else:
                self._stores.clear()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton itself. For testing only."""
        with cls._lock:
            cls._instance = None


def get_registry() -> StoreRegistry:
    """Get the global store registry."""
    return StoreRegistry()


# =============================================================================
# Store Keys (canonical identifiers)
# =============================================================================

class StoreKeys:
    """Canonical store key constants."""
    PATTERN = "sqlite_pattern"
    JOBLOG = "sqlite_joblog"
    STRIP_FAMILY = "sqlite_strip_family"
    PROFILE = "constraint_profile"
    ADVISORY_ASSET = "advisory_asset"
    PROMPT_HISTORY = "prompt_history"
    BUDGET_TRACKER = "budget_tracker"
    REQUEST_RECORD = "request_record"
    LEARNED_OVERRIDES = "learned_overrides"


# =============================================================================
# Factory Registration
# =============================================================================

def _register_default_factories_impl(registry: StoreRegistry) -> None:
    """
    Register default store factories on a registry instance.

    Called lazily by StoreRegistry._ensure_factories_registered().
    """
    # RMOS SQLite stores
    def _pattern_factory():
        from app.stores.sqlite_pattern_store import SQLitePatternStore
        return SQLitePatternStore()

    def _joblog_factory():
        from app.stores.sqlite_joblog_store import SQLiteJobLogStore
        return SQLiteJobLogStore()

    def _strip_family_factory():
        from app.stores.sqlite_strip_family_store import SQLiteStripFamilyStore
        return SQLiteStripFamilyStore()

    # Constraint profiles
    def _profile_factory():
        from app.rmos.constraint_profiles import ProfileStore
        return ProfileStore()

    # Advisory stores
    def _advisory_asset_factory():
        from app.advisory.store import AdvisoryAssetStore
        return AdvisoryAssetStore()

    def _prompt_history_factory():
        from app.advisory.store import PromptHistoryStore
        return PromptHistoryStore()

    def _budget_tracker_factory():
        from app.advisory.budget_store import BudgetTracker
        return BudgetTracker()

    def _request_record_factory():
        from app.advisory.budget_store import RequestRecordStore
        return RequestRecordStore()

    # Learned overrides
    def _learned_overrides_factory():
        from app._experimental.cnc_production.feeds_speeds.core.learned_overrides import LearnedOverridesStore
        return LearnedOverridesStore()

    # Register all
    registry.register_factory(StoreKeys.PATTERN, _pattern_factory)
    registry.register_factory(StoreKeys.JOBLOG, _joblog_factory)
    registry.register_factory(StoreKeys.STRIP_FAMILY, _strip_family_factory)
    registry.register_factory(StoreKeys.PROFILE, _profile_factory)
    registry.register_factory(StoreKeys.ADVISORY_ASSET, _advisory_asset_factory)
    registry.register_factory(StoreKeys.PROMPT_HISTORY, _prompt_history_factory)
    registry.register_factory(StoreKeys.BUDGET_TRACKER, _budget_tracker_factory)
    registry.register_factory(StoreKeys.REQUEST_RECORD, _request_record_factory)
    registry.register_factory(StoreKeys.LEARNED_OVERRIDES, _learned_overrides_factory)


# =============================================================================
# FastAPI Dependencies (use with Depends())
# =============================================================================

def get_pattern_store():
    """
    FastAPI dependency for pattern store.

    Usage:
        @router.get("/patterns")
        def list_patterns(store = Depends(get_pattern_store)):
            return store.list_all()
    """
    return get_registry().get(StoreKeys.PATTERN)


def get_joblog_store():
    """FastAPI dependency for job log store."""
    return get_registry().get(StoreKeys.JOBLOG)


def get_strip_family_store():
    """FastAPI dependency for strip family store."""
    return get_registry().get(StoreKeys.STRIP_FAMILY)


def get_profile_store():
    """FastAPI dependency for constraint profile store."""
    return get_registry().get(StoreKeys.PROFILE)


def get_advisory_store():
    """FastAPI dependency for advisory asset store."""
    return get_registry().get(StoreKeys.ADVISORY_ASSET)


def get_prompt_history_store():
    """FastAPI dependency for prompt history store."""
    return get_registry().get(StoreKeys.PROMPT_HISTORY)


def get_budget_tracker():
    """FastAPI dependency for budget tracker."""
    return get_registry().get(StoreKeys.BUDGET_TRACKER)


def get_request_record_store():
    """FastAPI dependency for request record store."""
    return get_registry().get(StoreKeys.REQUEST_RECORD)


def get_learned_overrides_store():
    """FastAPI dependency for learned overrides store."""
    return get_registry().get(StoreKeys.LEARNED_OVERRIDES)


# =============================================================================
# Test Utilities
# =============================================================================

def reset_all_stores() -> None:
    """Reset all store instances. For testing only."""
    get_registry().reset()


def reset_store(key: str) -> None:
    """Reset a specific store. For testing only."""
    get_registry().reset(key)
