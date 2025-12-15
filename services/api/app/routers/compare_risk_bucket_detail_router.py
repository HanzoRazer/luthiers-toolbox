"""
Phase 28.4: Risk Bucket Detail Router

API endpoint to retrieve individual entries for a specific risk bucket.
"""

from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ..services.compare_risk_bucket_detail import get_bucket_detail


router = APIRouter(prefix="/api/compare", tags=["compare"])


class BucketDetailEntry(BaseModel):
    """Individual compare history entry within a bucket."""
    ts: str = Field(..., description="ISO timestamp")
    lane: str = Field(..., description="Lane name (rosette, adaptive, etc.)")
    preset: str = Field(..., description="Post-processor preset (GRBL, Mach4, etc.)")
    job_id: str = Field(..., description="Unique job identifier")
    added_paths: int = Field(..., description="Number of added paths")
    removed_paths: int = Field(..., description="Number of removed paths")
    unchanged_paths: int = Field(..., description="Number of unchanged paths")


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
