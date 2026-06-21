"""
Review Intelligence Timeline

CAM Dev Order 7W: Timeline reconstruction for review-state continuity.

Provides:
  - ReviewIntelligenceTimeline model
  - Ordered observation progression
  - Review state tracking
  - Topology/fixture risk progression

7W invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Timelines reconstruct cognition progression.
  They do not authorize execution or generate output.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


ReplayContinuityState = Literal[
    "complete",
    "partial",
    "fragmented",
    "invalid",
]


class ReviewIntelligenceTimeline(BaseModel):
    """
    Timeline reconstruction for review-state continuity.

    Tracks ordered observation progression, review state changes,
    topology risk evolution, and fixture warning history.

    7W invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    timeline_id: str = Field(
        default_factory=lambda: f"rit-{uuid4().hex[:12]}",
        description="Unique timeline identifier"
    )

    replay_session_id: str = Field(
        ...,
        description="Parent replay session ID"
    )

    ordered_observation_ids: List[str] = Field(
        default_factory=list,
        description="Ordered list of observation IDs in timeline sequence"
    )

    review_state_progression: List[str] = Field(
        default_factory=list,
        description="Sequence of review state changes"
    )

    topology_risk_progression: List[str] = Field(
        default_factory=list,
        description="Sequence of topology risk observations"
    )

    fixture_warning_progression: List[str] = Field(
        default_factory=list,
        description="Sequence of fixture warnings"
    )

    continuity_state: ReplayContinuityState = Field(
        default="partial",
        description="Current continuity state"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7W does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7W does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_timeline_hash: str = Field(
        default="",
        description="Deterministic hash of timeline state"
    )

    @model_validator(mode="after")
    def enforce_7w_invariants(self) -> "ReviewIntelligenceTimeline":
        """Enforce 7W invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7W invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7W invariant violation: machine_output_allowed must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of timeline state."""
        hash_input = {
            "timeline_id": self.timeline_id,
            "replay_session_id": self.replay_session_id,
            "ordered_observation_ids": self.ordered_observation_ids,
            "review_state_progression": self.review_state_progression,
            "topology_risk_progression": self.topology_risk_progression,
            "fixture_warning_progression": self.fixture_warning_progression,
            "continuity_state": self.continuity_state,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_review_timeline(
    replay_session_id: str,
    ordered_observation_ids: Optional[List[str]] = None,
    review_state_progression: Optional[List[str]] = None,
    topology_risk_progression: Optional[List[str]] = None,
    fixture_warning_progression: Optional[List[str]] = None,
) -> ReviewIntelligenceTimeline:
    """
    Create a review intelligence timeline.

    Captures ordered observation progression for a replay session.
    """
    timeline = ReviewIntelligenceTimeline(
        replay_session_id=replay_session_id,
        ordered_observation_ids=ordered_observation_ids or [],
        review_state_progression=review_state_progression or [],
        topology_risk_progression=topology_risk_progression or [],
        fixture_warning_progression=fixture_warning_progression or [],
    )
    timeline.deterministic_timeline_hash = timeline.compute_hash()
    return timeline


def append_observation_to_timeline(
    timeline: ReviewIntelligenceTimeline,
    observation_id: str,
) -> ReviewIntelligenceTimeline:
    """Append an observation to the timeline (preserves order)."""
    if observation_id not in timeline.ordered_observation_ids:
        timeline.ordered_observation_ids.append(observation_id)
        timeline.updated_at = datetime.now(timezone.utc)
        timeline.deterministic_timeline_hash = timeline.compute_hash()
    return timeline


def append_review_state_to_timeline(
    timeline: ReviewIntelligenceTimeline,
    review_state: str,
) -> ReviewIntelligenceTimeline:
    """Append a review state change to the timeline."""
    timeline.review_state_progression.append(review_state)
    timeline.updated_at = datetime.now(timezone.utc)
    timeline.deterministic_timeline_hash = timeline.compute_hash()
    return timeline


def append_topology_risk_to_timeline(
    timeline: ReviewIntelligenceTimeline,
    topology_risk: str,
) -> ReviewIntelligenceTimeline:
    """Append a topology risk observation to the timeline."""
    timeline.topology_risk_progression.append(topology_risk)
    timeline.updated_at = datetime.now(timezone.utc)
    timeline.deterministic_timeline_hash = timeline.compute_hash()
    return timeline


def append_fixture_warning_to_timeline(
    timeline: ReviewIntelligenceTimeline,
    fixture_warning: str,
) -> ReviewIntelligenceTimeline:
    """Append a fixture warning to the timeline."""
    timeline.fixture_warning_progression.append(fixture_warning)
    timeline.updated_at = datetime.now(timezone.utc)
    timeline.deterministic_timeline_hash = timeline.compute_hash()
    return timeline


def update_timeline_continuity_state(
    timeline: ReviewIntelligenceTimeline,
    new_state: ReplayContinuityState,
) -> ReviewIntelligenceTimeline:
    """Update the timeline continuity state."""
    timeline.continuity_state = new_state
    timeline.updated_at = datetime.now(timezone.utc)
    timeline.deterministic_timeline_hash = timeline.compute_hash()
    return timeline


def validate_timeline(
    timeline: ReviewIntelligenceTimeline,
) -> tuple[bool, List[str]]:
    """
    Validate that a timeline is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if timeline.execution_authorized:
        issues.append("execution_authorized must be False")

    if timeline.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not timeline.replay_session_id:
        issues.append("Timeline must reference a replay session")

    if not timeline.ordered_observation_ids:
        issues.append("Timeline has no observations")

    return len(issues) == 0, issues


def is_timeline_complete(timeline: ReviewIntelligenceTimeline) -> bool:
    """Check if timeline is complete."""
    return (
        timeline.continuity_state == "complete" and
        len(timeline.ordered_observation_ids) > 0
    )


def get_timeline_length(timeline: ReviewIntelligenceTimeline) -> int:
    """Get the number of observations in the timeline."""
    return len(timeline.ordered_observation_ids)


def get_latest_review_state(timeline: ReviewIntelligenceTimeline) -> Optional[str]:
    """Get the most recent review state."""
    if timeline.review_state_progression:
        return timeline.review_state_progression[-1]
    return None


def get_latest_topology_risk(timeline: ReviewIntelligenceTimeline) -> Optional[str]:
    """Get the most recent topology risk."""
    if timeline.topology_risk_progression:
        return timeline.topology_risk_progression[-1]
    return None


def get_latest_fixture_warning(timeline: ReviewIntelligenceTimeline) -> Optional[str]:
    """Get the most recent fixture warning."""
    if timeline.fixture_warning_progression:
        return timeline.fixture_warning_progression[-1]
    return None


def has_topology_risks(timeline: ReviewIntelligenceTimeline) -> bool:
    """Check if timeline has topology risks."""
    return len(timeline.topology_risk_progression) > 0


def has_fixture_warnings(timeline: ReviewIntelligenceTimeline) -> bool:
    """Check if timeline has fixture warnings."""
    return len(timeline.fixture_warning_progression) > 0


def build_timeline_hash(timeline: ReviewIntelligenceTimeline) -> str:
    """Build deterministic hash for a timeline."""
    return timeline.compute_hash()


def get_timeline_summary(timeline: ReviewIntelligenceTimeline) -> Dict[str, Any]:
    """Get a summary of the timeline."""
    return {
        "timeline_id": timeline.timeline_id,
        "replay_session_id": timeline.replay_session_id,
        "observation_count": len(timeline.ordered_observation_ids),
        "review_state_count": len(timeline.review_state_progression),
        "topology_risk_count": len(timeline.topology_risk_progression),
        "fixture_warning_count": len(timeline.fixture_warning_progression),
        "continuity_state": timeline.continuity_state,
        "latest_review_state": get_latest_review_state(timeline),
        "latest_topology_risk": get_latest_topology_risk(timeline),
        "latest_fixture_warning": get_latest_fixture_warning(timeline),
    }
