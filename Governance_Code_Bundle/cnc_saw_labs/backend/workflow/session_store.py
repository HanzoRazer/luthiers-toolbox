from __future__ import annotations

from typing import Dict
from threading import RLock

from app.workflow.state_machine import WorkflowSession


class InMemoryWorkflowSessionStore:
    """
    Minimal session store for dev/tests.
    Replace with DB-backed store for production.
    """
    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: Dict[str, WorkflowSession] = {}

    def put(self, session: WorkflowSession) -> WorkflowSession:
        with self._lock:
            self._sessions[session.session_id] = session
            return session

    def get(self, session_id: str) -> WorkflowSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def require(self, session_id: str) -> WorkflowSession: