from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from .batch_summary import BatchSummaryPorts, build_batch_summary


router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/batch-summary")
def batch_summary(
    session_id: str = Query(...),
    batch_label: str = Query(...),
    tool_kind: Optional[str] = Query(None),
    max_nodes: int = Query(5000, ge=1, le=20000),
):
    """
    Batch summary dashboard endpoint (UI card-friendly rollup).
    """
    from . import store as runs_store

    ports = BatchSummaryPorts(
        list_runs_filtered=runs_store.list_runs_filtered,
        get_run=runs_store.get_run,
    )
    return build_batch_summary(
        ports,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        max_nodes=max_nodes,
    )
