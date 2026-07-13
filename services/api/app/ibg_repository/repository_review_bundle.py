"""
Repository review bundle — a single derived review artifact.

A ``RepositoryReviewBundle`` gathers the canonical serializations that a human needs to review a
governed proposal: the proposal itself, the advisory draft-PR metadata, an optional embedded IBG
``ReviewPackage``, optional normalized workspace metadata, and a provenance reference (plus optional
verified full lineage). It is a DERIVED artifact, never a second canonical proposal contract — it
embeds canonical serializations rather than re-modeling constitutional facts into independently
editable fields.

Soft dependency on PR B by design: workspace metadata is a serialization-only input accepted as
``None``, a validated ``Mapping``, or an object exposing ``to_canonical_dict()`` (e.g. a
``RepositoryWorktreeSpec``). Nothing here imports PR B, executes git, or touches the filesystem.

Deterministic: identical inputs yield a byte-stable bundle. No wall-clock time, environment paths,
object reprs, or unordered collections enter the canonical form (the environment-specific
``worktree_path`` is deliberately dropped from workspace metadata).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

from .draft_pull_request_package import (
    DraftPullRequestPackage,
    build_draft_pull_request_package,
)
from .repository_change_proposal import RepositoryChangeProposal

REVIEW_BUNDLE_SCHEMA_VERSION = "ibg_repository_review_bundle_v1"
REVIEW_BUNDLE_CONSTITUTIONAL_CLASSIFICATION = "derived_review_artifact__advisory_only"

# The workspace metadata fields this bundle RECOGNIZES (mirrors PR B's RepositoryWorktreeSpec
# canonical shape, declared locally so PR C never imports PR B). ``worktree_path`` is recognized for
# pass-through compatibility but excluded from the canonical form as an environment-specific path.
_RECOGNIZED_WORKSPACE_FIELDS = frozenset(
    {
        "workspace_id",
        "proposal_id",
        "repository_id",
        "branch",
        "worktree_path",
        "base_revision",
        "allowed_paths",
        "state",
    }
)
_ENVIRONMENT_WORKSPACE_FIELDS = frozenset({"worktree_path"})
# Recognized workspace fields whose list value is a SET (order carries no meaning) and is therefore
# sorted for determinism. Every other list is left in caller order — canonicalization must not
# silently reorder a sequence whose position could be semantic (see _canonicalize).
_SORTED_LIST_WORKSPACE_FIELDS = frozenset({"allowed_paths"})


class RepositoryReviewBundleError(Exception):
    """Raised when a review bundle cannot be assembled from its inputs."""


def _canonicalize(value: Any) -> Any:
    """Recursively produce a deterministic, JSON-safe value.

    Mapping keys are sorted (dict insertion order is not semantic). List/tuple ORDER IS PRESERVED —
    a list already carries a deterministic order from its input, and reordering it could silently
    destroy a sequence whose position is meaningful (e.g. an ordered lineage or fallback list inside
    an embedded review package or provenance payload). Fields that are genuinely set-like are sorted
    explicitly by their caller (see ``_SORTED_LIST_WORKSPACE_FIELDS``), not here.
    """
    if isinstance(value, Mapping):
        items = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise RepositoryReviewBundleError(f"non-string key not allowed: {k!r}")
            items[k] = _canonicalize(v)
        return {k: items[k] for k in sorted(items)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise RepositoryReviewBundleError(
        f"unsupported workspace metadata value type: {type(value).__name__}"
    )


def normalize_workspace_metadata(value: Any) -> Optional[Dict[str, Any]]:
    """
    Normalize optional workspace metadata to a deterministic mapping (or ``None``).

    Accepts exactly: ``None``; a ``Mapping`` of the recognized workspace fields; or an object
    exposing ``to_canonical_dict()`` (e.g. a ``RepositoryWorktreeSpec``). Rejects any other object,
    non-string keys, and unrecognized fields. Drops the environment-specific ``worktree_path`` from
    the canonical output. Never invokes git or filesystem behavior.
    """
    if value is None:
        return None

    if isinstance(value, Mapping):
        mapping: Mapping[str, Any] = value
    else:
        to_canonical = getattr(value, "to_canonical_dict", None)
        if not callable(to_canonical):
            raise RepositoryReviewBundleError(
                "workspace metadata must be None, a Mapping, or expose to_canonical_dict(); got "
                f"{type(value).__name__}"
            )
        produced = to_canonical()
        if not isinstance(produced, Mapping):
            raise RepositoryReviewBundleError(
                "workspace metadata to_canonical_dict() must return a mapping"
            )
        mapping = produced

    normalized: Dict[str, Any] = {}
    for key, val in mapping.items():
        if not isinstance(key, str):
            raise RepositoryReviewBundleError(f"non-string workspace metadata key: {key!r}")
        if key not in _RECOGNIZED_WORKSPACE_FIELDS:
            raise RepositoryReviewBundleError(f"unrecognized workspace metadata field: {key!r}")
        if key in _ENVIRONMENT_WORKSPACE_FIELDS:
            continue  # environment-specific; excluded from the deterministic canonical form
        canon = _canonicalize(val)
        if key in _SORTED_LIST_WORKSPACE_FIELDS and isinstance(canon, list):
            if not all(isinstance(e, str) for e in canon):
                raise RepositoryReviewBundleError(
                    f"workspace field {key!r} must be a list of strings"
                )
            canon = sorted(canon)  # set-like field: order is not semantic
        normalized[key] = canon
    return {k: normalized[k] for k in sorted(normalized)}


def _assert_workspace_consistent(
    workspace: Optional[Dict[str, Any]], proposal: RepositoryChangeProposal
) -> None:
    """Fail-closed if workspace metadata contradicts the proposal it is bundled with.

    Workspace metadata is an independently-produced input (a serialized PR B ``RepositoryWorktreeSpec``
    or a plain mapping). The overlapping identity fields — ``proposal_id``, ``repository_id``,
    ``base_revision`` — must name the SAME proposal/repository/base as this bundle's proposal, or the
    bundle would present internally inconsistent "canonical" facts. Fields the workspace omits are not
    invented; only supplied fields are checked.
    """
    if not workspace:
        return
    expected = {
        "proposal_id": proposal.proposal_id,
        "repository_id": proposal.target.repository_id,
        "base_revision": proposal.target.base_revision,
    }
    for field, want in expected.items():
        got = workspace.get(field)
        if got is not None and got != want:
            raise RepositoryReviewBundleError(
                f"workspace metadata {field!r} ({got!r}) does not match the proposal ({want!r})"
            )


def _embed_review_package(review_package: Any) -> Optional[Dict[str, Any]]:
    """Embed an optional IBG ReviewPackage via its ``to_dict()`` (PR A wrap-not-fork precedent)."""
    if review_package is None:
        return None
    if isinstance(review_package, Mapping):
        return _canonicalize(review_package)
    to_dict = getattr(review_package, "to_dict", None)
    if not callable(to_dict):
        raise RepositoryReviewBundleError(
            "review_package must be None, a Mapping, or expose a callable to_dict()"
        )
    produced = to_dict()
    if not isinstance(produced, Mapping):
        raise RepositoryReviewBundleError("review_package to_dict() must return a mapping")
    return _canonicalize(produced)


def _provenance_reference(proposal: RepositoryChangeProposal) -> Dict[str, str]:
    target = proposal.target
    return {
        "evidence_candidate_id": target.evidence_candidate_id,
        "evidence_provenance_hash": target.evidence_provenance_hash,
        "producing_subsystem": target.producing_subsystem,
        "source_authority_state": target.source_authority_state,
    }


def _embed_provenance_lineage(
    provenance: Any, expected_hash: str
) -> Dict[str, Any]:
    """Serialize + verify an explicitly-supplied governed provenance object. Fail-closed on mismatch."""
    to_dict = getattr(provenance, "to_dict", None)
    compute_hash = getattr(provenance, "compute_provenance_hash", None)
    if not callable(to_dict) or not callable(compute_hash):
        raise RepositoryReviewBundleError(
            "supplied provenance must expose to_dict() and compute_provenance_hash()"
        )
    actual = compute_hash()
    if actual != expected_hash:
        raise RepositoryReviewBundleError(
            "supplied provenance hash does not match the proposal's evidence_provenance_hash "
            f"({actual!r} != {expected_hash!r})"
        )
    produced = to_dict()
    if not isinstance(produced, Mapping):
        raise RepositoryReviewBundleError("provenance to_dict() must return a mapping")
    return _canonicalize(produced)


@dataclass(frozen=True)
class RepositoryReviewBundle:
    """Immutable derived review artifact embedding canonical serializations (advisory only)."""

    schema_version: str
    proposal_id: str
    proposal: Dict[str, Any]
    draft_pull_request: Dict[str, Any]
    review_package: Optional[Dict[str, Any]]
    workspace_metadata: Optional[Dict[str, Any]]
    provenance_reference: Dict[str, str]
    provenance_lineage: Optional[Dict[str, Any]]
    provenance_lineage_embedded: bool
    constitutional_classification: str

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Byte-stable serialization for identical inputs (no wall-clock time)."""
        return {
            "schema_version": self.schema_version,
            "proposal_id": self.proposal_id,
            "proposal": self.proposal,
            "draft_pull_request": self.draft_pull_request,
            "review_package": self.review_package,
            "workspace_metadata": self.workspace_metadata,
            "provenance_reference": dict(self.provenance_reference),
            "provenance_lineage": self.provenance_lineage,
            "provenance_lineage_embedded": self.provenance_lineage_embedded,
            "constitutional_classification": self.constitutional_classification,
        }


def build_review_bundle(
    *,
    proposal: RepositoryChangeProposal,
    draft_pull_request: Optional[DraftPullRequestPackage] = None,
    target_branch: str = "main",
    review_package: Any = None,
    workspace_metadata: Any = None,
    provenance: Any = None,
) -> RepositoryReviewBundle:
    """
    Assemble a deterministic ``RepositoryReviewBundle`` from a governed proposal.

    Embeds canonical serializations of the proposal and draft-PR metadata, optionally an IBG
    ReviewPackage and normalized workspace metadata, and always the proposal's provenance reference.
    Full provenance lineage is embedded ONLY when a governed provenance object is explicitly supplied
    and its computed hash matches the proposal's ``evidence_provenance_hash``. Fail-closed throughout.
    """
    if not isinstance(proposal, RepositoryChangeProposal):
        raise RepositoryReviewBundleError("proposal must be a RepositoryChangeProposal")

    if draft_pull_request is None:
        draft = build_draft_pull_request_package(proposal, target_branch=target_branch)
    else:
        if not isinstance(draft_pull_request, DraftPullRequestPackage):
            raise RepositoryReviewBundleError(
                "draft_pull_request must be a DraftPullRequestPackage"
            )
        if draft_pull_request.proposal_id != proposal.proposal_id:
            raise RepositoryReviewBundleError(
                "draft_pull_request.proposal_id does not match the proposal"
            )
        draft = draft_pull_request

    normalized_workspace = normalize_workspace_metadata(workspace_metadata)
    _assert_workspace_consistent(normalized_workspace, proposal)

    reference = _provenance_reference(proposal)
    if provenance is None:
        lineage: Optional[Dict[str, Any]] = None
        embedded = False
    else:
        lineage = _embed_provenance_lineage(
            provenance, proposal.target.evidence_provenance_hash
        )
        embedded = True

    return RepositoryReviewBundle(
        schema_version=REVIEW_BUNDLE_SCHEMA_VERSION,
        proposal_id=proposal.proposal_id,
        proposal=proposal.to_canonical_dict(),
        draft_pull_request=draft.to_canonical_dict(),
        review_package=_embed_review_package(review_package),
        workspace_metadata=normalized_workspace,
        provenance_reference=reference,
        provenance_lineage=lineage,
        provenance_lineage_embedded=embedded,
        constitutional_classification=REVIEW_BUNDLE_CONSTITUTIONAL_CLASSIFICATION,
    )
