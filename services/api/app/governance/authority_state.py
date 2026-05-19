"""
Authority State — Constitutional Runtime Foundation
====================================================

DEV ORDER 1D: IBG Constitutional Intake Foundation

Defines authority states for semantic objects in the IBG intake pipeline.
Authority state tracks the trust level of semantic artifacts through
the transformation pipeline.

Key principle:
    Visibility ≠ authority
    Evaluation ≠ authorship
    Semantic influence ≠ semantic legitimacy

Author: Constitutional Runtime Foundation
Date: 2026-05-18
Sprint: DEV ORDER 1D
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


class AuthorityState(str, Enum):
    """
    Authority states for semantic pipeline objects.

    Each state represents a trust level in the transformation pipeline.
    No silent transitions permitted - all changes must be explicit and logged.

    Hierarchy (lowest to highest):
        SANDBOX_EXPERIMENTAL < ADVISORY_CANDIDATE < SEMANTIC_INTERPRETATION
        < DERIVED_TOPOLOGY < CANONICAL_GEOMETRY

        HUMAN_REVIEWED and APPROVED_FOR_GENERATION require explicit human action.
        REJECTED is a terminal state.
    """

    # Source states
    CANONICAL_GEOMETRY = "canonical_geometry"

    # Transformation states (descending authority)
    DERIVED_TOPOLOGY = "derived_topology"
    SEMANTIC_INTERPRETATION = "semantic_interpretation"
    ADVISORY_CANDIDATE = "advisory_candidate"

    # Review states
    HUMAN_REVIEWED = "human_reviewed"
    APPROVED_FOR_GENERATION = "approved_for_generation"

    # Sandbox/terminal states
    SANDBOX_EXPERIMENTAL = "sandbox_experimental"
    REJECTED = "rejected"
    ARCHIVED_SUPERSEDED = "archived_superseded"


# Authority level ordering for comparison
AUTHORITY_LEVELS: Dict[AuthorityState, int] = {
    AuthorityState.REJECTED: -2,
    AuthorityState.ARCHIVED_SUPERSEDED: -1,
    AuthorityState.SANDBOX_EXPERIMENTAL: 0,
    AuthorityState.ADVISORY_CANDIDATE: 1,
    AuthorityState.SEMANTIC_INTERPRETATION: 2,
    AuthorityState.DERIVED_TOPOLOGY: 3,
    AuthorityState.CANONICAL_GEOMETRY: 4,
    AuthorityState.HUMAN_REVIEWED: 5,
    AuthorityState.APPROVED_FOR_GENERATION: 6,
}


# Valid state transitions
VALID_TRANSITIONS: Dict[AuthorityState, Set[AuthorityState]] = {
    AuthorityState.CANONICAL_GEOMETRY: {
        AuthorityState.DERIVED_TOPOLOGY,
        AuthorityState.SANDBOX_EXPERIMENTAL,
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.DERIVED_TOPOLOGY: {
        AuthorityState.SEMANTIC_INTERPRETATION,
        AuthorityState.SANDBOX_EXPERIMENTAL,
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.SEMANTIC_INTERPRETATION: {
        AuthorityState.ADVISORY_CANDIDATE,
        AuthorityState.SANDBOX_EXPERIMENTAL,
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.ADVISORY_CANDIDATE: {
        AuthorityState.HUMAN_REVIEWED,
        AuthorityState.REJECTED,
        AuthorityState.SANDBOX_EXPERIMENTAL,
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.HUMAN_REVIEWED: {
        AuthorityState.APPROVED_FOR_GENERATION,
        AuthorityState.REJECTED,
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.APPROVED_FOR_GENERATION: {
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.SANDBOX_EXPERIMENTAL: {
        AuthorityState.ADVISORY_CANDIDATE,  # Can be promoted after review
        AuthorityState.REJECTED,
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.REJECTED: {
        AuthorityState.ARCHIVED_SUPERSEDED,
    },
    AuthorityState.ARCHIVED_SUPERSEDED: set(),  # Terminal
}


# Forbidden transitions - these must NEVER occur
FORBIDDEN_TRANSITIONS: Set[Tuple[AuthorityState, AuthorityState]] = {
    # Cannot promote advisory to canonical without human review
    (AuthorityState.ADVISORY_CANDIDATE, AuthorityState.CANONICAL_GEOMETRY),
    (AuthorityState.ADVISORY_CANDIDATE, AuthorityState.DERIVED_TOPOLOGY),

    # Cannot promote derived to canonical
    (AuthorityState.DERIVED_TOPOLOGY, AuthorityState.CANONICAL_GEOMETRY),

    # Cannot promote semantic interpretation to canonical
    (AuthorityState.SEMANTIC_INTERPRETATION, AuthorityState.CANONICAL_GEOMETRY),
    (AuthorityState.SEMANTIC_INTERPRETATION, AuthorityState.DERIVED_TOPOLOGY),

    # Cannot skip human review for generation approval
    (AuthorityState.ADVISORY_CANDIDATE, AuthorityState.APPROVED_FOR_GENERATION),
    (AuthorityState.SANDBOX_EXPERIMENTAL, AuthorityState.APPROVED_FOR_GENERATION),
    (AuthorityState.SANDBOX_EXPERIMENTAL, AuthorityState.HUMAN_REVIEWED),

    # Cannot resurrect from rejected to canonical states
    (AuthorityState.REJECTED, AuthorityState.CANONICAL_GEOMETRY),
    (AuthorityState.REJECTED, AuthorityState.APPROVED_FOR_GENERATION),
}


class AuthorityTransitionError(Exception):
    """Raised when an invalid authority state transition is attempted."""

    def __init__(
        self,
        from_state: AuthorityState,
        to_state: AuthorityState,
        reason: str,
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        super().__init__(
            f"Invalid authority transition: {from_state.value} -> {to_state.value}. "
            f"Reason: {reason}"
        )


class ForbiddenTransitionError(AuthorityTransitionError):
    """Raised when a constitutionally forbidden transition is attempted."""
    pass


@dataclass
class AuthorityStateTransition:
    """
    Record of an authority state change.

    All transitions must be logged with actor and reason.
    This enables audit trails and governance replay.
    """
    from_state: AuthorityState
    to_state: AuthorityState
    timestamp: datetime
    actor: str  # "system:<component>" | "human:<id>" | "governance:<rule>"
    reason: str
    derivation_context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "reason": self.reason,
            "derivation_context": self.derivation_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorityStateTransition":
        """Create from dictionary."""
        return cls(
            from_state=AuthorityState(data["from_state"]),
            to_state=AuthorityState(data["to_state"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            actor=data["actor"],
            reason=data["reason"],
            derivation_context=data.get("derivation_context"),
        )


@dataclass
class AuthorityStateContainer:
    """
    Container for authority state with transition history.

    Enforces valid transitions and maintains audit log.
    """
    current_state: AuthorityState = AuthorityState.SANDBOX_EXPERIMENTAL
    transition_history: List[AuthorityStateTransition] = field(default_factory=list)

    def transition(
        self,
        to_state: AuthorityState,
        actor: str,
        reason: str,
        derivation_context: Optional[Dict[str, Any]] = None,
    ) -> AuthorityStateTransition:
        """
        Transition to a new authority state.

        Validates the transition and logs it.

        Args:
            to_state: Target authority state
            actor: Who/what initiated the transition
            reason: Why the transition is happening
            derivation_context: Optional context about the derivation

        Returns:
            The transition record

        Raises:
            ForbiddenTransitionError: If transition is constitutionally forbidden
            AuthorityTransitionError: If transition is not valid
        """
        # Check for forbidden transitions
        if (self.current_state, to_state) in FORBIDDEN_TRANSITIONS:
            raise ForbiddenTransitionError(
                self.current_state,
                to_state,
                "This transition is constitutionally forbidden"
            )

        # Check for valid transitions
        valid_targets = VALID_TRANSITIONS.get(self.current_state, set())
        if to_state not in valid_targets:
            raise AuthorityTransitionError(
                self.current_state,
                to_state,
                f"Valid targets from {self.current_state.value}: "
                f"{[s.value for s in valid_targets]}"
            )

        # Create transition record
        transition = AuthorityStateTransition(
            from_state=self.current_state,
            to_state=to_state,
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            reason=reason,
            derivation_context=derivation_context,
        )

        # Apply transition
        self.transition_history.append(transition)
        self.current_state = to_state

        return transition

    def can_transition_to(self, to_state: AuthorityState) -> bool:
        """Check if a transition to the given state is valid."""
        if (self.current_state, to_state) in FORBIDDEN_TRANSITIONS:
            return False
        valid_targets = VALID_TRANSITIONS.get(self.current_state, set())
        return to_state in valid_targets

    def authority_level(self) -> int:
        """Get the numeric authority level of the current state."""
        return AUTHORITY_LEVELS.get(self.current_state, 0)

    def meets_minimum_authority(self, minimum: AuthorityState) -> bool:
        """Check if current authority meets or exceeds a minimum level."""
        return self.authority_level() >= AUTHORITY_LEVELS.get(minimum, 0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current_state": self.current_state.value,
            "transition_history": [t.to_dict() for t in self.transition_history],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorityStateContainer":
        """Create from dictionary."""
        container = cls(
            current_state=AuthorityState(data["current_state"]),
        )
        container.transition_history = [
            AuthorityStateTransition.from_dict(t)
            for t in data.get("transition_history", [])
        ]
        return container


def compare_authority(
    state_a: AuthorityState,
    state_b: AuthorityState,
) -> int:
    """
    Compare two authority states.

    Returns:
        -1 if state_a < state_b
        0 if state_a == state_b
        1 if state_a > state_b
    """
    level_a = AUTHORITY_LEVELS.get(state_a, 0)
    level_b = AUTHORITY_LEVELS.get(state_b, 0)

    if level_a < level_b:
        return -1
    elif level_a > level_b:
        return 1
    else:
        return 0


def requires_human_review(state: AuthorityState) -> bool:
    """Check if a state requires human review before proceeding."""
    return state in {
        AuthorityState.ADVISORY_CANDIDATE,
        AuthorityState.SANDBOX_EXPERIMENTAL,
    }


def can_populate_ibg_memory(state: AuthorityState) -> bool:
    """Check if a state is authorized for IBG memory population."""
    return state in {
        AuthorityState.HUMAN_REVIEWED,
        AuthorityState.APPROVED_FOR_GENERATION,
    }
