"""
Phase 28.5: Risk Bucket Export Router
Phase 28.7: Time-window filtering support

Export detailed bucket data as CSV or JSON files.
"""

import io
import json
from typing import Optional
from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from ..services.compare_risk_bucket_detail import get_bucket_detail


router = APIRouter(prefix="/api/compare", tags=["compare"])


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
