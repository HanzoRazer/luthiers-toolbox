"""
Manufacturing Replay Session

CAM Dev Order 7W: Replayable review continuity sessions.

Provides:
  - ManufacturingReplaySession model
  - Replay continuity validation
  - Reference collection
  - Session hash computation

7W invariants:
  - replay_execution_present: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Replay sessions reconstruct review context.
  They do not replay execution or generate machine output.
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


class ManufacturingReplaySession(BaseModel):
    """
    Replayable review continuity session.

    Collects observation IDs, topology evaluations, fixture packages,
    and export packages for review replay.

    7W invariants (model-enforced):
      - replay_execution_present: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    replay_session_id: str = Field(
        default_factory=lambda: f"mrs-{uuid4().hex[:12]}",
        description="Unique replay session identifier"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="Source workspace ID"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="Source strategy ID"
    )

    observation_ids: List[str] = Field(
        default_factory=list,
        description="Manufacturing review observation IDs"
    )
    topology_evaluation_ids: List[str] = Field(
        default_factory=list,
        description="Topology evaluation IDs"
    )
    fixture_package_ids: List[str] = Field(
        default_factory=list,
        description="Fixture package IDs"
    )
    export_package_ids: List[str] = Field(
        default_factory=list,
        description="Export package IDs"
    )

    # 7X: Optional federation linkage
    federation_ref_ids: List[str] = Field(
        default_factory=list,
        description="Linked federation reference IDs (7X)"
    )

    replay_continuity_state: ReplayContinuityState = Field(
        default="partial",
        description="Current replay continuity state"
    )

    continuity_integrity_valid: bool = Field(
        default=True,
        description="Whether all referenced IDs can be resolved"
    )

    missing_refs_detected: bool = Field(
        default=False,
        description="Whether missing references were detected"
    )
    fragmented_replay_detected: bool = Field(
        default=False,
        description="Whether replay fragmentation was detected"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Issues blocking replay continuity"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    replay_execution_present: bool = Field(
        default=False,
        description="Always False — 7W does not replay execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7W does not allow machine output"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7W does not authorize execution"
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

    deterministic_replay_hash: str = Field(
        default="",
        description="Deterministic hash of replay session state"
    )

    @model_validator(mode="after")
    def enforce_7w_invariants(self) -> "ManufacturingReplaySession":
        """Enforce 7W invariants."""
        if self.replay_execution_present:
            raise ValueError(
                "7W invariant violation: replay_execution_present must be False — "
                "7W does not replay execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7W invariant violation: machine_output_allowed must be False"
            )
        if self.execution_authorized:
            raise ValueError(
                "7W invariant violation: execution_authorized must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of replay session state."""
        hash_input = {
            "replay_session_id": self.replay_session_id,
            "workspace_id": self.workspace_id,
            "strategy_id": self.strategy_id,
            "observation_ids": sorted(self.observation_ids),
            "topology_evaluation_ids": sorted(self.topology_evaluation_ids),
            "fixture_package_ids": sorted(self.fixture_package_ids),
            "export_package_ids": sorted(self.export_package_ids),
            "replay_continuity_state": self.replay_continuity_state,
            "blocking_issues": sorted(self.blocking_issues),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_replay_session(
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    observation_ids: Optional[List[str]] = None,
    topology_evaluation_ids: Optional[List[str]] = None,
    fixture_package_ids: Optional[List[str]] = None,
    export_package_ids: Optional[List[str]] = None,
) -> ManufacturingReplaySession:
    """
    Create a manufacturing replay session.

    Collects references without resolving objects or replaying execution.
    """
    session = ManufacturingReplaySession(
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        observation_ids=observation_ids or [],
        topology_evaluation_ids=topology_evaluation_ids or [],
        fixture_package_ids=fixture_package_ids or [],
        export_package_ids=export_package_ids or [],
    )
    session.deterministic_replay_hash = session.compute_hash()
    return session


def add_observation_to_session(
    session: ManufacturingReplaySession,
    observation_id: str,
) -> ManufacturingReplaySession:
    """Add an observation to the replay session."""
    if observation_id not in session.observation_ids:
        session.observation_ids.append(observation_id)
        session.updated_at = datetime.now(timezone.utc)
        session.deterministic_replay_hash = session.compute_hash()
    return session


def add_topology_evaluation_to_session(
    session: ManufacturingReplaySession,
    evaluation_id: str,
) -> ManufacturingReplaySession:
    """Add a topology evaluation to the replay session."""
    if evaluation_id not in session.topology_evaluation_ids:
        session.topology_evaluation_ids.append(evaluation_id)
        session.updated_at = datetime.now(timezone.utc)
        session.deterministic_replay_hash = session.compute_hash()
    return session


def add_fixture_package_to_session(
    session: ManufacturingReplaySession,
    package_id: str,
) -> ManufacturingReplaySession:
    """Add a fixture package to the replay session."""
    if package_id not in session.fixture_package_ids:
        session.fixture_package_ids.append(package_id)
        session.updated_at = datetime.now(timezone.utc)
        session.deterministic_replay_hash = session.compute_hash()
    return session


def add_export_package_to_session(
    session: ManufacturingReplaySession,
    package_id: str,
) -> ManufacturingReplaySession:
    """Add an export package to the replay session."""
    if package_id not in session.export_package_ids:
        session.export_package_ids.append(package_id)
        session.updated_at = datetime.now(timezone.utc)
        session.deterministic_replay_hash = session.compute_hash()
    return session


def add_blocking_issue_to_session(
    session: ManufacturingReplaySession,
    issue: str,
) -> ManufacturingReplaySession:
    """Add a blocking issue to the session."""
    if issue not in session.blocking_issues:
        session.blocking_issues.append(issue)
        session.updated_at = datetime.now(timezone.utc)
        session.deterministic_replay_hash = session.compute_hash()
    return session


def add_warning_to_session(
    session: ManufacturingReplaySession,
    warning: str,
) -> ManufacturingReplaySession:
    """Add a warning to the session."""
    if warning not in session.warnings:
        session.warnings.append(warning)
        session.updated_at = datetime.now(timezone.utc)
        session.deterministic_replay_hash = session.compute_hash()
    return session


def mark_missing_refs_detected(
    session: ManufacturingReplaySession,
) -> ManufacturingReplaySession:
    """Mark that missing references were detected."""
    session.missing_refs_detected = True
    session.continuity_integrity_valid = False
    session.updated_at = datetime.now(timezone.utc)
    session.deterministic_replay_hash = session.compute_hash()
    return session


def mark_fragmented_replay_detected(
    session: ManufacturingReplaySession,
) -> ManufacturingReplaySession:
    """Mark that replay fragmentation was detected."""
    session.fragmented_replay_detected = True
    session.replay_continuity_state = "fragmented"
    session.updated_at = datetime.now(timezone.utc)
    session.deterministic_replay_hash = session.compute_hash()
    return session


def update_continuity_state(
    session: ManufacturingReplaySession,
    new_state: ReplayContinuityState,
) -> ManufacturingReplaySession:
    """Update the replay continuity state."""
    session.replay_continuity_state = new_state
    session.updated_at = datetime.now(timezone.utc)
    session.deterministic_replay_hash = session.compute_hash()
    return session


def validate_replay_session(
    session: ManufacturingReplaySession,
) -> tuple[bool, List[str]]:
    """
    Validate that a replay session is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if session.replay_execution_present:
        issues.append("replay_execution_present must be False")

    if session.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if session.execution_authorized:
        issues.append("execution_authorized must be False")

    if not session.workspace_id and not session.strategy_id:
        issues.append("Session must reference a workspace or strategy")

    if not session.observation_ids:
        issues.append("Session has no observations")

    if session.blocking_issues and session.replay_continuity_state == "complete":
        issues.append("Session has blocking issues but is marked complete")

    return len(issues) == 0, issues


def is_replay_complete(session: ManufacturingReplaySession) -> bool:
    """Check if replay session is complete."""
    return (
        session.replay_continuity_state == "complete" and
        session.continuity_integrity_valid and
        not session.blocking_issues
    )


def is_replay_fragmented(session: ManufacturingReplaySession) -> bool:
    """Check if replay session is fragmented."""
    return (
        session.replay_continuity_state == "fragmented" or
        session.fragmented_replay_detected or
        session.missing_refs_detected
    )


def build_replay_session_hash(session: ManufacturingReplaySession) -> str:
    """Build deterministic hash for a replay session."""
    return session.compute_hash()


def get_session_ref_counts(session: ManufacturingReplaySession) -> Dict[str, int]:
    """Get reference counts for a session."""
    return {
        "observation_count": len(session.observation_ids),
        "topology_evaluation_count": len(session.topology_evaluation_ids),
        "fixture_package_count": len(session.fixture_package_ids),
        "export_package_count": len(session.export_package_ids),
    }
