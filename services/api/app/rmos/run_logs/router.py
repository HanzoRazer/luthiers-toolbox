"""
Run Log API endpoints.

Read-only, non-authoritative, safe to expose to ops tooling.

Endpoints:
- GET /api/rmos/run-logs/latest?limit=30  - Get latest entries
- GET /api/rmos/run-logs/export.csv       - Export as CSV
- GET /api/rmos/run-logs/export.json      - Export as JSONL
- GET /api/rmos/run-logs/summary          - Aggregate statistics
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, Field

from .schemas import RunLogEntry
from .exporters import (
    get_latest_entries,
    export_csv_string,
    count_by_risk_level,
    get_entries_by_risk,
    get_entries_with_override,
    read_jsonl,
)

router = APIRouter(prefix="/api/rmos/run-logs", tags=["rmos-run-logs"])


# =============================================================================
# Response Models
# =============================================================================

class RunLogLatestResponse(BaseModel):
    """Response for latest entries endpoint."""
    entries: List[RunLogEntry] = Field(default_factory=list)
    count: int = Field(0)
    limit: int = Field(30)


class RunLogSummaryResponse(BaseModel):
    """Aggregate statistics for run logs."""
    total: int = Field(0)
    by_risk_level: dict = Field(default_factory=dict)
    override_count: int = Field(0)
    last_run_id: Optional[str] = None
    last_run_at: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/latest", response_model=RunLogLatestResponse)
async def get_latest(
    limit: int = Query(30, ge=1, le=500, description="Number of entries to return"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (GREEN, YELLOW, RED)"),
) -> RunLogLatestResponse:
    """
    Get the most recent run log entries.

    Supports optional filtering by risk_level.
    """
    if risk_level:
        entries = get_entries_by_risk(risk_level.upper())
        entries = entries[-limit:] if len(entries) > limit else entries
    else:
        entries = get_latest_entries(limit=limit)

    return RunLogLatestResponse(
        entries=entries,
        count=len(entries),
        limit=limit,
    )


@router.get("/export.csv")
async def export_csv_endpoint(
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Limit entries (default: all)"),
) -> Response:
    """
    Export run log as CSV.

    Returns a downloadable CSV file with all entries (or limited if specified).
    """
    entries = list(read_jsonl())
    if limit:
        entries = entries[-limit:]

    csv_content = export_csv_string(entries)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=run_log.csv"},
    )


@router.get("/export.json")
async def export_json_endpoint(
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Limit entries (default: all)"),
) -> Response:
    """
    Export run log as JSONL (JSON Lines).

    Returns a downloadable JSONL file with all entries (or limited if specified).
    """
    entries = list(read_jsonl())
    if limit:
        entries = entries[-limit:]

    # Build JSONL content
    import json
    lines = []
    for entry in entries:
        lines.append(json.dumps(entry.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")))
    jsonl_content = "\n".join(lines)

    return Response(
        content=jsonl_content,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=run_log.jsonl"},
    )


@router.get("/summary", response_model=RunLogSummaryResponse)
async def get_summary() -> RunLogSummaryResponse:
    """
    Get aggregate statistics for run logs.

    Useful for dashboards and protocol validation.
    """
    entries = list(read_jsonl())

    if not entries:
        return RunLogSummaryResponse(
            total=0,
            by_risk_level={"GREEN": 0, "YELLOW": 0, "RED": 0},
            override_count=0,
        )

    # Count by risk level
    risk_counts = count_by_risk_level()

    # Count overrides
    override_count = sum(1 for e in entries if e.override_applied)

    # Get last run info
    last_entry = entries[-1]

    return RunLogSummaryResponse(
        total=len(entries),
        by_risk_level=risk_counts,
        override_count=override_count,
        last_run_id=last_entry.run_id,
        last_run_at=last_entry.created_at_utc.isoformat() if last_entry.created_at_utc else None,
    )


@router.get("/overrides", response_model=RunLogLatestResponse)
async def get_overrides(
    limit: int = Query(100, ge=1, le=500, description="Number of entries to return"),
) -> RunLogLatestResponse:
    """
    Get runs where an override was applied.

    Useful for audit review of manual interventions.
    """
    entries = get_entries_with_override()
    entries = entries[-limit:] if len(entries) > limit else entries

    return RunLogLatestResponse(
        entries=entries,
        count=len(entries),
        limit=limit,
    )
