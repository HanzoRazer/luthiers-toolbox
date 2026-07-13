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

Identity semantics: the id is content-addressed over the *canonical* content (JSON with sorted
keys), so it is independent of dict key insertion order and byte-level packet formatting; two
semantically identical proposals share an id. It is NOT independent of list ordering or of extra
optional fields — those are treated as material content.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .cbsp21_patch_adapter import validate_cbsp21_patch_packet
from .proposal_target import ProposalTargetBinding

PROPOSAL_CONSTITUTIONAL_CLASSIFICATION = "proposal_only__no_canonical_authority"

# git check-ref-format forbids these in a branch name (subset sufficient for a
# repo-relative feature branch): whitespace/control chars, the sequences below,
# a leading '-', and a trailing '/' or '.lock'.
_BRANCH_FORBIDDEN_SUBSTR = ("..", "~", "^", ":", "?", "*", "[", "\\", "@{", "//")


class RepositoryChangeProposalError(Exception):
    """Raised when a repository change proposal cannot be constructed."""


def validate_branch_ref(
    branch: str,
    *,
    field: str = "branch",
    error_cls: type = RepositoryChangeProposalError,
) -> str:
    """Fail-closed check that ``branch`` is a plausible git branch ref (git check-ref-format subset).

    Single source of truth for branch-ref shape validation across ``ibg_repository`` — both this
    module's ``proposed_branch`` check and the draft-PR package's ``target_branch``/``branch_name``
    checks delegate here so the accepted/rejected ref shape can never drift between them. Never
    queries git; never creates the branch. ``field`` names the offending input in error messages;
    ``error_cls`` selects the exception type the caller's contract expects.
    """
    if not isinstance(branch, str) or not branch.strip():
        raise error_cls(f"{field} is required")
    if branch != branch.strip():
        raise error_cls(f"{field} must not have leading/trailing whitespace: {branch!r}")
    if any(ch.isspace() or ord(ch) < 0x20 for ch in branch):
        raise error_cls(f"{field} contains whitespace/control characters: {branch!r}")
    if branch.startswith("-") or branch.startswith("/") or branch.endswith("/") or branch.endswith(".lock"):
        raise error_cls(f"invalid {field}: {branch!r}")
    if any(bad in branch for bad in _BRANCH_FORBIDDEN_SUBSTR):
        raise error_cls(f"invalid {field}: {branch!r}")
    return branch


def _hash_content(content: Dict[str, Any]) -> str:
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _as_list(value: Any) -> List[str]:
    """Coerce a scope field to a list of strings (a bare string is one entry, not chars)."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def _validate_branch_name(branch: str) -> str:
    """Fail-closed check that ``proposed_branch`` is a plausible git branch ref."""
    return validate_branch_ref(
        branch, field="proposed_branch", error_cls=RepositoryChangeProposalError
    )


def _file_within_authorized(file_path: str, authorized: Tuple[str, ...]) -> bool:
    """True if ``file_path`` is exactly an authorized entry or under one as a directory prefix.

    Mirrors the CBSP21 gate's ``_in_scope`` directory-prefix semantics so the authorized
    boundary is interpreted the same way here as at the gate.
    """
    f = file_path.strip().replace("\\", "/").strip("/")
    for entry in authorized:
        e = entry.strip("/")
        if not e:
            continue
        if f == e or f.startswith(e + "/"):
            return True
    return False


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
    from the packet's declared scope, enforces that every declared file falls within the
    binding's authorized target paths, and content-addresses the proposal id. Does not upgrade
    the evidence authority state — it is carried from the binding unchanged.

    Fail-closed: a malformed packet, an invalid branch, or a declared changed file outside the
    authorized boundary raises rather than producing a proposal.
    """
    if not isinstance(target, ProposalTargetBinding):
        raise RepositoryChangeProposalError("target must be a ProposalTargetBinding")
    validate_cbsp21_patch_packet(cbsp21_packet)
    branch = _validate_branch_name(proposed_branch)

    declared_raw = _as_list(
        cbsp21_packet.get("scope", {}).get("files_expected_to_change", [])
    )
    # Constitutional boundary: a proposal may not declare changes it is not authorized to make.
    outside = sorted(
        {
            f
            for f in declared_raw
            if not _file_within_authorized(f, target.authorized_target_paths)
        }
    )
    if outside:
        raise RepositoryChangeProposalError(
            "declared files_expected_to_change fall outside authorized_target_paths "
            f"{list(target.authorized_target_paths)}: {outside}"
        )
    changed_file_summary = tuple(sorted({str(f) for f in declared_raw}))

    content = {
        "target": target.to_canonical_dict(),
        "cbsp21_packet": cbsp21_packet,
        "proposed_branch": branch,
        "changed_file_summary": list(changed_file_summary),
        "constitutional_classification": PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    }
    proposal_id = "rcp-" + _hash_content(content)

    return RepositoryChangeProposal(
        proposal_id=proposal_id,
        target=target,
        cbsp21_packet=cbsp21_packet,
        proposed_branch=branch,
        changed_file_summary=changed_file_summary,
        constitutional_classification=PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
        created_at=created_at,
    )
