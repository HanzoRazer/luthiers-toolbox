"""
Canonical repository proposal pipeline — the single, thin orchestrator.

RATIFIED CANONICAL MISSION (owner-approved 2026-07-12):

    The canonical IBG repository proposal pipeline transforms governed engineering evidence into
    deterministic, provenance-bearing review artifacts. It terminates at the human-review boundary.
    It does not commit, push, create pull requests, merge, promote evidence, or exercise repository
    or canonical authority. Existing proposal, review-bundle, and draft-PR contracts remain the
    owning contracts; the pipeline only composes them.

This module is deliberately THIN. It composes the existing, already-owning builders in the canonical
order and adds NO logic of its own — no validation the builders don't already do, no serialization
the bundle doesn't already own, no new authority. The composition is:

    BodyEvidenceCandidate
        -> build_proposal_target_binding    (PR A: evidence-owned fields derived, fail-closed)
        -> build_repository_change_proposal  (PR A: content-addressed rcp- proposal)
        -> build_review_bundle               (PR C: review bundle + draft-PR metadata + provenance)
        -> STOP  (human-review boundary)

There is intentionally NO method here that executes, commits, pushes, merges, creates a pull request,
touches git/the filesystem/GitHub/the network, or promotes authority. The pipeline's terminal state
is a review artifact for a human; it is where IBG stops.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from .proposal_target import build_proposal_target_binding
from .repository_change_proposal import (
    RepositoryChangeProposal,
    build_repository_change_proposal,
)
from .repository_review_bundle import (
    RepositoryReviewBundle,
    build_review_bundle,
)

# The ratified mission, verbatim, so a consumer can read the canonical boundary from the code.
CANONICAL_PIPELINE_MISSION = (
    "The canonical IBG repository proposal pipeline transforms governed engineering evidence into "
    "deterministic, provenance-bearing review artifacts. It terminates at the human-review "
    "boundary. It does not commit, push, create pull requests, merge, promote evidence, or "
    "exercise repository or canonical authority. Existing proposal, review-bundle, and draft-PR "
    "contracts remain the owning contracts; the pipeline only composes them."
)

PIPELINE_TERMINAL_STAGE = "human_review"
PIPELINE_CONSTITUTIONAL_CLASSIFICATION = (
    "proposal_pipeline__composes_only__terminates_at_human_review"
)


class RepositoryProposalPipelineError(Exception):
    """Raised when the pipeline cannot compose a result (delegated fail-closed errors propagate)."""


@dataclass(frozen=True)
class RepositoryProposalPipelineResult:
    """
    Immutable pipeline result: the composed proposal + review bundle, terminating at human review.

    The bundle already embeds the canonical proposal, draft-PR metadata, and provenance — this
    result does NOT re-model any of them. ``proposal`` is carried as a convenience reference; its
    canonical serialization lives once, inside ``review_bundle``.
    """

    proposal: RepositoryChangeProposal
    review_bundle: RepositoryReviewBundle
    terminates_at: str = PIPELINE_TERMINAL_STAGE
    constitutional_classification: str = PIPELINE_CONSTITUTIONAL_CLASSIFICATION

    @property
    def draft_pull_request(self) -> Dict[str, Any]:
        """The advisory draft-PR metadata (owned by the bundle)."""
        return self.review_bundle.draft_pull_request

    @property
    def provenance_reference(self) -> Dict[str, str]:
        """The provenance reference carried unchanged from the proposal."""
        return dict(self.review_bundle.provenance_reference)

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Deterministic serialization: terminal marker + the bundle's canonical form (no duplication)."""
        return {
            "pipeline_terminates_at": self.terminates_at,
            "constitutional_classification": self.constitutional_classification,
            "review_bundle": self.review_bundle.to_canonical_dict(),
        }


@dataclass(frozen=True)
class RepositoryProposalPipeline:
    """
    The canonical, stateless proposal pipeline. Composes existing builders; owns no new logic.

    It has exactly one operation — ``run`` — and deliberately no execute/commit/push/PR method.
    """

    def run(
        self,
        *,
        candidate: Any,
        repository_id: str,
        base_revision: str,
        authorized_target_paths: Iterable[str],
        change_intent: str,
        proposed_branch: str,
        cbsp21_packet: Dict[str, Any],
        target_branch: str = "main",
        review_package: Any = None,
        workspace_metadata: Any = None,
        provenance: Any = None,
    ) -> RepositoryProposalPipelineResult:
        """
        Compose evidence -> proposal -> review bundle, terminating at the human-review boundary.

        Every stage is an existing, owning builder; this method adds no validation or serialization
        of its own. Fail-closed behaviour is inherited: any builder that rejects its input raises,
        and the pipeline lets that error propagate rather than degrading to a partial result.
        """
        binding = build_proposal_target_binding(
            candidate,
            repository_id=repository_id,
            base_revision=base_revision,
            authorized_target_paths=authorized_target_paths,
            change_intent=change_intent,
        )
        proposal = build_repository_change_proposal(
            target=binding,
            cbsp21_packet=cbsp21_packet,
            proposed_branch=proposed_branch,
        )
        bundle = build_review_bundle(
            proposal=proposal,
            target_branch=target_branch,
            review_package=review_package,
            workspace_metadata=workspace_metadata,
            provenance=provenance,
        )
        return RepositoryProposalPipelineResult(proposal=proposal, review_bundle=bundle)


def run_repository_proposal_pipeline(
    *,
    candidate: Any,
    repository_id: str,
    base_revision: str,
    authorized_target_paths: Iterable[str],
    change_intent: str,
    proposed_branch: str,
    cbsp21_packet: Dict[str, Any],
    target_branch: str = "main",
    review_package: Any = None,
    workspace_metadata: Any = None,
    provenance: Any = None,
) -> RepositoryProposalPipelineResult:
    """Convenience: run the canonical pipeline once (equivalent to ``RepositoryProposalPipeline().run(...)``)."""
    return RepositoryProposalPipeline().run(
        candidate=candidate,
        repository_id=repository_id,
        base_revision=base_revision,
        authorized_target_paths=authorized_target_paths,
        change_intent=change_intent,
        proposed_branch=proposed_branch,
        cbsp21_packet=cbsp21_packet,
        target_branch=target_branch,
        review_package=review_package,
        workspace_metadata=workspace_metadata,
        provenance=provenance,
    )
