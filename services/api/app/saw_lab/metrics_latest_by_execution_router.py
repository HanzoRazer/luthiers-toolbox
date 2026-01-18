from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class LatestMetricsByExecutionResponse(BaseModel):
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: str = "saw"
    latest_metrics_artifact_id: Optional[str] = None
    kpis: Optional[dict] = None


@router.get("/execution/metrics/latest", response_model=LatestMetricsByExecutionResponse)
def latest_metrics_by_execution(
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> LatestMetricsByExecutionResponse:
    """
    Finished API surface helper:
      execution -> latest metrics artifact + kpis
    """
    if not batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")

    from .metrics_lookup_service import resolve_latest_metrics_for_execution

    mx = resolve_latest_metrics_for_execution(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    mx_payload = (mx.get("payload") or mx.get("data") or {}) if isinstance(mx, dict) else {}
    kpis = mx_payload.get("kpis") if isinstance(mx_payload.get("kpis"), dict) else None

    mx_id = None
    if isinstance(mx, dict):
        v = mx.get("id") or mx.get("artifact_id")
        mx_id = str(v) if v else None

    return LatestMetricsByExecutionResponse(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        latest_metrics_artifact_id=mx_id,
        kpis=kpis,
    )
