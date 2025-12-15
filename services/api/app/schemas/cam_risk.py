# services/api/app/schemas/cam_risk.py
"""
CAM Risk Analytics Schema - Phase 18.0

Models for job risk reporting and timeline tracking.
Enables post-simulation risk analysis with severity tracking.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskIssue(BaseModel):
    """Single risk issue from simulation."""
    index: int
    type: str
    severity: str  # info, low, medium, high, critical
    x: float
    y: float
    z: Optional[float] = None
    extra_time_s: Optional[float] = None
    note: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class RiskAnalytics(BaseModel):
    """Computed risk analytics from issues."""
    total_issues: int
    severity_counts: Dict[str, int]
    risk_score: float
    total_extra_time_s: float
    total_extra_time_human: str


class RiskReportIn(BaseModel):
    """Incoming risk report submission."""
    job_id: str = Field(..., description="User/job chosen ID, e.g., pipeline run ID or filename")
    pipeline_id: Optional[str] = Field(
        default=None, description="Optional pipeline definition/flow ID"
    )
    op_id: Optional[str] = Field(
        default=None, description="Which op produced these issues (e.g. 'rosette_sim')"
    )
    machine_profile_id: Optional[str] = None
    post_preset: Optional[str] = None

    design_source: Optional[str] = Field(
        default=None, description="e.g., 'dxf', 'svg', 'blueprint'"
    )
    design_path: Optional[str] = Field(
        default=None, description="Path to DXF/SVG/blueprint if known"
    )

    issues: List[RiskIssue] = Field(default_factory=list)
    analytics: RiskAnalytics


class RiskReportOut(BaseModel):
    """Stored risk report with metadata."""
    id: str
    created_at: datetime
    job_id: str
    pipeline_id: Optional[str]
    op_id: Optional[str]
    machine_profile_id: Optional[str]
    post_preset: Optional[str]
    design_source: Optional[str]
    design_path: Optional[str]
    issues: List[RiskIssue]
    analytics: RiskAnalytics

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RiskReportSummary(BaseModel):
    """Lightweight summary for timeline browsing."""
    id: str
    created_at: datetime
    job_id: str
    pipeline_id: Optional[str]
    op_id: Optional[str]
    machine_profile_id: Optional[str]
    post_preset: Optional[str]
    
    # Analytics summary
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    risk_score: float
    total_extra_time_s: float

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
