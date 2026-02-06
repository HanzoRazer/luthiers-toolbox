"""
Event Emission Contract v1

Unified event vocabulary for cross-repo agent coordination.
Events flow from tools → agent layer → experience shell.

Design principles:
1. Events are immutable facts about what happened
2. Vocabulary is shared across all repos
3. Privacy layer is explicit on every event
4. Events can be aggregated without losing meaning
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """
    Unified event vocabulary.

    Categories:
    - ANALYSIS_*: Analysis lifecycle events
    - ARTIFACT_*: Artifact creation/mutation events
    - DECISION_*: Decision point events
    - USER_*: User interaction events
    - SYSTEM_*: System/infrastructure events
    """
    # Analysis lifecycle
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"

    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_VALIDATED = "artifact_validated"
    ARTIFACT_REJECTED = "artifact_rejected"
    ARTIFACT_PROMOTED = "artifact_promoted"

    # Decision events
    DECISION_REQUIRED = "decision_required"
    DECISION_MADE = "decision_made"
    DECISION_DEFERRED = "decision_deferred"

    # Attention events
    ATTENTION_REQUESTED = "attention_requested"
    ATTENTION_ACKNOWLEDGED = "attention_acknowledged"
    ATTENTION_DISMISSED = "attention_dismissed"

    # User interaction
    USER_ACTION = "user_action"
    USER_FEEDBACK = "user_feedback"
    USER_PREFERENCE_UPDATED = "user_preference_updated"

    # System events
    SYSTEM_HEALTH = "system_health"
    SYSTEM_ERROR = "system_error"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"


class EventSource(BaseModel):
    """
    Where an event originated.

    Enables cross-repo event correlation.
    """
    model_config = ConfigDict(extra="forbid")

    repo: str = Field(
        description="Source repository (e.g., 'tap_tone_pi', 'luthiers-toolbox')"
    )
    component: str = Field(
        description="Component within repo (e.g., 'wolf_detector', 'feasibility_engine')"
    )
    version: str = Field(
        default="",
        description="Component version"
    )


class AgentEventV1(BaseModel):
    """
    Cross-repo event for agent coordination.

    Events are the "nervous system" of the agentic layer.
    They enable:
    - Loose coupling: Tools emit events, agents react
    - Observability: Full audit trail
    - Privacy: Explicit layer on every event
    - Aggregation: Events can be rolled up without loss

    Example (analysis completed):
        AgentEventV1(
            event_id="evt_abc123",
            event_type=EventType.ANALYSIS_COMPLETED,
            source=EventSource(repo="tap_tone_pi", component="wolf_detector"),
            payload={"candidates_found": 3, "confidence": 0.87},
            privacy_layer=2,
            correlation_id="session_xyz",
        )
    """
    model_config = ConfigDict(extra="forbid")

    # Identity
    event_id: str = Field(
        min_length=1,
        description="Unique event ID"
    )
    event_type: EventType = Field(
        description="Event type from unified vocabulary"
    )

    # Source
    source: EventSource = Field(
        description="Where this event originated"
    )

    # Payload
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data (schema varies by event_type)"
    )

    # Privacy
    privacy_layer: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Privacy layer (0=ephemeral, 5=cohort-only aggregates)"
    )
    redacted_fields: list[str] = Field(
        default_factory=list,
        description="Fields that were redacted before emission"
    )

    # Correlation
    correlation_id: str = Field(
        default="",
        description="ID for correlating related events (e.g., session ID)"
    )
    causation_id: str = Field(
        default="",
        description="ID of event that caused this one"
    )
    parent_event_id: str = Field(
        default="",
        description="Parent event for hierarchical correlation"
    )

    # Timestamps
    occurred_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the event occurred"
    )
    recorded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the event was recorded (may differ from occurred_at)"
    )

    # Metadata
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for filtering/aggregation"
    )
    schema_version: str = Field(
        default="1.0.0",
        description="Version of this event schema"
    )
