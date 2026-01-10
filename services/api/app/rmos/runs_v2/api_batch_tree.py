from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from .batch_tree import list_batch_tree, resolve_batch_root


router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/batch-root")
def get_batch_root(
    session_id: str = Query(...),
    batch_label: str = Query(...),
    tool_kind: Optional[str] = Query(None),
):
    """
    Convenience alias: resolve the canonical root artifact id for a batch.
    """
    from . import store as runs_store  # local import to avoid cycles

    root = resolve_batch_root(
        list_runs_filtered=runs_store.list_runs_filtered,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    return {"session_id": session_id, "batch_label": batch_label, "tool_kind": tool_kind, "root_artifact_id": root}


@router.get("/batch-tree")
def get_batch_tree(
    session_id: str = Query(...),
    batch_label: str = Query(...),
    tool_kind: Optional[str] = Query(None),
):
    """
    Returns a hierarchical tree for the batch (nodes + parent/children).
    """
    from . import store as runs_store  # local import to avoid cycles

    return list_batch_tree(
        list_runs_filtered=runs_store.list_runs_filtered,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
