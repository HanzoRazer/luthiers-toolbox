"""
Compare Risk Router

Risk aggregation, bucket detail, and export operations.

Migrated from:
    - routers/compare_risk_aggregate_router.py
    - routers/compare_risk_bucket_detail_router.py
    - routers/compare_risk_bucket_export_router.py

Endpoints:
    GET /risk_aggregate      - Get lane+preset risk aggregates
    GET /risk_bucket_detail  - Get individual bucket entries
    GET /risk_bucket_export  - Export bucket data as CSV/JSON
"""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, Field

from ....services.compare_risk_aggregate import aggregate_compare_history
from ....services.compare_risk_bucket_detail import get_bucket_detail

router = APIRouter()


# ---- Models ----


class RiskAggregateBucket(BaseModel):
    lane: str = Field(..., description="Compare lane, e.g. 'rosette', 'adaptive', 'relief', 'pipeline'")
    preset: str = Field(..., description="Preset name or '(none)'")
    count: int = Field(..., description="Number of compare entries in this bucket")
    avg_added: float = Field(..., description="Average added_paths")
    avg_removed: float = Field(..., description="Average removed_paths")
    avg_unchanged: float = Field(..., description="Average unchanged_paths")
    risk_score: float = Field(..., description="Numeric risk score")
    risk_label: str = Field(..., description="Risk label: Low / Medium / High / Extreme")
    added_series: list[float] = Field(..., description="Time-ordered added_paths series")
    removed_series: list[float] = Field(..., description="Time-ordered removed_paths series")


class BucketDetailEntry(BaseModel):
    """Individual compare history entry within a bucket."""
    ts: str = Field(..., description="ISO timestamp")
    lane: str = Field(..., description="Lane name (rosette, adaptive, etc.)")
    preset: str = Field(..., description="Post-processor preset (GRBL, Mach4, etc.)")
    job_id: str = Field(..., description="Unique job identifier")
    added_paths: int = Field(..., description="Number of added paths")
    removed_paths: int = Field(..., description="Number of removed paths")
    unchanged_paths: int = Field(..., description="Number of unchanged paths")


# ---- Endpoints ----


@router.get("/risk_aggregate", response_model=List[RiskAggregateBucket])
def get_risk_aggregate(
    since: Optional[str] = Query(None, description="ISO timestamp: only include entries >= this time"),
    until: Optional[str] = Query(None, description="ISO timestamp: only include entries < this time")
) -> List[RiskAggregateBucket]:
    """
    Return lane+preset aggregates for the compare history log.

    This is the server-side counterpart to the Cross-Lab Preset Risk Dashboard.

    Phase 28.7: Time-windowing support via `since` and `until` parameters.
    """
    data = aggregate_compare_history(since=since, until=until)
    return [RiskAggregateBucket(**row) for row in data]


@router.get("/risk_bucket_detail", response_model=List[BucketDetailEntry])
def get_risk_bucket_detail(
    lane: Optional[str] = Query(None, description="Filter by lane"),
    preset: Optional[str] = Query(None, description="Filter by preset"),
    since: Optional[str] = Query(None, description="ISO timestamp: only include entries >= this time"),
    until: Optional[str] = Query(None, description="ISO timestamp: only include entries < this time")
):
    """
    Get detailed individual entries for a specific risk bucket.

    Phase 28.4: Bucket detail retrieval
    Phase 28.7: Time-window filtering via `since` and `until` parameters

    Query Parameters:
        - lane: Filter by lane (optional)
        - preset: Filter by preset (optional)
        - since: ISO timestamp filter (optional)
        - until: ISO timestamp filter (optional)

    Returns:
        List of individual compare history entries sorted chronologically.

    Examples:
        GET /api/compare/risk_bucket_detail?lane=rosette&preset=GRBL
        GET /api/compare/risk_bucket_detail?lane=adaptive
        GET /api/compare/risk_bucket_detail?since=2025-11-12T00:00:00
        GET /api/compare/risk_bucket_detail  (all entries)
    """
    entries = get_bucket_detail(lane=lane, preset=preset, since=since, until=until)
    return entries


@router.get("/risk_bucket_export")
def export_risk_bucket(
    format: str = Query("csv", regex="^(csv|json)$", description="Export format: csv or json"),
    lane: Optional[str] = Query(None, description="Filter by lane"),
    preset: Optional[str] = Query(None, description="Filter by preset"),
    since: Optional[str] = Query(None, description="ISO timestamp: only include entries >= this time"),
    until: Optional[str] = Query(None, description="ISO timestamp: only include entries < this time")
):
    """
    Export detailed bucket entries as CSV or JSON file.

    Phase 28.7: Added time-window filtering via `since` and `until` parameters.

    Query Parameters:
        - format: 'csv' or 'json' (default: csv)
        - lane: Filter by lane (optional)
        - preset: Filter by preset (optional)
        - since: ISO timestamp filter (optional)
        - until: ISO timestamp filter (optional)

    Returns:
        File download (CSV or JSON) with appropriate Content-Disposition header.

    Examples:
        GET /api/compare/risk_bucket_export?lane=rosette&preset=GRBL&format=csv
        GET /api/compare/risk_bucket_export?format=json  (all entries)
        GET /api/compare/risk_bucket_export?since=2025-11-12T00:00:00&format=csv
    """
    # Get filtered entries (now with time-window support)
    entries = get_bucket_detail(lane=lane, preset=preset, since=since, until=until)

    # Build filename
    filename_parts = ["risk_bucket"]
    if lane:
        filename_parts.append(lane)
    if preset:
        filename_parts.append(preset)

    if format == "csv":
        # Generate CSV
        filename = "_".join(filename_parts) + ".csv"
        csv_content = _generate_csv(entries)

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    else:  # json
        # Generate JSON
        filename = "_".join(filename_parts) + ".json"
        json_content = json.dumps(entries, indent=2)

        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )


def _generate_csv(entries: list) -> str:
    """Generate CSV content from entries."""
    if not entries:
        return "ts,lane,preset,job_id,added_paths,removed_paths,unchanged_paths\n"

    # CSV header
    csv_lines = ["ts,lane,preset,job_id,added_paths,removed_paths,unchanged_paths"]

    # CSV rows
    for entry in entries:
        row = [
            entry.get("ts", ""),
            entry.get("lane", ""),
            entry.get("preset", ""),
            entry.get("job_id", ""),
            str(entry.get("added_paths", 0)),
            str(entry.get("removed_paths", 0)),
            str(entry.get("unchanged_paths", 0))
        ]
        # Escape commas and quotes in fields
        row = [f'"{field}"' if ',' in field or '"' in field else field for field in row]
        csv_lines.append(",".join(row))

    return "\n".join(csv_lines)
