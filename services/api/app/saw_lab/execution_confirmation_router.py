from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ExecutionConfirmRequest(BaseModel):
    batch_execution_artifact_id: str = Field(..., description="Execution artifact id to confirm")
    session_id: str
    batch_label: str
    operator_id: str

    # Minimal hard-stop checks (extend freely)
    checks: Dict[str, bool] = Field(
        ...,
        description="Checklist confirmations; all must be True to confirm",
        examples=[
            {
                "material_loaded": True,
                "clamps_engaged": True,
                "blade_verified": True,
                "zero_set": True,
                "dust_collection_on": True,
            }
        ],
    )
    notes: Optional[str] = None
    tool_kind: str = "saw"


class ExecutionConfirmResponse(BaseModel):
    confirmation_artifact_id: str
    batch_execution_artifact_id: str
    state: str = "CONFIRMED"


class LatestExecutionConfirmResponse(BaseModel):
    batch_execution_artifact_id: str
    confirmation_artifact_id: Optional[str] = None
    state: Optional[str] = None


@router.post("/execution/confirm", response_model=ExecutionConfirmResponse)
def confirm_execution(req: ExecutionConfirmRequest) -> ExecutionConfirmResponse:
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")
    if not req.operator_id:
        raise HTTPException(status_code=400, detail="operator_id required")
    if not isinstance(req.checks, dict) or not req.checks:
        raise HTTPException(status_code=400, detail="checks must be a non-empty dict[str,bool]")

    # Hard stop: all checks must be True
    bad = [k for k, v in req.checks.items() if v is not True]
    if bad:
        raise HTTPException(status_code=409, detail=f"confirmation blocked; checks not satisfied: {bad}")

    # Ensure execution exists (so we don't confirm a phantom id)
    from app.rmos.runs_v2 import store as runs_store

    ex = runs_store.get_run(req.batch_execution_artifact_id)
    if not isinstance(ex, dict):
        raise HTTPException(status_code=404, detail="execution artifact not found")

    from .execution_confirmation_service import write_execution_confirmation_artifact

    confirmation_id = write_execution_confirmation_artifact(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        operator_id=req.operator_id,
        checks=req.checks,
        notes=req.notes,
        tool_kind=req.tool_kind,
    )

    return ExecutionConfirmResponse(
        confirmation_artifact_id=confirmation_id,
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        state="CONFIRMED",
    )


@router.get("/execution/confirmations/latest", response_model=LatestExecutionConfirmResponse)
def latest_confirmation_for_execution(
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> LatestExecutionConfirmResponse:
    if not batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")

    from .execution_confirmation_service import get_latest_execution_confirmation

    c = get_latest_execution_confirmation(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    if not isinstance(c, dict):
        return LatestExecutionConfirmResponse(batch_execution_artifact_id=batch_execution_artifact_id)

    cid = c.get("id") or c.get("artifact_id")
    payload = c.get("payload") or c.get("data") or {}
    state = payload.get("state") if isinstance(payload, dict) else None

    return LatestExecutionConfirmResponse(
        batch_execution_artifact_id=batch_execution_artifact_id,
        confirmation_artifact_id=str(cid) if cid else None,
        state=str(state) if state else None,
    )
