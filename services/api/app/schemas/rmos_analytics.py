"""
RMOS Analytics Schemas (MM-4)

Lane-based risk analytics with material fragility awareness.
Aggregates job metadata (from MM-2) into global and per-lane statistics.
"""

from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel


RiskGrade = Literal["GREEN", "YELLOW", "RED", "unknown"]
Lane = Literal["safe", "tuned_v1", "tuned_v2", "experimental", "archived", "unknown"]


class MaterialRiskSummary(BaseModel):
    """Global material risk statistics."""
    material_type: str
    job_count: int
    avg_fragility: Optional[float] = None
    worst_fragility: Optional[float] = None


class LaneRiskSummary(BaseModel):
    """Per-lane risk and material statistics."""
    lane: Lane
    job_count: int
    avg_risk_score: Optional[float] = None
    grade_counts: dict  # { "GREEN": int, "YELLOW": int, "RED": int, "unknown": int }

    # MM-4 additions:
    avg_fragility_score: Optional[float] = None
    dominant_material_types: List[str] = []


class GlobalRiskSummary(BaseModel):
    """Global RMOS risk statistics."""
    total_jobs: int
    total_presets: int
    avg_risk_score: Optional[float] = None
    grade_counts: dict

    # MM-4 additions:
    overall_fragility_score: Optional[float] = None
    material_risk_by_type: List[MaterialRiskSummary] = []


class RecentRunItem(BaseModel):
    """Recent job run with risk and fragility metadata."""
    job_id: str
    preset_id: Optional[str] = None
    created_at: str
    lane: Lane
    job_type: str
    risk_grade: RiskGrade
    doc_grade: Optional[RiskGrade] = None
    gantry_grade: Optional[RiskGrade] = None

    # MM-4: worst fragility per job
    worst_fragility_score: Optional[float] = None


class LaneTransition(BaseModel):
    """Lane promotion/rollback transition."""
    from_lane: Lane
    to_lane: Lane
    count: int


class LaneAnalyticsResponse(BaseModel):
    """Complete lane analytics response."""
    global_summary: GlobalRiskSummary
    lane_summaries: List[LaneRiskSummary]
    recent_runs: List[RecentRunItem]
    lane_transitions: List[LaneTransition]

    # MM-4: explicit global material breakdown
    material_risk_global: List[MaterialRiskSummary] = []


class RiskTimelinePoint(BaseModel):
    """Single point in risk timeline."""
    job_id: str
    created_at: str
    lane: Lane
    risk_grade: RiskGrade
    risk_score: Optional[float] = None
    worst_fragility_score: Optional[float] = None


class RiskTimelineResponse(BaseModel):
    """Risk timeline for a preset."""
    preset_id: str
    points: List[RiskTimelinePoint]
