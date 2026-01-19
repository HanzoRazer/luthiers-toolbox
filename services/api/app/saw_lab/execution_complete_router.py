from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ExecutionCompleteChecklist(BaseModel):
    all_cuts_complete: bool = Field(True, description="All planned cuts finished")
    material_removed: bool = Field(True, description="Workpiece removed from fixture")
    workpiece_inspected: bool = Field(True, description="Visual QC performed")
    area_cleared: bool = Field(True, description="Work area cleared for next batch")


class ExecutionCompleteRequest(BaseModel):
    batch_execution_artifact_id: str = Field(..., description="Execution artifact id to complete")
    session_id: str
    batch_label: str
    notes: Optional[str] = None
    operator_id: Optional[str] = None
    tool_kind: str = "saw"
    checklist: Optional[ExecutionCompleteChecklist] = None
    statistics: Optional[Dict[str, Any]] = None


class ExecutionCompleteResponse(BaseModel):
    batch_execution_artifact_id: str
    complete_artifact_id: str
    state: str = "COMPLETE"


@router.post("/execution/complete", response_model=ExecutionCompleteResponse)
def complete_execution(req: ExecutionCompleteRequest) -> ExecutionCompleteResponse:
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    # Ensure execution exists
    from app.rmos.runs_v2 import store as runs_store

    ex = runs_store.get_run(req.batch_execution_artifact_id)
    if not isinstance(ex, dict):
        raise HTTPException(status_code=404, detail="execution artifact not found")

    # Convert checklist pydantic model to dict if provided
    checklist_dict = None
    if req.checklist:
        checklist_dict = req.checklist.model_dump()

    from .execution_complete_service import write_execution_complete_artifact

    complete_id = write_execution_complete_artifact(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        notes=req.notes,
        operator_id=req.operator_id,
        tool_kind=req.tool_kind,
        checklist=checklist_dict,
        statistics=req.statistics,
    )

    return ExecutionCompleteResponse(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        complete_artifact_id=complete_id,
        state="COMPLETE",
    )
