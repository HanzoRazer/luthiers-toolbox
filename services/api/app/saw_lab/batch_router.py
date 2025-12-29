"""
Saw Lab Batch Router

API endpoints for batch operations:
  - POST /api/saw/batch/spec      - Create batch specification
  - POST /api/saw/batch/plan      - Generate plan from spec
  - POST /api/saw/batch/approve   - Approve plan with execution order
  - POST /api/saw/batch/toolpaths - Generate toolpaths from decision
  - GET  /api/saw/batch/execution - Lookup latest execution for decision
  - GET  /api/saw/batch/executions/by-decision - List executions by decision
  - GET  /api/saw/batch/executions - List execution artifacts
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException

from app.saw_lab.schemas_batch import (
    SawBatchSpecRequest,
    SawBatchSpecResponse,
    SawBatchPlanRequest,
    SawBatchPlanResponse,
    SawBatchPlanChooseRequest,
    SawBatchPlanChooseResponse,
    SawBatchToolpathsRequest,
    SawBatchToolpathsResponse,
)
from app.services.saw_lab_batch_spec_service import create_batch_spec
from app.services.saw_lab_batch_plan_service import create_batch_plan
from app.services.saw_lab_batch_decision_service import create_batch_plan_decision
from app.services.saw_lab_batch_toolpaths_service import generate_batch_toolpaths_from_decision
from app.services.saw_lab_batch_execution_lookup_service import (
    latest_execution_for_decision,
    list_executions_for_decision,
)
from app.rmos.run_artifacts.store import query_run_artifacts
from app.services.saw_lab_batch_link_graph_service import build_batch_link_graph
from app.saw_lab.schemas_batch_lookup import SawBatchLinkSummary
from app.services.saw_lab_batch_retry_service import retry_batch_execution
from app.services.saw_lab_batch_job_log_service import write_job_log
from app.services.saw_lab_batch_metrics_rollup_service import (
    compute_execution_rollup,
    persist_execution_rollup,
)
from app.services.saw_lab_learning_hook_config import is_saw_lab_learning_hook_enabled
from app.services.saw_lab_learning_decision_service import create_learning_decision
from app.services.saw_lab_learned_overrides_resolver import resolve_learned_multipliers
from app.services.saw_lab_learning_apply_service import (
    is_apply_accepted_overrides_enabled,
    tune_context_from_accepted_learning,
)
from app.services.saw_lab_execution_lookup_service import (
    list_executions_by_decision as lookup_executions_by_decision,
    list_executions_with_learning_applied,
)
from app.services.saw_lab_execution_metrics_rollup_service import (
    compute_execution_metrics_rollup,
    persist_execution_metrics_rollup,
)
from app.services.saw_lab_decision_metrics_rollup_service import (
    compute_decision_metrics_rollup,
    persist_decision_metrics_rollup,
)


router = APIRouter(prefix="/api/saw/batch", tags=["saw-batch"])


@router.post("/spec", response_model=SawBatchSpecResponse)
def create_spec(req: SawBatchSpecRequest) -> SawBatchSpecResponse:
    """
    Create a batch specification from a list of items.

    The spec artifact stores the input items and generates op_ids for tracking.
    """
    out = create_batch_spec(
        batch_label=req.batch_label,
        session_id=req.session_id,
        tool_id=req.tool_id,
        items=[item.model_dump() for item in req.items],
    )
    return SawBatchSpecResponse(**out)


@router.post("/plan", response_model=SawBatchPlanResponse)
def generate_plan(req: SawBatchPlanRequest) -> SawBatchPlanResponse:
    """
    Generate a batch plan from a spec artifact.

    Groups items into setups by material and computes feasibility for each op.
    """
    out = create_batch_plan(batch_spec_artifact_id=req.batch_spec_artifact_id)
    return SawBatchPlanResponse(**out)


@router.post("/approve", response_model=SawBatchPlanChooseResponse)
def approve_plan(req: SawBatchPlanChooseRequest) -> SawBatchPlanChooseResponse:
    """
    Approve a batch plan with operator-defined execution order.

    Creates a decision artifact that locks in the setup and op order.
    """
    out = create_batch_plan_decision(
        batch_plan_artifact_id=req.batch_plan_artifact_id,
        approved_by=req.approved_by,
        reason=req.reason,
        setup_order=req.setup_order,
        op_order=req.op_order,
    )
    return SawBatchPlanChooseResponse(**out)


@router.post("/toolpaths", response_model=SawBatchToolpathsResponse)
def toolpaths_from_batch_decision(req: SawBatchToolpathsRequest) -> SawBatchToolpathsResponse:
    """
    Batch execution scaffold:
    - consumes saw_batch_decision
    - recomputes feasibility per op
    - generates toolpaths per op when feasible
    - persists child op artifacts + one parent execution artifact
    """
    out = generate_batch_toolpaths_from_decision(batch_decision_artifact_id=req.batch_decision_artifact_id)
    return SawBatchToolpathsResponse(**out)


@router.get("/execution")
def get_latest_execution_for_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact id (kind='saw_batch_decision')"),
):
    """
    Convenience alias:
      GET /api/saw/batch/execution?batch_decision_artifact_id=...
    Returns the newest parent execution artifact that was produced from this decision.
    """
    it = latest_execution_for_decision(batch_decision_artifact_id)
    if not it:
        raise HTTPException(status_code=404, detail="No execution artifact found for batch_decision_artifact_id")
    return it


@router.get("/executions/by-decision")
def list_executions_by_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact id (kind='saw_batch_decision')"),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Convenience alias:
      GET /api/saw/batch/executions/by-decision?batch_decision_artifact_id=...&limit=&offset=
    Returns a newest-first list of parent execution artifacts produced from this decision.
    """
    return list_executions_for_decision(
        batch_decision_artifact_id=batch_decision_artifact_id,
        limit=limit,
        offset=offset,
    )


@router.get("/decisions")
def list_decisions(
    batch_label: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    List batch decision artifacts, optionally filtered by batch_label or session_id.
    """
    return query_run_artifacts(kind="saw_batch_decision", batch_label=batch_label, session_id=session_id, limit=limit, offset=offset)


@router.get("/decisions/by-plan")
def list_decisions_by_plan(
    batch_plan_artifact_id: str = Query(..., description="Plan artifact id (kind='saw_batch_plan')"),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Convenience alias:
      GET /api/saw/batch/decisions/by-plan?batch_plan_artifact_id=...&limit=&offset=
    Returns newest-first decisions that reference this plan.
    """
    items = query_run_artifacts(
        kind="saw_batch_decision",
        parent_batch_plan_artifact_id=batch_plan_artifact_id,
        limit=max(limit, 50),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


@router.get("/decisions/by-spec")
def list_decisions_by_spec(
    batch_spec_artifact_id: str = Query(..., description="Spec artifact id (kind='saw_batch_spec')"),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Convenience alias:
      GET /api/saw/batch/decisions/by-spec?batch_spec_artifact_id=...&limit=&offset=
    Returns newest-first decisions that reference this spec.
    """
    items = query_run_artifacts(
        kind="saw_batch_decision",
        parent_batch_spec_artifact_id=batch_spec_artifact_id,
        limit=max(limit, 50),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


@router.get("/executions")
def list_executions(
    batch_label: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    List batch execution artifacts, optionally filtered by batch_label or session_id.
    """
    return query_run_artifacts(kind="saw_batch_execution", batch_label=batch_label, session_id=session_id, limit=limit, offset=offset)


@router.get("/executions/by-plan")
def list_executions_by_plan(
    batch_plan_artifact_id: str = Query(..., description="Plan artifact id (kind='saw_batch_plan')"),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Convenience alias:
      GET /api/saw/batch/executions/by-plan?batch_plan_artifact_id=...&limit=&offset=
    Returns newest-first executions produced from this plan.
    """
    items = query_run_artifacts(
        kind="saw_batch_execution",
        parent_batch_plan_artifact_id=batch_plan_artifact_id,
        limit=max(limit, 50),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


@router.get("/executions/by-spec")
def list_executions_by_spec(
    batch_spec_artifact_id: str = Query(..., description="Spec artifact id (kind='saw_batch_spec')"),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Convenience alias:
      GET /api/saw/batch/executions/by-spec?batch_spec_artifact_id=...&limit=&offset=
    Returns newest-first executions produced from this spec.
    """
    items = query_run_artifacts(
        kind="saw_batch_execution",
        parent_batch_spec_artifact_id=batch_spec_artifact_id,
        limit=max(limit, 50),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


@router.get("/links", response_model=SawBatchLinkSummary)
def get_batch_link_graph(
    batch_label: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    limit_each: int = Query(default=25, ge=1, le=200),
):
    """
    Convenience endpoint for UI:
      GET /api/saw/batch/links?batch_label=...&session_id=...
    Returns newest-first IDs for spec/plan/decision/execution, plus bounded lists.
    """
    out = build_batch_link_graph(batch_label=batch_label, session_id=session_id, limit_each=limit_each)
    return SawBatchLinkSummary(**out)


@router.get("/op-toolpaths/by-execution")
def list_op_toolpaths_by_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact id (kind='saw_batch_execution')"),
    limit: int = Query(default=200, ge=1, le=2000),
):
    """
    Convenience alias:
      GET /api/saw/batch/op-toolpaths/by-execution?batch_execution_artifact_id=...
    Returns child op toolpaths artifacts referenced by the execution parent.
    """
    from app.rmos.run_artifacts.store import read_run_artifact

    parent = read_run_artifact(batch_execution_artifact_id)
    parent_d: Dict[str, Any] = parent if isinstance(parent, dict) else {
        "kind": getattr(parent, "kind", None),
        "payload": getattr(parent, "payload", None),
    }
    if str(parent_d.get("kind") or "") != "saw_batch_execution":
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id is not a saw_batch_execution artifact")

    payload = parent_d.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    children = payload.get("children") or []
    if not isinstance(children, list):
        children = []

    # children are stored as {"artifact_id": "...", "kind": "..."}
    child_ids = [c.get("artifact_id") for c in children if isinstance(c, dict) and c.get("artifact_id")]
    child_ids = child_ids[:limit]

    # Read each child (small N per batch). If store has batch read later, can optimize.
    out: List[Dict[str, Any]] = []
    for cid in child_ids:
        it = read_run_artifact(cid)
        if isinstance(it, dict):
            out.append(it)
        else:
            out.append({
                "artifact_id": getattr(it, "artifact_id", None) or getattr(it, "id", None),
                "kind": getattr(it, "kind", None),
                "status": getattr(it, "status", None),
                "index_meta": getattr(it, "index_meta", None),
                "payload": getattr(it, "payload", None),
                "created_utc": getattr(it, "created_utc", None),
            })
    return out


@router.get("/op-toolpaths/by-decision")
def list_op_toolpaths_by_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact id (kind='saw_batch_decision')"),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
):
    """
    Convenience alias:
      GET /api/saw/batch/op-toolpaths/by-decision?batch_decision_artifact_id=...&limit=&offset=
    Returns op toolpaths artifacts produced under this decision (newest-first).
    """
    items = query_run_artifacts(
        kind="saw_batch_op_toolpaths",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=max(limit, 200),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


@router.post("/executions/retry")
def retry_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact id (kind='saw_batch_execution')"),
    reason: str = Query(default="retry"),
    op_id: Optional[List[str]] = Query(default=None, description="Optional subset of op_ids to retry"),
):
    """
    Convenience endpoint:
      POST /api/saw/batch/executions/retry?batch_execution_artifact_id=...&reason=...&op_id=op1&op_id=op2

    Creates a NEW execution (immutable) that re-runs BLOCKED/ERROR ops (or explicit op_id subset).
    Writes:
      - saw_batch_execution_retry artifact
      - new saw_batch_execution artifact (parent)
      - new saw_batch_op_toolpaths artifacts (children)
    """
    return retry_batch_execution(
        batch_execution_artifact_id=batch_execution_artifact_id,
        op_ids=op_id,
        reason=reason,
    )


@router.post("/job-log")
def create_job_log(
    batch_execution_artifact_id: str,
    operator: str,
    notes: str,
    status: str = "COMPLETED",
    metrics: Optional[dict] = None,
):
    """
    Operator job log for a batch execution.
    Persists a governed RunArtifact.
    """
    return write_job_log(
        batch_execution_artifact_id=batch_execution_artifact_id,
        operator=operator,
        notes=notes,
        status=status,
        metrics=metrics,
    )


@router.get("/job-log/by-execution")
def list_job_logs_by_execution(
    batch_execution_artifact_id: str,
    limit: int = 50,
):
    """
    Convenience alias:
      GET /api/saw/batch/job-log/by-execution?batch_execution_artifact_id=...
    """
    return query_run_artifacts(
        kind="saw_batch_job_log",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=limit,
    )


@router.get("/metrics/rollup/by-execution")
def get_execution_metrics_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact id (kind='saw_batch_execution')"),
    limit_logs: int = Query(default=200, ge=1, le=2000),
):
    """
    Compute-only rollup (no persistence):
      GET /api/saw/batch/metrics/rollup/by-execution?batch_execution_artifact_id=...&limit_logs=...
    """
    return compute_execution_rollup(batch_execution_artifact_id=batch_execution_artifact_id, limit_logs=limit_logs)


@router.post("/metrics/rollup/by-execution")
def create_execution_metrics_rollup_artifact(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact id (kind='saw_batch_execution')"),
    limit_logs: int = Query(default=200, ge=1, le=2000),
):
    """
    Compute + persist rollup as governed artifact:
      POST /api/saw/batch/metrics/rollup/by-execution?batch_execution_artifact_id=...&limit_logs=...
    Writes kind='saw_batch_execution_rollup' with parent_batch_execution_artifact_id in index_meta.
    """
    return persist_execution_rollup(batch_execution_artifact_id=batch_execution_artifact_id, limit_logs=limit_logs)


@router.get("/metrics/rollup/alias")
def get_latest_rollup_artifact_for_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact id (kind='saw_batch_execution')"),
    limit: int = Query(default=25, ge=1, le=500),
):
    """
    Convenience alias:
      GET /api/saw/batch/metrics/rollup/alias?batch_execution_artifact_id=...
    Returns newest-first rollup artifacts for a given execution.
    """
    items = query_run_artifacts(
        kind="saw_batch_execution_rollup",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=max(limit, 50),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items


@router.get("/learning-events/by-execution")
def list_learning_events_by_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact id (kind='saw_batch_execution')"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Convenience alias:
      GET /api/saw/batch/learning-events/by-execution?batch_execution_artifact_id=...&limit=&offset=
    Returns newest-first learning events emitted from job logs (or otherwise) for a given execution.
    """
    items = query_run_artifacts(
        kind="saw_lab_learning_event",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=max(limit, 100),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


@router.get("/learning-hook/status")
def get_learning_hook_status():
    """
    Simple status endpoint so UI/dev can confirm if the feature is enabled.
    """
    return {"SAW_LAB_LEARNING_HOOK_ENABLED": is_saw_lab_learning_hook_enabled()}


@router.post("/learning-events/approve")
def approve_learning_event(
    learning_event_artifact_id: str = Query(..., description="Artifact id for kind='saw_lab_learning_event'"),
    policy_decision: str = Query(..., description="PROPOSE|ACCEPT|REJECT"),
    approved_by: str = Query(...),
    reason: str = Query(default=""),
):
    """
    Governance-safe approval: creates a new decision artifact.
      POST /api/saw/batch/learning-events/approve?learning_event_artifact_id=...&policy_decision=ACCEPT&approved_by=...&reason=...
    """
    return create_learning_decision(
        learning_event_artifact_id=learning_event_artifact_id,
        policy_decision=policy_decision,
        approved_by=approved_by,
        reason=reason,
    )


@router.get("/learning-events/decisions/by-event")
def list_learning_decisions_by_event(
    learning_event_artifact_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Alias:
      GET /api/saw/batch/learning-events/decisions/by-event?learning_event_artifact_id=...
    """
    items = query_run_artifacts(
        kind="saw_lab_learning_decision",
        parent_learning_event_artifact_id=learning_event_artifact_id,
        limit=max(limit, 100),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


@router.get("/learning-overrides/resolve")
def resolve_learning_overrides_preview(
    tool_id: Optional[str] = Query(default=None),
    material_id: Optional[str] = Query(default=None),
    thickness_mm: Optional[float] = Query(default=None),
    limit_events: int = Query(default=200, ge=1, le=2000),
):
    """
    Read-path preview:
      GET /api/saw/batch/learning-overrides/resolve?tool_id=...&material_id=...

    Returns averaged multipliers ONLY from ACCEPTed learning events.
    Does not apply them anywhere automatically.
    """
    return resolve_learned_multipliers(
        tool_id=tool_id,
        material_id=material_id,
        thickness_mm=thickness_mm,
        limit_events=limit_events,
    )


@router.get("/learning-overrides/apply/status")
def get_learning_overrides_apply_status():
    """
    Simple status endpoint so UI/dev can confirm if the apply feature is enabled.
    """
    return {"SAW_LAB_APPLY_ACCEPTED_OVERRIDES": is_apply_accepted_overrides_enabled()}


@router.post("/learning-overrides/apply")
def apply_learning_overrides_to_context(
    context: dict,
    tool_id: Optional[str] = Query(default=None),
    material_id: Optional[str] = Query(default=None),
    thickness_mm: Optional[float] = Query(default=None),
    limit_events: int = Query(default=200, ge=1, le=2000),
):
    """
    Safe apply preview:
      POST /api/saw/batch/learning-overrides/apply?tool_id=...&material_id=...
      Body: { "spindle_rpm": 8000, "feed_rate": 1200, "doc_mm": 3.0 }

    Returns:
      - resolved multipliers (from ACCEPTed events)
      - tuned_context (copy with multipliers applied)
      - tuning_stamp (before/after, applied flag)
      - apply_enabled (current flag state)

    Does NOT persist anything. Pure read+compute.
    """
    return tune_context_from_accepted_learning(
        context=context,
        tool_id=tool_id,
        material_id=material_id,
        thickness_mm=thickness_mm,
        limit_events=limit_events,
    )


@router.get("/executions/with-learning")
def get_executions_with_learning_applied(
    batch_label: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    only_applied: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Alias:
      GET /api/saw/batch/executions/with-learning?only_applied=true&batch_label=...&session_id=...
    """
    return list_executions_with_learning_applied(
        batch_label=batch_label,
        session_id=session_id,
        only_applied=only_applied,
        limit=limit,
        offset=offset,
    )


@router.get("/executions/metrics-rollup/by-execution")
def get_execution_metrics_rollup_preview(
    batch_execution_artifact_id: str = Query(...),
    limit_job_logs: int = Query(default=500, ge=1, le=2000),
):
    """
    Preview rollup without persisting:
      GET /api/saw/batch/executions/metrics-rollup/by-execution?batch_execution_artifact_id=...
    """
    return compute_execution_metrics_rollup(
        batch_execution_artifact_id=batch_execution_artifact_id,
        limit_job_logs=limit_job_logs,
    )


@router.post("/executions/metrics-rollup/by-execution")
def persist_execution_metrics_rollup_endpoint(
    batch_execution_artifact_id: str = Query(...),
    limit_job_logs: int = Query(default=500, ge=1, le=2000),
):
    """
    Persist governed rollup artifact:
      POST /api/saw/batch/executions/metrics-rollup/by-execution?batch_execution_artifact_id=...
    """
    return persist_execution_metrics_rollup(
        batch_execution_artifact_id=batch_execution_artifact_id,
        limit_job_logs=limit_job_logs,
    )


@router.get("/decisions/metrics-rollup/by-decision")
def get_decision_metrics_rollup_preview(
    batch_decision_artifact_id: str = Query(...),
    limit_executions: int = Query(default=200, ge=1, le=2000),
    limit_job_logs_per_execution: int = Query(default=500, ge=1, le=2000),
):
    """
    Preview rollup without persisting:
      GET /api/saw/batch/decisions/metrics-rollup/by-decision?batch_decision_artifact_id=...
    """
    return compute_decision_metrics_rollup(
        batch_decision_artifact_id=batch_decision_artifact_id,
        limit_executions=limit_executions,
        limit_job_logs_per_execution=limit_job_logs_per_execution,
    )


@router.post("/decisions/metrics-rollup/by-decision")
def persist_decision_metrics_rollup_endpoint(
    batch_decision_artifact_id: str = Query(...),
    limit_executions: int = Query(default=200, ge=1, le=2000),
    limit_job_logs_per_execution: int = Query(default=500, ge=1, le=2000),
):
    """
    Persist governed rollup artifact:
      POST /api/saw/batch/decisions/metrics-rollup/by-decision?batch_decision_artifact_id=...
    """
    return persist_decision_metrics_rollup(
        batch_decision_artifact_id=batch_decision_artifact_id,
        limit_executions=limit_executions,
        limit_job_logs_per_execution=limit_job_logs_per_execution,
    )
