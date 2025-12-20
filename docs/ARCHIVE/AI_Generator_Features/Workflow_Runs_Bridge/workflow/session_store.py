"""
Workflow Session Store - In-Memory Implementation

Minimal session store for dev/tests.
Use DbWorkflowSessionStore (in workflow/db/store.py) for production.
"""
from __future__ import annotations

from typing import Dict, Optional
from threading import RLock

from .state_machine import WorkflowSession


class InMemoryWorkflowSessionStore:
    """
    In-memory session store for development and testing.

    Thread-safe using RLock.
    Replace with DB-backed store for production.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: Dict[str, WorkflowSession] = {}

    def put(self, session: WorkflowSession) -> WorkflowSession:
        """Store or update a session."""
        with self._lock:
            self._sessions[session.session_id] = session
            return session

    def get(self, session_id: str) -> Optional[WorkflowSession]:
        """Get a session by ID. Returns None if not found."""
        with self._lock:
            return self._sessions.get(session_id)

    def require(self, session_id: str) -> WorkflowSession:
        """Get a session by ID. Raises KeyError if not found."""
        s = self.get(session_id)
        if s is None:
            raise KeyError(f"Workflow session not found: {session_id}")
        return s

    def delete(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def list_all(self) -> list[WorkflowSession]:
        """List all sessions (newest first by session_id)."""
        with self._lock:
            return sorted(
                self._sessions.values(),
                key=lambda s: s.session_id,
                reverse=True
            )

    def clear(self) -> None:
        """Clear all sessions. Useful for testing."""
        with self._lock:
            self._sessions.clear()


# Global singleton for simple usage
STORE = InMemoryWorkflowSessionStore()
