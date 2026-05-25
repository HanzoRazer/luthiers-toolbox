"""
Provenance Attachment Draft — Cross-Repository Governance Contracts
====================================================================

SPRINT: Cross-Repo Governance Normalization 1A (2026-05-24)

Defines preparation-only structures for provenance attachment.
These are DRAFT structures pending R1 ratification.

Key constraints:
    - Do NOT wire to DXF export
    - Do NOT unblock IBG
    - Do NOT change lifecycle classification
    - IBG default status is BLOCKED or PENDING_RATIFICATION

Contract-like governance models currently live flat under app/governance
pending package normalization.

Author: Cross-Repo Governance Normalization Sprint
Date: 2026-05-24
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class ProvenanceAttachmentStatus(str, Enum):
    """
    Status of a provenance attachment draft.

    Statuses:
        DRAFT: Initial creation, not yet submitted for review
        PENDING_RATIFICATION: Submitted, awaiting governance ratification
        RATIFIED: Governance approved, may be wired to export
        BLOCKED: Explicitly blocked from ratification (IBG default)
    """
    DRAFT = "draft"
    PENDING_RATIFICATION = "pending_ratification"
    RATIFIED = "ratified"
    BLOCKED = "blocked"


# Statuses that are NOT eligible for DXF export wiring
NON_EXPORTABLE_STATUSES = frozenset({
    ProvenanceAttachmentStatus.DRAFT,
    ProvenanceAttachmentStatus.PENDING_RATIFICATION,
    ProvenanceAttachmentStatus.BLOCKED,
})

# IBG default status — cannot be changed without governance session
IBG_DEFAULT_STATUS = ProvenanceAttachmentStatus.BLOCKED


@dataclass
class ProvenanceAttachmentDraft:
    """
    Draft provenance attachment pending ratification.

    This structure captures provenance metadata WITHOUT authorizing
    export or lifecycle promotion. It is a preparation-only artifact.

    Key invariants:
        - status defaults to BLOCKED for IBG origins
        - ratified status requires explicit governance action
        - draft structures do not wire to DXF export
        - export_authorized is ALWAYS False until ratification

    Attributes:
        attachment_id: Unique identifier for this draft
        source_artifact_id: Original source path/ID
        derivation_chain: Full ancestry of object IDs
        transformation_stage: Last transformation stage applied
        transformation_method: Function that produced this output
        transformation_params: Parameters used in transformation
        authority_state: Current authority state (from AuthorityState enum)
        epistemic_status: Epistemic posture (from EpistemicStatus enum)
        status: Attachment ratification status
        export_authorized: ALWAYS False for drafts
        blocking_reason: Why attachment is blocked (if applicable)
        ratification_requirements: What's needed for ratification
        created_at: Draft creation timestamp
        updated_at: Last update timestamp
        metadata: Additional context
    """
    attachment_id: str
    source_artifact_id: str
    derivation_chain: List[str] = field(default_factory=list)
    transformation_stage: Optional[str] = None
    transformation_method: Optional[str] = None
    transformation_params: Dict[str, Any] = field(default_factory=dict)
    authority_state: str = "sandbox_experimental"
    epistemic_status: str = "predicted"
    status: ProvenanceAttachmentStatus = ProvenanceAttachmentStatus.DRAFT
    export_authorized: Literal[False] = False
    blocking_reason: Optional[str] = None
    ratification_requirements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate draft invariants."""
        if self.export_authorized is not False:
            raise ValueError(
                "Draft provenance attachments cannot authorize export. "
                "export_authorized must be False."
            )

    def is_exportable(self) -> Literal[False]:
        """
        Check if this attachment authorizes export.

        Draft attachments are NEVER exportable. This method always
        returns False as a constitutional safeguard.
        """
        return False

    def is_blocked(self) -> bool:
        """Check if this attachment is explicitly blocked."""
        return self.status == ProvenanceAttachmentStatus.BLOCKED

    def is_pending_ratification(self) -> bool:
        """Check if this attachment is awaiting ratification."""
        return self.status == ProvenanceAttachmentStatus.PENDING_RATIFICATION

    def can_submit_for_ratification(self) -> bool:
        """
        Check if this draft can be submitted for ratification.

        Returns False if:
            - Already ratified
            - Explicitly blocked
            - Missing required fields
        """
        if self.status == ProvenanceAttachmentStatus.RATIFIED:
            return False
        if self.status == ProvenanceAttachmentStatus.BLOCKED:
            return False
        if not self.source_artifact_id:
            return False
        return True

    def submit_for_ratification(
        self,
        requirements: Optional[List[str]] = None,
    ) -> "ProvenanceAttachmentDraft":
        """
        Submit this draft for ratification.

        Does NOT ratify — only marks as pending.
        Actual ratification requires governance session.

        Args:
            requirements: List of ratification requirements

        Returns:
            Updated draft with PENDING_RATIFICATION status

        Raises:
            ValueError: If draft cannot be submitted
        """
        if not self.can_submit_for_ratification():
            raise ValueError(
                f"Cannot submit draft for ratification. "
                f"Current status: {self.status.value}"
            )

        self.status = ProvenanceAttachmentStatus.PENDING_RATIFICATION
        self.ratification_requirements = requirements or []
        self.updated_at = datetime.now(timezone.utc)
        return self

    def block(self, reason: str) -> "ProvenanceAttachmentDraft":
        """
        Explicitly block this attachment.

        Args:
            reason: Why the attachment is blocked

        Returns:
            Updated draft with BLOCKED status
        """
        self.status = ProvenanceAttachmentStatus.BLOCKED
        self.blocking_reason = reason
        self.updated_at = datetime.now(timezone.utc)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "attachment_id": self.attachment_id,
            "source_artifact_id": self.source_artifact_id,
            "derivation_chain": self.derivation_chain,
            "transformation_stage": self.transformation_stage,
            "transformation_method": self.transformation_method,
            "transformation_params": self.transformation_params,
            "authority_state": self.authority_state,
            "epistemic_status": self.epistemic_status,
            "status": self.status.value,
            "export_authorized": self.export_authorized,
            "blocking_reason": self.blocking_reason,
            "ratification_requirements": self.ratification_requirements,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceAttachmentDraft":
        """Create from dictionary."""
        return cls(
            attachment_id=data["attachment_id"],
            source_artifact_id=data["source_artifact_id"],
            derivation_chain=data.get("derivation_chain", []),
            transformation_stage=data.get("transformation_stage"),
            transformation_method=data.get("transformation_method"),
            transformation_params=data.get("transformation_params", {}),
            authority_state=data.get("authority_state", "sandbox_experimental"),
            epistemic_status=data.get("epistemic_status", "predicted"),
            status=ProvenanceAttachmentStatus(data.get("status", "draft")),
            blocking_reason=data.get("blocking_reason"),
            ratification_requirements=data.get("ratification_requirements", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )


def create_ibg_provenance_draft(
    attachment_id: str,
    source_artifact_id: str,
    derivation_chain: Optional[List[str]] = None,
    transformation_stage: Optional[str] = None,
    transformation_method: Optional[str] = None,
) -> ProvenanceAttachmentDraft:
    """
    Create a provenance draft for IBG output.

    IBG drafts default to BLOCKED status per governance policy.
    They cannot be ratified without explicit R1 governance session.

    Args:
        attachment_id: Unique identifier
        source_artifact_id: Original source path/ID
        derivation_chain: Ancestry chain
        transformation_stage: Last transformation stage
        transformation_method: Transformation function

    Returns:
        ProvenanceAttachmentDraft with IBG defaults
    """
    return ProvenanceAttachmentDraft(
        attachment_id=attachment_id,
        source_artifact_id=source_artifact_id,
        derivation_chain=derivation_chain or [],
        transformation_stage=transformation_stage,
        transformation_method=transformation_method,
        authority_state="advisory_candidate",
        epistemic_status="predicted",
        status=IBG_DEFAULT_STATUS,
        blocking_reason="IBG provenance requires R1 ratification session",
        ratification_requirements=[
            "R1 governance session",
            "Canonical provenance model ratification",
            "IBG constitutional runtime foundation ratification",
            "Epistemic status mapping approval",
        ],
    )


class ProvenanceAttachmentDraftError(Exception):
    """Raised when provenance attachment draft operations fail."""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(
            f"Provenance attachment draft error during {operation}: {reason}"
        )


class ProvenanceRatificationNotAuthorizedError(Exception):
    """Raised when attempting to ratify without authorization."""

    def __init__(self, attachment_id: str):
        self.attachment_id = attachment_id
        super().__init__(
            f"Cannot ratify provenance attachment {attachment_id}. "
            "Ratification requires explicit governance session. "
            "This code path does not have ratification authority."
        )
