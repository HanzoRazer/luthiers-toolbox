# services/api/app/rmos/schemas_logs_ai.py
"""
Log view schemas for RMOS AI endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .api_contracts import RiskBucket


class AiAttemptLogView(BaseModel):
    """Read-only view of a single AI constraint attempt log entry."""

    run_id: str
    timestamp: datetime

    attempt_index: int
    workflow_mode: str

    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None

    geometry_engine: Optional[str] = None

    score: float
    risk_bucket: RiskBucket
    is_acceptable: bool

    design_version: Optional[str] = None
    ring_count: Optional[int] = None
    notes: Optional[str] = None


class AiRunSummaryLogView(BaseModel):
    """Read-only view of an AI constraint run summary."""

    run_id: str
    timestamp: datetime

    workflow_mode: str
    max_attempts: int
    time_limit_seconds: float

    attempts: int
    success: bool
    reason: str

    selected_score: Optional[float] = None
    selected_risk_bucket: Optional[RiskBucket] = None

    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None

    geometry_engine: Optional[str] = None


class AiLogQueryParams(BaseModel):
    """Backend-side representation of query filters."""

    run_id: Optional[str] = Field(
        default=None, description="Filter by specific run_id (exact match)."
    )
    tool_id: Optional[str] = Field(
        default=None, description="Filter by tool_id (exact match)."
    )
    material_id: Optional[str] = Field(
        default=None, description="Filter by material_id (exact match)."
    )
    workflow_mode: Optional[str] = Field(
        default=None, description="Optional filter by workflow_mode."
    )

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of log entries to return.",
    )


class AiLogKind(BaseModel):
    """Simple wrapper for different kinds of log views."""

    kind: Literal["attempts", "runs"] = "attempts"
