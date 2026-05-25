"""
Authority Metadata — Cross-Repository Governance Contracts
===========================================================

SPRINT: Cross-Repo Governance Normalization 1A (2026-05-24)

Defines additive authority metadata structure for cross-repo normalization.
All fields are optional or have safe defaults to enable gradual adoption.

Key constraints:
    - Compatibility layer, not replacement
    - All fields optional or default-safe
    - Does not grant authority
    - Does not replace existing authority models

Contract-like governance models currently live flat under app/governance
pending package normalization.

Author: Cross-Repo Governance Normalization Sprint
Date: 2026-05-24
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ReviewState(str, Enum):
    """
    Review state for authority metadata.

    Aligned with luthiers 8E review queue semantics.
    """
    NOT_SUBMITTED = "not_submitted"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    DEFERRED = "deferred"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


class LifecycleState(str, Enum):
    """
    Lifecycle state for exports and artifacts.

    Aligned with luthiers DXF lifecycle classification.
    """
    R_AND_D_EXCLUDED = "r_and_d_excluded"
    BLOCKED_PROVENANCE = "blocked_provenance"
    DIRECT_SAVE_GAP = "direct_save_gap"
    COMPAT_ONLY = "compat_only"
    LIFECYCLE_GOVERNED = "lifecycle_governed"


class SourceRepo(str, Enum):
    """
    Source repository for cross-repo tracking.
    """
    LUTHIERS_TOOLBOX = "luthiers_toolbox"
    TAP_TONE_PI = "tap_tone_pi"
    CAM_ASSIST_BLUEPRINT = "cam_assist_blueprint"
    VECTORIZER_SANDBOX = "vectorizer_sandbox"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


@dataclass
class AuthorityMetadata:
    """
    Additive authority metadata for cross-repo normalization.

    This structure captures authority context WITHOUT granting authority.
    All fields are optional or have safe defaults to enable gradual adoption.

    Key invariants:
        - This metadata describes authority state, it does not grant it
        - Non-authoritative by default
        - All fields serializable
        - Safe for cross-repo exchange

    Attributes:
        authority_state: Current authority state (optional, from AuthorityState)
        epistemic_status: Epistemic posture (optional, from EpistemicStatus)
        review_state: Review queue state (optional)
        lifecycle_state: Export lifecycle state (optional)
        source_repo: Originating repository
        source_subsystem: Originating subsystem within repo
        non_authoritative_reason: Why this is not authoritative (if applicable)
        authority_exclusions: What this metadata does NOT authorize
        created_at: Metadata creation timestamp
        updated_at: Last update timestamp
        metadata: Additional context (use metadata["notes"] for notes)
    """
    authority_state: Optional[str] = None
    epistemic_status: Optional[str] = None
    review_state: Optional[ReviewState] = None
    lifecycle_state: Optional[LifecycleState] = None
    source_repo: SourceRepo = SourceRepo.UNKNOWN
    source_subsystem: Optional[str] = None
    non_authoritative_reason: Optional[str] = None
    authority_exclusions: List[str] = field(default_factory=lambda: [
        "execution authorization",
        "production deployment",
        "governance bypass",
        "review bypass",
        "lifecycle promotion",
        "cross-repo authority propagation",
    ])
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        """
        Check if this metadata represents authoritative state.

        Returns False if:
            - non_authoritative_reason is set
            - authority_state indicates sandbox/experimental
            - lifecycle_state is excluded or blocked
        """
        if self.non_authoritative_reason:
            return False

        non_authoritative_states = {
            "sandbox_experimental",
            "advisory_candidate",
            "rejected",
        }
        if self.authority_state in non_authoritative_states:
            return False

        non_authoritative_lifecycles = {
            LifecycleState.R_AND_D_EXCLUDED,
            LifecycleState.BLOCKED_PROVENANCE,
            LifecycleState.DIRECT_SAVE_GAP,
        }
        if self.lifecycle_state in non_authoritative_lifecycles:
            return False

        return True

    def is_production_ready(self) -> bool:
        """
        Check if this metadata indicates production readiness.

        Returns True only if:
            - lifecycle_state is LIFECYCLE_GOVERNED
            - authority_state indicates approved
            - review_state is REVIEWED
        """
        if self.lifecycle_state != LifecycleState.LIFECYCLE_GOVERNED:
            return False

        if self.authority_state not in {"approved_for_generation", "human_reviewed"}:
            return False

        if self.review_state != ReviewState.REVIEWED:
            return False

        return True

    def requires_review(self) -> bool:
        """Check if this artifact requires review before proceeding."""
        review_required_states = {
            ReviewState.NOT_SUBMITTED,
            ReviewState.PENDING_REVIEW,
            ReviewState.IN_REVIEW,
            ReviewState.NEEDS_MORE_EVIDENCE,
            ReviewState.DEFERRED,
        }
        if self.review_state in review_required_states:
            return True

        # Sandbox and advisory always require review
        if self.authority_state in {"sandbox_experimental", "advisory_candidate"}:
            return True

        return False

    def mark_non_authoritative(self, reason: str) -> "AuthorityMetadata":
        """
        Mark this metadata as non-authoritative.

        Args:
            reason: Why this is not authoritative

        Returns:
            Updated metadata with non-authoritative flag
        """
        self.non_authoritative_reason = reason
        self.updated_at = datetime.now(timezone.utc)
        return self

    def add_authority_exclusion(self, exclusion: str) -> "AuthorityMetadata":
        """
        Add an authority exclusion.

        Args:
            exclusion: What this metadata does NOT authorize

        Returns:
            Updated metadata with added exclusion
        """
        if exclusion not in self.authority_exclusions:
            self.authority_exclusions.append(exclusion)
            self.updated_at = datetime.now(timezone.utc)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "authority_state": self.authority_state,
            "epistemic_status": self.epistemic_status,
            "review_state": self.review_state.value if self.review_state else None,
            "lifecycle_state": (
                self.lifecycle_state.value if self.lifecycle_state else None
            ),
            "source_repo": self.source_repo.value,
            "source_subsystem": self.source_subsystem,
            "non_authoritative_reason": self.non_authoritative_reason,
            "authority_exclusions": self.authority_exclusions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorityMetadata":
        """Create from dictionary."""
        return cls(
            authority_state=data.get("authority_state"),
            epistemic_status=data.get("epistemic_status"),
            review_state=(
                ReviewState(data["review_state"])
                if data.get("review_state")
                else None
            ),
            lifecycle_state=(
                LifecycleState(data["lifecycle_state"])
                if data.get("lifecycle_state")
                else None
            ),
            source_repo=SourceRepo(data.get("source_repo", "unknown")),
            source_subsystem=data.get("source_subsystem"),
            non_authoritative_reason=data.get("non_authoritative_reason"),
            authority_exclusions=data.get("authority_exclusions", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )


def create_luthiers_authority_metadata(
    authority_state: Optional[str] = None,
    epistemic_status: Optional[str] = None,
    review_state: Optional[ReviewState] = None,
    lifecycle_state: Optional[LifecycleState] = None,
    subsystem: Optional[str] = None,
) -> AuthorityMetadata:
    """
    Create authority metadata for luthiers-toolbox artifacts.

    Args:
        authority_state: Authority state from AuthorityState enum
        epistemic_status: Epistemic status from EpistemicStatus enum
        review_state: Review queue state
        lifecycle_state: DXF lifecycle state
        subsystem: Originating subsystem (e.g., "ibg", "cam", "blueprint")

    Returns:
        AuthorityMetadata configured for luthiers-toolbox
    """
    return AuthorityMetadata(
        authority_state=authority_state,
        epistemic_status=epistemic_status,
        review_state=review_state,
        lifecycle_state=lifecycle_state,
        source_repo=SourceRepo.LUTHIERS_TOOLBOX,
        source_subsystem=subsystem,
    )


def create_vectorizer_authority_metadata(
    subsystem: Optional[str] = None,
) -> AuthorityMetadata:
    """
    Create authority metadata for vectorizer-sandbox artifacts.

    Vectorizer outputs are always R_AND_D_EXCLUDED and non-authoritative.

    Args:
        subsystem: Originating subsystem (e.g., "research", "experiments")

    Returns:
        AuthorityMetadata configured for vectorizer-sandbox
    """
    return AuthorityMetadata(
        authority_state="sandbox_experimental",
        epistemic_status="predicted",
        review_state=ReviewState.NOT_SUBMITTED,
        lifecycle_state=LifecycleState.R_AND_D_EXCLUDED,
        source_repo=SourceRepo.VECTORIZER_SANDBOX,
        source_subsystem=subsystem,
        non_authoritative_reason="R&D excluded — research output only",
        authority_exclusions=[
            "execution authorization",
            "production deployment",
            "governance bypass",
            "review bypass",
            "lifecycle promotion",
            "cross-repo authority propagation",
            "spine integration",
            "IBG memory population",
        ],
    )


def create_ibg_authority_metadata(
    authority_state: str = "advisory_candidate",
    epistemic_status: str = "predicted",
) -> AuthorityMetadata:
    """
    Create authority metadata for IBG artifacts.

    IBG artifacts default to BLOCKED_PROVENANCE lifecycle.

    Args:
        authority_state: Authority state (default: advisory_candidate)
        epistemic_status: Epistemic status (default: predicted)

    Returns:
        AuthorityMetadata configured for IBG with blocked provenance
    """
    return AuthorityMetadata(
        authority_state=authority_state,
        epistemic_status=epistemic_status,
        review_state=ReviewState.NOT_SUBMITTED,
        lifecycle_state=LifecycleState.BLOCKED_PROVENANCE,
        source_repo=SourceRepo.LUTHIERS_TOOLBOX,
        source_subsystem="ibg",
        non_authoritative_reason="IBG provenance blocked pending R1 ratification",
        authority_exclusions=[
            "execution authorization",
            "production deployment",
            "governance bypass",
            "review bypass",
            "lifecycle promotion",
            "cross-repo authority propagation",
            "DXF export",
            "IBG memory population",
        ],
    )


class AuthorityMetadataError(Exception):
    """Raised when authority metadata operations fail."""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(
            f"Authority metadata error during {operation}: {reason}"
        )
