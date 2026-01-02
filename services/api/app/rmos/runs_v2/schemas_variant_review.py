"""
RMOS Variant Review Schemas

Product Bundle: Variant Review, Rating, and Promotion
Pydantic models for API requests and responses.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, Literal, List
from pydantic import BaseModel, Field, field_validator

RoleName = Literal["admin", "operator", "engineer", "viewer", "anonymous"]

# Variant triage status (computed server-side)
VariantStatus = Literal["NEW", "REVIEWED", "PROMOTED", "REJECTED"]

# Risk levels for quick triage (GREEN = safe, YELLOW = caution, RED = blocked)
RiskLevel = Literal["GREEN", "YELLOW", "RED"]


class AdvisoryVariantSummary(BaseModel):
    """Summary of an advisory variant for listing."""
    advisory_id: str
    mime: str
    filename: str
    size_bytes: int
    preview_blocked: bool = False
    preview_block_reason: Optional[str] = None

    # Review state
    rating: Optional[int] = None
    notes: Optional[str] = None
    promoted: bool = False

    # === NEW: Status & Risk (Variant Status & Filters bundle) ===
    status: VariantStatus = "NEW"
    risk_level: RiskLevel = "GREEN"
    created_at_utc: Optional[str] = None
    updated_at_utc: Optional[str] = None
    rejected: bool = False
    rejection_reason: Optional[str] = None

    # === NEW: Rejection details (Undo Reject bundle) ===
    rejection_reason_code: Optional[str] = None
    rejection_reason_detail: Optional[str] = None
    rejection_operator_note: Optional[str] = None
    rejected_at_utc: Optional[str] = None


class AdvisoryVariantListResponse(BaseModel):
    """Response for listing advisory variants."""
    run_id: str
    count: int
    items: List[AdvisoryVariantSummary]


class AdvisoryVariantReviewRequest(BaseModel):
    """Request to save a review for an advisory variant."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=4000)

    @field_validator("notes")
    @classmethod
    def _trim_notes(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class AdvisoryVariantReviewRecord(BaseModel):
    """Record of a saved review."""
    advisory_id: str
    rating: Optional[int] = None
    notes: Optional[str] = None
    updated_at_utc: str
    updated_by: Optional[str] = None


class PromoteVariantRequest(BaseModel):
    """Request to promote an advisory variant to manufacturing."""
    label: Optional[str] = Field(None, max_length=120)
    note: Optional[str] = Field(None, max_length=2000)


class PromoteVariantResponse(BaseModel):
    """Response from promoting an advisory variant."""
    run_id: str
    advisory_id: str
    decision: Literal["ALLOW", "BLOCK"]
    risk_level: Literal["GREEN", "YELLOW", "RED"]
    score: float
    reason: str
    manufactured_candidate_id: Optional[str] = None
    message: Optional[str] = None


# =============================================================================
# Bulk Promote (Product Bundle)
# =============================================================================

class BulkPromoteRequest(BaseModel):
    """Request body for bulk-promoting multiple advisory variants."""
    advisory_ids: List[str] = Field(..., min_length=1, max_length=100)
    label: Optional[str] = Field(None, max_length=120)
    note: Optional[str] = Field(None, max_length=2000)


class BulkPromoteItemResult(BaseModel):
    """Result of promoting a single advisory variant."""
    advisory_id: str
    success: bool
    decision: Optional[Literal["ALLOW", "BLOCK"]] = None
    risk_level: Optional[Literal["GREEN", "YELLOW", "RED"]] = None
    score: Optional[float] = None
    reason: Optional[str] = None
    manufactured_candidate_id: Optional[str] = None
    error: Optional[str] = None


class BulkPromoteResponse(BaseModel):
    """Response from bulk-promoting advisory variants."""
    run_id: str
    total: int
    succeeded: int
    failed: int
    blocked: int
    results: List[BulkPromoteItemResult]
