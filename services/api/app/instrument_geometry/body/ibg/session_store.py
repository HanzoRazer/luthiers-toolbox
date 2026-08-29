"""
IBG Session Store
=================

Abstraction for IBG body solver session storage with pluggable backends.

Backends:
- InMemoryIBGSessionStore: Development/testing (default)
- RedisIBGSessionStore: Production multi-worker deployment

Selection via environment variable:
    IBG_SESSION_STORE=memory  (default)
    IBG_SESSION_STORE=redis   (requires REDIS_URL)

Session TTL: 24 hours (configurable via IBG_SESSION_TTL_SECONDS)

Failure policy (IBG-2B-FIX, 2026-08-29)
---------------------------------------
When the operator explicitly requests ``IBG_SESSION_STORE=redis``, a failure to
reach Redis raises ``IBGSessionStoreUnavailable`` instead of downgrading to the
in-memory store. Silent downgrade gave every worker a private dict, so sessions
404'd non-deterministically depending on which worker served the request, with
one startup log line as the only evidence.

Set ``IBG_SESSION_STORE_ALLOW_FALLBACK=1`` to restore the old degrade-to-memory
behaviour (local development only). It logs at WARNING every time it engages.

Author: Production Shop
Sprint: IBG-2B
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


DEFAULT_TTL_SECONDS = 86400  # 24 hours

# Session id entropy. 16 hex chars = 64 bits.
# The previous value of 8 (32 bits) reaches a ~50% birthday-collision
# probability near 77k live sessions, and create() does not check for an
# existing key — a collision silently overwrites another user's solved model.
SESSION_ID_HEX_CHARS = 16

# In-memory store only: minimum interval between expiry sweeps. The sweep is
# O(n) over live sessions and previously ran on every get().
_SWEEP_INTERVAL = timedelta(seconds=60)


def _utcnow() -> datetime:
    """Timezone-aware UTC now. ``datetime.utcnow()`` is deprecated in 3.12+."""
    return datetime.now(timezone.utc)


def _new_session_id() -> str:
    return f"sess_{uuid4().hex[:SESSION_ID_HEX_CHARS]}"


class IBGSessionStoreUnavailable(RuntimeError):
    """
    Raised when the configured session backend cannot be initialised and
    fallback is not permitted.

    This is deliberately fatal. A multi-worker deployment that silently falls
    back to per-process memory is worse than one that refuses to start.
    """


class IBGSessionStore:
    """
    Abstract interface for IBG session storage.

    Sessions store solved body models, landmarks, and instrument specs.
    """

    def create(self, data: Dict[str, Any]) -> str:
        """Create a new session. Returns session_id."""
        raise NotImplementedError

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID, or None if not found."""
        raise NotImplementedError

    def update(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data. Returns True if found and updated."""
        raise NotImplementedError

    def delete(self, session_id: str) -> None:
        """Delete session by ID."""
        raise NotImplementedError

    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return self.get(session_id) is not None


class InMemoryIBGSessionStore(IBGSessionStore):
    """
    In-memory session store for development/testing.

    NOT suitable for production multi-worker deployments.
    Sessions expire after TTL to prevent memory leaks.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = Lock()
        self._ttl = timedelta(seconds=ttl_seconds)
        self._last_sweep = _utcnow()

    def create(self, data: Dict[str, Any]) -> str:
        session_id = _new_session_id()
        now = _utcnow()
        with self._lock:
            self._sessions[session_id] = data
            self._timestamps[session_id] = now
        logger.debug("IBG_SESSION_CREATE | session_id=%s", session_id)
        return session_id

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        self._cleanup_expired()
        with self._lock:
            ts = self._timestamps.get(session_id)
            if ts is not None and _utcnow() - ts > self._ttl:
                # Expired but not yet swept — do not serve it.
                return None
            return self._sessions.get(session_id)

    def update(self, session_id: str, data: Dict[str, Any]) -> bool:
        with self._lock:
            if session_id not in self._sessions:
                return False
            self._sessions[session_id] = data
            self._timestamps[session_id] = _utcnow()
        logger.debug("IBG_SESSION_UPDATE | session_id=%s", session_id)
        return True

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._timestamps.pop(session_id, None)
        logger.debug("IBG_SESSION_DELETE | session_id=%s", session_id)

    def _cleanup_expired(self, force: bool = False) -> None:
        """Remove sessions older than TTL. Rate-limited to _SWEEP_INTERVAL."""
        now = _utcnow()
        with self._lock:
            if not force and now - self._last_sweep < _SWEEP_INTERVAL:
                return
            self._last_sweep = now
            expired = [
                sid for sid, ts in self._timestamps.items()
                if now - ts > self._ttl
            ]
            for sid in expired:
                del self._sessions[sid]
                del self._timestamps[sid]
                logger.debug("IBG_SESSION_EXPIRED | session_id=%s", sid)


class RedisIBGSessionStore(IBGSessionStore):
    """
    Redis-backed session store for production multi-worker deployments.

    Each session is stored as a JSON blob with automatic TTL expiration.
    Key format: ibg_session:{session_id}

    Requires: pip install redis
    """

    def __init__(
        self,
        client: "redis.Redis",
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        key_prefix: str = "ibg_session",
    ):
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    def _key(self, session_id: str) -> str:
        return f"{self._key_prefix}:{session_id}"

    def create(self, data: Dict[str, Any]) -> str:
        session_id = _new_session_id()
        self._client.setex(
            self._key(session_id),
            self._ttl_seconds,
            json.dumps(data),
        )
        logger.debug("REDIS_IBG_SESSION_CREATE | session_id=%s", session_id)
        return session_id

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        raw = self._client.get(self._key(session_id))
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def update(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update only if the key currently exists.

        ``SET ... XX`` performs the existence check and the write in one
        round trip. The previous exists()-then-setex sequence could resurrect
        a key that expired between the two calls and report success.
        """
        written = self._client.set(
            self._key(session_id),
            json.dumps(data),
            ex=self._ttl_seconds,
            xx=True,
        )
        if not written:
            return False
        logger.debug("REDIS_IBG_SESSION_UPDATE | session_id=%s", session_id)
        return True

    def delete(self, session_id: str) -> None:
        self._client.delete(self._key(session_id))
        logger.debug("REDIS_IBG_SESSION_DELETE | session_id=%s", session_id)

    def exists(self, session_id: str) -> bool:
        """Override: avoid deserialising the whole blob to answer a boolean."""
        return bool(self._client.exists(self._key(session_id)))


# Module-level store instance (lazy initialization)
_store: Optional[IBGSessionStore] = None
_store_lock = Lock()


def _fallback_allowed() -> bool:
    return os.getenv("IBG_SESSION_STORE_ALLOW_FALLBACK", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _fail_or_fallback(reason: str, ttl_seconds: int) -> IBGSessionStore:
    """
    Redis was explicitly requested and could not be initialised.

    Raise unless fallback is explicitly permitted.
    """
    if _fallback_allowed():
        logger.warning(
            "IBG_SESSION_STORE=redis requested but unavailable (%s). "
            "IBG_SESSION_STORE_ALLOW_FALLBACK is set, so falling back to "
            "IN-MEMORY sessions. Sessions will NOT be shared across workers "
            "and will be lost on restart. Do not use this in production.",
            reason,
        )
        return InMemoryIBGSessionStore(ttl_seconds=ttl_seconds)

    raise IBGSessionStoreUnavailable(
        f"IBG_SESSION_STORE=redis was requested but the backend could not be "
        f"initialised: {reason}. Refusing to fall back to in-memory sessions, "
        f"which are per-worker and would produce intermittent 404s. Fix the "
        f"backend, or set IBG_SESSION_STORE_ALLOW_FALLBACK=1 for local "
        f"development only."
    )


def get_session_store() -> IBGSessionStore:
    """
    Get the IBG session store instance.

    Environment variables:
        IBG_SESSION_STORE: "memory" (default) or "redis"
        REDIS_URL: Redis connection URL (required if backend is "redis")
        IBG_SESSION_TTL_SECONDS: Session TTL in seconds (default: 86400)
        IBG_SESSION_STORE_ALLOW_FALLBACK: permit degrade-to-memory (dev only)

    Returns:
        IBGSessionStore instance

    Raises:
        IBGSessionStoreUnavailable: backend is "redis", initialisation failed,
            and fallback is not permitted.

    Call this once at application startup so a misconfiguration fails at boot
    rather than on the first request.
    """
    global _store

    if _store is not None:
        return _store

    with _store_lock:
        if _store is not None:
            return _store

        backend = os.getenv("IBG_SESSION_STORE", "memory").strip().lower()
        ttl_seconds = int(os.getenv("IBG_SESSION_TTL_SECONDS", str(DEFAULT_TTL_SECONDS)))

        if backend != "redis":
            if backend not in ("", "memory"):
                logger.warning(
                    "Unrecognised IBG_SESSION_STORE=%r; using in-memory store.",
                    backend,
                )
            _store = InMemoryIBGSessionStore(ttl_seconds=ttl_seconds)
            logger.info("IBG session store initialized with in-memory storage")
            return _store

        # backend == "redis" — explicit operator intent from here down.
        if not REDIS_AVAILABLE:
            _store = _fail_or_fallback("redis package not installed", ttl_seconds)
            return _store

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            _store = _fail_or_fallback("REDIS_URL not set", ttl_seconds)
            return _store

        try:
            client = redis.from_url(redis_url)
            client.ping()
        except Exception as exc:
            _store = _fail_or_fallback(f"connection failed: {exc}", ttl_seconds)
            return _store

        _store = RedisIBGSessionStore(client=client, ttl_seconds=ttl_seconds)
        logger.info("IBG session store initialized with Redis")
        return _store


def reset_session_store() -> None:
    """Reset the store instance. For testing only."""
    global _store
    with _store_lock:
        _store = None
