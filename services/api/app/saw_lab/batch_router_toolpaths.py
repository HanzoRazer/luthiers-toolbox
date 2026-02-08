"""Saw Lab Batch Workflow — Toolpath generation endpoints.

Extracted from batch_router.py (WP-3) for god-object decomposition.
Sub-router: included by batch_router.router.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.saw_lab.store import (
    store_artifact,
    get_artifact,
    query_accepted_learning_events,
)
from app.saw_lab.batch_router_helpers import (
    extract_base_context as _extract_base_context,
    apply_patch_to_context as _apply_patch_to_context_patch,
    generate_toolpaths_for_ops,
    compute_rollup_from_logs,
    store_rollup_for_query as _store_rollup_for_query,
)
from app.saw_lab.batch_router_schemas import (
    BatchPlanChooseRequest,
    BatchPlanChooseResponse,
    BatchToolpathsFromDecisionRequest,
    BatchToolpathsFromDecisionResponse,
    BatchToolpathsRequest,
    BatchOpResult,
    BatchToolpathsResponse,
    JobLogMetrics,
    JobLogRequest,
    LearningEvent,
    RollupArtifacts,
    JobLogResponse,
    LearningTuningStamp,
    LearningResolved,
    LearningInfo,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Plan Choose (operator approval with optional patch application)
# ---------------------------------------------------------------------------


@router.post("/plan/choose", response_model=BatchPlanChooseResponse)
def choose_batch_plan(req: BatchPlanChooseRequest) -> BatchPlanChooseResponse:
    """Operator approval: select ops from a plan, optionally apply recommended patch."""
    plan = get_artifact(req.batch_plan_artifact_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Batch plan not found")

    plan_payload = plan.get("payload", {})
    batch_label = plan_payload.get("batch_label", "")
    session_id = plan_payload.get("session_id", "")
    spec_id = plan_payload.get("batch_spec_artifact_id", "")

    # Extract tool_id and material_id from the plan (needed for advisory lookup)
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    for setup in plan_payload.get("setups", []):
        if setup.get("setup_key") == req.selected_setup_key:
            tool_id = setup.get("tool_id")
            break

    # Get material_id from spec
    spec = get_artifact(spec_id) if spec_id else None
    if spec:
        spec_payload = spec.get("payload", {})
        items = spec_payload.get("items", [])
        if items:
            material_id = items[0].get("material_id")

    # Build context patch if operator opted in
    applied_context_patch: Optional[Dict[str, Any]] = None
    applied_multipliers: Optional[Dict[str, float]] = None
    advisory_source_decision_artifact_id: Optional[str] = None

    if req.apply_recommended_patch and tool_id and material_id:
        try:
            from app.saw_lab.decision_intel_apply_service import (
                find_latest_approved_tuning_decision,
                ArtifactStorePorts,
            )
            from app.rmos.runs_v2 import store as runs_store  # type: ignore

            store = ArtifactStorePorts(
                list_runs_filtered=getattr(runs_store, "list_runs_filtered"),
                persist_run_artifact=getattr(runs_store, "persist_run_artifact"),
            )
            decision_id, delta = find_latest_approved_tuning_decision(
                store, tool_id=tool_id, material_id=material_id
            )
            if decision_id and delta:
                advisory_source_decision_artifact_id = decision_id
                applied_multipliers = {
                    "rpm_mul": (
                        delta.rpm_mul
                        if hasattr(delta, "rpm_mul")
                        else getattr(delta, "rpm_mul", 1.0)
                    ),
                    "feed_mul": (
                        delta.feed_mul
                        if hasattr(delta, "feed_mul")
                        else getattr(delta, "feed_mul", 1.0)
                    ),
                    "doc_mul": (
                        delta.doc_mul
                        if hasattr(delta, "doc_mul")
                        else getattr(delta, "doc_mul", 1.0)
                    ),
                }

                base_context = _extract_base_context(spec, req.batch_plan_artifact_id)
                applied_context_patch = _apply_patch_to_context_patch(
                    base_context, applied_multipliers
                )
        except (ImportError, KeyError, ValueError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
            pass

    # Create the decision artifact
    payload = {
        "batch_plan_artifact_id": req.batch_plan_artifact_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "selected_setup_key": req.selected_setup_key,
        "selected_op_ids": req.selected_op_ids,
        "apply_recommended_patch": req.apply_recommended_patch,
        "operator_note": req.operator_note,
        "applied_context_patch": applied_context_patch,
        "applied_multipliers": applied_multipliers,
        "advisory_source_decision_artifact_id": advisory_source_decision_artifact_id,
        "approved_by": "operator",
        "reason": req.operator_note or "plan/choose",
        "setup_order": [req.selected_setup_key],
        "op_order": req.selected_op_ids,
    }
    artifact_id = store_artifact(
        kind="saw_batch_decision",
        payload=payload,
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


@router.post(
    "/toolpaths/from-decision", response_model=BatchToolpathsFromDecisionResponse
)
def toolpaths_from_decision(
    req: BatchToolpathsFromDecisionRequest,
) -> BatchToolpathsFromDecisionResponse:
    """
    Selected decision -> generate toolpaths
    Toolpaths artifact is parented to the decision and inherits lineage stamps.
    """
    from .saw_lab_toolpaths_from_decision_service import (
        generate_toolpaths_from_decision,
    )

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


@router.post("/toolpaths", response_model=BatchToolpathsResponse)
def generate_batch_toolpaths(req: BatchToolpathsRequest) -> BatchToolpathsResponse:
    """Generate toolpaths (G-code) from an approved decision."""
    decision = get_artifact(req.batch_decision_artifact_id)
    if not decision:
        error_payload = {
            "batch_decision_artifact_id": req.batch_decision_artifact_id,
            "error": f"Batch decision not found: {req.batch_decision_artifact_id}",
            "summary": {
                "op_count": 0,
                "ok_count": 0,
                "blocked_count": 0,
                "error_count": 1,
            },
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

    plan = get_artifact(plan_id) if plan_id else None
    plan_payload = plan.get("payload", {}) if plan else {}
    setups = plan_payload.get("setups", [])

    op_by_id: Dict[str, Dict[str, Any]] = {}
    for setup in setups:
        if isinstance(setup, dict):
            setup_key = setup.get("setup_key", "")
            for op in setup.get("ops", []):
                if isinstance(op, dict) and op.get("op_id"):
                    op["setup_key"] = setup_key
                    op_by_id[op["op_id"]] = op

    child_ids, child_results, ok_count, total_gcode_lines = generate_toolpaths_for_ops(
        decision_artifact_id=req.batch_decision_artifact_id,
        plan_id=plan_id,
        spec_id=spec_id,
        batch_label=batch_label,
        session_id=session_id,
        op_order=op_order,
        op_by_id=op_by_id,
    )

    apply_enabled = os.getenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "").lower() == "true"
    learning_enabled = os.getenv("SAW_LAB_LEARNING_HOOK_ENABLED", "").lower() == "true"

    accepted_events = (
        query_accepted_learning_events(req.batch_decision_artifact_id)
        if learning_enabled
        else []
    )
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

    learning_payload = {
        "apply_enabled": apply_enabled,
        "resolved": {"source_count": source_count},
        "tuning_stamp": tuning_stamp_dict,
    }

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
        "children": [
            {"artifact_id": cid, "kind": "saw_batch_op_toolpaths"} for cid in child_ids
        ],
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


@router.post("/job-log", response_model=JobLogResponse)
def log_batch_job(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
    operator: str = Query("unknown", description="Operator name"),
    notes: str = Query("", description="Job notes"),
    status: str = Query("COMPLETED", description="Job status"),
    req: Optional[JobLogRequest] = None,
) -> JobLogResponse:
    """Log job completion for an execution, optionally creating a metrics rollup."""
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Batch execution not found")

    decision_id = execution["payload"].get("batch_decision_artifact_id")
    metrics = req.metrics if req else JobLogMetrics()

    job_log_payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "operator": operator,
        "notes": notes,
        "status": status,
        "metrics": metrics.model_dump(),
    }
    job_log_id = store_artifact(
        kind="batch_job_log",
        payload=job_log_payload,
        parent_id=batch_execution_artifact_id,
    )

    try:
        from .execution_metrics_autorollup import maybe_autorollup_execution_metrics

        maybe_autorollup_execution_metrics(
            batch_execution_artifact_id=batch_execution_artifact_id,
            session_id=execution.get("session_id"),
            batch_label=execution.get("batch_label"),
            tool_kind="saw",
        )
    except (ImportError, RuntimeError, ValueError, TypeError):  # WP-1: narrowed from except Exception
        pass

    rollup_id: Optional[str] = None
    rollups_resp: Optional[RollupArtifacts] = None
    rollup_hook_enabled = (
        os.getenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "").lower() == "true"
    )

    if rollup_hook_enabled:
        rollup_payload = compute_rollup_from_logs(batch_execution_artifact_id)
        rollup_payload["parent_batch_decision_artifact_id"] = decision_id

        rollup_id = store_artifact(
            kind="saw_batch_execution_metrics_rollup",
            payload=rollup_payload,
            parent_id=batch_execution_artifact_id,
        )

        _store_rollup_for_query(rollup_id, rollup_payload, decision_id)

        exec_rollup_artifact = {
            "artifact_id": rollup_id,
            "kind": "saw_batch_execution_metrics_rollup",
            "payload": rollup_payload,
        }
        rollups_resp = RollupArtifacts(execution_rollup_artifact=exec_rollup_artifact)

    learning_event_resp: Optional[LearningEvent] = None
    learning_enabled = os.getenv("SAW_LAB_LEARNING_HOOK_ENABLED", "").lower() == "true"
    if learning_enabled and (metrics.burn or metrics.tearout or metrics.kickback):
        suggestion_type = "parameter_override"
        if metrics.burn:
            suggestion_type = "reduce_feed_rate"
        elif metrics.tearout:
            suggestion_type = "reduce_depth_per_pass"
        elif metrics.kickback:
            suggestion_type = "reduce_rpm"

        learning_payload_data = {
            "batch_decision_artifact_id": decision_id,
            "batch_execution_artifact_id": batch_execution_artifact_id,
            "job_log_artifact_id": job_log_id,
            "suggestion_type": suggestion_type,
            "trigger": {
                "burn": metrics.burn,
                "tearout": metrics.tearout,
                "kickback": metrics.kickback,
            },
            "policy_decision": None,
        }
        learning_event_id = store_artifact(
            kind="saw_batch_learning_event",
            payload=learning_payload_data,
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
    from app.saw_lab.store import query_job_logs_by_execution

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
