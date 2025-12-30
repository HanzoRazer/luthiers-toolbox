"""
Saw Lab Batch Workflow Router

Full batch workflow: spec → plan → approve → toolpaths → job-log
Plus decision trends endpoint for metrics rollup analysis.

Mounted at: /api/saw/batch
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

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


class BatchToolpathsResponse(BaseModel):
    batch_execution_artifact_id: str
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
# In-memory store for batch artifacts (demo/testing)
# ---------------------------------------------------------------------------

_batch_artifacts: Dict[str, Dict[str, Any]] = {}


def _store_artifact(kind: str, payload: Dict[str, Any], parent_id: Optional[str] = None) -> str:
    """Store an artifact and return its ID."""
    artifact_id = f"{kind}_{uuid.uuid4().hex[:12]}"
    _batch_artifacts[artifact_id] = {
        "artifact_id": artifact_id,
        "kind": kind,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "parent_id": parent_id,
        "payload": payload,
    }
    return artifact_id


def _get_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    return _batch_artifacts.get(artifact_id)


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
    artifact_id = _store_artifact("batch_spec", payload)
    return BatchSpecResponse(batch_spec_artifact_id=artifact_id)


@router.post("/plan", response_model=BatchPlanResponse)
def create_batch_plan(req: BatchPlanRequest) -> BatchPlanResponse:
    """
    Generate a batch plan from a spec.
    
    Creates setups and operations for the batch.
    """
    spec = _get_artifact(req.batch_spec_artifact_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Batch spec not found")
    
    # Generate mock setups/ops from spec items
    items = spec["payload"].get("items", [])
    tool_id = spec["payload"].get("tool_id", "saw:thin_140")
    
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
        "setups": [s.model_dump() for s in setups],
    }
    artifact_id = _store_artifact("batch_plan", payload, parent_id=req.batch_spec_artifact_id)
    
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
    plan = _get_artifact(req.batch_plan_artifact_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Batch plan not found")
    
    payload = {
        "batch_plan_artifact_id": req.batch_plan_artifact_id,
        "approved_by": req.approved_by,
        "reason": req.reason,
        "setup_order": req.setup_order,
        "op_order": req.op_order,
    }
    artifact_id = _store_artifact("batch_decision", payload, parent_id=req.batch_plan_artifact_id)
    
    return BatchApproveResponse(batch_decision_artifact_id=artifact_id)


@router.post("/toolpaths", response_model=BatchToolpathsResponse)
def generate_batch_toolpaths(req: BatchToolpathsRequest) -> BatchToolpathsResponse:
    """
    Generate toolpaths (G-code) from an approved decision.
    
    Creates an execution artifact.
    """
    decision = _get_artifact(req.batch_decision_artifact_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Batch decision not found")
    
    payload = {
        "batch_decision_artifact_id": req.batch_decision_artifact_id,
        "gcode_lines": 150,  # Mock value
    }
    artifact_id = _store_artifact("batch_execution", payload, parent_id=req.batch_decision_artifact_id)
    
    return BatchToolpathsResponse(
        batch_execution_artifact_id=artifact_id,
        gcode_lines=150,
    )


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
    execution = _get_artifact(batch_execution_artifact_id)
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
    job_log_id = _store_artifact("batch_job_log", job_log_payload, parent_id=batch_execution_artifact_id)
    
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
        rollup_id = _store_artifact("saw_batch_execution_metrics_rollup", rollup_payload, parent_id=decision_id)
        
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
