"""
Repository Change Proposal — deterministic, content-addressed proposal contract.

Binds a governed ``ProposalTargetBinding`` to a CBSP21-formatted patch packet and a proposed
branch. The proposal is content-addressed: ``proposal_id`` is derived from a canonical hash of
its content, so identical inputs yield a byte-stable proposal. Wall-clock time is EXCLUDED from
the id, the content hash, and the canonical serialization; an optional informational
``created_at`` surfaces only through ``to_audit_dict()``.

Constitutional boundary: a proposal carries no canonical authority. It never promotes or relabels
the evidence authority state — it only *carries* the state observed on the binding. The
classification is fixed to proposal-only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .cbsp21_patch_adapter import validate_cbsp21_patch_packet
from .proposal_target import ProposalTargetBinding

PROPOSAL_CONSTITUTIONAL_CLASSIFICATION = "proposal_only__no_canonical_authority"


class RepositoryChangeProposalError(Exception):
    """Raised when a repository change proposal cannot be constructed."""


def _hash_content(content: Dict[str, Any]) -> str:
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class RepositoryChangeProposal:
    """Immutable, content-addressed repository change proposal (no runtime authority)."""

    proposal_id: str
    target: ProposalTargetBinding
    cbsp21_packet: Dict[str, Any]
    proposed_branch: str
    changed_file_summary: Tuple[str, ...]
    constitutional_classification: str = PROPOSAL_CONSTITUTIONAL_CLASSIFICATION
    # Informational only — excluded from proposal_id, content hash, and canonical serialization.
    created_at: Optional[datetime] = None

    def _canonical_content(self) -> Dict[str, Any]:
        return {
            "target": self.target.to_canonical_dict(),
            "cbsp21_packet": self.cbsp21_packet,
            "proposed_branch": self.proposed_branch,
            "changed_file_summary": list(self.changed_file_summary),
            "constitutional_classification": self.constitutional_classification,
        }

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Byte-stable serialization for identical inputs (no wall-clock time)."""
        content = self._canonical_content()
        content["proposal_id"] = self.proposal_id
        return content

    def to_audit_dict(self) -> Dict[str, Any]:
        """Non-canonical serialization that may include the informational timestamp."""
        content = self.to_canonical_dict()
        content["created_at"] = self.created_at.isoformat() if self.created_at else None
        return content

    def compute_proposal_hash(self) -> str:
        """Deterministic content hash (matches the id suffix)."""
        return _hash_content(self._canonical_content())


def build_repository_change_proposal(
    *,
    target: ProposalTargetBinding,
    cbsp21_packet: Dict[str, Any],
    proposed_branch: str,
    created_at: Optional[datetime] = None,
) -> RepositoryChangeProposal:
    """
    Build a deterministic RepositoryChangeProposal.

    Validates the CBSP21 packet (rejecting a malformed one), derives the changed-file summary
    from the packet's declared scope, and content-addresses the proposal id. Does not upgrade
    the evidence authority state — it is carried from the binding unchanged.
    """
    if not isinstance(target, ProposalTargetBinding):
        raise RepositoryChangeProposalError("target must be a ProposalTargetBinding")
    validate_cbsp21_patch_packet(cbsp21_packet)
    if not isinstance(proposed_branch, str) or not proposed_branch.strip():
        raise RepositoryChangeProposalError("proposed_branch is required")

    declared = cbsp21_packet.get("scope", {}).get("files_expected_to_change", [])
    changed_file_summary = tuple(sorted({str(f) for f in declared}))

    content = {
        "target": target.to_canonical_dict(),
        "cbsp21_packet": cbsp21_packet,
        "proposed_branch": proposed_branch.strip(),
        "changed_file_summary": list(changed_file_summary),
        "constitutional_classification": PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    }
    proposal_id = "rcp-" + _hash_content(content)

    return RepositoryChangeProposal(
        proposal_id=proposal_id,
        target=target,
        cbsp21_packet=cbsp21_packet,
        proposed_branch=proposed_branch.strip(),
        changed_file_summary=changed_file_summary,
        constitutional_classification=PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
        created_at=created_at,
    )
