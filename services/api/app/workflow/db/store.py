"""
DB-backed Workflow Session Store

Production-ready store that persists WorkflowSession to SQLite/PostgreSQL.
Stores full session as JSON while indexing key fields for queries.
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.workflow.state_machine import WorkflowSession
from .models import WorkflowSessionRow


class DbWorkflowSessionStore:
    """
    DB-backed session store.

    Stores WorkflowSession as JSON for flexibility while indexing key
    fields for efficient filtering. Uses SQLAlchemy Session for transactions.

    Usage:
        from app.db.session import db_session

        with db_session() as db:
            session = STORE.get(db, session_id)
            # ... modify session ...
            STORE.put(db, session)
    """

    def put(self, db: Session, session: WorkflowSession) -> WorkflowSession:
        """Store or update a session."""
        payload = session.model_dump(mode="json")

        # Extract index fields from index_meta
        tool_id = (session.index_meta or {}).get("tool_id")
        material_id = (session.index_meta or {}).get("material_id")
        machine_id = (session.index_meta or {}).get("machine_id")

        row = db.get(WorkflowSessionRow, session.session_id)
        if row is None:
            row = WorkflowSessionRow(
                session_id=session.session_id,
                mode=session.mode.value,
                state=session.state.value,
                session_json=json.dumps(payload),
                tool_id=tool_id,
                material_id=material_id,
                machine_id=machine_id,
                candidate_attempt_count=session.candidate_attempt_count,
            )
            db.add(row)
        else:
            row.mode = session.mode.value
            row.state = session.state.value
            row.session_json = json.dumps(payload)
            row.tool_id = tool_id
            row.material_id = material_id
            row.machine_id = machine_id
            row.candidate_attempt_count = session.candidate_attempt_count

        return session

    def get(self, db: Session, session_id: str) -> Optional[WorkflowSession]:
        """Get a session by ID. Returns None if not found."""
        row = db.get(WorkflowSessionRow, session_id)
        if row is None:
            return None
        data = json.loads(row.session_json)
        return WorkflowSession.model_validate(data)

    def require(self, db: Session, session_id: str) -> WorkflowSession:
        """Get a session by ID. Raises KeyError if not found."""
        s = self.get(db, session_id)
        if s is None:
            raise KeyError(f"Workflow session not found: {session_id}")
        return s

    def delete(self, db: Session, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        row = db.get(WorkflowSessionRow, session_id)
        if row is not None:
            db.delete(row)
            return True
        return False


# Global singleton for simple usage
STORE = DbWorkflowSessionStore()
