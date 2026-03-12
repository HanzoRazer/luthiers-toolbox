# tests/test_store_registry.py
"""
Tests for the centralized Store Registry.

Verifies:
1. Singleton behavior within a process
2. Factory registration and lazy instantiation
3. Reset functionality for test isolation
4. Backward compatibility with legacy imports
"""
import pytest


class TestStoreRegistry:
    """Tests for StoreRegistry class."""

    def test_registry_is_singleton(self):
        """Registry should be a singleton."""
        from app.core.store_registry import StoreRegistry, get_registry

        reg1 = get_registry()
        reg2 = get_registry()
        reg3 = StoreRegistry()

        assert reg1 is reg2
        assert reg1 is reg3

    def test_factory_registration(self):
        """Factories should be registered and invoked lazily."""
        from app.core.store_registry import get_registry, StoreRegistry

        # Reset for clean test
        StoreRegistry.reset_instance()

        reg = get_registry()
        calls = []

        def test_factory():
            calls.append(1)
            return {"created": True}

        reg.register_factory("test_store", test_factory)

        # Factory not called yet
        assert len(calls) == 0

        # First get creates instance
        store1 = reg.get("test_store")
        assert len(calls) == 1
        assert store1 == {"created": True}

        # Second get returns same instance (no new factory call)
        store2 = reg.get("test_store")
        assert len(calls) == 1
        assert store1 is store2

        # Cleanup
        StoreRegistry.reset_instance()

    def test_reset_single_store(self):
        """reset(key) should reset only the specified store."""
        from app.core.store_registry import get_registry, StoreRegistry

        StoreRegistry.reset_instance()
        reg = get_registry()

        calls_a = []
        calls_b = []

        reg.register_factory("store_a", lambda: (calls_a.append(1), "A")[1])
        reg.register_factory("store_b", lambda: (calls_b.append(1), "B")[1])

        # Create both stores
        reg.get("store_a")
        reg.get("store_b")
        assert len(calls_a) == 1
        assert len(calls_b) == 1

        # Reset only store_a
        reg.reset("store_a")

        # Re-get should recreate only store_a
        reg.get("store_a")
        reg.get("store_b")
        assert len(calls_a) == 2
        assert len(calls_b) == 1

        StoreRegistry.reset_instance()

    def test_reset_all_stores(self):
        """reset() with no args should reset all stores."""
        from app.core.store_registry import get_registry, StoreRegistry, reset_all_stores

        StoreRegistry.reset_instance()
        reg = get_registry()

        calls_a = []
        calls_b = []

        reg.register_factory("store_a", lambda: (calls_a.append(1), "A")[1])
        reg.register_factory("store_b", lambda: (calls_b.append(1), "B")[1])

        reg.get("store_a")
        reg.get("store_b")

        reset_all_stores()

        reg.get("store_a")
        reg.get("store_b")

        assert len(calls_a) == 2
        assert len(calls_b) == 2

        StoreRegistry.reset_instance()

    def test_missing_factory_raises(self):
        """Getting unregistered store should raise KeyError."""
        from app.core.store_registry import get_registry, StoreRegistry

        StoreRegistry.reset_instance()
        reg = get_registry()

        with pytest.raises(KeyError, match="No factory registered"):
            reg.get("nonexistent_store")

        StoreRegistry.reset_instance()


class TestStoreKeys:
    """Tests for StoreKeys constants."""

    def test_all_keys_defined(self):
        """All expected store keys should be defined."""
        from app.core.store_registry import StoreKeys

        expected = [
            "PATTERN",
            "JOBLOG",
            "STRIP_FAMILY",
            "PROFILE",
            "ADVISORY_ASSET",
            "PROMPT_HISTORY",
            "BUDGET_TRACKER",
            "REQUEST_RECORD",
            "LEARNED_OVERRIDES",
        ]

        for key in expected:
            assert hasattr(StoreKeys, key), f"Missing StoreKeys.{key}"


class TestStoreDependencies:
    """Tests for FastAPI dependency functions."""

    def test_get_pattern_store_returns_instance(self, tmp_path, monkeypatch):
        """get_pattern_store should return a store instance."""
        from app.core.store_registry import StoreRegistry, get_pattern_store
        from app.stores.sqlite_pattern_store import SQLitePatternStore

        # Use tmp_path for SQLite
        monkeypatch.setenv("RMOS_DB_PATH", str(tmp_path / "test.db"))
        StoreRegistry.reset_instance()

        store = get_pattern_store()
        assert store is not None
        assert isinstance(store, SQLitePatternStore)

        StoreRegistry.reset_instance()

    def test_get_profile_store_returns_instance(self, tmp_path, monkeypatch):
        """get_profile_store should return a ProfileStore instance."""
        from app.core.store_registry import StoreRegistry, get_profile_store

        monkeypatch.setenv("RMOS_PROFILE_YAML_PATH", str(tmp_path / "profiles.yaml"))
        StoreRegistry.reset_instance()

        store = get_profile_store()
        assert store is not None
        assert hasattr(store, "get")
        assert hasattr(store, "list_all")

        StoreRegistry.reset_instance()


class TestBackwardCompatibility:
    """Tests for backward compatibility with legacy imports."""

    def test_rmos_stores_legacy_import(self, tmp_path, monkeypatch):
        """Legacy import from rmos_stores should still work."""
        from app.core.store_registry import StoreRegistry

        monkeypatch.setenv("RMOS_DB_PATH", str(tmp_path / "test.db"))
        StoreRegistry.reset_instance()

        # This is the legacy import pattern
        from app.api.deps.rmos_stores import get_pattern_store

        store = get_pattern_store()
        assert store is not None

        StoreRegistry.reset_instance()

    def test_advisory_store_legacy_import(self, tmp_path, monkeypatch):
        """Legacy import from advisory.store should still work."""
        from app.core.store_registry import StoreRegistry

        monkeypatch.setenv("ADVISORY_ASSETS_ROOT", str(tmp_path / "advisory"))
        StoreRegistry.reset_instance()

        from app.advisory.store import get_advisory_store

        store = get_advisory_store()
        assert store is not None

        StoreRegistry.reset_instance()

    def test_constraint_profiles_legacy_import(self, tmp_path, monkeypatch):
        """Legacy import from constraint_profiles should still work."""
        from app.core.store_registry import StoreRegistry

        monkeypatch.setenv("RMOS_PROFILE_YAML_PATH", str(tmp_path / "profiles.yaml"))
        StoreRegistry.reset_instance()

        from app.rmos.constraint_profiles import get_profile_store

        store = get_profile_store()
        assert store is not None

        StoreRegistry.reset_instance()

    def test_deps_reexports_stores(self):
        """app.api.deps should re-export all store getters."""
        from app.api.deps import (
            get_pattern_store,
            get_joblog_store,
            get_strip_family_store,
            get_profile_store,
            get_advisory_store,
            get_prompt_history_store,
            get_budget_tracker,
            get_request_record_store,
            get_learned_overrides_store,
        )

        # Just verify imports work
        assert callable(get_pattern_store)
        assert callable(get_joblog_store)
        assert callable(get_profile_store)
        assert callable(get_advisory_store)


class TestTestIsolation:
    """Tests for test isolation utilities."""

    def test_reset_store_by_key(self, tmp_path, monkeypatch):
        """reset_store(key) should clear specific store."""
        from app.core.store_registry import (
            StoreRegistry,
            get_profile_store,
            reset_store,
            StoreKeys,
        )

        monkeypatch.setenv("RMOS_PROFILE_YAML_PATH", str(tmp_path / "profiles.yaml"))
        StoreRegistry.reset_instance()

        store1 = get_profile_store()
        reset_store(StoreKeys.PROFILE)
        store2 = get_profile_store()

        # Should be different instances after reset
        assert store1 is not store2

        StoreRegistry.reset_instance()

    def test_legacy_reset_functions(self, tmp_path, monkeypatch):
        """Legacy reset_*_store() functions should still work."""
        from app.core.store_registry import StoreRegistry

        monkeypatch.setenv("ADVISORY_ASSETS_ROOT", str(tmp_path / "advisory"))
        StoreRegistry.reset_instance()

        from app.advisory.store import get_advisory_store, reset_advisory_store

        store1 = get_advisory_store()
        reset_advisory_store()
        store2 = get_advisory_store()

        assert store1 is not store2

        StoreRegistry.reset_instance()
