"""
RMOS Run Override Schemas - YELLOW Unlock Primitive

Allows operators to override YELLOW (and optionally RED) blocked runs
without regenerating CAM/G-code.

Governance:
- Override is permanently traceable via content-addressed attachment
- Original decision.risk_level is preserved (history remains authoritative)
- meta.override tracks the unlock action
- Override attachment is immutable once written
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Override Request/Response
# =============================================================================

OverrideScope = Literal["YELLOW", "RED"]


class OverrideRequest(BaseModel):
    """Request to override a blocked run."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Justification for the override (min 10 chars)",
    )
    scope: OverrideScope = Field(
        "YELLOW",
        description="Override scope: YELLOW (default) or RED (requires RMOS_ALLOW_RED_OVERRIDE=1)",
    )
    acknowledge_risk: bool = Field(
        False,
        description="Explicit acknowledgment of risk for RED overrides",
    )


class OverrideRecord(BaseModel):
    """
    Content-addressed override record.

    Stored as override.json attachment for permanent traceability.
    """

    # Identity
    override_id: str = Field(
        ...,
        description="Unique override identifier (UUID)",
    )
    run_id: str = Field(
        ...,
        description="Run being overridden",
    )

    # Actor
    operator_id: str = Field(
        ...,
        description="Who performed the override",
    )
    operator_name: Optional[str] = Field(
        None,
        description="Display name of operator",
    )

    # Action
    scope: OverrideScope = Field(
        ...,
        description="What was overridden: YELLOW or RED",
    )
    reason: str = Field(
        ...,
        description="Justification text",
    )
    acknowledged_risk: bool = Field(
        False,
        description="True if operator acknowledged risk (required for RED)",
    )

    # Context
    original_risk_level: str = Field(
        ...,
        description="Original risk level before override",
    )
    original_status: str = Field(
        ...,
        description="Original status before override (BLOCKED)",
    )

    # Timestamp
    created_at_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the override was created",
    )

    # Correlation
    request_id: Optional[str] = Field(
        None,
        description="Request ID for audit trail",
    )


class OverrideMetaUpdate(BaseModel):
    """
    Meta update applied to run after override.

    Stored in run.meta.override for quick access.
    """

    override_id: str
    by: str  # operator_id
    reason: str
    scope: OverrideScope
    at_utc: str  # ISO timestamp
    attachment_sha256: str  # Hash of override.json


class OverrideResponse(BaseModel):
    """Response after successful override."""

    run_id: str
    override_id: str
    new_status: str = Field(
        ...,
        description="New run status after override (OK for YELLOW)",
    )
    attachment_sha256: str = Field(
        ...,
        description="Content hash of override.json attachment",
    )
    message: str = Field(
        default="Override applied successfully",
    )


class OverrideError(BaseModel):
    """Error response for override failures."""

    error: str
    code: str
    run_id: str
    current_risk_level: Optional[str] = None
    current_status: Optional[str] = None
    detail: Optional[str] = None
