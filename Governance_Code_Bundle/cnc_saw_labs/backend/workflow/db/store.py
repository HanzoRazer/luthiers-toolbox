from __future__ import annotations

import json
from sqlalchemy.orm import Session

from app.workflow.state_machine import WorkflowSession
from app.workflow.db.models import WorkflowSessionRow


class DbWorkflowSessionStore:
    """
    DB-backed session store.
    Stores WorkflowSession as JSON to keep it lightweight.
    """

    def put(self, db: Session, session: WorkflowSession) -> WorkflowSession:
        payload = session.model_dump()
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

    def get(self, db: Session, session_id: str) -> WorkflowSession | None:
        row = db.get(WorkflowSessionRow, session_id)
        if row is None:
            return None
        data = json.loads(row.session_json)
        return WorkflowSession.model_validate(data)

    def require(self, db: Session, session_id: str) -> WorkflowSession:
        s = self.get(db, session_id)
        if s is None:
            raise KeyError(f"Workflow session not found: {session_id}")
        return s


STORE = DbWorkflowSessionStore()

4) DB init helper
Add this in your app/main.py (or wherever app is created).
services/api/app/main.py patch
from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.routers.rmos_workflow_router import router as rmos_workflow_router
from app.routers.run_artifacts_router import router as run_artifacts_router
from app.routers.workflow_router import router as workflow_router

app = FastAPI()

# Create tables on startup (lightweight; ok for SQLite dev/prod small scale)
@app.on_event("startup")