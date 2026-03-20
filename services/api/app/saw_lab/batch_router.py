"""Saw Lab Batch Workflow Router"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

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
# Plan Choose (operator approval with optional tuning patch)
# ---------------------------------------------------------------------------


@router.post("/plan/choose", response_model=BatchPlanChooseResponse)
def choose_batch_plan(req: BatchPlanChooseRequest) -> BatchPlanChooseResponse:
    """
    Operator approval: select ops from a plan, optionally apply recommended patch.

    This creates a saw_batch_decision artifact with the selected operations.
    If apply_recommended_patch=True, looks up the latest approved tuning decision
    and applies the multipliers to the decision payload.
    """
    # Load the plan artifact
    plan = get_artifact(req.batch_plan_artifact_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Batch plan not found")

    plan_payload = plan.get("payload", {})
    batch_label = plan_payload.get("batch_label", "")
    session_id = plan_payload.get("session_id", "")
    spec_id = plan_payload.get("batch_spec_artifact_id", "")

    # Extract tool_id and material_id for tuning lookup
    setups = plan_payload.get("setups", [])
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    if setups and isinstance(setups, list) and len(setups) > 0:
        first_setup = setups[0] if isinstance(setups[0], dict) else {}
        tool_id = first_setup.get("tool_id")

    # Try to get material_id from spec
    if spec_id:
        spec = get_artifact(spec_id)
        if spec:
            spec_payload = spec.get("payload", {})
            items = spec_payload.get("items", [])
            if items and isinstance(items, list) and len(items) > 0:
                first_item = items[0] if isinstance(items[0], dict) else {}
                material_id = first_item.get("material_id")

    # Build decision payload
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

    # Apply tuning patch if requested
    if req.apply_recommended_patch and tool_id and material_id:
        try:
            from .decision_intel_apply_service import (
                find_latest_approved_tuning_decision,
                ArtifactStorePorts,
            )
            from ..rmos.runs_v2 import store as runs_store

            # Create store ports adapter
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

    # Store the decision artifact
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
