"""
Draft pull-request package — advisory PR metadata, never a GitHub action.

A ``DraftPullRequestPackage`` describes the pull request a human *could* open for a governed
proposal. It is metadata only: no GitHub ids, no URLs, no network state, no git queries, no branch
creation. ``branch_name`` is the proposal's intended PR *head* branch (``proposed_branch``) — never
the disposable worktree branch or the current implementation branch — and ``target_branch`` is the
caller-supplied base (default ``main``). Both branch names are validated as plausible refs WITHOUT
consulting git, and the package never asserts either branch exists.

Deterministic: identical proposals + target branch yield a byte-stable package (no wall-clock time).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

from .cbsp21_patch_adapter import compute_packet_hash
from .repository_change_proposal import RepositoryChangeProposal, validate_branch_ref
from .review_summary_builder import (
    build_changed_file_summary,
    build_review_summary,
    build_review_title,
    normalize_review_sections,
)

DRAFT_PR_CONSTITUTIONAL_CLASSIFICATION = "draft_pr_metadata_only__no_github_action"


class DraftPullRequestPackageError(Exception):
    """Raised when draft PR metadata cannot be constructed."""


def _validate_branch_ref(branch: str, field: str) -> str:
    """Fail-closed ref-shape validation via the shared ibg_repository validator.

    Delegates to ``repository_change_proposal.validate_branch_ref`` so the accepted/rejected ref
    shape stays mechanically identical to PR A's ``proposed_branch`` rules (no local copy to drift).
    Never queries git; never creates the branch.
    """
    return validate_branch_ref(branch, field=field, error_cls=DraftPullRequestPackageError)


def _build_summary(proposal: RepositoryChangeProposal) -> str:
    """Deterministic one-line summary from canonical proposal facts (no time, no paths outside repo)."""
    target = proposal.target
    n = len(proposal.changed_file_summary)
    files = "file" if n == 1 else "files"
    return (
        f"Proposes {n} {files} to {target.repository_id} from base "
        f"{target.base_revision} (proposal {proposal.proposal_id})."
    )


@dataclass(frozen=True)
class DraftPullRequestPackage:
    """Immutable advisory PR metadata derived from a proposal (no GitHub/network/git state)."""

    title: str
    summary: str
    proposal_id: str
    branch_name: str
    target_branch: str
    review_sections: Tuple[Dict[str, str], ...]
    changed_file_summary: Tuple[str, ...]
    constitutional_classification: str
    cbsp21_patch_id: str
    cbsp21_packet_hash: str

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Deterministic, byte-stable serialization (no wall-clock time)."""
        return {
            "title": self.title,
            "summary": self.summary,
            "proposal_id": self.proposal_id,
            "branch_name": self.branch_name,
            "target_branch": self.target_branch,
            "review_sections": [dict(s) for s in self.review_sections],
            "changed_file_summary": list(self.changed_file_summary),
            "constitutional_classification": self.constitutional_classification,
            "cbsp21_patch_id": self.cbsp21_patch_id,
            "cbsp21_packet_hash": self.cbsp21_packet_hash,
        }


def build_draft_pull_request_package(
    proposal: RepositoryChangeProposal,
    *,
    target_branch: str = "main",
    review_sections: Optional[Iterable[Any]] = None,
) -> DraftPullRequestPackage:
    """
    Build advisory draft-PR metadata from a governed proposal.

    ``branch_name`` is fixed to ``proposal.proposed_branch`` (the intended PR head). ``target_branch``
    is caller-supplied (default ``main``). Both are validated as plausible refs without touching git.
    If ``review_sections`` is omitted, the canonical review summary for the proposal is used.
    """
    if not isinstance(proposal, RepositoryChangeProposal):
        raise DraftPullRequestPackageError("proposal must be a RepositoryChangeProposal")

    branch_name = _validate_branch_ref(proposal.proposed_branch, "branch_name")
    target = _validate_branch_ref(target_branch, "target_branch")

    sections = (
        normalize_review_sections(review_sections)
        if review_sections is not None
        else build_review_summary(proposal)
    )

    packet = proposal.cbsp21_packet
    return DraftPullRequestPackage(
        title=build_review_title(proposal),
        summary=_build_summary(proposal),
        proposal_id=proposal.proposal_id,
        branch_name=branch_name,
        target_branch=target,
        review_sections=sections,
        changed_file_summary=build_changed_file_summary(proposal),
        constitutional_classification=DRAFT_PR_CONSTITUTIONAL_CLASSIFICATION,
        cbsp21_patch_id=str(packet.get("patch_id", "")),
        cbsp21_packet_hash=compute_packet_hash(packet),
    )
