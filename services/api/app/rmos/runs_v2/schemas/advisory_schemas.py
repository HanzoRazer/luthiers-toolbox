# services/api/app/rmos/runs_v2/schemas/advisory_schemas.py
"""
Advisory Ledger Plane Schemas

These schemas govern the review/promote lifecycle for AI-generated advisories
attached to RMOS runs. State lives ONLY in the run ledger.

IMPORTANT: Keep vocabulary aligned with runs_v2/schemas.py (UI + SDK lockpoints).
The canonical AdvisoryInputRef model lives in schemas.py; these are API payloads.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

VariantStatus = Literal["NEW", "REVIEWED", "PROMOTED", "REJECTED"]
RiskLevel = Literal["GREEN", "YELLOW", "RED", "UNKNOWN", "ERROR"]
RejectReasonCode = Literal[
    "GEOMETRY_UNSAFE",
    "TEXT_REQUIRES_OUTLINE",
    "AESTHETIC",
    "DUPLICATE",
    "OTHER",
]


class AdvisoryAttachRequest(BaseModel):
    advisory_id: str = Field(..., description="Authoritative linkage id (CAS sha256)")
    kind: Literal["advisory", "explanation", "note"] = Field("advisory")
    mime: Optional[str] = None
    filename: Optional[str] = None
    size_bytes: Optional[int] = None


class AdvisoryAttachResponse(BaseModel):
    run_id: str
    advisory_id: str
    attached: bool
    message: str = ""


class AdvisoryVariantReviewRequest(BaseModel):
    # Unified review surface (reject/undo/re-rate/notes/status)
    rejected: Optional[bool] = None
    rejection_reason_code: Optional[RejectReasonCode] = None
    rejection_reason_detail: Optional[str] = None
    rejection_operator_note: Optional[str] = None
    status: Optional[VariantStatus] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    risk_level: Optional[RiskLevel] = None


class AdvisoryVariantReviewRecord(BaseModel):
    run_id: str
    advisory_id: str
    status: VariantStatus
    rejected: bool = False
    rating: Optional[int] = None
    notes: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    rejection_reason_code: Optional[RejectReasonCode] = None
    rejection_reason_detail: Optional[str] = None
    rejection_operator_note: Optional[str] = None
    rejected_at_utc: Optional[str] = None
    updated_at_utc: Optional[str] = None


class BulkReviewAdvisoryVariantsRequest(BaseModel):
    advisory_ids: List[str] = Field(..., min_length=1)
    rejected: Optional[bool] = None
    rejection_reason_code: Optional[RejectReasonCode] = None
    rejection_reason_detail: Optional[str] = None
    rejection_operator_note: Optional[str] = None
    status: Optional[VariantStatus] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    risk_level: Optional[RiskLevel] = None


class BulkReviewAdvisoryVariantsResponse(BaseModel):
    updated_count: int
    advisory_ids: List[str]


class PromoteVariantResponse(BaseModel):
    run_id: str
    advisory_id: str
    promoted: bool
    promoted_candidate_id: Optional[str] = None
