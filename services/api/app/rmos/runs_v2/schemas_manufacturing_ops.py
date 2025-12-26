# services/api/app/rmos/runs_v2/schemas_manufacturing_ops.py
"""
Manufacturing Candidate Operations Schemas.

Pydantic models for the candidate queue: list, approve/reject, export.
"""

from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

ManufacturingDecision = Literal["ACCEPT", "REJECT"]


class CandidateListItem(BaseModel):
    """Single candidate in the queue."""

    candidate_id: str
    advisory_id: str
    status: Literal["PROPOSED", "ACCEPTED", "REJECTED"]
    label: Optional[str] = None
    note: Optional[str] = None
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
    """Request to approve or reject a candidate."""

    decision: ManufacturingDecision
    note: Optional[str] = Field(None, max_length=2000)

    @field_validator("note")
    @classmethod
    def _trim(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class CandidateDecisionResponse(BaseModel):
    """Response after deciding on a candidate."""

    run_id: str
    candidate_id: str
    advisory_id: str
    status: Literal["ACCEPTED", "REJECTED"]
    updated_at_utc: str
    updated_by: Optional[str] = None
