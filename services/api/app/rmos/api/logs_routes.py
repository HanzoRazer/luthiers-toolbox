"""
RMOS Logs Routes v2 - Bundle 31.0.27.1 + H2 Hardening

Enhanced logs API with runs_v2 integration for filtered run artifact queries.

H2 Hardening:
- Cursor-based pagination (scales better than offset)
- Server-side filtering (pushed into query)
- Consistent response format with next_cursor
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..runs_v2 import RunStoreV2, get_run
from ..runs_v2.store import query_recent


router = APIRouter(prefix="/logs", tags=["rmos-logs"])


# Adapter to support multiple store interfaces
def _load_recent_run_dicts(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Load recent runs as dicts using the best available method.

    Tries multiple store APIs for compatibility.
    """
    store = RunStoreV2()

    # Try list_recent first (if it exists)
    fn = getattr(store, "list_recent", None)
    if callable(fn):
        items = fn(limit=limit)
        return [r.model_dump() if hasattr(r, 'model_dump') else dict(r) for r in items]

    # Fall back to list_runs
    runs = store.list_runs(limit=limit)
    return [r.model_dump() for r in runs]


def _match(filter_val: Optional[str], actual: Optional[str]) -> bool:
    """Check if filter matches (None filter = match all)."""
    if filter_val is None:
        return True
    return str(actual).upper() == str(filter_val).upper()


class RunLogEntry(BaseModel):
    """Lightweight run log entry for list view."""
    run_id: str
    created_at_utc: str
    mode: str
    tool_id: str
    status: str
    risk_level: str
    score: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    source: Optional[str] = None


class RecentLogsResponse(BaseModel):
    """Response for recent logs query (legacy offset-based)."""
    entries: List[RunLogEntry]
    total: int
    filters_applied: Dict[str, Optional[str]]


class RecentLogsResponseV2(BaseModel):
    """
    Response for recent logs query (H2 cursor-based).

    Uses cursor pagination for better scalability.
    """
    entries: List[RunLogEntry]
    next_cursor: Optional[str] = None
    has_more: bool = False
    filters_applied: Dict[str, Optional[str]] = Field(default_factory=dict)


class RunDetailsResponse(BaseModel):
    """Full run artifact details."""
    run_id: str
    created_at_utc: str
    mode: str
    tool_id: str
    status: str
    request_summary: Dict[str, Any]
    feasibility: Dict[str, Any]
    decision: Dict[str, Any]
    hashes: Dict[str, Any]
    outputs: Dict[str, Any]
    meta: Dict[str, Any]


@router.get("/recent", response_model=RecentLogsResponse)
async def logs_recent(
    mode: Optional[str] = Query(None, description="Filter by mode (e.g., art_studio, saw)"),
    tool_id: Optional[str] = Query(None, description="Filter by tool_id"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: GREEN, YELLOW, RED, ERROR, UNKNOWN"),
    status: Optional[str] = Query(None, description="Filter by status: OK, BLOCKED, ERROR"),
    source: Optional[str] = Query(None, description="Filter by source in meta"),
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
):
    """
    Get recent RMOS run logs with filtering.

    Returns lightweight entries for list display.
    Filters are applied in-memory after loading from store.
    """
    # Load all recent runs
    items = _load_recent_run_dicts(limit=limit * 2)  # Over-fetch to account for filtering

    # Apply filters
    filtered = []
    for r in items:
        if not _match(mode, r.get("mode")):
            continue
        if not _match(tool_id, r.get("tool_id")):
            continue
        if not _match(status, r.get("status")):
            continue

        # Risk level from decision
        decision = r.get("decision", {})
        actual_risk = decision.get("risk_level", "UNKNOWN")
        if not _match(risk_level, actual_risk):
            continue

        # Source from meta
        meta = r.get("meta", {})
        actual_source = meta.get("source") or meta.get("workflow")
        if source and not _match(source, actual_source):
            continue

        # Build log entry
        created = r.get("created_at_utc")
        if hasattr(created, 'isoformat'):
            created = created.isoformat()

        entry = RunLogEntry(
            run_id=r.get("run_id", ""),
            created_at_utc=str(created),
            mode=r.get("mode", ""),
            tool_id=r.get("tool_id", ""),
            status=r.get("status", ""),
            risk_level=actual_risk,
            score=decision.get("score"),
            warnings=decision.get("warnings", []),
            source=actual_source,
        )
        filtered.append(entry)

        if len(filtered) >= limit:
            break

    return RecentLogsResponse(
        entries=filtered,
        total=len(filtered),
        filters_applied={
            "mode": mode,
            "tool_id": tool_id,
            "risk_level": risk_level,
            "status": status,
            "source": source,
        },
    )


@router.get("/recent/v2", response_model=RecentLogsResponseV2)
async def logs_recent_v2(
    cursor: Optional[str] = Query(None, description="Pagination cursor from previous response"),
    mode: Optional[str] = Query(None, description="Filter by mode (e.g., art_studio, saw)"),
    tool_id: Optional[str] = Query(None, description="Filter by tool_id"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: GREEN, YELLOW, RED, ERROR, UNKNOWN"),
    status: Optional[str] = Query(None, description="Filter by status: OK, BLOCKED, ERROR"),
    source: Optional[str] = Query(None, description="Filter by source in meta"),
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
):
    """
    Get recent RMOS run logs with cursor-based pagination.

    H2 Hardening: Uses server-side filtering and cursor pagination for scalability.

    Cursor format: "<created_at_utc>|<run_id>"
    Pass next_cursor from response to get the next page.
    """
    result = query_recent(
        limit=limit,
        cursor=cursor,
        mode=mode,
        tool_id=tool_id,
        risk_level=risk_level,
        status=status,
        source=source,
    )

    items = result.get("items", [])
    next_cursor = result.get("next_cursor")

    # Convert to RunLogEntry
    entries: List[RunLogEntry] = []
    for r in items:
        decision = r.get("decision", {})
        if hasattr(decision, 'model_dump'):
            decision = decision.model_dump()

        meta = r.get("meta", {})
        actual_risk = decision.get("risk_level") or decision.get("risk_bucket") or "UNKNOWN"
        actual_source = meta.get("source") or meta.get("workflow")

        created = r.get("created_at_utc")
        if hasattr(created, 'isoformat'):
            created = created.isoformat()

        entry = RunLogEntry(
            run_id=r.get("run_id", ""),
            created_at_utc=str(created or ""),
            mode=r.get("mode", ""),
            tool_id=r.get("tool_id", ""),
            status=r.get("status", ""),
            risk_level=actual_risk,
            score=decision.get("score"),
            warnings=decision.get("warnings", []),
            source=actual_source,
        )
        entries.append(entry)

    return RecentLogsResponseV2(
        entries=entries,
        next_cursor=next_cursor,
        has_more=bool(next_cursor),
        filters_applied={
            "mode": mode,
            "tool_id": tool_id,
            "risk_level": risk_level,
            "status": status,
            "source": source,
        },
    )


@router.get("/{run_id}", response_model=RunDetailsResponse)
async def logs_get_run(run_id: str):
    """
    Get full details for a single run artifact.

    Returns complete run data including request, feasibility, decision, and outputs.
    """
    artifact = get_run(run_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Convert datetime to string
    created = artifact.created_at_utc
    if hasattr(created, 'isoformat'):
        created = created.isoformat()

    return RunDetailsResponse(
        run_id=artifact.run_id,
        created_at_utc=str(created),
        mode=artifact.mode,
        tool_id=artifact.tool_id,
        status=artifact.status,
        request_summary=artifact.request_summary,
        feasibility=artifact.feasibility,
        decision=artifact.decision.model_dump() if hasattr(artifact.decision, 'model_dump') else dict(artifact.decision),
        hashes=artifact.hashes.model_dump() if hasattr(artifact.hashes, 'model_dump') else dict(artifact.hashes),
        outputs=artifact.outputs.model_dump() if hasattr(artifact.outputs, 'model_dump') else dict(artifact.outputs),
        meta=artifact.meta,
    )
