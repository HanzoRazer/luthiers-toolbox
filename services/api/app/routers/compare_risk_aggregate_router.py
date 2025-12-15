# services/api/app/routers/compare_risk_aggregate_router.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.compare_risk_aggregate import aggregate_compare_history

router = APIRouter(prefix="/api/compare", tags=["compare"])


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
