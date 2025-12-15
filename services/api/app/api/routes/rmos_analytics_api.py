"""
RMOS Lane Analytics API Router (MM-4)

Endpoints for material-aware risk analytics.
"""

from fastapi import APIRouter, HTTPException

from app.core.rmos_analytics import (
    compute_lane_analytics,
    compute_risk_timeline_for_preset,
)
from app.schemas.rmos_analytics import (
    LaneAnalyticsResponse,
    RiskTimelineResponse,
)

router = APIRouter()


@router.get("/lane-analytics", response_model=LaneAnalyticsResponse)
def get_lane_analytics(limit_recent: int = 200):
    """
    Get material-aware lane analytics.
    
    Returns:
    - Global risk summary with overall fragility score
    - Per-lane risk and material statistics
    - Recent runs with fragility scores
    - Lane transitions (promotions/rollbacks)
    - Global material risk breakdown
    
    Query params:
    - limit_recent: Max recent runs to return (default 200)
    """
    try:
        return compute_lane_analytics(limit_recent=limit_recent)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics computation failed: {str(e)}")


@router.get("/risk-timeline/{preset_id}", response_model=RiskTimelineResponse)
def get_risk_timeline(preset_id: str, limit: int = 200):
    """
    Get risk timeline for a specific preset.
    
    Returns chronological sequence of job runs with risk grades and fragility scores.
    
    Path params:
    - preset_id: Preset ID to analyze
    
    Query params:
    - limit: Max timeline points to return (default 200)
    """
    try:
        return compute_risk_timeline_for_preset(preset_id=preset_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline computation failed: {str(e)}")
