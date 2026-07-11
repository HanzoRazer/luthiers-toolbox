"""
Proposal Target Binding — constitutional adapter over BodyEvidenceCandidate.

Binds a governed ``BodyEvidenceCandidate`` to a proposed repository operation. Evidence-owned
facts are DERIVED from the candidate and cannot be supplied or overridden by callers; only the
repository-context facts (repository id, base revision, authorized paths, change intent) are
caller-supplied. The binding never promotes the candidate, never relabels its authority state,
never bypasses candidate/provenance validation, and never accepts an untyped dict as evidence.

Fail-closed: any missing/incomplete provenance, an underivable producing-subsystem, or an
invalid target path raises rather than degrading to a permissive default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Tuple

from app.instrument_geometry.body.ibg.body_evidence_candidate import BodyEvidenceCandidate


class ProposalBindingError(Exception):
    """Base error for proposal target binding construction."""


class EvidenceContractError(ProposalBindingError):
    """Raised when the evidence input violates the constitutional input contract."""


class InvalidTargetPathError(ProposalBindingError):
    """Raised when an authorized target path is absolute, escaping, or malformed."""


# A normalized subsystem token: lowercase, starts with a letter, [a-z0-9_] only.
_SUBSYSTEM_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def normalize_producing_subsystem(actor: str) -> str:
    """
    Normalize a provenance actor id into a stable subsystem token.

    The producing subsystem is *derived from* the actor recorded on the final provenance
    transformation, but the raw actor id is NOT exposed as the subsystem value — actor
    identity and subsystem ownership are related but not identical, and coupling the proposal
    schema to an actor-id convention would make actor renames look like subsystem changes.

    ``"system:body_isolation" -> "body_isolation"``

    Fail-closed: raises ``EvidenceContractError`` on empty/invalid actor or when the result
    cannot be normalized into a safe token. Never falls back to a guess.
    """
    if not isinstance(actor, str) or not actor.strip():
        raise EvidenceContractError("cannot derive producing_subsystem: empty or invalid actor")
    token = actor.strip().lower()
    if ":" in token:
        # Drop the actor scheme ("system:" / "human:"); keep the identity segment.
        token = token.split(":", 1)[1]
    token = re.sub(r"[\s\-]+", "_", token.strip())
    if not _SUBSYSTEM_RE.match(token):
        raise EvidenceContractError(
            f"cannot normalize producing_subsystem from actor {actor!r}"
        )
    return token


def _normalize_target_paths(paths: Iterable[str]) -> Tuple[str, ...]:
    """Normalize, validate, dedupe, and sort authorized target paths (repo-relative, posix)."""
    if paths is None:
        raise InvalidTargetPathError("authorized_target_paths is required")
    materialized = list(paths)
    if not materialized:
        raise InvalidTargetPathError("authorized_target_paths must be non-empty")
    normalized = set()
    for raw in materialized:
        if not isinstance(raw, str) or not raw.strip():
            raise InvalidTargetPathError(f"invalid target path: {raw!r}")
        candidate = raw.strip().replace("\\", "/")
        if candidate.startswith("/") or _WINDOWS_DRIVE_RE.match(candidate):
            raise InvalidTargetPathError(f"absolute target paths are forbidden: {raw!r}")
        if ".." in candidate.split("/"):
            raise InvalidTargetPathError(f"path traversal is forbidden: {raw!r}")
        candidate = candidate.strip("/")
        if not candidate:
            raise InvalidTargetPathError(f"empty target path after normalization: {raw!r}")
        normalized.add(candidate)
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class ProposalTargetBinding:
    """
    Immutable binding of a governed evidence candidate to a proposed repository operation.

    Evidence-owned (derived, never caller-supplied):
        evidence_candidate_id, evidence_provenance_hash, producing_subsystem,
        source_authority_state
    Repository-context (caller-supplied, describe the proposed operation, not the evidence):
        repository_id, base_revision, authorized_target_paths, change_intent
    """

    evidence_candidate_id: str
    evidence_provenance_hash: str
    producing_subsystem: str
    source_authority_state: str
    repository_id: str
    base_revision: str
    authorized_target_paths: Tuple[str, ...]
    change_intent: str

    def to_canonical_dict(self) -> dict:
        """Deterministic, byte-stable serialization for identical inputs."""
        return {
            "evidence_candidate_id": self.evidence_candidate_id,
            "evidence_provenance_hash": self.evidence_provenance_hash,
            "producing_subsystem": self.producing_subsystem,
            "source_authority_state": self.source_authority_state,
            "repository_id": self.repository_id,
            "base_revision": self.base_revision,
            "authorized_target_paths": list(self.authorized_target_paths),
            "change_intent": self.change_intent,
        }


def build_proposal_target_binding(
    candidate: BodyEvidenceCandidate,
    *,
    repository_id: str,
    base_revision: str,
    authorized_target_paths: Iterable[str],
    change_intent: str,
) -> ProposalTargetBinding:
    """
    Construct a ProposalTargetBinding from a real BodyEvidenceCandidate.

    Derives the evidence-owned fields from the governed candidate and validates the
    caller-supplied repository context. Never mutates or promotes the candidate.
    """
    if not isinstance(candidate, BodyEvidenceCandidate):
        raise EvidenceContractError(
            "evidence input must be a BodyEvidenceCandidate, not "
            f"{type(candidate).__name__}"
        )

    provenance = candidate.provenance
    if provenance is None or not provenance.has_complete_lineage():
        raise EvidenceContractError(
            "candidate provenance is missing or has incomplete lineage"
        )

    last = provenance.get_last_transformation()
    if last is None:
        raise EvidenceContractError(
            "candidate provenance has no transformation to derive producing_subsystem"
        )
    producing_subsystem = normalize_producing_subsystem(last.actor)

    if not isinstance(repository_id, str) or not repository_id.strip():
        raise ProposalBindingError("repository_id is required")
    if not isinstance(base_revision, str) or not base_revision.strip():
        raise ProposalBindingError("base_revision is required")
    if not isinstance(change_intent, str) or not change_intent.strip():
        raise ProposalBindingError("change_intent is required")

    paths = _normalize_target_paths(authorized_target_paths)

    return ProposalTargetBinding(
        evidence_candidate_id=candidate.candidate_id,
        evidence_provenance_hash=provenance.compute_provenance_hash(),
        producing_subsystem=producing_subsystem,
        source_authority_state=candidate.authority_state.value,
        repository_id=repository_id.strip(),
        base_revision=base_revision.strip(),
        authorized_target_paths=paths,
        change_intent=change_intent.strip(),
    )
