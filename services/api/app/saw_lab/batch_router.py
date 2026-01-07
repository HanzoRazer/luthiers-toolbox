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

from app.saw_lab.store import (
    store_artifact,
    get_artifact,
    query_executions_by_decision,
    query_latest_by_label_and_session,
    query_job_logs_by_execution,
    query_executions_by_label,
    query_decisions_by_plan,
    query_decisions_by_spec,
    query_executions_by_plan,
    query_executions_by_spec,
    query_op_toolpaths_by_decision,
    query_op_toolpaths_by_execution,
    query_metrics_rollups_by_execution,
    query_accepted_learning_events,
    query_all_accepted_learning_events,
    query_learning_events_by_execution,
    query_execution_rollups_by_decision,
    query_executions_with_learning,
)
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
    learning: Optional[LearningInfo] = None


class JobLogMetrics(BaseModel):
    parts_ok: int = 0
    parts_scrap: int = 0
    cut_time_s: float = 0.0
    setup_time_s: float = 0.0
    burn: bool = False
    tearout: bool = False
    kickback: bool = False


class JobLogRequest(BaseModel):
    metrics: JobLogMetrics = Field(default_factory=JobLogMetrics)


class LearningEvent(BaseModel):
    artifact_id: str
    id: str
    kind: str = "saw_batch_learning_event"
    suggestion_type: str = "parameter_override"


class RollupArtifacts(BaseModel):
    execution_rollup_artifact: Optional[Dict[str, Any]] = None
    decision_rollup_artifact: Optional[Dict[str, Any]] = None


class JobLogResponse(BaseModel):
    job_log_artifact_id: str
    metrics_rollup_artifact_id: Optional[str] = None
    learning_event: Optional[LearningEvent] = None
    learning_hook_enabled: Optional[bool] = None
    rollups: Optional[RollupArtifacts] = None


class LearningTuningStamp(BaseModel):
    applied: bool = False
    event_ids: List[str] = []


class LearningResolved(BaseModel):
    source_count: int = 0


class LearningInfo(BaseModel):
    apply_enabled: bool = False
    resolved: LearningResolved = Field(default_factory=LearningResolved)
    tuning_stamp: Optional[LearningTuningStamp] = None


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
    Always returns 200 with status="ERROR" for invalid decisions (governance: always persist artifacts).
    """
    decision = get_artifact(req.batch_decision_artifact_id)
    if not decision:
        # Governance: always persist an artifact even on failure
        error_payload = {
            "batch_decision_artifact_id": req.batch_decision_artifact_id,
            "error": f"Batch decision not found: {req.batch_decision_artifact_id}",
            "summary": {"op_count": 0, "ok_count": 0, "blocked_count": 0, "error_count": 1},
            "children": [],
            "results": [],
        }
        error_exec_id = store_artifact(
            kind="saw_batch_execution",
            payload=error_payload,
            parent_id=req.batch_decision_artifact_id,
            status="ERROR",
        )
        return BatchToolpathsResponse(
            batch_execution_artifact_id=error_exec_id,
            batch_decision_artifact_id=req.batch_decision_artifact_id,
            status="ERROR",
            op_count=0,
            ok_count=0,
            blocked_count=0,
            error_count=1,
            results=[],
            gcode_lines=0,
        )
    
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
    
    # Build learning info first so we can store it with the execution
    apply_enabled = os.getenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "").lower() == "true"
    learning_enabled = os.getenv("SAW_LAB_LEARNING_HOOK_ENABLED", "").lower() == "true"

    # Query accepted learning events for this decision
    accepted_events = query_accepted_learning_events(req.batch_decision_artifact_id) if learning_enabled else []
    source_count = len(accepted_events)

    tuning_stamp = None
    tuning_stamp_dict = None
    if apply_enabled and source_count > 0:
        tuning_stamp = LearningTuningStamp(
            applied=True,
            event_ids=[e.get("artifact_id") for e in accepted_events],
        )
        tuning_stamp_dict = {
            "applied": True,
            "event_ids": [e.get("artifact_id") for e in accepted_events],
        }

    learning_info = LearningInfo(
        apply_enabled=apply_enabled,
        resolved=LearningResolved(source_count=source_count),
        tuning_stamp=tuning_stamp,
    )

    # Learning payload to store with execution
    learning_payload = {
        "apply_enabled": apply_enabled,
        "resolved": {"source_count": source_count},
        "tuning_stamp": tuning_stamp_dict,
    }

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
        "learning": learning_payload,
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
        learning=learning_info,
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


@router.get("/executions")
def list_executions_by_label(
    batch_label: str = Query(..., description="Batch label to filter by"),
    session_id: Optional[str] = Query(None, description="Optional session ID filter"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts by batch_label, newest first.

    Optionally filter by session_id.
    """
    executions = query_executions_by_label(batch_label, session_id)[:limit]

    results = []
    for ex in executions:
        payload = ex.get("payload", {})
        index_meta = ex.get("index_meta") or {}
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


@router.get("/decisions/by-plan")
def list_decisions_by_plan(
    batch_plan_artifact_id: str = Query(..., description="Plan artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List decision artifacts for a given plan, newest first.
    """
    decisions = query_decisions_by_plan(batch_plan_artifact_id)[:limit]

    results = []
    for dec in decisions:
        payload = dec.get("payload", {})
        index_meta = dec.get("index_meta") or {}
        index_meta.setdefault("parent_batch_plan_artifact_id", batch_plan_artifact_id)
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append({
            "artifact_id": dec.get("artifact_id"),
            "id": dec.get("artifact_id"),
            "kind": dec.get("kind", "saw_batch_decision"),
            "status": dec.get("status", "OK"),
            "created_utc": dec.get("created_utc"),
            "index_meta": index_meta,
        })

    return results


@router.get("/decisions/by-spec")
def list_decisions_by_spec(
    batch_spec_artifact_id: str = Query(..., description="Spec artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List decision artifacts for a given spec, newest first.
    """
    decisions = query_decisions_by_spec(batch_spec_artifact_id)[:limit]

    results = []
    for dec in decisions:
        payload = dec.get("payload", {})
        index_meta = dec.get("index_meta") or {}
        index_meta.setdefault("parent_batch_spec_artifact_id", batch_spec_artifact_id)
        index_meta.setdefault("batch_label", payload.get("batch_label"))
        index_meta.setdefault("session_id", payload.get("session_id"))
        index_meta.setdefault("tool_kind", "saw_lab")
        index_meta.setdefault("kind_group", "batch")

        results.append({
            "artifact_id": dec.get("artifact_id"),
            "id": dec.get("artifact_id"),
            "kind": dec.get("kind", "saw_batch_decision"),
            "status": dec.get("status", "OK"),
            "created_utc": dec.get("created_utc"),
            "index_meta": index_meta,
        })

    return results


@router.get("/executions/by-plan")
def list_executions_by_plan(
    batch_plan_artifact_id: str = Query(..., description="Plan artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts for a given plan, newest first.
    """
    executions = query_executions_by_plan(batch_plan_artifact_id)[:limit]

    results = []
    for ex in executions:
        payload = ex.get("payload", {})
        index_meta = ex.get("index_meta") or {}
        index_meta.setdefault("parent_batch_plan_artifact_id", batch_plan_artifact_id)
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


@router.get("/executions/by-spec")
def list_executions_by_spec(
    batch_spec_artifact_id: str = Query(..., description="Spec artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts for a given spec, newest first.
    """
    executions = query_executions_by_spec(batch_spec_artifact_id)[:limit]

    results = []
    for ex in executions:
        payload = ex.get("payload", {})
        index_meta = ex.get("index_meta") or {}
        index_meta.setdefault("parent_batch_spec_artifact_id", batch_spec_artifact_id)
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
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
    operator: str = Query("unknown", description="Operator name"),
    notes: str = Query("", description="Job notes"),
    status: str = Query("COMPLETED", description="Job status"),
    req: Optional[JobLogRequest] = None,
) -> JobLogResponse:
    """
    Log job completion for an execution, optionally creating a metrics rollup.

    If SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED=true, also persists a rollup artifact.
    If SAW_LAB_LEARNING_HOOK_ENABLED=true, emits learning events for burn/tearout/kickback.
    Body with metrics is optional - defaults to zero metrics if not provided.
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Batch execution not found")

    # Get the decision artifact ID for rollup parent reference
    decision_id = execution["payload"].get("batch_decision_artifact_id")

    # Use provided metrics or default to empty
    metrics = req.metrics if req else JobLogMetrics()

    job_log_payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "operator": operator,
        "notes": notes,
        "status": status,
        "metrics": metrics.model_dump(),
    }
    job_log_id = store_artifact(kind="batch_job_log", payload=job_log_payload, parent_id=batch_execution_artifact_id)

    # Optionally create metrics rollup
    rollup_id: Optional[str] = None
    rollups_resp: Optional[RollupArtifacts] = None
    rollup_hook_enabled = os.getenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "").lower() == "true"

    if rollup_hook_enabled:
        # Compute aggregated metrics from all job logs
        all_logs = query_job_logs_by_execution(batch_execution_artifact_id)
        total_cut_time = 0.0
        total_setup_time = 0.0
        parts_ok = 0
        parts_scrap = 0
        burn_events = 0
        tearout_events = 0
        kickback_events = 0

        for log in all_logs:
            log_metrics = log.get("payload", {}).get("metrics", {})
            total_cut_time += log_metrics.get("cut_time_s", 0.0)
            total_setup_time += log_metrics.get("setup_time_s", 0.0)
            parts_ok += log_metrics.get("parts_ok", 0)
            parts_scrap += log_metrics.get("parts_scrap", 0)
            if log_metrics.get("burn"):
                burn_events += 1
            if log_metrics.get("tearout"):
                tearout_events += 1
            if log_metrics.get("kickback"):
                kickback_events += 1

        rollup_payload = {
            "batch_execution_artifact_id": batch_execution_artifact_id,
            "parent_batch_decision_artifact_id": decision_id,
            "metrics": {
                "cut_time_s": total_cut_time,
                "setup_time_s": total_setup_time,
                "total_time_s": total_cut_time + total_setup_time,
                "parts_ok": parts_ok,
                "parts_scrap": parts_scrap,
            },
            "counts": {"job_log_count": len(all_logs)},
            "signals": {"burn_events": burn_events, "tearout_events": tearout_events, "kickback_events": kickback_events},
        }
        rollup_id = store_artifact(kind="saw_batch_execution_metrics_rollup", payload=rollup_payload, parent_id=batch_execution_artifact_id)

        # Also store in the runs artifact index for query_run_artifacts to find
        _store_rollup_for_query(rollup_id, rollup_payload, decision_id)

        exec_rollup_artifact = {
            "artifact_id": rollup_id,
            "kind": "saw_batch_execution_metrics_rollup",
            "payload": rollup_payload,
        }
        rollups_resp = RollupArtifacts(execution_rollup_artifact=exec_rollup_artifact)

    # Optionally emit learning events for burn/tearout/kickback
    learning_event_resp: Optional[LearningEvent] = None
    learning_enabled = os.getenv("SAW_LAB_LEARNING_HOOK_ENABLED", "").lower() == "true"
    if learning_enabled and (metrics.burn or metrics.tearout or metrics.kickback):
        # Determine suggestion type based on event
        suggestion_type = "parameter_override"
        if metrics.burn:
            suggestion_type = "reduce_feed_rate"
        elif metrics.tearout:
            suggestion_type = "reduce_depth_per_pass"
        elif metrics.kickback:
            suggestion_type = "reduce_rpm"

        learning_payload = {
            "batch_decision_artifact_id": decision_id,
            "batch_execution_artifact_id": batch_execution_artifact_id,
            "job_log_artifact_id": job_log_id,
            "suggestion_type": suggestion_type,
            "trigger": {
                "burn": metrics.burn,
                "tearout": metrics.tearout,
                "kickback": metrics.kickback,
            },
            "policy_decision": None,  # Pending approval
        }
        learning_event_id = store_artifact(
            kind="saw_batch_learning_event",
            payload=learning_payload,
            parent_id=decision_id,
        )
        learning_event_resp = LearningEvent(
            artifact_id=learning_event_id,
            id=learning_event_id,
            kind="saw_batch_learning_event",
            suggestion_type=suggestion_type,
        )

    return JobLogResponse(
        job_log_artifact_id=job_log_id,
        metrics_rollup_artifact_id=rollup_id,
        learning_event=learning_event_resp,
        learning_hook_enabled=learning_enabled,
        rollups=rollups_resp,
    )


@router.get("/job-log/by-execution")
def list_job_logs_by_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> List[Dict[str, Any]]:
    """
    List all job logs for a given execution, newest first.
    """
    logs = query_job_logs_by_execution(batch_execution_artifact_id)
    return [
        {
            "artifact_id": log.get("artifact_id"),
            "kind": log.get("kind"),
            "status": log.get("status"),
            "created_utc": log.get("created_utc"),
            "payload": log.get("payload", {}),
        }
        for log in logs
    ]


# ---------------------------------------------------------------------------
# CSV Export Endpoints
# ---------------------------------------------------------------------------


@router.get("/executions/job-logs.csv")
def export_job_logs_csv(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> PlainTextResponse:
    """
    Export job logs for an execution as CSV.
    """
    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    # Build CSV
    headers = ["job_log_artifact_id", "operator", "notes", "status", "parts_ok", "parts_scrap", "cut_time_s", "setup_time_s", "created_utc"]
    lines = [",".join(headers)]

    for log in logs:
        payload = log.get("payload", {})
        metrics = payload.get("metrics", {})
        row = [
            log.get("artifact_id", ""),
            payload.get("operator", ""),
            payload.get("notes", "").replace(",", ";").replace("\n", " "),
            payload.get("status", ""),
            str(metrics.get("parts_ok", 0)),
            str(metrics.get("parts_scrap", 0)),
            str(metrics.get("cut_time_s", 0)),
            str(metrics.get("setup_time_s", 0)),
            log.get("created_utc", ""),
        ]
        lines.append(",".join(row))

    csv_content = "\n".join(lines)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="job_logs_{batch_execution_artifact_id[:8]}.csv"'},
    )


@router.get("/decisions/execution-rollups.csv")
def export_execution_rollups_csv(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> PlainTextResponse:
    """
    Export execution rollups for a decision as CSV.
    """
    rollups = query_execution_rollups_by_decision(batch_decision_artifact_id)

    # Build CSV
    headers = ["rollup_artifact_id", "batch_execution_artifact_id", "log_count", "parts_ok", "parts_scrap", "scrap_rate", "cut_time_s", "setup_time_s", "created_utc"]
    lines = [",".join(headers)]

    for rollup in rollups:
        payload = rollup.get("payload", {})
        metrics = payload.get("metrics", {})
        parts_ok = metrics.get("parts_ok", 0)
        parts_scrap = metrics.get("parts_scrap", 0)
        parts_total = parts_ok + parts_scrap
        scrap_rate = (parts_scrap / parts_total) if parts_total > 0 else 0.0

        row = [
            rollup.get("artifact_id", ""),
            payload.get("batch_execution_artifact_id", ""),
            str(payload.get("log_count", payload.get("counts", {}).get("job_log_count", 0))),
            str(parts_ok),
            str(parts_scrap),
            f"{scrap_rate:.4f}",
            str(metrics.get("cut_time_s", 0)),
            str(metrics.get("setup_time_s", 0)),
            rollup.get("created_utc", ""),
        ]
        lines.append(",".join(row))

    csv_content = "\n".join(lines)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="execution_rollups_{batch_decision_artifact_id[:8]}.csv"'},
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
# Learning Events Endpoints
# ---------------------------------------------------------------------------


class LearningEventApprovalResponse(BaseModel):
    learning_event_artifact_id: str
    policy_decision: str
    approved_by: str


@router.post("/learning-events/approve", response_model=LearningEventApprovalResponse)
def approve_learning_event(
    learning_event_artifact_id: str = Query(..., description="Learning event to approve/reject"),
    policy_decision: str = Query(..., description="ACCEPT or REJECT"),
    approved_by: str = Query(..., description="Approver name"),
    reason: str = Query("", description="Approval reason"),
) -> LearningEventApprovalResponse:
    """
    Approve or reject a learning event.

    Sets policy_decision field on the event artifact.
    """
    event = get_artifact(learning_event_artifact_id)
    if not event:
        raise HTTPException(status_code=404, detail="Learning event not found")

    # Update the event payload with the decision
    payload = event.get("payload", {})
    payload["policy_decision"] = policy_decision
    payload["approved_by"] = approved_by
    payload["approval_reason"] = reason

    # Update in place (in-memory store allows this)
    from app.saw_lab.store import _batch_artifacts
    _batch_artifacts[learning_event_artifact_id]["payload"] = payload

    return LearningEventApprovalResponse(
        learning_event_artifact_id=learning_event_artifact_id,
        policy_decision=policy_decision,
        approved_by=approved_by,
    )


@router.get("/learning-events/by-execution")
def list_learning_events_by_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List learning event artifacts for a given execution.
    """
    events = query_learning_events_by_execution(batch_execution_artifact_id)[:limit]

    results = []
    for ev in events:
        payload = ev.get("payload", {})
        results.append({
            "artifact_id": ev.get("artifact_id"),
            "id": ev.get("artifact_id"),
            "kind": "saw_lab_learning_event",  # Use saw_lab_ prefix for consistency
            "status": ev.get("status", "OK"),
            "created_utc": ev.get("created_utc"),
            "suggestion_type": payload.get("suggestion_type"),
            "policy_decision": payload.get("policy_decision"),
            "payload": payload,
        })

    return results


def _is_truthy(value: str) -> bool:
    """Check if env var value is truthy (1, true, yes, y, on)."""
    return value.lower() in ("1", "true", "yes", "y", "on")


@router.get("/learning-overrides/apply/status")
def get_apply_flag_status() -> Dict[str, Any]:
    """
    Get the current status of the SAW_LAB_APPLY_ACCEPTED_OVERRIDES flag.

    Returns the flag value as a boolean.
    """
    raw_value = os.getenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "")
    is_enabled = _is_truthy(raw_value)

    return {
        "SAW_LAB_APPLY_ACCEPTED_OVERRIDES": is_enabled,
    }


# ---------------------------------------------------------------------------
# Execution Metrics Rollup Endpoints (new paths)
# ---------------------------------------------------------------------------


def _compute_execution_rollup(batch_execution_artifact_id: str) -> Dict[str, Any]:
    """Compute metrics rollup from job logs for an execution."""
    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        m = log.get("payload", {}).get("metrics", {})
        total_cut_time += m.get("cut_time_s", 0.0)
        total_setup_time += m.get("setup_time_s", 0.0)
        parts_ok += m.get("parts_ok", 0)
        parts_scrap += m.get("parts_scrap", 0)
        if m.get("burn"):
            burn_events += 1
        if m.get("tearout"):
            tearout_events += 1
        if m.get("kickback"):
            kickback_events += 1

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "counts": {"job_log_count": len(logs)},
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "total_time_s": total_cut_time + total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
        },
        "signals": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }


@router.get("/executions/metrics-rollup/by-execution")
def preview_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """Preview (compute but don't persist) metrics rollup for an execution."""
    return _compute_execution_rollup(batch_execution_artifact_id)


@router.post("/executions/metrics-rollup/by-execution")
def persist_execution_rollup_new(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """Compute and persist metrics rollup for an execution."""
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    decision_id = execution.get("payload", {}).get("batch_decision_artifact_id", "")
    rollup_data = _compute_execution_rollup(batch_execution_artifact_id)
    rollup_data["parent_batch_decision_artifact_id"] = decision_id

    rollup_id = store_artifact(
        kind="saw_batch_execution_metrics_rollup",
        payload=rollup_data,
        parent_id=batch_execution_artifact_id,
    )

    return {
        "artifact_id": rollup_id,
        "kind": "saw_batch_execution_metrics_rollup",
        "payload": rollup_data,
    }


@router.get("/executions/metrics-rollup/latest")
def get_latest_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """Get the latest persisted rollup for an execution."""
    rollups = query_metrics_rollups_by_execution(batch_execution_artifact_id)
    if not rollups:
        return {"found": False, "batch_execution_artifact_id": batch_execution_artifact_id}

    latest = rollups[0]
    return {
        "found": True,
        "artifact_id": latest.get("artifact_id"),
        "kind": latest.get("kind", "saw_batch_execution_metrics_rollup"),
        "created_utc": latest.get("created_utc"),
        "payload": latest.get("payload", {}),
    }


@router.get("/executions/metrics-rollup/history")
def get_execution_rollup_history(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
) -> List[Dict[str, Any]]:
    """Get rollup history for an execution."""
    rollups = query_metrics_rollups_by_execution(batch_execution_artifact_id)[:limit]
    return [
        {
            "artifact_id": r.get("artifact_id"),
            "id": r.get("artifact_id"),
            "kind": r.get("kind", "saw_batch_execution_metrics_rollup"),
            "created_utc": r.get("created_utc"),
            "payload": r.get("payload", {}),
        }
        for r in rollups
    ]


# ---------------------------------------------------------------------------
# Decision Metrics Rollup Endpoints
# ---------------------------------------------------------------------------


def _compute_decision_rollup(batch_decision_artifact_id: str) -> Dict[str, Any]:
    """Compute aggregated metrics rollup across all executions for a decision."""
    executions = query_executions_by_decision(batch_decision_artifact_id)

    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    job_log_count = 0

    for ex in executions:
        ex_id = ex.get("artifact_id")
        logs = query_job_logs_by_execution(ex_id)
        job_log_count += len(logs)
        for log in logs:
            m = log.get("payload", {}).get("metrics", {})
            total_cut_time += m.get("cut_time_s", 0.0)
            total_setup_time += m.get("setup_time_s", 0.0)
            parts_ok += m.get("parts_ok", 0)
            parts_scrap += m.get("parts_scrap", 0)

    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "counts": {
            "execution_count": len(executions),
            "job_log_count": job_log_count,
        },
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "total_time_s": total_cut_time + total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
        },
    }


@router.get("/decisions/metrics-rollup/by-decision")
def preview_decision_rollup(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> Dict[str, Any]:
    """Preview (compute but don't persist) metrics rollup for a decision."""
    return _compute_decision_rollup(batch_decision_artifact_id)


@router.post("/decisions/metrics-rollup/by-decision")
def persist_decision_rollup(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> Dict[str, Any]:
    """Compute and persist metrics rollup for a decision."""
    rollup_data = _compute_decision_rollup(batch_decision_artifact_id)

    rollup_id = store_artifact(
        kind="saw_batch_decision_metrics_rollup",
        payload=rollup_data,
        parent_id=batch_decision_artifact_id,
    )

    return {
        "artifact_id": rollup_id,
        "kind": "saw_batch_decision_metrics_rollup",
        "payload": rollup_data,
    }


@router.get("/decisions/metrics-rollup/latest")
def get_latest_decision_rollup(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> Dict[str, Any]:
    """Get the latest persisted rollup for a decision."""
    rollups = query_execution_rollups_by_decision(batch_decision_artifact_id)
    if not rollups:
        return {"found": False, "batch_decision_artifact_id": batch_decision_artifact_id}

    latest = rollups[0]
    return {
        "found": True,
        "artifact_id": latest.get("artifact_id"),
        "kind": latest.get("kind", "saw_batch_decision_metrics_rollup"),
        "created_utc": latest.get("created_utc"),
        "payload": latest.get("payload", {}),
    }


# ---------------------------------------------------------------------------
# Rollup Diff Endpoint
# ---------------------------------------------------------------------------


@router.get("/rollups/diff")
def compute_rollup_diff(
    left_rollup_artifact_id: str = Query(..., description="Left rollup artifact ID"),
    right_rollup_artifact_id: str = Query(..., description="Right rollup artifact ID"),
) -> Dict[str, Any]:
    """Compute diff between two rollup artifacts."""
    left = get_artifact(left_rollup_artifact_id)
    right = get_artifact(right_rollup_artifact_id)

    if not left:
        raise HTTPException(status_code=404, detail=f"Left rollup not found: {left_rollup_artifact_id}")
    if not right:
        raise HTTPException(status_code=404, detail=f"Right rollup not found: {right_rollup_artifact_id}")

    left_metrics = left.get("payload", {}).get("metrics", {})
    right_metrics = right.get("payload", {}).get("metrics", {})

    # Compute diffs
    metrics_diff = {}
    all_keys = set(left_metrics.keys()) | set(right_metrics.keys())
    for key in all_keys:
        left_val = left_metrics.get(key, 0)
        right_val = right_metrics.get(key, 0)
        if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
            metrics_diff[key] = {
                "left": left_val,
                "right": right_val,
                "delta": right_val - left_val,
            }

    return {
        "left_artifact_id": left_rollup_artifact_id,
        "right_artifact_id": right_rollup_artifact_id,
        "metrics": metrics_diff,
    }


# ---------------------------------------------------------------------------
# Op-Toolpaths Alias Endpoints
# ---------------------------------------------------------------------------


@router.get("/op-toolpaths/by-decision")
def list_op_toolpaths_by_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
    limit: int = Query(200, ge=1, le=1000, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List op_toolpaths artifacts for a given decision.
    """
    items = query_op_toolpaths_by_decision(batch_decision_artifact_id)[:limit]

    results = []
    for art in items:
        payload = art.get("payload", {})
        index_meta = art.get("index_meta") or {}
        index_meta.setdefault("parent_batch_decision_artifact_id", batch_decision_artifact_id)
        index_meta.setdefault("op_id", payload.get("op_id"))
        index_meta.setdefault("setup_key", payload.get("setup_key"))

        results.append({
            "artifact_id": art.get("artifact_id"),
            "id": art.get("artifact_id"),
            "kind": art.get("kind", "saw_batch_op_toolpaths"),
            "status": art.get("status", "OK"),
            "created_utc": art.get("created_utc"),
            "index_meta": index_meta,
            "payload": payload,
        })

    return results


@router.get("/op-toolpaths/by-execution")
def list_op_toolpaths_by_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> List[Dict[str, Any]]:
    """
    List op_toolpaths artifacts for a given execution (from children).
    """
    items = query_op_toolpaths_by_execution(batch_execution_artifact_id)

    results = []
    for art in items:
        payload = art.get("payload", {})
        index_meta = art.get("index_meta") or {}
        index_meta.setdefault("parent_batch_execution_artifact_id", batch_execution_artifact_id)
        index_meta.setdefault("op_id", payload.get("op_id"))
        index_meta.setdefault("setup_key", payload.get("setup_key"))

        results.append({
            "artifact_id": art.get("artifact_id"),
            "id": art.get("artifact_id"),
            "kind": art.get("kind", "saw_batch_op_toolpaths"),
            "status": art.get("status", "OK"),
            "created_utc": art.get("created_utc"),
            "index_meta": index_meta,
            "payload": payload,
        })

    return results


# ---------------------------------------------------------------------------
# Execution Retry Endpoint
# ---------------------------------------------------------------------------


class RetryResponse(BaseModel):
    source_execution_artifact_id: str
    new_execution_artifact_id: str
    retry_artifact_id: str


@router.post("/executions/retry", response_model=RetryResponse)
def retry_execution(
    batch_execution_artifact_id: str = Query(..., description="Source execution to retry"),
    reason: str = Query("", description="Reason for retry"),
) -> RetryResponse:
    """
    Create a retry execution from a source execution.

    Retries BLOCKED or ERROR ops. If all OK, creates an empty retry.
    """
    source = get_artifact(batch_execution_artifact_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source execution not found")

    source_payload = source.get("payload", {})
    decision_id = source_payload.get("batch_decision_artifact_id", "")
    plan_id = source_payload.get("batch_plan_artifact_id", "")
    spec_id = source_payload.get("batch_spec_artifact_id", "")
    batch_label = source_payload.get("batch_label", "")
    session_id = source_payload.get("session_id", "")

    # Collect ops that need retry (BLOCKED/ERROR)
    results = source_payload.get("results", [])
    retry_ops = [r for r in results if r.get("status") in ("BLOCKED", "ERROR")]

    # Create new child op_toolpaths for retry ops (or empty if all OK)
    new_children = []
    new_results = []
    for op in retry_ops:
        op_payload = {
            "batch_decision_artifact_id": decision_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "op_id": op.get("op_id"),
            "setup_key": op.get("setup_key", ""),
            "toolpaths": {"moves": []},  # Empty retry toolpaths
            "retry_source": batch_execution_artifact_id,
        }
        child_id = store_artifact(
            kind="saw_batch_op_toolpaths",
            payload=op_payload,
            parent_id=decision_id,
            session_id=session_id,
            status="OK",
        )
        new_children.append({"artifact_id": child_id, "kind": "saw_batch_op_toolpaths"})
        new_results.append({
            "op_id": op.get("op_id"),
            "setup_key": op.get("setup_key", ""),
            "status": "OK",
            "toolpaths_artifact_id": child_id,
        })

    # Create new execution artifact
    new_exec_payload = {
        "batch_decision_artifact_id": decision_id,
        "batch_plan_artifact_id": plan_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "summary": {
            "op_count": len(new_results),
            "ok_count": len(new_results),
            "blocked_count": 0,
            "error_count": 0,
        },
        "children": new_children,
        "results": new_results,
        "retry_source_execution_id": batch_execution_artifact_id,
    }
    new_exec_id = store_artifact(
        kind="saw_batch_execution",
        payload=new_exec_payload,
        parent_id=decision_id,
        session_id=session_id,
        status="OK",
    )

    # Create retry artifact
    retry_payload = {
        "source_execution_artifact_id": batch_execution_artifact_id,
        "new_execution_artifact_id": new_exec_id,
        "reason": reason,
        "retry_op_count": len(retry_ops),
    }
    retry_id = store_artifact(
        kind="saw_batch_execution_retry",
        payload=retry_payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
    )

    return RetryResponse(
        source_execution_artifact_id=batch_execution_artifact_id,
        new_execution_artifact_id=new_exec_id,
        retry_artifact_id=retry_id,
    )


# ---------------------------------------------------------------------------
# Metrics Rollup Endpoints
# ---------------------------------------------------------------------------


@router.get("/metrics/rollup/by-execution")
def compute_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """
    Compute metrics rollup for an execution from its job logs (read-only).
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    # Aggregate metrics
    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        metrics = log.get("payload", {}).get("metrics", {})
        total_cut_time += metrics.get("cut_time_s", 0.0)
        total_setup_time += metrics.get("setup_time_s", 0.0)
        parts_ok += metrics.get("parts_ok", 0)
        parts_scrap += metrics.get("parts_scrap", 0)
        if metrics.get("burn"):
            burn_events += 1
        if metrics.get("tearout"):
            tearout_events += 1
        if metrics.get("kickback"):
            kickback_events += 1

    parts_total = parts_ok + parts_scrap
    scrap_rate = (parts_scrap / parts_total) if parts_total > 0 else 0.0

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "log_count": len(logs),
        "times": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
        },
        "yield": {
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
            "parts_total": parts_total,
            "scrap_rate": scrap_rate,
        },
        "events": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }


@router.post("/metrics/rollup/by-execution")
def persist_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """
    Compute and persist metrics rollup artifact for an execution.
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    exec_payload = execution.get("payload", {})
    decision_id = exec_payload.get("batch_decision_artifact_id", "")

    # Compute rollup
    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        metrics = log.get("payload", {}).get("metrics", {})
        total_cut_time += metrics.get("cut_time_s", 0.0)
        total_setup_time += metrics.get("setup_time_s", 0.0)
        parts_ok += metrics.get("parts_ok", 0)
        parts_scrap += metrics.get("parts_scrap", 0)
        if metrics.get("burn"):
            burn_events += 1
        if metrics.get("tearout"):
            tearout_events += 1
        if metrics.get("kickback"):
            kickback_events += 1

    parts_total = parts_ok + parts_scrap

    rollup_payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "parent_batch_decision_artifact_id": decision_id,
        "log_count": len(logs),
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
        },
        "counts": {"job_log_count": len(logs)},
        "signals": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }

    rollup_id = store_artifact(
        kind="saw_batch_execution_rollup",
        payload=rollup_payload,
        parent_id=batch_execution_artifact_id,
    )

    return {
        "artifact_id": rollup_id,
        "kind": "saw_batch_execution_rollup",
        "payload": rollup_payload,
    }


@router.get("/metrics/rollup/alias")
def list_metrics_rollups(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> List[Dict[str, Any]]:
    """
    List metrics rollup artifacts for a given execution.
    """
    rollups = query_metrics_rollups_by_execution(batch_execution_artifact_id)

    results = []
    for art in rollups:
        results.append({
            "artifact_id": art.get("artifact_id"),
            "kind": art.get("kind", "saw_batch_execution_rollup"),
            "status": art.get("status", "OK"),
            "created_utc": art.get("created_utc"),
            "payload": art.get("payload", {}),
        })

    return results


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


# ---------------------------------------------------------------------------
# Learning Event Approval Endpoints
# ---------------------------------------------------------------------------


@router.post("/learning-events/approve")
def approve_learning_event(
    learning_event_artifact_id: str = Query(..., description="Learning event artifact ID"),
    policy_decision: str = Query(..., description="Policy decision (ACCEPT or REJECT)"),
    approved_by: str = Query(..., description="Approver name"),
    reason: str = Query("", description="Reason for decision"),
) -> Dict[str, Any]:
    """
    Approve or reject a learning event.

    Updates the learning event's policy_decision field.
    """
    event = get_artifact(learning_event_artifact_id)
    if not event:
        raise HTTPException(status_code=404, detail="Learning event not found")

    # Update the event payload with the decision
    payload = event.get("payload", {})
    payload["policy_decision"] = policy_decision.upper()
    payload["approved_by"] = approved_by
    payload["approval_reason"] = reason

    # Update in store (in-memory update)
    event["payload"] = payload

    return {
        "artifact_id": learning_event_artifact_id,
        "policy_decision": policy_decision.upper(),
        "approved_by": approved_by,
    }


@router.get("/learning-overrides/resolve")
def resolve_learning_overrides(
    limit_events: int = Query(200, ge=1, le=1000, description="Max events to consider"),
) -> Dict[str, Any]:
    """
    Resolve accumulated learning overrides from all accepted events.

    Returns multipliers for spindle_rpm, feed_rate, doc based on accepted suggestions.
    """
    accepted = query_all_accepted_learning_events(limit=limit_events)

    # Default multipliers
    spindle_rpm_mult = 1.0
    feed_rate_mult = 1.0
    doc_mult = 1.0

    # Apply multipliers from accepted events
    for event in accepted:
        payload = event.get("payload", {})
        suggestion_type = payload.get("suggestion_type", "")
        trigger = payload.get("trigger", {})

        if trigger.get("burn"):
            # burn => reduce RPM, increase feed
            spindle_rpm_mult *= 0.9
            feed_rate_mult *= 1.05
        elif trigger.get("tearout"):
            # tearout => reduce DOC
            doc_mult *= 0.85
        elif trigger.get("kickback"):
            # kickback => reduce RPM
            spindle_rpm_mult *= 0.85

    return {
        "resolved": {
            "spindle_rpm_mult": round(spindle_rpm_mult, 4),
            "feed_rate_mult": round(feed_rate_mult, 4),
            "doc_mult": round(doc_mult, 4),
        },
        "source_count": len(accepted),
    }


@router.post("/learning-overrides/apply")
def apply_learning_overrides(
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply resolved learning overrides to a context.

    Takes spindle_rpm, feed_rate, doc_mm and returns tuned values.
    """
    apply_enabled = _is_truthy(os.getenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", ""))

    # Get resolved multipliers
    accepted = query_all_accepted_learning_events(limit=200)

    spindle_rpm_mult = 1.0
    feed_rate_mult = 1.0
    doc_mult = 1.0

    for event in accepted:
        payload = event.get("payload", {})
        trigger = payload.get("trigger", {})

        if trigger.get("burn"):
            spindle_rpm_mult *= 0.9
            feed_rate_mult *= 1.05
        elif trigger.get("tearout"):
            doc_mult *= 0.85
        elif trigger.get("kickback"):
            spindle_rpm_mult *= 0.85

    # Extract original values
    orig_rpm = context.get("spindle_rpm", 0)
    orig_feed = context.get("feed_rate", 0)
    orig_doc = context.get("doc_mm", 0)

    # Apply multipliers
    tuned_rpm = round(orig_rpm * spindle_rpm_mult, 2)
    tuned_feed = round(orig_feed * feed_rate_mult, 2)
    tuned_doc = round(orig_doc * doc_mult, 2)

    tuned_context = {
        "spindle_rpm": tuned_rpm,
        "feed_rate": tuned_feed,
        "doc_mm": tuned_doc,
    }

    return {
        "apply_enabled": apply_enabled,
        "resolved": {
            "spindle_rpm_mult": round(spindle_rpm_mult, 4),
            "feed_rate_mult": round(feed_rate_mult, 4),
            "doc_mult": round(doc_mult, 4),
        },
        "tuning_stamp": {
            "applied": apply_enabled,
            "before": {
                "spindle_rpm": orig_rpm,
                "feed_rate": orig_feed,
                "doc_mm": orig_doc,
            },
            "after": {
                "spindle_rpm": tuned_rpm,
                "feed_rate": tuned_feed,
                "doc_mm": tuned_doc,
            },
            "multipliers": {
                "spindle_rpm_mult": round(spindle_rpm_mult, 4),
                "feed_rate_mult": round(feed_rate_mult, 4),
                "doc_mult": round(doc_mult, 4),
            },
        },
        "tuned_context": tuned_context,
    }


@router.get("/executions/with-learning")
def list_executions_with_learning(
    only_applied: str = Query("false", description="Filter to only executions with learning applied"),
    batch_label: Optional[str] = Query(None, description="Filter by batch label"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts with learning info.

    If only_applied=true, only returns executions where learning was actually applied.
    """
    only_applied_bool = only_applied.lower() in ("true", "1", "yes")
    results = query_executions_with_learning(batch_label=batch_label, only_applied=only_applied_bool)

    return [
        {
            "artifact_id": art.get("artifact_id"),
            "id": art.get("artifact_id"),
            "kind": art.get("kind"),
            "status": art.get("status"),
            "created_utc": art.get("created_utc"),
            "batch_label": art.get("payload", {}).get("batch_label"),
            "session_id": art.get("payload", {}).get("session_id"),
            "learning": art.get("payload", {}).get("learning", {}),
        }
        for art in results
    ]


# ---------------------------------------------------------------------------
# Alternative Metrics Rollup Endpoints (different path format)
# ---------------------------------------------------------------------------


@router.get("/metrics/rollup/by-execution")
def get_metrics_rollup_by_execution_alt(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """
    Compute metrics rollup preview for an execution (alternative path).

    Returns aggregated metrics from all job logs.
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    # Aggregate metrics
    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        metrics = log.get("payload", {}).get("metrics", {})
        total_cut_time += metrics.get("cut_time_s", 0.0)
        total_setup_time += metrics.get("setup_time_s", 0.0)
        parts_ok += metrics.get("parts_ok", 0)
        parts_scrap += metrics.get("parts_scrap", 0)
        if metrics.get("burn"):
            burn_events += 1
        if metrics.get("tearout"):
            tearout_events += 1
        if metrics.get("kickback"):
            kickback_events += 1

    parts_total = parts_ok + parts_scrap
    yield_pct = (parts_ok / parts_total * 100) if parts_total > 0 else 0.0

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "log_count": len(logs),
        "times": {
            "total_cut_time_s": total_cut_time,
            "total_setup_time_s": total_setup_time,
            "total_time_s": total_cut_time + total_setup_time,
        },
        "yield": {
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
            "parts_total": parts_total,
            "yield_pct": round(yield_pct, 2),
        },
        "events": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }


@router.post("/metrics/rollup/by-execution")
def persist_metrics_rollup_by_execution_alt(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """
    Persist metrics rollup artifact for an execution (alternative path).

    Creates and stores a rollup artifact with aggregated metrics.
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Compute metrics same as GET
    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        metrics = log.get("payload", {}).get("metrics", {})
        total_cut_time += metrics.get("cut_time_s", 0.0)
        total_setup_time += metrics.get("setup_time_s", 0.0)
        parts_ok += metrics.get("parts_ok", 0)
        parts_scrap += metrics.get("parts_scrap", 0)
        if metrics.get("burn"):
            burn_events += 1
        if metrics.get("tearout"):
            tearout_events += 1
        if metrics.get("kickback"):
            kickback_events += 1

    parts_total = parts_ok + parts_scrap
    yield_pct = (parts_ok / parts_total * 100) if parts_total > 0 else 0.0

    decision_id = execution.get("payload", {}).get("batch_decision_artifact_id")

    rollup_payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "parent_batch_decision_artifact_id": decision_id,
        "log_count": len(logs),
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "total_time_s": total_cut_time + total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
            "parts_total": parts_total,
            "yield_pct": round(yield_pct, 2),
        },
        "events": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }

    rollup_id = store_artifact(
        kind="saw_batch_execution_rollup",
        payload=rollup_payload,
        parent_id=batch_execution_artifact_id,
    )

    return {
        "artifact_id": rollup_id,
        "kind": "saw_batch_execution_rollup",
        "payload": rollup_payload,
    }


@router.get("/metrics/rollup/alias")
def get_metrics_rollup_alias(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> List[Dict[str, Any]]:
    """
    List all metrics rollup artifacts for an execution (alias lookup).
    """
    rollups = query_metrics_rollups_by_execution(batch_execution_artifact_id)

    return [
        {
            "artifact_id": r.get("artifact_id"),
            "id": r.get("artifact_id"),
            "kind": r.get("kind"),
            "created_utc": r.get("created_utc"),
            "payload": r.get("payload", {}),
        }
        for r in rollups
    ]
