from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class LatestMetricsByBatchLabelResponse(BaseModel):
    session_id: str
    batch_label: str
    tool_kind: str = "saw"
    latest_approved_decision_artifact_id: Optional[str] = None
    latest_execution_artifact_id: Optional[str] = None
    latest_metrics_artifact_id: Optional[str] = None
    kpis: Optional[dict] = None


@router.get("/execution/metrics/latest-by-batch", response_model=LatestMetricsByBatchLabelResponse)
def latest_metrics_by_batch(
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
) -> LatestMetricsByBatchLabelResponse:
    """
    Convenience alias:
      batch -> latest execution -> latest metrics
    Also returns latest approved decision id (if present) for context.
    """
    if not session_id or not batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    from .latest_batch_chain_service import resolve_latest_metrics_for_batch

    out = resolve_latest_metrics_for_batch(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    return LatestMetricsByBatchLabelResponse(**out)
