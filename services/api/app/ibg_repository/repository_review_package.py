"""
Repository Proposal Review Package — narrow wrapper over the existing IBG review package.

Adds only repository-specific facts (base revision, authorized paths, changed-file summary,
CBSP21 packet reference/hash, proposed branch, constitutional classification) around the
existing IBG evidence review. It does NOT fork a review base model — the underlying evidence
review remains owned by ``instrument_geometry/body/ibg/workflow/review_package.py`` and is
consumed here only via its ``to_dict()`` output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .cbsp21_patch_adapter import compute_packet_hash
from .repository_change_proposal import RepositoryChangeProposal


class RepositoryReviewPackageError(Exception):
    """Raised when a repository proposal review package cannot be constructed."""


@dataclass(frozen=True)
class RepositoryProposalReviewPackage:
    """Reviewer-facing wrapper: repository facts + (optional) embedded IBG evidence review."""

    proposal_id: str
    repository_id: str
    base_revision: str
    proposed_branch: str
    authorized_paths: Tuple[str, ...]
    changed_file_summary: Tuple[str, ...]
    cbsp21_patch_id: str
    cbsp21_packet_hash: str
    constitutional_classification: str
    evidence_review: Optional[Dict[str, Any]] = None

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "repository_id": self.repository_id,
            "base_revision": self.base_revision,
            "proposed_branch": self.proposed_branch,
            "authorized_paths": list(self.authorized_paths),
            "changed_file_summary": list(self.changed_file_summary),
            "cbsp21_patch_id": self.cbsp21_patch_id,
            "cbsp21_packet_hash": self.cbsp21_packet_hash,
            "constitutional_classification": self.constitutional_classification,
            "evidence_review": self.evidence_review,
        }


def build_repository_proposal_review_package(
    *,
    proposal: RepositoryChangeProposal,
    evidence_review_package: Optional[Any] = None,
) -> RepositoryProposalReviewPackage:
    """
    Build a RepositoryProposalReviewPackage from a proposal.

    If ``evidence_review_package`` is supplied it must expose ``to_dict()`` (e.g. the existing
    IBG ``ReviewPackage``); its serialized form is embedded, never re-modeled.
    """
    if not isinstance(proposal, RepositoryChangeProposal):
        raise RepositoryReviewPackageError("proposal must be a RepositoryChangeProposal")

    evidence_review: Optional[Dict[str, Any]] = None
    if evidence_review_package is not None:
        to_dict = getattr(evidence_review_package, "to_dict", None)
        if not callable(to_dict):
            raise RepositoryReviewPackageError(
                "evidence_review_package must expose a callable to_dict()"
            )
        evidence_review = to_dict()

    packet = proposal.cbsp21_packet
    return RepositoryProposalReviewPackage(
        proposal_id=proposal.proposal_id,
        repository_id=proposal.target.repository_id,
        base_revision=proposal.target.base_revision,
        proposed_branch=proposal.proposed_branch,
        authorized_paths=proposal.target.authorized_target_paths,
        changed_file_summary=proposal.changed_file_summary,
        cbsp21_patch_id=str(packet.get("patch_id", "")),
        cbsp21_packet_hash=compute_packet_hash(packet),
        constitutional_classification=proposal.constitutional_classification,
        evidence_review=evidence_review,
    )
