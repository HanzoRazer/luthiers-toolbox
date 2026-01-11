# services/api/app/rmos/runs_v2/schemas_manufacturing_ops.py
"""
Manufacturing Candidate Operations Schemas.

Pydantic models for the candidate queue: list, decide, export.

Bundle C: Manufacturing Readiness & Decision Control
- decision: RiskLevel | null (null = NEEDS_DECISION)
- GREEN required for export
- Append-only decision_history for audit
"""

from __future__ import annotations

from typing import Optional, Literal, List
from pydantic import BaseModel, Field, field_validator

# Canonical decision types (Bundle C spine-lock)
RiskLevel = Literal["GREEN", "YELLOW", "RED"]
ManufacturingDecisionInput = Optional[RiskLevel]  # null clears decision

# Legacy compat (status derived from decision)
ManufacturingStatus = Literal["PROPOSED", "ACCEPTED", "REJECTED"]


class DecisionHistoryItem(BaseModel):
    """Single decision history entry (append-only audit record)."""

    decision: RiskLevel
    note: Optional[str] = None
    decided_at_utc: str
    decided_by: Optional[str] = None


class CandidateListItem(BaseModel):
    """Single candidate in the queue (Bundle C enhanced)."""

    candidate_id: str
    advisory_id: str

    # Bundle C decision protocol
    decision: Optional[RiskLevel] = None  # null = NEEDS_DECISION
    decision_note: Optional[str] = None
    decided_at_utc: Optional[str] = None
    decided_by: Optional[str] = None
    decision_history: Optional[List[DecisionHistoryItem]] = None

    # Legacy compat (derived from decision)
    status: ManufacturingStatus = "PROPOSED"

    # Metadata
    label: Optional[str] = None
    note: Optional[str] = None  # promotion note (distinct from decision_note)
    score: Optional[float] = None
    risk_level: Optional[str] = None  # bind-time risk assessment

    created_at_utc: str
    created_by: Optional[str] = None
    updated_at_utc: str
    updated_by: Optional[str] = None


class CandidateListResponse(BaseModel):
    """Response for listing manufacturing candidates."""

    run_id: str
    count: int
    items: list[CandidateListItem]


class CandidateDecisionRequest(BaseModel):
    """Request to set decision on a candidate (Bundle C).

    decision:
      - null: clear decision (NEEDS_DECISION)
      - GREEN: OK to manufacture
      - YELLOW: caution/hold
      - RED: do not manufacture
    """

    decision: ManufacturingDecisionInput = None
    note: Optional[str] = Field(None, max_length=2000)
    decided_by: Optional[str] = Field(None, max_length=200)  # operator identity

    @field_validator("note")
    @classmethod
    def _trim(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class CandidateDecisionResponse(BaseModel):
    """Response after deciding on a candidate (Bundle C).

    Returns full decision state including history for UI sync.
    """

    run_id: str
    candidate_id: str
    advisory_id: str

    # Bundle C decision state
    decision: Optional[RiskLevel] = None
    decision_note: Optional[str] = None
    decided_at_utc: Optional[str] = None
    decided_by: Optional[str] = None
    decision_history: Optional[List[DecisionHistoryItem]] = None

    # Legacy compat (derived)
    status: ManufacturingStatus = "PROPOSED"

    updated_at_utc: str
    updated_by: Optional[str] = None
