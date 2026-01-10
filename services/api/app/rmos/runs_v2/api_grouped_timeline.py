from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from .batch_grouped_timeline import GroupedTimelinePorts, build_grouped_timeline


router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/batch-timeline-grouped")
def batch_timeline_grouped(
    session_id: str = Query(...),
    batch_label: str = Query(...),
    tool_kind: Optional[str] = Query(None),
    max_nodes: int = Query(2000, ge=1, le=10000),
    include_types: Optional[str] = Query(
        None,
        description="Comma-separated type buckets to include (e.g. spec,plan,decision,toolpaths,execution,job_log,learning_event,other)",
    ),
    collapse_other: bool = Query(
        False,
        description='If true, collapses "other" nodes under the nearest batch parent (anchor).',
    ),
    collapse_other_under: str = Query(
        "auto",
        description='Anchor type for collapsing "other": auto|spec|plan|decision|toolpaths|execution',
    ),
):
    """
    Grouped timeline view: nested (tree-aware) structure + by_type buckets.
    """
    from . import store as runs_store

    ports = GroupedTimelinePorts(
        list_runs_filtered=runs_store.list_runs_filtered,
        get_run=runs_store.get_run,
    )
    include_set = None
    if include_types:
        include_set = {t.strip() for t in include_types.split(",") if t.strip()}
    return build_grouped_timeline(
        ports,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        max_nodes=max_nodes,
        include_types=include_set,
        collapse_other=collapse_other,
        collapse_other_under=collapse_other_under,
    )
