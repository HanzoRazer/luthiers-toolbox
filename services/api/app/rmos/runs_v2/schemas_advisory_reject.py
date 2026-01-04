"""
Schemas for advisory variant rejection.

Reason codes are a tight vocabulary - add codes later without breaking old clients.
"""
from __future__ import annotations

from typing import Literal, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# Keep this tight + stable. Add codes later without breaking old clients.
RejectReasonCode = Literal[
    "GEOMETRY_UNSAFE",
    "TEXT_REQUIRES_OUTLINE",
    "AESTHETIC",
    "DUPLICATE",
    "OTHER",
]


class RejectVariantRequest(BaseModel):
    """Request body for rejecting an advisory variant."""

    reason_code: RejectReasonCode = Field(
        ..., description="Operator rejection reason code."
    )
    reason_detail: Optional[str] = Field(
        None,
        description="Optional free text detail (shown to operator, stored for audit).",
        max_length=500,
    )
    operator_note: Optional[str] = Field(
        None,
        description="Optional operator note separate from reason_detail (UI convenience).",
        max_length=2000,
    )


class AdvisoryVariantRejectionRecord(BaseModel):
    """Persisted rejection record for an advisory variant."""

    run_id: str
    advisory_id: str
    rejected_at_utc: str = Field(..., description="ISO timestamp (UTC).")
    reason_code: RejectReasonCode
    reason_detail: Optional[str] = None
    operator_note: Optional[str] = None



class RejectVariantResponse(BaseModel):
    """Response from rejecting an advisory variant."""

    run_id: str
    advisory_id: str
    rejected: bool = True
    reason_code: RejectReasonCode
    reason_detail: Optional[str] = None
    rejected_at_utc: str
    message: str = "Variant rejected successfully."


class UnrejectVariantResponse(BaseModel):
    """Response from unreject (clearing rejection) of an advisory variant."""

    run_id: str
    advisory_id: str
    rejected: bool = False
    cleared_at_utc: str
    message: str = "Rejection cleared successfully."


def utc_now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()
