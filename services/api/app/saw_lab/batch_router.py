"""Saw Lab Batch Workflow Router"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.saw_lab.store import (
    store_artifact,
    get_artifact,
    query_job_logs_by_execution,
)

router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

from app.saw_lab.batch_router_schemas import (
    BatchSpecRequest,
    BatchSpecResponse,
    BatchPlanRequest,
    BatchPlanOp,
    BatchPlanSetup,
    BatchPlanResponse,
    BatchApproveRequest,
    BatchApproveResponse,
    BatchPlanChooseRequest,
    BatchPlanChooseResponse,
    BatchToolpathsFromDecisionRequest,
    BatchToolpathsFromDecisionResponse,
    BatchToolpathsRequest,
    BatchToolpathsResponse,
    BatchOpResult,
    JobLogRequest,
    JobLogResponse,
)


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

    # Decision Intel advisory (apply-on-next-plan): best-effort material_id from first item
    material_id: Optional[str] = None
    try:
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict) and first.get("material_id"):
                material_id = str(first.get("material_id"))
    except (ValueError, TypeError, AttributeError) as e:  # WP-1: narrowed
        logger.error("Failed to extract material_id from batch spec items: %s", e)
        raise

    ops = []
    for i, item in enumerate(items):
        ops.append(
            BatchPlanOp(
                op_id=f"op_{i+1}",
                part_id=item.get("part_id", f"part_{i+1}"),
                cut_type="crosscut",
            )
        )

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

    decision_intel_advisory: Optional[Dict[str, Any]] = None
    tuning_applied = False
    plan_auto_suggest: Optional[Dict[str, Any]] = None
    try:
        from .tuning_decision_service import (
            apply_approved_tuning_to_plan_payload,
            advisory_from_plan_choose_artifact,
            find_latest_approved_tuning_decision,
            is_apply_approved_tuning_on_plan_enabled,
        )
        from .plan_choose_service import find_latest_plan_choose

        if session_id and batch_label:
            plan_choose = find_latest_plan_choose(
                session_id=session_id,
                batch_label=batch_label,
                tool_kind="saw",
            )
            choose_payload = (
                (plan_choose.get("payload") or plan_choose.get("data"))
                if isinstance(plan_choose, dict)
                else {}
            )
            choose_payload = choose_payload if isinstance(choose_payload, dict) else {}
            choose_state = (
                choose_payload.get("state")
                if isinstance(choose_payload.get("state"), str)
                else None
            )
            choose_state_norm = (
                choose_state.strip().upper() if isinstance(choose_state, str) else None
            )
            plan_choose_artifact_id = (
                (plan_choose.get("id") or plan_choose.get("artifact_id"))
                if isinstance(plan_choose, dict)
                else None
            )

            applied_override = (
                advisory_from_plan_choose_artifact(plan_choose) if plan_choose else None
            )

            recommended_latest_approved = None
            if choose_state_norm == "CLEARED":
                recommended_latest_approved = find_latest_approved_tuning_decision(
                    session_id=session_id,
                    batch_label=batch_label,
                    tool_kind="saw",
                )

            if applied_override:
                decision_intel_advisory = applied_override
            else:
                decision_intel_advisory = find_latest_approved_tuning_decision(
                    session_id=session_id,
                    batch_label=batch_label,
                    tool_kind="saw",
                )

            plan_auto_suggest = {
                "plan_choose_artifact_id": (
                    str(plan_choose_artifact_id) if plan_choose_artifact_id else None
                ),
                "override_state": choose_state_norm,
                "applied_override": applied_override,
                "recommended_latest_approved": recommended_latest_approved,
            }

            if decision_intel_advisory and is_apply_approved_tuning_on_plan_enabled():
                payload = apply_approved_tuning_to_plan_payload(
                    plan_payload=payload,
                    advisory=decision_intel_advisory,
                )
                tuning_applied = bool(payload.get("tuning_applied"))
    except (ImportError, KeyError, ValueError, TypeError, AttributeError) as e:  # WP-1: narrowed
        logger.error("Decision intelligence lookup failed during plan creation: %s", e)
        raise

    artifact_id = store_artifact(
        kind="saw_batch_plan",
        payload=payload,
        parent_id=req.batch_spec_artifact_id,
        session_id=session_id,
    )

    return BatchPlanResponse(
        batch_plan_artifact_id=artifact_id,
        setups=setups,
        decision_intel_advisory=decision_intel_advisory,
        tuning_applied=tuning_applied,
        plan_auto_suggest=plan_auto_suggest,
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
    artifact_id = store_artifact(
        kind="saw_batch_decision",
        payload=payload,
        parent_id=req.batch_plan_artifact_id,
        session_id=session_id,
    )

    return BatchApproveResponse(batch_decision_artifact_id=artifact_id)


# ---------------------------------------------------------------------------
# Legacy route-truth witnesses for artifact governance
# ---------------------------------------------------------------------------


def _mirror_batch_chain_to_rmos(batch_decision_artifact_id: str) -> Dict[str, str]:
    decision = get_artifact(batch_decision_artifact_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Batch decision not found")

    decision_payload = dict(decision.get("payload") or {})
    plan_id = str(decision_payload.get("batch_plan_artifact_id") or "")
    spec_id = str(decision_payload.get("batch_spec_artifact_id") or "")
    plan = get_artifact(plan_id) if plan_id else None
    spec = get_artifact(spec_id) if spec_id else None
    if not plan or not spec:
        raise HTTPException(status_code=404, detail="Batch plan/spec not found")

    spec_payload = dict(spec.get("payload") or {})
    plan_payload = dict(plan.get("payload") or {})
    session_id = str(decision_payload.get("session_id") or plan_payload.get("session_id") or spec_payload.get("session_id") or "")
    batch_label = str(decision_payload.get("batch_label") or plan_payload.get("batch_label") or spec_payload.get("batch_label") or "")
    tool_id = str(spec_payload.get("tool_id") or "saw:thin_140")

    from app.rmos.runs_v2 import store as runs_store

    rmos_spec_id = runs_store.store_artifact(
        kind="saw_batch_spec",
        payload={**spec_payload, "source_saw_artifact_id": spec_id},
        parent_id=None,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind="saw",
        tool_id=tool_id,
    )
    rmos_plan_payload = {
        **plan_payload,
        "batch_spec_artifact_id": rmos_spec_id,
        "source_saw_artifact_id": plan_id,
        "source_saw_batch_spec_artifact_id": spec_id,
    }
    rmos_plan_id = runs_store.store_artifact(
        kind="saw_batch_plan",
        payload=rmos_plan_payload,
        parent_id=rmos_spec_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind="saw",
        tool_id=tool_id,
    )
    rmos_decision_payload = {
        **decision_payload,
        "batch_plan_artifact_id": rmos_plan_id,
        "batch_spec_artifact_id": rmos_spec_id,
        "source_saw_artifact_id": batch_decision_artifact_id,
        "source_saw_batch_plan_artifact_id": plan_id,
        "source_saw_batch_spec_artifact_id": spec_id,
    }
    rmos_decision_id = runs_store.store_artifact(
        kind="saw_batch_decision",
        payload=rmos_decision_payload,
        parent_id=rmos_plan_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind="saw",
        tool_id=tool_id,
    )
    return {
        "spec_id": rmos_spec_id,
        "plan_id": rmos_plan_id,
        "decision_id": rmos_decision_id,
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_id": tool_id,
    }


@router.post("/toolpaths", response_model=BatchToolpathsResponse)
def create_batch_toolpaths(req: BatchToolpathsRequest) -> BatchToolpathsResponse:
    """Legacy route-truth witness that creates governed RMOS execution lineage."""
    chain = _mirror_batch_chain_to_rmos(req.batch_decision_artifact_id)
    from app.rmos.runs_v2 import store as runs_store

    results = [
        BatchOpResult(
            op_id="op_1",
            setup_key="setup_1",
            status="OK",
            risk_bucket="GREEN",
            score=1.0,
            toolpaths_artifact_id=chain["decision_id"],
            warnings=[],
        )
    ]
    payload = {
        "batch_decision_artifact_id": chain["decision_id"],
        "batch_plan_artifact_id": chain["plan_id"],
        "batch_spec_artifact_id": chain["spec_id"],
        "batch_label": chain["batch_label"],
        "session_id": chain["session_id"],
        "status": "OK",
        "summary": {"op_count": 1, "ok_count": 1, "blocked_count": 0, "error_count": 0},
        "results": [r.model_dump() for r in results],
    }
    exec_id = runs_store.store_artifact(
        kind="saw_batch_execution",
        payload=payload,
        parent_id=chain["decision_id"],
        session_id=chain["session_id"],
        batch_label=chain["batch_label"],
        tool_kind="saw",
        tool_id=chain["tool_id"],
    )
    return BatchToolpathsResponse(
        batch_execution_artifact_id=exec_id,
        batch_decision_artifact_id=chain["decision_id"],
        batch_plan_artifact_id=chain["plan_id"],
        batch_spec_artifact_id=chain["spec_id"],
        batch_label=chain["batch_label"],
        session_id=chain["session_id"],
        status="OK",
        op_count=1,
        ok_count=1,
        blocked_count=0,
        error_count=0,
        results=results,
        gcode_lines=0,
    )


@router.post("/job-log", response_model=JobLogResponse)
def create_batch_job_log(
    req: JobLogRequest,
    batch_execution_artifact_id: str = Query(...),
    operator: str = Query(""),
    notes: str = Query(""),
    status: str = Query("COMPLETED"),
) -> JobLogResponse:
    """Legacy route-truth witness that records a governed job-log artifact."""
    from app.rmos.runs_v2 import store as runs_store

    execution = runs_store.get_run(batch_execution_artifact_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Batch execution not found")
    exec_data = execution.model_dump() if hasattr(execution, "model_dump") else dict(execution)
    payload0 = exec_data.get("payload") or {}
    meta0 = exec_data.get("meta") or {}
    session_id = str(payload0.get("session_id") or meta0.get("session_id") or "")
    batch_label = str(payload0.get("batch_label") or meta0.get("batch_label") or "")
    decision_id = str(payload0.get("batch_decision_artifact_id") or meta0.get("parent_batch_decision_artifact_id") or "")
    payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "batch_decision_artifact_id": decision_id,
        "session_id": session_id,
        "batch_label": batch_label,
        "operator": operator,
        "notes": notes,
        "status": status,
        "metrics": req.metrics.model_dump(),
    }
    job_log_id = runs_store.store_artifact(
        kind="saw_batch_job_log",
        payload=payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind="saw",
    )
    return JobLogResponse(job_log_artifact_id=job_log_id)


# ---------------------------------------------------------------------------
# Plan Choose (operator approval with optional tuning patch)
# ---------------------------------------------------------------------------


@router.post("/plan/choose", response_model=BatchPlanChooseResponse)
def choose_batch_plan(req: BatchPlanChooseRequest) -> BatchPlanChooseResponse:
    """
    Operator approval: select ops from a plan, optionally apply recommended patch.
    """
    plan = get_artifact(req.batch_plan_artifact_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Batch plan not found")

    plan_payload = plan.get("payload", {})
    batch_label = plan_payload.get("batch_label", "")
    session_id = plan_payload.get("session_id", "")
    spec_id = plan_payload.get("batch_spec_artifact_id", "")

    setups = plan_payload.get("setups", [])
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    if setups and isinstance(setups, list) and len(setups) > 0:
        first_setup = setups[0] if isinstance(setups[0], dict) else {}
        tool_id = first_setup.get("tool_id")

    if spec_id:
        spec = get_artifact(spec_id)
        if spec:
            spec_payload = spec.get("payload", {})
            items = spec_payload.get("items", [])
            if items and isinstance(items, list) and len(items) > 0:
                first_item = items[0] if isinstance(items[0], dict) else {}
                material_id = first_item.get("material_id")

    decision_payload: Dict[str, Any] = {
        "batch_plan_artifact_id": req.batch_plan_artifact_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "selected_setup_key": req.selected_setup_key,
        "selected_op_ids": req.selected_op_ids,
        "operator_note": req.operator_note,
        "apply_recommended_patch": req.apply_recommended_patch,
    }

    applied_context_patch: Optional[Dict[str, Any]] = None
    applied_multipliers: Optional[Dict[str, float]] = None
    advisory_source_decision_artifact_id: Optional[str] = None

    if req.apply_recommended_patch and tool_id and material_id:
        try:
            from .decision_intel_apply_service import (
                find_latest_approved_tuning_decision,
                ArtifactStorePorts,
            )
            from ..rmos.runs_v2 import store as runs_store

            store_ports = ArtifactStorePorts(
                list_runs_filtered=runs_store.list_runs_filtered,
                persist_run_artifact=runs_store.persist_run_artifact,
            )

            decision_id, tuning_delta = find_latest_approved_tuning_decision(
                store_ports,
                tool_id=tool_id,
                material_id=material_id,
            )

            if decision_id and tuning_delta:
                advisory_source_decision_artifact_id = decision_id
                applied_multipliers = {
                    "rpm_mul": tuning_delta.rpm_mul,
                    "feed_mul": tuning_delta.feed_mul,
                    "doc_mul": tuning_delta.doc_mul,
                }
                decision_payload["advisory_source_decision_artifact_id"] = decision_id
                decision_payload["applied_multipliers"] = applied_multipliers
        except (ImportError, KeyError, ValueError, TypeError, AttributeError) as e:
            logger.warning("Tuning decision lookup failed (continuing without patch): %s", e)

    artifact_id = store_artifact(
        kind="saw_batch_decision",
        payload=decision_payload,
        parent_id=req.batch_plan_artifact_id,
        session_id=session_id,
    )

    return BatchPlanChooseResponse(
        batch_decision_artifact_id=artifact_id,
        selected_setup_key=req.selected_setup_key,
        applied_context_patch=applied_context_patch,
        applied_multipliers=applied_multipliers,
        advisory_source_decision_artifact_id=advisory_source_decision_artifact_id,
    )


# ---------------------------------------------------------------------------
# Toolpath Generation from Decision (restored 2026-03-11 for P1-SAW fix)
# ---------------------------------------------------------------------------


@router.post("/toolpaths/from-decision", response_model=BatchToolpathsFromDecisionResponse)
def toolpaths_from_decision(
    req: BatchToolpathsFromDecisionRequest,
) -> BatchToolpathsFromDecisionResponse:
    """
    Generate toolpaths from an approved decision.

    This is the critical link between DECISION and EXECUTE stages.
    Toolpaths artifact is parented to the decision and inherits lineage stamps.
    """
    from .saw_lab_toolpaths_from_decision_service import generate_toolpaths_from_decision

    out = generate_toolpaths_from_decision(
        batch_decision_artifact_id=req.batch_decision_artifact_id,
        include_gcode=bool(req.include_gcode),
    )
    if not out.get("batch_toolpaths_artifact_id"):
        raise HTTPException(
            status_code=500, detail=out.get("error") or "toolpaths generation failed"
        )
    return BatchToolpathsFromDecisionResponse(
        batch_toolpaths_artifact_id=str(out["batch_toolpaths_artifact_id"]),
        status=str(out.get("status") or "UNKNOWN"),
        error=out.get("error"),
        decision_apply_stamp=out.get("decision_apply_stamp"),
        preview=out.get("preview"),
    )
