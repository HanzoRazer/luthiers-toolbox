"""
Consolidated execution lifecycle router.

Combines:
- execution_abort_router (POST /execution/abort)
- execution_complete_router (POST /execution/complete)
- execution_confirmation_router (POST /execution/confirm, GET /execution/confirmations/latest)
- execution_metrics_router (POST /execution/metrics/rollup)
- execution_start_from_toolpaths_router (POST /execution/start-from-toolpaths)
- execution_status_router (GET /execution/{id}/status)

7 routes total covering the full execution lifecycle:
  start → confirm → status → complete/abort → metrics
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])

# Schemas: Abort
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


# Schemas: Complete
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


# Schemas: Confirmation
class ExecutionConfirmRequest(BaseModel):
    batch_execution_artifact_id: str = Field(..., description="Execution artifact id to confirm")
    session_id: str
    batch_label: str
    operator_id: str
    checks: Dict[str, bool] = Field(
        ...,
        description="Checklist confirmations; all must be True to confirm",
        examples=[{
            "material_loaded": True,
            "clamps_engaged": True,
            "blade_verified": True,
            "zero_set": True,
            "dust_collection_on": True,
        }],
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


# Schemas: Metrics Rollup
class ExecutionMetricsRollupRequest(BaseModel):
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None


class ExecutionMetricsRollupResponse(BaseModel):
    batch_execution_artifact_id: str
    metrics_artifact_id: str


# Schemas: Start from Toolpaths
class ExecutionStartFromToolpathsRequest(BaseModel):
    session_id: str
    batch_label: str
    tool_kind: str = "saw"
    toolpaths_artifact_id: str
    decision_artifact_id: Optional[str] = None
    machine_profile_artifact_id: Optional[str] = None
    validate_first: bool = True
    safe_z_mm: float = 5.0
    bounds_mm: Optional[Dict[str, float]] = None


class ExecutionStartFromToolpathsResponse(BaseModel):
    batch_execution_artifact_id: str
    status: str  # OK | BLOCKED
    lint_artifact_id: Optional[str] = None
    toolpaths_artifact_id: str
    decision_artifact_id: Optional[str] = None


# Schemas: Status
class ExecutionStatusResponse(BaseModel):
    ok: bool
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: str = "saw"
    status: str
    created_utc: Optional[str] = None
    updated_utc: Optional[str] = None
    links: Dict[str, Optional[str]] = Field(default_factory=dict, description="Related artifact IDs")
    kpis: Optional[Dict[str, Any]] = None


# Route: Abort
@router.post("/execution/abort", response_model=ExecutionAbortResponse)
def abort_execution(req: ExecutionAbortRequest) -> ExecutionAbortResponse:
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

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


# Route: Complete
@router.post("/execution/complete", response_model=ExecutionCompleteResponse)
def complete_execution(req: ExecutionCompleteRequest) -> ExecutionCompleteResponse:
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    from app.rmos.runs_v2 import store as runs_store
    from .execution_complete_service import (
        extract_parent_id,
        extract_payload,
        select_latest_artifact,
        metrics_indicate_work,
        write_execution_complete_artifact,
    )

    ex = runs_store.get_run(req.batch_execution_artifact_id)
    if not isinstance(ex, dict):
        raise HTTPException(status_code=404, detail="execution artifact not found")

    # Check for prior abort/complete
    aborts = runs_store.list_runs_filtered(
        session_id=req.session_id, batch_label=req.batch_label,
        kind="saw_batch_execution_abort", limit=5000,
    )
    completes = runs_store.list_runs_filtered(
        session_id=req.session_id, batch_label=req.batch_label,
        kind="saw_batch_execution_complete", limit=5000,
    )
    job_logs = runs_store.list_runs_filtered(
        session_id=req.session_id, batch_label=req.batch_label,
        kind="saw_batch_job_log", limit=5000,
    )

    for a in aborts:
        if extract_parent_id(a) == str(req.batch_execution_artifact_id):
            raise HTTPException(status_code=409, detail="execution already aborted")

    for c in completes:
        if extract_parent_id(c) == str(req.batch_execution_artifact_id):
            raise HTTPException(status_code=409, detail="execution already completed")

    exec_logs = [jl for jl in job_logs if extract_parent_id(jl) == str(req.batch_execution_artifact_id)]
    if not exec_logs:
        raise HTTPException(status_code=409, detail="execution has no job logs; cannot complete")

    latest_log = select_latest_artifact(exec_logs)
    p = extract_payload(latest_log)
    status = p.get("status")
    if isinstance(status, str) and status.upper() == "ABORTED":
        raise HTTPException(status_code=409, detail="latest job log indicates ABORTED; cannot complete")
    metrics = p.get("metrics")
    if not metrics_indicate_work(metrics):
        raise HTTPException(status_code=409, detail="latest job log lacks work metrics; cannot complete")

    checklist_dict = req.checklist.model_dump() if req.checklist else None
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


# Routes: Confirmation
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

    bad = [k for k, v in req.checks.items() if v is not True]
    if bad:
        raise HTTPException(status_code=409, detail=f"confirmation blocked; checks not satisfied: {bad}")

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


# Route: Metrics Rollup
@router.post("/execution/metrics/rollup", response_model=ExecutionMetricsRollupResponse)
def rollup_execution_metrics(req: ExecutionMetricsRollupRequest) -> ExecutionMetricsRollupResponse:
    """Writes a saw_batch_execution_metrics artifact from job logs."""
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")

    from .execution_metrics_rollup_service import write_execution_metrics_rollup_artifact
    mid = write_execution_metrics_rollup_artifact(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        tool_kind="saw",
    )
    return ExecutionMetricsRollupResponse(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        metrics_artifact_id=str(mid),
    )


# Route: Start from Toolpaths
@router.post("/execution/start-from-toolpaths", response_model=ExecutionStartFromToolpathsResponse)
def start_execution_from_toolpaths(req: ExecutionStartFromToolpathsRequest) -> ExecutionStartFromToolpathsResponse:
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")
    if not req.toolpaths_artifact_id:
        raise HTTPException(status_code=400, detail="toolpaths_artifact_id required")

    lint_id: Optional[str] = None
    ok = True

    if req.validate_first:
        from .toolpaths_lint_service import write_toolpaths_lint_report_artifact
        from .machine_profile_resolver import resolve_machine_profile_constraints

        safe_z_mm = req.safe_z_mm
        bounds_mm = req.bounds_mm
        if req.machine_profile_artifact_id:
            c = resolve_machine_profile_constraints(machine_profile_artifact_id=req.machine_profile_artifact_id)
            if isinstance(c.get("safe_z_mm"), (int, float)):
                safe_z_mm = float(c["safe_z_mm"])
            if isinstance(c.get("bounds_mm"), dict):
                bounds_mm = c["bounds_mm"]

        out = write_toolpaths_lint_report_artifact(
            toolpaths_artifact_id=req.toolpaths_artifact_id,
            session_id=req.session_id,
            batch_label=req.batch_label,
            tool_kind=req.tool_kind,
            machine_profile_artifact_id=req.machine_profile_artifact_id,
            safe_z_mm=safe_z_mm,
            bounds_mm=bounds_mm,
        )
        lint_id = out.get("lint_artifact_id")
        result = out.get("result") or {}
        ok = bool(result.get("ok"))

    payload: Dict[str, Any] = {
        "session_id": req.session_id,
        "batch_label": req.batch_label,
        "tool_kind": req.tool_kind,
        "toolpaths_artifact_id": req.toolpaths_artifact_id,
        "decision_artifact_id": req.decision_artifact_id,
        "machine_profile_artifact_id": req.machine_profile_artifact_id,
        "lint_artifact_id": lint_id,
        "status": "OK" if ok else "BLOCKED",
    }
    parent_id = req.decision_artifact_id or req.toolpaths_artifact_id

    from app.rmos.runs_v2.store import store_artifact
    exec_id = store_artifact(
        kind="saw_batch_execution",
        payload=payload,
        parent_id=parent_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        tool_kind=req.tool_kind,
    )
    return ExecutionStartFromToolpathsResponse(
        batch_execution_artifact_id=exec_id,
        status="OK" if ok else "BLOCKED",
        lint_artifact_id=lint_id,
        toolpaths_artifact_id=req.toolpaths_artifact_id,
        decision_artifact_id=req.decision_artifact_id,
    )


# Route: Status
@router.get("/execution/{batch_execution_artifact_id}/status", response_model=ExecutionStatusResponse)
def get_execution_status(
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> ExecutionStatusResponse:
    """
    Operator-facing execution status endpoint.

    Returns a single authoritative status derived from artifacts:
      PENDING | CONFIRMED | RUNNING | COMPLETE | ABORTED | BLOCKED
    """
    if not batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")

    from .execution_status_service import compute_execution_status
    result = compute_execution_status(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    if not isinstance(result, dict) or not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "execution not found"))

    return ExecutionStatusResponse(**result)
