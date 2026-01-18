from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class LatestToolpathsByExecutionResponse(BaseModel):
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: str = "saw"
    latest_toolpaths_artifact_id: Optional[str] = None
    attachments: Optional[dict] = None


@router.get("/toolpaths/latest", response_model=LatestToolpathsByExecutionResponse)
def latest_toolpaths_by_execution(
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> LatestToolpathsByExecutionResponse:
    """
    execution -> latest toolpaths artifact (+ attachments block if present).
    """
    if not batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")

    from .toolpaths_lookup_service import resolve_latest_toolpaths_for_execution

    tp = resolve_latest_toolpaths_for_execution(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    tp_id = None
    attachments = None
    if isinstance(tp, dict):
        v = tp.get("id") or tp.get("artifact_id")
        tp_id = str(v) if v else None
        payload = tp.get("payload") or tp.get("data") or {}
        if isinstance(payload, dict) and isinstance(payload.get("attachments"), dict):
            attachments = payload["attachments"]

    return LatestToolpathsByExecutionResponse(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        latest_toolpaths_artifact_id=tp_id,
        attachments=attachments,
    )


class LatestToolpathsByBatchResponse(BaseModel):
    session_id: str
    batch_label: str
    tool_kind: str = "saw"
    latest_execution_artifact_id: Optional[str] = None
    latest_toolpaths_artifact_id: Optional[str] = None
    attachments: Optional[dict] = None


@router.get("/toolpaths/latest-by-batch", response_model=LatestToolpathsByBatchResponse)
def latest_toolpaths_by_batch(
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
) -> LatestToolpathsByBatchResponse:
    """
    batch -> latest execution -> latest toolpaths
    """
    if not session_id or not batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    from .toolpaths_lookup_service import resolve_latest_toolpaths_for_batch

    out = resolve_latest_toolpaths_for_batch(session_id=session_id, batch_label=batch_label, tool_kind=tool_kind)
    return LatestToolpathsByBatchResponse(**out)
