"""
Consolidated metrics lookup router.

Combines:
- metrics_lookup_router (GET /execution/metrics/latest-by-decision)
- latest_batch_chain_router (GET /execution/metrics/latest-by-batch)
- metrics_latest_by_execution_router (GET /execution/metrics/latest)

3 routes for metrics lookup by different keys:
  by-decision | by-batch | by-execution
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


# =============================================================================
# Schemas
# =============================================================================


class LatestMetricsByDecisionResponse(BaseModel):
    decision_artifact_id: str
    latest_execution_artifact_id: Optional[str] = None
    latest_metrics_artifact_id: Optional[str] = None
    kpis: Optional[dict] = None


class LatestMetricsByBatchLabelResponse(BaseModel):
    session_id: str
    batch_label: str
    tool_kind: str = "saw"
    latest_approved_decision_artifact_id: Optional[str] = None
    latest_execution_artifact_id: Optional[str] = None
    latest_metrics_artifact_id: Optional[str] = None
    kpis: Optional[dict] = None


class LatestMetricsByExecutionResponse(BaseModel):
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: str = "saw"
    latest_metrics_artifact_id: Optional[str] = None
    kpis: Optional[dict] = None


# =============================================================================
# Routes
# =============================================================================


@router.get("/execution/metrics/latest-by-decision", response_model=LatestMetricsByDecisionResponse)
def latest_metrics_by_decision(
    decision_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
) -> LatestMetricsByDecisionResponse:
    """
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


@router.get("/execution/metrics/latest-by-batch", response_model=LatestMetricsByBatchLabelResponse)
def latest_metrics_by_batch(
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
) -> LatestMetricsByBatchLabelResponse:
    """
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


@router.get("/execution/metrics/latest", response_model=LatestMetricsByExecutionResponse)
def latest_metrics_by_execution(
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> LatestMetricsByExecutionResponse:
    """
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
