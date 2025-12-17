from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.session import db_session
from app.workflow.db.store import STORE
from app.workflow.state_machine import ActorRole, approve, WorkflowSession


router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class ApproveRequest(BaseModel):
    session_id: str
    actor: ActorRole = ActorRole.OPERATOR
    note: str | None = None


class ApproveResponse(BaseModel):
    session_id: str
    state: str
    approved: bool
    message: str


@router.post("/approve", response_model=ApproveResponse)
def approve_session(req: ApproveRequest) -> ApproveResponse:
    with db_session() as db:
        try:
            session: WorkflowSession = STORE.require(db, req.session_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

        try:
            approve(session, actor=req.actor, note=req.note)
            STORE.put(db, session)
            return ApproveResponse(
                session_id=session.session_id,
                state=session.state.value,
                approved=True,
                message="Session approved.",
            )
        except Exception as e:
            raise HTTPException(status_code=409, detail={"session_id": req.session_id, "error": str(e)})

6) Update /api/rmos/feasibility and /api/rmos/toolpaths router to use DB store
You already have rmos_workflow_router.py. Here are the key changes (copy/paste edits).
A) Imports
Add:
from app.db.session import db_session
from app.workflow.db.store import STORE
B) In feasibility() endpoint: persist the created session to DB
Right after session creation:
session = new_session(req.mode, index_meta=_index_meta(req.context))
with db_session() as db:
    STORE.put(db, session)
When you finish computing/storing feasibility, persist session again:
with db_session() as db:
    STORE.put(db, session)
C) In toolpaths() endpoint: require session_id and load from DB
At top of toolpaths endpoint:
if not req.session_id:
    raise HTTPException(status_code=400, detail="session_id is required for toolpaths when using approve flow.")

with db_session() as db:
    try:
        session = STORE.require(db, req.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))