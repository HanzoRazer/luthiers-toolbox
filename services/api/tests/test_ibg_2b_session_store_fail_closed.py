"""
IBG-2B-FIX — session store failure policy tests.

Guards the property that an explicit IBG_SESSION_STORE=redis never silently
degrades to per-worker in-memory sessions.
"""

from __future__ import annotations

import importlib.util
import os

import pytest


def _load_session_store_module():
    """Load session_store.py without ibg/__init__.py (ezdxf)."""
    module_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "instrument_geometry", "body", "ibg", "session_store.py",
    )
    spec = importlib.util.spec_from_file_location(
        "ibg_session_store_fail_closed", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ss = _load_session_store_module()


@pytest.fixture(autouse=True)
def _reset():
    ss.reset_session_store()
    yield
    ss.reset_session_store()


def _env(monkeypatch, **kw):
    for key in (
        "IBG_SESSION_STORE",
        "REDIS_URL",
        "IBG_SESSION_STORE_ALLOW_FALLBACK",
        "IBG_SESSION_TTL_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, val in kw.items():
        monkeypatch.setenv(key, val)


# ── default path ──────────────────────────────────────────────────────────────

def test_default_is_memory_and_does_not_raise(monkeypatch):
    _env(monkeypatch)
    assert isinstance(ss.get_session_store(), ss.InMemoryIBGSessionStore)


def test_unrecognised_backend_falls_back_to_memory(monkeypatch):
    _env(monkeypatch, IBG_SESSION_STORE="postgres")
    assert isinstance(ss.get_session_store(), ss.InMemoryIBGSessionStore)


# ── fail-closed: the point of this patch ──────────────────────────────────────

def test_redis_requested_without_url_raises(monkeypatch):
    _env(monkeypatch, IBG_SESSION_STORE="redis")
    monkeypatch.setattr(ss, "REDIS_AVAILABLE", True)
    with pytest.raises(ss.IBGSessionStoreUnavailable, match="REDIS_URL not set"):
        ss.get_session_store()


def test_redis_requested_but_package_missing_raises(monkeypatch):
    _env(monkeypatch, IBG_SESSION_STORE="redis", REDIS_URL="redis://x:6379/0")
    monkeypatch.setattr(ss, "REDIS_AVAILABLE", False)
    with pytest.raises(ss.IBGSessionStoreUnavailable, match="not installed"):
        ss.get_session_store()


def test_redis_requested_but_unreachable_raises(monkeypatch):
    _env(monkeypatch, IBG_SESSION_STORE="redis", REDIS_URL="redis://x:6379/0")
    monkeypatch.setattr(ss, "REDIS_AVAILABLE", True)

    class _Boom:
        @staticmethod
        def from_url(_url):
            raise ConnectionError("refused")

    monkeypatch.setattr(ss, "redis", _Boom)
    with pytest.raises(ss.IBGSessionStoreUnavailable, match="connection failed"):
        ss.get_session_store()


def test_ping_failure_raises(monkeypatch):
    _env(monkeypatch, IBG_SESSION_STORE="redis", REDIS_URL="redis://x:6379/0")
    monkeypatch.setattr(ss, "REDIS_AVAILABLE", True)

    class _Client:
        def ping(self):
            raise ConnectionError("no route to host")

    class _Mod:
        @staticmethod
        def from_url(_url):
            return _Client()

    monkeypatch.setattr(ss, "redis", _Mod)
    with pytest.raises(ss.IBGSessionStoreUnavailable):
        ss.get_session_store()


# ── explicit escape hatch ─────────────────────────────────────────────────────

def test_allow_fallback_downgrades_and_warns(monkeypatch, caplog):
    _env(
        monkeypatch,
        IBG_SESSION_STORE="redis",
        IBG_SESSION_STORE_ALLOW_FALLBACK="1",
    )
    with caplog.at_level("WARNING"):
        store = ss.get_session_store()
    assert isinstance(store, ss.InMemoryIBGSessionStore)
    assert any("IN-MEMORY" in r.getMessage() for r in caplog.records)


# ── bundled fixes ─────────────────────────────────────────────────────────────

def test_session_id_entropy_is_64_bits():
    sid = ss._new_session_id()
    assert sid.startswith("sess_")
    assert len(sid) == len("sess_") + 16


def test_session_ids_are_unique_across_many_creates():
    store = ss.InMemoryIBGSessionStore()
    ids = {store.create({"n": i}) for i in range(5000)}
    assert len(ids) == 5000


def test_expired_session_is_not_served_before_sweep():
    store = ss.InMemoryIBGSessionStore(ttl_seconds=0)
    sid = store.create({"a": 1})
    assert store.get(sid) is None


def test_update_returns_false_for_unknown_session():
    store = ss.InMemoryIBGSessionStore()
    assert store.update("sess_doesnotexist", {"a": 1}) is False


def test_timestamps_are_timezone_aware():
    store = ss.InMemoryIBGSessionStore()
    sid = store.create({"a": 1})
    assert store._timestamps[sid].tzinfo is not None
