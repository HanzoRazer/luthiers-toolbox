from __future__ import annotations

from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ExecutionStatusResponse(BaseModel):
    ok: bool
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: str = "saw"

    status: str

    created_utc: Optional[str] = None
    updated_utc: Optional[str] = None

    links: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Related artifact IDs",
    )

    kpis: Optional[Dict[str, Any]] = None


@router.get(
    "/execution/{batch_execution_artifact_id}/status",
    response_model=ExecutionStatusResponse,
)
def get_execution_status(
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> ExecutionStatusResponse:
    """
    Operator-facing execution status endpoint.

    Returns a single authoritative status derived from artifacts:
      PENDING | CONFIRMED | RUNNING | COMPLETE | ABORTED | BLOCKED
    """
    if not batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")

    from .execution_status_service import compute_execution_status

    result = compute_execution_status(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    if not isinstance(result, dict) or not result.get("ok"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "execution not found"),
        )

    return ExecutionStatusResponse(**result)
