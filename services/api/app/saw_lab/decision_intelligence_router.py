from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from .decision_intelligence_service import (
    ArtifactStorePorts,
    build_suggestion_for_execution,
    enrich_index_meta_with_tool_material,
    persist_decision_artifact,
    persist_suggestion_artifact,
)
from .schemas_decision_intelligence import (
    ApproveSuggestionRequest,
    ApproveSuggestionResponse,
    CreateSuggestionResponse,
)


router = APIRouter(prefix="/api/saw/batch/decision-intel", tags=["Saw", "Decision-Intel"])


def _get_store_ports() -> ArtifactStorePorts:
    """
    Adapter to your repo's RunArtifact store.
    Update this function ONLY if your store module names change.
    """
    # Common patterns seen in your repo:
    # - app.rmos.runs_v2.store: list_runs_filtered(), persist_run_artifact()
    from app.rmos.runs_v2 import store as runs_store  # type: ignore

    if not hasattr(runs_store, "list_runs_filtered"):
        raise RuntimeError("runs_store.list_runs_filtered not found")
    if not hasattr(runs_store, "persist_run_artifact"):
        raise RuntimeError("runs_store.persist_run_artifact not found")

    return ArtifactStorePorts(
        list_runs_filtered=getattr(runs_store, "list_runs_filtered"),
        persist_run_artifact=getattr(runs_store, "persist_run_artifact"),
    )


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

    # Build minimal index_meta (carry through batch/session if known)
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

    # Load suggestion artifact to inherit index_meta + execution id
    try:
        res = store.list_runs_filtered(id=req.suggestion_artifact_id, limit=1)
        items = res.get("items") if isinstance(res, dict) else res
        items = items or []
        suggestion_art = items[0] if items else None
    except (KeyError, ValueError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
        suggestion_art = None

    if not isinstance(suggestion_art, dict):
        raise HTTPException(status_code=404, detail="Suggestion artifact not found")

    index_meta = (suggestion_art.get("index_meta") or {}).copy()
    index_meta["tool_kind"] = index_meta.get("tool_kind") or "saw"
    index_meta["parent_suggestion_artifact_id"] = req.suggestion_artifact_id
    # Ensure tool/material tags propagate into decisions for lookup.
    index_meta = enrich_index_meta_with_tool_material(index_meta, index_meta.get("tool_id"), index_meta.get("material_id"))

    # Compute effective delta:
    # - if approved and operator provided chosen_delta, use it
    # - else use suggestion payload delta if present
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
            except (ImportError, ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
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
