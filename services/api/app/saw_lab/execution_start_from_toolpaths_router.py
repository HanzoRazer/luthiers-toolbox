from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ExecutionStartFromToolpathsRequest(BaseModel):
    session_id: str
    batch_label: str
    tool_kind: str = "saw"

    toolpaths_artifact_id: str
    decision_artifact_id: Optional[str] = None
    machine_profile_artifact_id: Optional[str] = None

    # validation controls
    validate_first: bool = True
    safe_z_mm: float = 5.0
    bounds_mm: Optional[Dict[str, float]] = None


class ExecutionStartFromToolpathsResponse(BaseModel):
    batch_execution_artifact_id: str
    status: str  # OK | BLOCKED
    lint_artifact_id: Optional[str] = None
    toolpaths_artifact_id: str
    decision_artifact_id: Optional[str] = None


@router.post("/execution/start-from-toolpaths", response_model=ExecutionStartFromToolpathsResponse)
def start_execution_from_toolpaths(req: ExecutionStartFromToolpathsRequest) -> ExecutionStartFromToolpathsResponse:
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")
    if not req.toolpaths_artifact_id:
        raise HTTPException(status_code=400, detail="toolpaths_artifact_id required")

    lint_id: Optional[str] = None
    ok = True

    if req.validate_first:
        # write governed lint artifact and use it as the gate
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

    # Always write an execution artifact (OK or BLOCKED)
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

    # Link parent: prefer decision, else toolpaths
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
