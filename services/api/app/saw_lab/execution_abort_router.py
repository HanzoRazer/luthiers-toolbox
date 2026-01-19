from __future__ import annotations

from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class AbortReason(str, Enum):
    JAM = "JAM"
    BURN = "BURN"
    TEAROUT = "TEAROUT"
    MISALIGNMENT = "MISALIGNMENT"
    KICKBACK = "KICKBACK"
    TOOL_BREAK = "TOOL_BREAK"
    OPERATOR_ABORT = "OPERATOR_ABORT"
    OTHER = "OTHER"


class ExecutionAbortRequest(BaseModel):
    batch_execution_artifact_id: str = Field(..., description="Execution artifact id to abort")
    session_id: str
    batch_label: str
    reason: AbortReason
    notes: Optional[str] = None
    operator_id: Optional[str] = None
    tool_kind: str = "saw"


class ExecutionAbortResponse(BaseModel):
    batch_execution_artifact_id: str
    abort_artifact_id: str
    state: str = "ABORTED"


@router.post("/execution/abort", response_model=ExecutionAbortResponse)
def abort_execution(req: ExecutionAbortRequest) -> ExecutionAbortResponse:
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    # Ensure execution exists (avoid aborting phantom IDs)
    from app.rmos.runs_v2 import store as runs_store

    ex = runs_store.get_run(req.batch_execution_artifact_id)
    if not isinstance(ex, dict):
        raise HTTPException(status_code=404, detail="execution artifact not found")

    from .execution_abort_service import write_execution_abort_artifact

    abort_id = write_execution_abort_artifact(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        reason=str(req.reason.value),
        notes=req.notes,
        operator_id=req.operator_id,
        tool_kind=req.tool_kind,
    )

    return ExecutionAbortResponse(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        abort_artifact_id=abort_id,
        state="ABORTED",
    )
