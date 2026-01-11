from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ExecutionMetricsRollupRequest(BaseModel):
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None


class ExecutionMetricsRollupResponse(BaseModel):
    batch_execution_artifact_id: str
    metrics_artifact_id: str


@router.post("/execution/metrics/rollup", response_model=ExecutionMetricsRollupResponse)
def rollup_execution_metrics(
    req: ExecutionMetricsRollupRequest,
) -> ExecutionMetricsRollupResponse:
    """
    Writes a saw_batch_execution_metrics artifact from job logs.
    This is a controlled writer (governed, auditable).
    """
    from .execution_metrics_rollup_service import (
        write_execution_metrics_rollup_artifact,
    )

    if not req.batch_execution_artifact_id:
        raise HTTPException(
            status_code=400, detail="batch_execution_artifact_id required"
        )

    mid = write_execution_metrics_rollup_artifact(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        tool_kind="saw",
    )
    return ExecutionMetricsRollupResponse(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        metrics_artifact_id=str(mid),
    )
