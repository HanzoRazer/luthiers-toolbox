"""Consolidated Decision Intelligence Router.

Merged from:
- decision_intelligence_router.py (2 routes)
- decision_intel_apply_router.py (2 routes)

Total: 4 routes under /api/saw/batch/decision-intel
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

# Services from both modules
from .decision_intelligence_service import (
    ArtifactStorePorts as IntelStorePorts,
    build_suggestion_for_execution,
    enrich_index_meta_with_tool_material,
    persist_decision_artifact,
    persist_suggestion_artifact,
)
from .decision_intel_apply_service import (
    ArtifactStorePorts as ApplyStorePorts,
    find_latest_approved_tuning_decision,
    persist_plan_intel_link,
)

# Schemas from both modules
from .schemas_decision_intelligence import (
    ApproveSuggestionRequest,
    ApproveSuggestionResponse,
    CreateSuggestionResponse,
)
from .schemas_apply_on_next_plan import (
    LatestApprovedDeltaResponse,
    StampPlanIntelLinkRequest,
    StampPlanIntelLinkResponse,
)


router = APIRouter(prefix="/api/saw/batch/decision-intel", tags=["Saw", "Decision-Intel"])


def _get_store_ports() -> IntelStorePorts:
    """Adapter to RunArtifact store."""
    from app.rmos.runs_v2 import store as runs_store  # type: ignore

    if not hasattr(runs_store, "list_runs_filtered"):
        raise RuntimeError("runs_store.list_runs_filtered not found")
    if not hasattr(runs_store, "persist_run_artifact"):
        raise RuntimeError("runs_store.persist_run_artifact not found")

    return IntelStorePorts(
        list_runs_filtered=getattr(runs_store, "list_runs_filtered"),
        persist_run_artifact=getattr(runs_store, "persist_run_artifact"),
    )


# =============================================================================
# Routes from decision_intelligence_router.py
# =============================================================================


@router.get("/suggestions", response_model=CreateSuggestionResponse)
def get_suggestion_for_execution(
    batch_execution_artifact_id: str = Query(...),
    session_id: Optional[str] = Query(None),
    batch_label: Optional[str] = Query(None),
    tool_id: Optional[str] = Query(None),
    material_id: Optional[str] = Query(None),
) -> CreateSuggestionResponse:
    """
    Builds + persists a governed tuning suggestion (conservative deltas only).
    NO auto-application.
    """
    store = _get_store_ports()
    suggestion = build_suggestion_for_execution(
        store,
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
    )

    index_meta: Dict[str, Any] = {
        "tool_kind": "saw",
        "batch_execution_artifact_id": batch_execution_artifact_id,
    }
    if session_id:
        index_meta["session_id"] = session_id
    if batch_label:
        index_meta["batch_label"] = batch_label

    index_meta = enrich_index_meta_with_tool_material(index_meta, tool_id, material_id)

    artifact_id = persist_suggestion_artifact(
        store,
        suggestion=suggestion,
        index_meta=index_meta,
        parent_artifact_id=batch_execution_artifact_id,
    )
    if not artifact_id:
        raise HTTPException(status_code=500, detail="Failed to persist suggestion artifact")

    return CreateSuggestionResponse(artifact_id=artifact_id, suggestion=suggestion)


@router.post("/approve", response_model=ApproveSuggestionResponse)
def approve_suggestion(req: ApproveSuggestionRequest) -> ApproveSuggestionResponse:
    """
    Records operator approval/rejection.
    If approved, appends a best-effort JSONL override entry (still NOT auto-applied).
    """
    store = _get_store_ports()

    try:
        res = store.list_runs_filtered(id=req.suggestion_artifact_id, limit=1)
        items = res.get("items") if isinstance(res, dict) else res
        items = items or []
        suggestion_art = items[0] if items else None
    except (KeyError, ValueError, TypeError, AttributeError):
        suggestion_art = None

    if not isinstance(suggestion_art, dict):
        raise HTTPException(status_code=404, detail="Suggestion artifact not found")

    index_meta = (suggestion_art.get("index_meta") or {}).copy()
    index_meta["tool_kind"] = index_meta.get("tool_kind") or "saw"
    index_meta["parent_suggestion_artifact_id"] = req.suggestion_artifact_id
    index_meta = enrich_index_meta_with_tool_material(
        index_meta, index_meta.get("tool_id"), index_meta.get("material_id")
    )

    effective_delta = None
    if req.approved:
        if req.chosen_delta is not None:
            effective_delta = req.chosen_delta
        else:
            payload = suggestion_art.get("payload") or suggestion_art.get("data") or {}
            delta = (payload.get("delta") if isinstance(payload, dict) else None) or {}
            try:
                from .schemas_decision_intelligence import TuningDelta

                effective_delta = TuningDelta(**delta) if isinstance(delta, dict) else None
            except (ImportError, ValueError, TypeError, KeyError):
                effective_delta = None

    decision_id, wrote = persist_decision_artifact(
        store,
        suggestion_artifact_id=req.suggestion_artifact_id,
        approved=req.approved,
        approved_by=req.approved_by,
        note=req.note,
        effective_delta=effective_delta,
        index_meta=index_meta,
    )
    if not decision_id:
        raise HTTPException(status_code=500, detail="Failed to persist decision artifact")

    return ApproveSuggestionResponse(
        decision_artifact_id=decision_id,
        approved=req.approved,
        effective_delta=effective_delta,
        wrote_overrides_jsonl=wrote,
    )


# =============================================================================
# Routes from decision_intel_apply_router.py
# =============================================================================


@router.get("/latest-approved", response_model=LatestApprovedDeltaResponse)
def latest_approved(
    tool_id: str = Query(...),
    material_id: str = Query(...),
) -> LatestApprovedDeltaResponse:
    """
    Advisory: return latest approved tuning delta for (tool_id, material_id).
    Used to suggest apply-on-next-plan (still requires explicit operator approval).
    """
    store = _get_store_ports()
    decision_id, delta = find_latest_approved_tuning_decision(
        store, tool_id=tool_id, material_id=material_id
    )
    if not decision_id or not delta:
        return LatestApprovedDeltaResponse(tool_id=tool_id, material_id=material_id)
    return LatestApprovedDeltaResponse(
        tool_id=tool_id,
        material_id=material_id,
        decision_artifact_id=decision_id,
        effective_delta=delta,
        note="Found latest approved delta. Use /stamp-plan-link after operator chooses to apply.",
    )


@router.post("/stamp-plan-link", response_model=StampPlanIntelLinkResponse)
def stamp_plan_link(req: StampPlanIntelLinkRequest) -> StampPlanIntelLinkResponse:
    """
    Creates a governed linkage artifact:
      saw_lab_plan_intel_link (parent = batch_plan)
    This stamps that the plan used a specific approved decision delta.
    """
    store = _get_store_ports()
    if not req.decision_artifact_id:
        raise HTTPException(status_code=400, detail="decision_artifact_id required")

    link_id, wrote = persist_plan_intel_link(
        store,
        batch_plan_artifact_id=req.batch_plan_artifact_id,
        tool_id=req.tool_id,
        material_id=req.material_id,
        decision_artifact_id=req.decision_artifact_id,
        effective_delta=req.effective_delta,
        stamped_by=req.stamped_by,
        note=req.note,
        session_id=None,
        batch_label=None,
        write_jsonl=True,
    )
    if not link_id:
        raise HTTPException(status_code=500, detail="Failed to persist plan intel link artifact")
    return StampPlanIntelLinkResponse(
        artifact_id=link_id,
        batch_plan_artifact_id=req.batch_plan_artifact_id,
        decision_artifact_id=req.decision_artifact_id,
        applied_delta=req.effective_delta,
        wrote_overrides_jsonl=wrote,
    )
