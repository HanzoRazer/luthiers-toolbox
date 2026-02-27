from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .decision_intel_apply_service import ArtifactStorePorts, find_latest_approved_tuning_decision, persist_plan_intel_link
from .schemas_apply_on_next_plan import LatestApprovedDeltaResponse, StampPlanIntelLinkRequest, StampPlanIntelLinkResponse


router = APIRouter(prefix="/api/saw/batch/decision-intel", tags=["Saw", "Decision-Intel"])


def _get_store_ports() -> ArtifactStorePorts:
    from app.rmos.runs_v2 import store as runs_store  # type: ignore

    return ArtifactStorePorts(
        list_runs_filtered=getattr(runs_store, "list_runs_filtered"),
        persist_run_artifact=getattr(runs_store, "persist_run_artifact"),
    )


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
    decision_id, delta = find_latest_approved_tuning_decision(store, tool_id=tool_id, material_id=material_id)
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
