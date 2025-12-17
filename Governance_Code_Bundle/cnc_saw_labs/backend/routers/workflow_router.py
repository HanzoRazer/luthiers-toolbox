from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.workflow.session_store import STORE
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
    try:
        session: WorkflowSession = STORE.require(req.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        approve(session, actor=req.actor, note=req.note)
        STORE.put(session)
        return ApproveResponse(
            session_id=session.session_id,
            state=session.state.value,
            approved=True,
            message="Session approved.",
        )
    except Exception as e:
        # approval may be blocked by governance rules
        raise HTTPException(status_code=409, detail={"session_id": req.session_id, "error": str(e)})
Wire into app
In app.main:
from app.routers.workflow_router import router as workflow_router
app.include_router(workflow_router)

3) Update RMOS feasibility/toolpaths wrappers to support session reuse