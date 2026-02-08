"""Saw Lab Batch Workflow Router"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.saw_lab.store import (
    store_artifact,
    get_artifact,
    query_job_logs_by_execution,
    query_accepted_learning_events,
)
from app.saw_lab.batch_router_helpers import (
    extract_plan_snapshot as _extract_plan_snapshot,
    find_setup_ops as _find_setup_ops,
    extract_base_context as _extract_base_context,
    apply_patch_to_context as _apply_patch_to_context_patch,
    generate_toolpaths_for_ops,
    compute_rollup_from_logs,
    store_rollup_for_query as _store_rollup_for_query,
)

router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

from app.saw_lab.batch_router_schemas import (
    BatchSpecItem,
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
    except (ValueError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
        material_id = None

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

    # Option A — Decision Intelligence (with explicit operator override):
    # Prefer latest plan-choose override, else latest APPROVED tuning decision.
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

            # Recommended latest approved is only shown when override is CLEARED (explicitly)
            recommended_latest_approved = None
            if choose_state_norm == "CLEARED":
                recommended_latest_approved = find_latest_approved_tuning_decision(
                    session_id=session_id,
                    batch_label=batch_label,
                    tool_kind="saw",
                )

            # The applied decision for this plan:
            if applied_override:
                decision_intel_advisory = applied_override
            else:
                # No active override; fall back to latest approved (but we still only *show* recommended when CLEARED)
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
    except (ImportError, KeyError, ValueError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
        # Never block planning on intelligence lookup
        decision_intel_advisory = None
        tuning_applied = False
        plan_auto_suggest = None

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
# WP-3: Toolpath generation endpoints extracted to batch_router_toolpaths.py
# ---------------------------------------------------------------------------
from app.saw_lab.batch_router_toolpaths import router as _toolpaths_router  # noqa: E402
from app.saw_lab.batch_router_toolpaths import (  # noqa: E402  # re-export for test consumers
    choose_batch_plan as choose_batch_plan,
)

router.include_router(_toolpaths_router)

