"""
Agentic Spine Schemas — Data models for events, moments, and decisions.

These schemas match the frontend AgentEventV1 contract for interoperability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class EventSource(BaseModel):
    """Source metadata for an event."""
    repo: str = "luthiers-toolbox"
    component: str = "ui"
    version: str = "1.0.0"


class SessionInfo(BaseModel):
    """Session information attached to each event."""
    session_id: str


class AgentEventV1(BaseModel):
    """
    Core event schema matching frontend AgentEventV1.

    These events are emitted by UI components and processed by the spine
    to detect moments and generate directives.
    """
    event_id: str
    event_type: str
    source: EventSource
    payload: Dict[str, Any] = Field(default_factory=dict)
    privacy_layer: int = 2
    occurred_at: str  # ISO timestamp
    schema_version: str = "1.0.0"
    session: SessionInfo


class DetectedMoment(BaseModel):
    """
    A detected moment from event analysis.

    Moments represent significant points where the system should consider
    providing guidance to the user.

    Moment types (in priority order):
    - ERROR: Something went wrong
    - OVERLOAD: User is overwhelmed (3+ undos, explicit "too much" feedback)
    - DECISION_REQUIRED: User needs to make a choice
    - FINDING: Analysis found something significant
    - HESITATION: User appears stuck (idle timeout)
    - FIRST_SIGNAL: Initial engagement (view rendered, analysis complete)
    """
    moment: str
    confidence: float
    trigger_events: List[str]


class AttentionDirective(BaseModel):
    """
    A directive for the UI to display to the user.

    Actions:
    - INSPECT: Focus on a specific element
    - REVIEW: Look over results or changes
    - COMPARE: Compare multiple options
    - DECIDE: Make a choice
    - CONFIRM: Verify an action
    - NONE: No directive (suppressed)
    """
    action: Literal["INSPECT", "REVIEW", "COMPARE", "DECIDE", "CONFIRM", "NONE"]
    title: str
    detail: str


class PolicyDiagnostic(BaseModel):
    """Diagnostic information about the policy decision."""
    rule_id: str
    max_directives: Optional[int] = None
    would_have_emitted: Optional[AttentionDirective] = None


class PolicyDecision(BaseModel):
    """
    Result of applying UWSM policy to a detected moment.

    Contains the directive to emit (if any) and diagnostic info
    for debugging/tuning.
    """
    attention_action: str
    emit_directive: bool
    directive: AttentionDirective
    diagnostic: PolicyDiagnostic


class UWSMDimension(BaseModel):
    """A single UWSM dimension value."""
    value: str


class UWSMDimensions(BaseModel):
    """User Working Style Model dimensions."""
    guidance_density: UWSMDimension = Field(default_factory=lambda: UWSMDimension(value="medium"))
    initiative_tolerance: UWSMDimension = Field(default_factory=lambda: UWSMDimension(value="shared_control"))
    cognitive_load_sensitivity: UWSMDimension = Field(default_factory=lambda: UWSMDimension(value="medium"))
    expertise_proxy: UWSMDimension = Field(default_factory=lambda: UWSMDimension(value="intermediate"))
    comparison_preference: UWSMDimension = Field(default_factory=lambda: UWSMDimension(value="side_by_side"))
    visual_density_tolerance: UWSMDimension = Field(default_factory=lambda: UWSMDimension(value="moderate"))
    exploration_vs_confirmation: UWSMDimension = Field(default_factory=lambda: UWSMDimension(value="balanced"))


class UWSMSnapshot(BaseModel):
    """
    User Working Style Model snapshot.

    Captures user preferences that influence directive generation.
    """
    dimensions: UWSMDimensions = Field(default_factory=UWSMDimensions)


# Default UWSM for new sessions
DEFAULT_UWSM = UWSMSnapshot()


# Moment priority (lower = higher priority)
MOMENT_PRIORITY: Dict[str, int] = {
    "ERROR": 1,
    "OVERLOAD": 2,
    "DECISION_REQUIRED": 3,
    "FINDING": 4,
    "HESITATION": 5,
    "FIRST_SIGNAL": 6,
}

# Critical moments that bypass cooldowns
CRITICAL_MOMENTS = {"ERROR", "OVERLOAD", "DECISION_REQUIRED"}
