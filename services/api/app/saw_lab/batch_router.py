"""
Saw Lab Batch Workflow Router

Full batch workflow: spec → plan → approve → toolpaths → job-log
Plus decision trends endpoint for metrics rollup analysis.

Mounted at: /api/saw/batch
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.saw_lab.store import store_artifact, get_artifact, query_executions_by_decision, query_latest_by_label_and_session
from app.services.saw_lab_metrics_trends_service import compute_decision_trends

router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class BatchSpecItem(BaseModel):
    part_id: str
    qty: int = 1
    material_id: str = "maple"
    thickness_mm: float = 6.0
    length_mm: float = 300.0
    width_mm: float = 30.0


class BatchSpecRequest(BaseModel):
    batch_label: str
    session_id: str
    tool_id: str = "saw:thin_140"
    items: List[BatchSpecItem]


class BatchSpecResponse(BaseModel):
    batch_spec_artifact_id: str


class BatchPlanRequest(BaseModel):
    batch_spec_artifact_id: str


class BatchPlanOp(BaseModel):
    op_id: str
    part_id: str
    cut_type: str = "crosscut"


class BatchPlanSetup(BaseModel):
    setup_key: str
    tool_id: str
    ops: List[BatchPlanOp]


class BatchPlanResponse(BaseModel):
    batch_plan_artifact_id: str
    setups: List[BatchPlanSetup]


class BatchApproveRequest(BaseModel):
    batch_plan_artifact_id: str
    approved_by: str
    reason: str
    setup_order: List[str]
    op_order: List[str]


class BatchApproveResponse(BaseModel):
    batch_decision_artifact_id: str


class BatchToolpathsRequest(BaseModel):
    batch_decision_artifact_id: str


class BatchOpResult(BaseModel):
    op_id: str
    setup_key: str = ""
    status: str = "OK"
    risk_bucket: str = "GREEN"
    score: float = 1.0
    toolpaths_artifact_id: str
    warnings: List[str] = []


class BatchToolpathsResponse(BaseModel):
    batch_execution_artifact_id: str
    batch_decision_artifact_id: Optional[str] = None
    batch_plan_artifact_id: Optional[str] = None
    batch_spec_artifact_id: Optional[str] = None
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    status: str = "OK"
    op_count: int = 0
    ok_count: int = 0
    blocked_count: int = 0
    error_count: int = 0
    results: List[BatchOpResult] = []
    gcode_lines: int = 0


class JobLogMetrics(BaseModel):
    parts_ok: int = 0
    parts_scrap: int = 0
    cut_time_s: float = 0.0
    setup_time_s: float = 0.0


class JobLogRequest(BaseModel):
    metrics: JobLogMetrics


class JobLogResponse(BaseModel):
    job_log_artifact_id: str
    metrics_rollup_artifact_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/spec", response_model=BatchSpecResponse)
def create_batch_spec(req: BatchSpecRequest) -> BatchSpecResponse:
    """
    Create a batch specification artifact.
    
    This is the first step in the batch workflow.
    """
    payload = {
        "batch_label": req.batch_label,
        "session_id": req.session_id,
        "tool_id": req.tool_id,
        "items": [item.model_dump() for item in req.items],
    }
    artifact_id = store_artifact(kind="saw_batch_spec", payload=payload)
    return BatchSpecResponse(batch_spec_artifact_id=artifact_id)


@router.post("/plan", response_model=BatchPlanResponse)
def create_batch_plan(req: BatchPlanRequest) -> BatchPlanResponse:
    """
    Generate a batch plan from a spec.
    
    Creates setups and operations for the batch.
    """
    spec = get_artifact(req.batch_spec_artifact_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Batch spec not found")
    
    spec_payload = spec.get("payload", {})
    items = spec_payload.get("items", [])
    tool_id = spec_payload.get("tool_id", "saw:thin_140")
    batch_label = spec_payload.get("batch_label", "")
    session_id = spec_payload.get("session_id", "")
    
    ops = []
    for i, item in enumerate(items):
        ops.append(BatchPlanOp(
            op_id=f"op_{i+1}",
            part_id=item.get("part_id", f"part_{i+1}"),
            cut_type="crosscut",
        ))
    
    setups = [
        BatchPlanSetup(
            setup_key="setup_1",
            tool_id=tool_id,
            ops=ops,
        )
    ]
    
    payload = {
        "batch_spec_artifact_id": req.batch_spec_artifact_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "setups": [s.model_dump() for s in setups],
    }
    artifact_id = store_artifact(kind="saw_batch_plan", payload=payload, parent_id=req.batch_spec_artifact_id, session_id=session_id)
    
    return BatchPlanResponse(
        batch_plan_artifact_id=artifact_id,
        setups=setups,
    )


@router.post("/approve", response_model=BatchApproveResponse)
def approve_batch_plan(req: BatchApproveRequest) -> BatchApproveResponse:
    """
    Approve a batch plan, creating a decision artifact.
    
    This locks in the execution order.
    """
    plan = get_artifact(req.batch_plan_artifact_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Batch plan not found")
    
    plan_payload = plan.get("payload", {})
    batch_label = plan_payload.get("batch_label", "")
    session_id = plan_payload.get("session_id", "")
    spec_id = plan_payload.get("batch_spec_artifact_id", "")
    
    payload = {
        "batch_plan_artifact_id": req.batch_plan_artifact_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "approved_by": req.approved_by,
        "reason": req.reason,
        "setup_order": req.setup_order,
        "op_order": req.op_order,
    }
    artifact_id = store_artifact(kind="saw_batch_decision", payload=payload, parent_id=req.batch_plan_artifact_id, session_id=session_id)
    
    return BatchApproveResponse(batch_decision_artifact_id=artifact_id)


@router.post("/toolpaths", response_model=BatchToolpathsResponse)
def generate_batch_toolpaths(req: BatchToolpathsRequest) -> BatchToolpathsResponse:
    """
    Generate toolpaths (G-code) from an approved decision.
    
    Creates child op_toolpaths artifacts and parent execution artifact.
    """
    decision = get_artifact(req.batch_decision_artifact_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Batch decision not found")
    
    dec_payload = decision.get("payload", {})
    plan_id = dec_payload.get("batch_plan_artifact_id", "")
    spec_id = dec_payload.get("batch_spec_artifact_id", "")
    batch_label = dec_payload.get("batch_label", "")
    session_id = dec_payload.get("session_id", "")
    op_order = dec_payload.get("op_order", [])
    
    # Get plan to access ops
    plan = get_artifact(plan_id) if plan_id else None
    plan_payload = plan.get("payload", {}) if plan else {}
    setups = plan_payload.get("setups", [])
    
    # Build op lookup
    op_by_id: Dict[str, Dict[str, Any]] = {}
    for setup in setups:
        if isinstance(setup, dict):
            setup_key = setup.get("setup_key", "")
            for op in setup.get("ops", []):
                if isinstance(op, dict) and op.get("op_id"):
                    op["setup_key"] = setup_key
                    op_by_id[op["op_id"]] = op
    
    # Generate toolpaths for each op
    child_ids: List[str] = []
    child_results: List[Dict[str, Any]] = []
    ok_count = 0
    total_gcode_lines = 0
    
    for op_id in op_order:
        op = op_by_id.get(op_id, {})
        setup_key = op.get("setup_key", "")
        
        # Generate mock G-code moves
        gcode_moves = [
            {"code": "G21", "comment": "Units: mm"},
            {"code": "G90", "comment": "Absolute positioning"},
            {"code": "G0", "z": 10.0, "comment": "Rapid to safe height"},
            {"code": "G0", "x": 0.0, "y": 0.0, "comment": "Move to start"},
            {"code": "M3", "comment": "Spindle on"},
            {"code": "G1", "z": -6.0, "f": 100.0, "comment": "Plunge"},
            {"code": "G1", "x": 300.0, "f": 800.0, "comment": "Cut"},
            {"code": "G0", "z": 10.0, "comment": "Retract"},
            {"code": "M5", "comment": "Spindle off"},
        ]
        
        op_payload = {
            "batch_decision_artifact_id": req.batch_decision_artifact_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "op_id": op_id,
            "setup_key": setup_key,
            "toolpaths": {"moves": gcode_moves},
        }
        
        child_id = store_artifact(
            kind="saw_batch_op_toolpaths",
            payload=op_payload,
            parent_id=req.batch_decision_artifact_id,
            session_id=session_id,
            status="OK",
        )
        child_ids.append(child_id)
        ok_count += 1
        total_gcode_lines += len(gcode_moves)
        
        child_results.append({
            "op_id": op_id,
            "setup_key": setup_key,
            "status": "OK",
            "risk_bucket": "GREEN",
            "score": 1.0,
            "toolpaths_artifact_id": child_id,
            "warnings": [],
        })
    
    # Create parent execution artifact
    exec_payload = {
        "batch_decision_artifact_id": req.batch_decision_artifact_id,
        "batch_plan_artifact_id": plan_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "summary": {
            "op_count": len(op_order),
            "ok_count": ok_count,
            "blocked_count": 0,
            "error_count": 0,
        },
        "children": [{"artifact_id": cid, "kind": "saw_batch_op_toolpaths"} for cid in child_ids],
        "results": child_results,
        "gcode_lines": total_gcode_lines,
    }
    
    exec_id = store_artifact(
        kind="saw_batch_execution",
        payload=exec_payload,
        parent_id=req.batch_decision_artifact_id,
        session_id=session_id,
        status="OK",
    )
    
    return BatchToolpathsResponse(
        batch_execution_artifact_id=exec_id,
        batch_decision_artifact_id=req.batch_decision_artifact_id,
        batch_plan_artifact_id=plan_id,
        batch_spec_artifact_id=spec_id,
        batch_label=batch_label,
        session_id=session_id,
        status="OK",
        op_count=len(op_order),
        ok_count=ok_count,
        blocked_count=0,
        error_count=0,
        results=[BatchOpResult(**r) for r in child_results],
        gcode_lines=total_gcode_lines,
    )


@router.get("/execution")
def get_execution_by_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID to look up execution for"),
) -> Dict[str, Any]:
    """
    Look up the latest execution artifact for a given decision.

    Returns the execution artifact with id, kind, status, and index_meta.
    Returns 404 if no execution exists for the decision.
    """
    executions = query_executions_by_decision(batch_decision_artifact_id)
    if not executions:
        raise HTTPException(
            status_code=404,
            detail=f"No execution artifact found for decision {batch_decision_artifact_id}",
        )

    # Return the latest execution (first in sorted list)
    latest = executions[0]
    payload = latest.get("payload", {})

    # Build index_meta with setdefault fallbacks for older artifacts
    index_meta = latest.get("index_meta") or {}
    index_meta.setdefault("parent_batch_decision_artifact_id", payload.get("batch_decision_artifact_id") or batch_decision_artifact_id)
    index_meta.setdefault("batch_label", payload.get("batch_label"))
    index_meta.setdefault("session_id", payload.get("session_id"))
    index_meta.setdefault("tool_kind", "saw_lab")
    index_meta.setdefault("kind_group", "batch")

    return {
        "artifact_id": latest.get("artifact_id"),
        "id": latest.get("artifact_id"),  # Alias for compatibility
        "kind": latest.get("kind", "saw_batch_execution"),
        "status": latest.get("status", "OK"),
        "created_utc": latest.get("created_utc"),
        "index_meta": index_meta,
    }


@router.get("/executions/by-decision")
def list_executions_by_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List all execution artifacts for a given decision, newest first.

    Returns list of execution artifacts with id, kind, status, index_meta.
    """
    executions = query_executions_by_decision(batch_decision_artifact_id)[:limit]

    results = []
    for ex in executions:
        payload = ex.get("payload", {})
        index_meta = ex.get("index_meta") or {}
        index_meta.setdefault("parent_batch_decision_artifact_id", payload.get("batch_decision_artifact_id") or batch_decision_artifact_id)
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append({
            "artifact_id": ex.get("artifact_id"),
            "id": ex.get("artifact_id"),
            "kind": ex.get("kind", "saw_batch_execution"),
            "status": ex.get("status", "OK"),
            "created_utc": ex.get("created_utc"),
            "index_meta": index_meta,
        })

    return results


@router.get("/links")
def get_batch_links(
    batch_label: str = Query(..., description="Batch label to look up"),
    session_id: str = Query(..., description="Session ID to look up"),
) -> Dict[str, Optional[str]]:
    """
    Get latest artifact IDs for a batch label + session.

    Returns latest_spec_artifact_id, latest_plan_artifact_id,
    latest_decision_artifact_id, latest_execution_artifact_id.
    """
    return query_latest_by_label_and_session(batch_label, session_id)


@router.post("/job-log", response_model=JobLogResponse)
def log_batch_job(
    req: JobLogRequest,
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
    operator: str = Query("unknown", description="Operator name"),
    notes: str = Query("", description="Job notes"),
    status: str = Query("COMPLETED", description="Job status"),
) -> JobLogResponse:
    """
    Log job completion for an execution, optionally creating a metrics rollup.
    
    If SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED=true, also persists a rollup artifact.
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Batch execution not found")
    
    # Get the decision artifact ID for rollup parent reference
    decision_id = execution["payload"].get("batch_decision_artifact_id")
    
    job_log_payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "operator": operator,
        "notes": notes,
        "status": status,
        "metrics": req.metrics.model_dump(),
    }
    job_log_id = store_artifact(kind="batch_job_log", payload=job_log_payload, parent_id=batch_execution_artifact_id)
    
    # Optionally create metrics rollup
    rollup_id: Optional[str] = None
    if os.getenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "").lower() == "true":
        rollup_payload = {
            "batch_execution_artifact_id": batch_execution_artifact_id,
            "parent_batch_decision_artifact_id": decision_id,
            "metrics": req.metrics.model_dump(),
            "counts": {"job_log_count": 1},
            "signals": {"burn_events": 0, "tearout_events": 0, "kickback_events": 0},
        }
        rollup_id = store_artifact(kind="saw_batch_execution_metrics_rollup", payload=rollup_payload, parent_id=decision_id)
        
        # Also store in the runs artifact index for query_run_artifacts to find
        _store_rollup_for_query(rollup_id, rollup_payload, decision_id)
    
    return JobLogResponse(
        job_log_artifact_id=job_log_id,
        metrics_rollup_artifact_id=rollup_id,
    )


def _store_rollup_for_query(rollup_id: str, payload: Dict[str, Any], decision_id: str) -> None:
    """
    Store rollup in a format that query_run_artifacts can find.
    
    This bridges the in-memory store to the runs_v2 query layer.
    """
    try:
        from app.rmos.run_artifacts.store import persist_run_artifact
        persist_run_artifact(
            kind="saw_batch_execution_metrics_rollup",
            payload=payload,
            index_meta={
                "parent_batch_decision_artifact_id": decision_id,
                "parent_batch_execution_artifact_id": payload.get("batch_execution_artifact_id"),
            },
        )
    except Exception:
        # Graceful fallback if runs artifact store not available
        pass


# ---------------------------------------------------------------------------
# Decision Trends Endpoint
# ---------------------------------------------------------------------------


@router.get("/decisions/trends")
def get_decision_trends(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
    window: int = Query(default=20, ge=2, le=200, description="Window size for trend calculation"),
) -> Dict[str, Any]:
    """
    Compute trend deltas for a batch decision's execution metrics over time.
    
    Returns:
    - Time-series points from metrics rollup artifacts
    - Aggregates for last window vs previous window
    - Delta comparisons (scrap rate changes, etc.)
    
    Even with 0-1 data points, returns a valid shape with deltas.available=False.
    """
    return compute_decision_trends(
        batch_decision_artifact_id=batch_decision_artifact_id,
        window=window,
    )

# ---------------------------------------------------------------------------
# G-code Export Endpoints
# ---------------------------------------------------------------------------


@router.get("/executions/{batch_execution_artifact_id}/gcode")
def get_execution_gcode(batch_execution_artifact_id: str) -> PlainTextResponse:
    """
    Export combined G-code for all OK ops in an execution.

    Returns plain text G-code with Content-Disposition for download.
    """
    from app.saw_lab.store import read_artifact as read_saw_artifact
    from app.services.saw_lab_gcode_emit_service import export_execution_gcode

    try:
        result = export_execution_gcode(
            batch_execution_artifact_id=batch_execution_artifact_id,
            read_artifact=read_saw_artifact,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Execution artifact not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = result.get("filename", f"{batch_execution_artifact_id[:8]}.ngc")

    return PlainTextResponse(
        content=result["gcode"],
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/op-toolpaths/{op_toolpaths_artifact_id}/gcode")
def get_op_toolpaths_gcode(op_toolpaths_artifact_id: str) -> PlainTextResponse:
    """
    Export G-code for a single op toolpath artifact.

    Returns plain text G-code with Content-Disposition for download.
    """
    from app.saw_lab.store import read_artifact as read_saw_artifact
    from app.services.saw_lab_gcode_emit_service import export_op_toolpaths_gcode

    try:
        result = export_op_toolpaths_gcode(
            op_toolpaths_artifact_id=op_toolpaths_artifact_id,
            read_artifact=read_saw_artifact,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Op toolpaths artifact not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = result.get("filename", f"{op_toolpaths_artifact_id[:8]}.ngc")

    return PlainTextResponse(
        content=result["gcode"],
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
