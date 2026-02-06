"""
Analyzer Attention Contract v1

Defines how agents direct user attention to analysis results.
This is a presentation-layer contract, not computational.

Design principles:
1. Attention is a finite resource - directives must be prioritized
2. Focus targets are abstract (UI decides rendering)
3. Urgency and confidence are explicit
4. Dismissal rules prevent alert fatigue
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AttentionAction(str, Enum):
    """
    What the agent wants the user to do.

    Ordered by urgency (INSPECT < REVIEW < DECIDE < INTERVENE).
    """
    # Low urgency - FYI
    INSPECT = "inspect"  # Look at this when you have time

    # Medium urgency - needs review
    REVIEW = "review"  # Please look at this soon
    COMPARE = "compare"  # Compare these two things

    # High urgency - needs decision
    DECIDE = "decide"  # Make a choice between options
    CONFIRM = "confirm"  # Approve or reject

    # Critical - needs immediate action
    INTERVENE = "intervene"  # Stop and fix this now
    ABORT = "abort"  # Stop everything


class FocusTarget(BaseModel):
    """
    Where to direct attention.

    Targets are abstract references that the UI layer resolves
    to specific views, panels, or highlights.
    """
    model_config = ConfigDict(extra="forbid")

    # Target type
    target_type: str = Field(
        description="Type of target (e.g., 'run', 'artifact', 'region', 'parameter')"
    )
    target_id: str = Field(
        description="ID of the target within its type"
    )

    # Optional specificity
    highlight_region: dict[str, Any] | None = Field(
        default=None,
        description="Specific region to highlight (e.g., bounding box, time range)"
    )
    context_refs: list[str] = Field(
        default_factory=list,
        description="Related artifacts for context"
    )


class AttentionDirectiveV1(BaseModel):
    """
    Agent's request for user attention.

    This contract flows from analyzer/agent to the experience shell (UI).
    The UI decides how to render it (toast, modal, highlight, etc.).

    Example (wolf tone detected):
        AttentionDirectiveV1(
            directive_id="attn_abc123",
            action=AttentionAction.REVIEW,
            summary="Potential wolf tone at 247Hz",
            focus=FocusTarget(
                target_type="spectrum_region",
                target_id="peak_3",
                highlight_region={"freq_hz": 247, "bandwidth_hz": 10}
            ),
            urgency=0.7,
            confidence=0.85,
            evidence_refs=["wolf_candidates_v1:abc123:peak_3"],
        )
    """
    model_config = ConfigDict(extra="forbid")

    # Identity
    directive_id: str = Field(
        min_length=1,
        description="Unique directive ID for tracking/dismissal"
    )

    # Action
    action: AttentionAction = Field(
        description="What the agent wants the user to do"
    )
    summary: str = Field(
        min_length=1,
        max_length=256,
        description="One-line summary for notification"
    )
    detail: str = Field(
        default="",
        max_length=2048,
        description="Extended explanation (markdown allowed)"
    )

    # Focus
    focus: FocusTarget = Field(
        description="Where to direct attention"
    )

    # Confidence/Urgency
    urgency: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How urgent (0=FYI, 1=critical)"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How confident in this directive"
    )

    # Evidence trail
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="References to supporting evidence (schema:id:path)"
    )
    source_tool: str = Field(
        default="",
        description="Tool that generated this directive"
    )

    # Dismissal rules
    auto_dismiss_after_seconds: int | None = Field(
        default=None,
        ge=1,
        description="Auto-dismiss after N seconds (None=manual only)"
    )
    dismiss_on_action: bool = Field(
        default=True,
        description="Dismiss when user takes any action on target"
    )
    supersedes: list[str] = Field(
        default_factory=list,
        description="Directive IDs this supersedes (auto-dismiss those)"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When directive was created"
    )
    expires_at: datetime | None = Field(
        default=None,
        description="When directive expires (None=never)"
    )
