from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ExecutionOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    SCRAP = "SCRAP"


class ExecutionCompleteChecklist(BaseModel):
    all_cuts_complete: bool = Field(True, description="All planned cuts finished")
    material_removed: bool = Field(True, description="Workpiece removed from fixture")
    workpiece_inspected: bool = Field(True, description="Visual QC performed")
    area_cleared: bool = Field(True, description="Work area cleared for next batch")


class ExecutionCompleteRequest(BaseModel):
    batch_execution_artifact_id: str = Field(..., description="Execution artifact id to complete")
    session_id: str
    batch_label: str
    outcome: ExecutionOutcome
    notes: Optional[str] = None
    operator_id: Optional[str] = None
    tool_kind: str = "saw"
    checklist: Optional[ExecutionCompleteChecklist] = None
    statistics: Optional[Dict[str, Any]] = None


class ExecutionCompleteResponse(BaseModel):
    batch_execution_artifact_id: str
    complete_artifact_id: str
    state: str = "COMPLETED"


@router.post("/execution/complete", response_model=ExecutionCompleteResponse)
def complete_execution(req: ExecutionCompleteRequest) -> ExecutionCompleteResponse:
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    from app.rmos.runs_v2 import store as runs_store

    # Ensure execution exists (avoid completing phantom IDs)
    ex = runs_store.get_run(req.batch_execution_artifact_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="execution artifact not found")

    # Guardrails:
    # - do not allow completion if already aborted
    # - do not allow double completion
    # - require at least one job log to exist for this execution
    def _items(res: Any) -> list:
        if isinstance(res, dict):
            v = res.get("items")
            return v if isinstance(v, list) else []
        return res if isinstance(res, list) else []

    def _parent_id(art: Any) -> Optional[str]:
        if isinstance(art, dict):
            return str(art.get("parent_id") or art.get("parent_artifact_id") or "") or None
        meta = getattr(art, "meta", None)
        if isinstance(meta, dict):
            pid = meta.get("parent_id")
            return str(pid) if pid else None
        return None

    def _payload(art: Any) -> Dict[str, Any]:
        if isinstance(art, dict):
            p = art.get("payload") or art.get("data") or {}
            return p if isinstance(p, dict) else {}
        return {}

    # Prefer filtered lists; tolerate older store signatures
    try:
        aborts = _items(
            runs_store.list_runs_filtered(
                session_id=req.session_id,
                batch_label=req.batch_label,
                kind="saw_batch_execution_abort",
                limit=5000,
            )
        )
        completes = _items(
            runs_store.list_runs_filtered(
                session_id=req.session_id,
                batch_label=req.batch_label,
                kind="saw_batch_execution_complete",
                limit=5000,
            )
        )
        job_logs = _items(
            runs_store.list_runs_filtered(
                session_id=req.session_id,
                batch_label=req.batch_label,
                kind="saw_batch_job_log",
                limit=5000,
            )
        )
    except TypeError:
        aborts = _items(runs_store.list_runs_filtered(session_id=req.session_id, batch_label=req.batch_label))
        completes = _items(runs_store.list_runs_filtered(session_id=req.session_id, batch_label=req.batch_label))
        job_logs = _items(runs_store.list_runs_filtered(session_id=req.session_id, batch_label=req.batch_label))

    for a in aborts:
        if _parent_id(a) == str(req.batch_execution_artifact_id):
            raise HTTPException(status_code=409, detail="execution already aborted")

    for c in completes:
        if _parent_id(c) == str(req.batch_execution_artifact_id):
            raise HTTPException(status_code=409, detail="execution already completed")

    # Prerequisite: at least one QUALIFYING job log must exist for this execution.
    # Qualifying means:
    #   - parented to this execution
    #   - payload.status != "ABORTED"
    #   - payload.metrics indicates work (yield or time > 0)
    def _metrics_indicate_work(m: Any) -> bool:
        if not isinstance(m, dict):
            return False
        try:
            parts_ok = int(m.get("parts_ok") or 0)
            parts_scrap = int(m.get("parts_scrap") or 0)
        except Exception:
            parts_ok, parts_scrap = 0, 0

        def _f(key: str) -> float:
            try:
                return float(m.get(key) or 0.0)
            except Exception:
                return 0.0

        cut_time_s = _f("cut_time_s")
        total_time_s = _f("total_time_s")

        return (parts_ok + parts_scrap) > 0 or cut_time_s > 0.0 or total_time_s > 0.0

    qualifying = False
    for jl in job_logs:
        if _parent_id(jl) != str(req.batch_execution_artifact_id):
            continue
        p = _payload(jl)
        status = p.get("status")
        if isinstance(status, str) and status.upper() == "ABORTED":
            continue
        metrics = p.get("metrics")
        if _metrics_indicate_work(metrics):
            qualifying = True
            break

    if not qualifying:
        raise HTTPException(
            status_code=409,
            detail="execution lacks qualifying job log (non-ABORTED with work metrics); cannot complete",
        )

    # Convert checklist pydantic model to dict if provided
    checklist_dict = req.checklist.model_dump() if req.checklist else None

    from .execution_complete_service import write_execution_complete_artifact

    complete_id = write_execution_complete_artifact(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        outcome=str(req.outcome.value),
        notes=req.notes,
        operator_id=req.operator_id,
        tool_kind=req.tool_kind,
        checklist=checklist_dict,
        statistics=req.statistics,
    )

    return ExecutionCompleteResponse(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        complete_artifact_id=complete_id,
        state="COMPLETED",
    )
