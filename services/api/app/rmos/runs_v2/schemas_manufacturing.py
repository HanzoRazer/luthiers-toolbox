"""
RMOS Manufacturing Candidate Schemas

Product Bundle: Manufacturing candidate records for promoted variants.
"""
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


ManufacturingCandidateStatus = Literal["PROPOSED", "ACCEPTED", "REJECTED"]


class ManufacturingCandidate(BaseModel):
    """Manufacturing candidate record for a promoted variant."""
    candidate_id: str = Field(..., description="Stable ID for this candidate record")
    advisory_id: str = Field(..., description="CAS sha256 (must be in run.advisory_inputs[*].advisory_id)")
    status: ManufacturingCandidateStatus = Field("PROPOSED")
    label: Optional[str] = Field(None, max_length=120, description="Optional human label")
    note: Optional[str] = Field(None, max_length=2000, description="Optional operator note")
    created_at_utc: str
    created_by: Optional[str] = None
    updated_at_utc: str
    updated_by: Optional[str] = None
