# services/api/app/rmos/api/log_routes.py
"""
RMOS Logs API routes.

Provides endpoints for viewing and exporting RMOS feasibility event logs.
Supports filtering by source, mode, and risk_bucket.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from ..api_contracts import RiskBucket
from ..logs import (
    RmosLogEntry,
    RosetteDesignSnapshot,
    get_recent_logs,
    logs_to_csv,
    clear_logs,
)

router = APIRouter(tags=["RMOS Logs"])


class LogEntryResponse(BaseModel):
    """Single log entry in API response."""
    
    id: int
    timestamp: str  # ISO format
    source: str
    mode: Optional[str]
    
    # Design snapshot
    design: Dict[str, Any]
    design_outer_diameter_mm: float
    design_inner_diameter_mm: float
    ring_count: int
    
    # Feasibility
    overall_score: float
    risk_bucket: str
    estimated_cut_time_min: float
    material_efficiency: float
    
    # Context
    material_id: Optional[str]
    tool_id: Optional[str]
    machine_profile_id: Optional[str]
    
    # Warnings
    warnings: List[str]


class RmosLogListResponse(BaseModel):
    """Response for log listing."""
    
    entries: List[LogEntryResponse]
    total: int = Field(..., description="Number of entries returned")


def _entry_to_response(entry: RmosLogEntry) -> LogEntryResponse:
    """Convert internal log entry to API response format."""
    
    # Convert design to dict
    if hasattr(entry.design, 'dict'):
        design_dict = entry.design.dict()
    elif hasattr(entry.design, 'model_dump'):
        design_dict = entry.design.model_dump()
    else:
        design_dict = {
            "outer_diameter_mm": entry.design.outer_diameter_mm,
            "inner_diameter_mm": entry.design.inner_diameter_mm,
            "ring_count": entry.design.ring_count,
            "ring_params": entry.design.ring_params,
            "depth_mm": entry.design.depth_mm,
        }
    
    # Convert risk bucket to string
    risk_str = entry.risk_bucket.value if hasattr(entry.risk_bucket, 'value') else str(entry.risk_bucket)
    
    return LogEntryResponse(
        id=entry.id,
        timestamp=entry.timestamp.isoformat(),
        source=entry.source,
        mode=entry.mode,
        design=design_dict,
        design_outer_diameter_mm=entry.design_outer_diameter_mm,
        design_inner_diameter_mm=entry.design_inner_diameter_mm,
        ring_count=entry.ring_count,
        overall_score=entry.overall_score,
        risk_bucket=risk_str,
        estimated_cut_time_min=entry.estimated_cut_time_min,
        material_efficiency=entry.material_efficiency,
        material_id=entry.material_id,
        tool_id=entry.tool_id,
        machine_profile_id=entry.machine_profile_id,
        warnings=entry.warnings,
    )


@router.get("/recent", response_model=RmosLogListResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=500, description="Maximum entries to return"),
    source: Optional[str] = Query(None, description="Filter by source"),
    mode: Optional[str] = Query(None, description="Filter by workflow mode"),
    risk_bucket: Optional[str] = Query(None, description="Filter by risk: GREEN, YELLOW, RED"),
) -> RmosLogListResponse:
    """
    Get recent RMOS feasibility event logs.
    
    Returns logs newest-first with optional filtering.
    
    Filters:
    - source: Match exact source string (e.g., 'constraint_search')
    - mode: Match workflow mode (e.g., 'design_first')
    - risk_bucket: Match risk level (GREEN, YELLOW, RED)
    """
    # Convert risk_bucket string to enum if provided
    risk_enum: Optional[RiskBucket] = None
    if risk_bucket:
        try:
            risk_enum = RiskBucket(risk_bucket.upper())
        except ValueError:
            pass  # Invalid risk bucket, ignore filter
    
    entries = get_recent_logs(
        limit=limit,
        source=source,
        mode=mode,
        risk_bucket=risk_enum,
    )
    
    return RmosLogListResponse(
        entries=[_entry_to_response(e) for e in entries],
        total=len(entries),
    )


@router.get(
    "/export",
    response_class=PlainTextResponse,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV export of log entries"
        }
    }
)
async def export_logs_csv(
    limit: int = Query(100, ge=1, le=500, description="Maximum entries to export"),
    source: Optional[str] = Query(None, description="Filter by source"),
    mode: Optional[str] = Query(None, description="Filter by workflow mode"),
    risk_bucket: Optional[str] = Query(None, description="Filter by risk: GREEN, YELLOW, RED"),
) -> PlainTextResponse:
    """
    Export RMOS logs as CSV for spreadsheet analysis.
    
    Returns text/csv response that can be saved directly.
    Note: Full design JSON is not included in CSV export.
    """
    # Convert risk_bucket string to enum if provided
    risk_enum: Optional[RiskBucket] = None
    if risk_bucket:
        try:
            risk_enum = RiskBucket(risk_bucket.upper())
        except ValueError:
            pass
    
    entries = get_recent_logs(
        limit=limit,
        source=source,
        mode=mode,
        risk_bucket=risk_enum,
    )
    
    csv_content = logs_to_csv(entries)
    
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=rmos_logs.csv"
        }
    )


@router.delete("/clear")
async def clear_all_logs() -> Dict[str, Any]:
    """
    Clear all log entries from the in-memory buffer.
    
    Use with caution - this cannot be undone.
    """
    count = clear_logs()
    return {
        "cleared": count,
        "message": f"Cleared {count} log entries"
    }
