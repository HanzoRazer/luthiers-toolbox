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

Author: Production Shop
Sprint: IBG-2B
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, Iterator, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


DEFAULT_TTL_SECONDS = 86400  # 24 hours


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

    def create(self, data: Dict[str, Any]) -> str:
        session_id = f"sess_{uuid4().hex[:8]}"
        now = datetime.utcnow()
        with self._lock:
            self._sessions[session_id] = data
            self._timestamps[session_id] = now
        logger.debug(f"IBG_SESSION_CREATE | session_id={session_id}")
        return session_id

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        self._cleanup_expired()
        with self._lock:
            return self._sessions.get(session_id)

    def update(self, session_id: str, data: Dict[str, Any]) -> bool:
        with self._lock:
            if session_id not in self._sessions:
                return False
            self._sessions[session_id] = data
            self._timestamps[session_id] = datetime.utcnow()
        logger.debug(f"IBG_SESSION_UPDATE | session_id={session_id}")
        return True

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._timestamps.pop(session_id, None)
        logger.debug(f"IBG_SESSION_DELETE | session_id={session_id}")

    def _cleanup_expired(self) -> None:
        """Remove sessions older than TTL."""
        now = datetime.utcnow()
        with self._lock:
            expired = [
                sid for sid, ts in self._timestamps.items()
                if now - ts > self._ttl
            ]
            for sid in expired:
                del self._sessions[sid]
                del self._timestamps[sid]
                logger.debug(f"IBG_SESSION_EXPIRED | session_id={sid}")


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
        session_id = f"sess_{uuid4().hex[:8]}"
        self._client.setex(
            self._key(session_id),
            self._ttl_seconds,
            json.dumps(data),
        )
        logger.debug(f"REDIS_IBG_SESSION_CREATE | session_id={session_id}")
        return session_id

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        raw = self._client.get(self._key(session_id))
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def update(self, session_id: str, data: Dict[str, Any]) -> bool:
        key = self._key(session_id)
        if not self._client.exists(key):
            return False
        self._client.setex(key, self._ttl_seconds, json.dumps(data))
        logger.debug(f"REDIS_IBG_SESSION_UPDATE | session_id={session_id}")
        return True

    def delete(self, session_id: str) -> None:
        self._client.delete(self._key(session_id))
        logger.debug(f"REDIS_IBG_SESSION_DELETE | session_id={session_id}")


# Module-level store instance (lazy initialization)
_store: Optional[IBGSessionStore] = None
_store_lock = Lock()


def get_session_store() -> IBGSessionStore:
    """
    Get the IBG session store instance.

    Environment variables:
        IBG_SESSION_STORE: "memory" (default) or "redis"
        REDIS_URL: Redis connection URL (required if backend is "redis")
        IBG_SESSION_TTL_SECONDS: Session TTL in seconds (default: 86400)

    Returns:
        IBGSessionStore instance
    """
    global _store

    if _store is not None:
        return _store

    with _store_lock:
        if _store is not None:
            return _store

        backend = os.getenv("IBG_SESSION_STORE", "memory").lower()
        ttl_seconds = int(os.getenv("IBG_SESSION_TTL_SECONDS", str(DEFAULT_TTL_SECONDS)))

        if backend == "redis":
            if not REDIS_AVAILABLE:
                logger.error(
                    "IBG_SESSION_STORE=redis but redis package not installed. "
                    "Falling back to memory."
                )
                _store = InMemoryIBGSessionStore(ttl_seconds=ttl_seconds)
            else:
                redis_url = os.getenv("REDIS_URL")
                if not redis_url:
                    logger.error(
                        "IBG_SESSION_STORE=redis but REDIS_URL not set. "
                        "Falling back to memory."
                    )
                    _store = InMemoryIBGSessionStore(ttl_seconds=ttl_seconds)
                else:
                    try:
                        client = redis.from_url(redis_url)
                        client.ping()
                        _store = RedisIBGSessionStore(client=client, ttl_seconds=ttl_seconds)
                        logger.info(f"IBG session store initialized with Redis: {redis_url}")
                    except Exception as e:
                        logger.error(f"Failed to connect to Redis: {e}. Falling back to memory.")
                        _store = InMemoryIBGSessionStore(ttl_seconds=ttl_seconds)
        else:
            _store = InMemoryIBGSessionStore(ttl_seconds=ttl_seconds)
            logger.info("IBG session store initialized with in-memory storage")

        return _store


def reset_session_store() -> None:
    """Reset the session store instance. For testing only."""
    global _store
    with _store_lock:
        _store = None
