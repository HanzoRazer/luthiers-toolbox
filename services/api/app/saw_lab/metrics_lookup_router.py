from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class LatestMetricsByDecisionResponse(BaseModel):
    decision_artifact_id: str
    latest_execution_artifact_id: Optional[str] = None
    latest_metrics_artifact_id: Optional[str] = None
    kpis: Optional[dict] = None


@router.get("/execution/metrics/latest-by-decision", response_model=LatestMetricsByDecisionResponse)
def latest_metrics_by_decision(
    decision_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
) -> LatestMetricsByDecisionResponse:
    """
    Tiny alias helper for dashboards:
      decision -> latest execution -> latest metrics (for that execution)
    """
    if not decision_artifact_id:
        raise HTTPException(status_code=400, detail="decision_artifact_id required")

    from .metrics_lookup_service import resolve_latest_metrics_by_decision

    out = resolve_latest_metrics_by_decision(
        decision_artifact_id=decision_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind="saw",
    )
    return LatestMetricsByDecisionResponse(**out)
