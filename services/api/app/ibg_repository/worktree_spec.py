"""
Repository worktree specification — descriptive metadata for a disposable proposal workspace.

A ``RepositoryWorktreeSpec`` names *where* an isolated worktree lives and *what* it is allowed to
touch. It is metadata, never authority: nothing here creates, mutates, commits, or removes a
worktree (that is the builder's job through an injected ``GitRunner``). Workspace identity is
DERIVED deterministically from the proposal identifier — never from wall-clock time — so the same
proposal always maps to the same workspace id and branch, and a spec is byte-stable for identical
inputs.

Fail-closed: id/branch derivation and allowed-path normalization raise on malformed input rather
than degrading to a permissive default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Tuple

from .worktree_state import RepositoryWorktreeState

# A content-addressed proposal id is ``rcp-<16 hex>`` (see repository_change_proposal). The
# workspace id reuses the SAME suffix under a ``wt-`` prefix so the mapping is 1:1 and obvious.
_PROPOSAL_ID_RE = re.compile(r"^rcp-([0-9a-f]{6,64})$")
_WORKSPACE_ID_RE = re.compile(r"^wt-[0-9a-f]{6,64}$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class WorktreeSpecError(Exception):
    """Raised when a worktree spec value cannot be derived or normalized."""


def derive_workspace_id(proposal_id: str) -> str:
    """
    Derive a deterministic workspace id from a content-addressed proposal id.

    ``"rcp-8123ab91" -> "wt-8123ab91"``

    The id is derived from the proposal's own content hash (never a timestamp), so identical
    proposals yield identical workspace ids. Fail-closed: a proposal id that is not the expected
    ``rcp-<hex>`` shape raises rather than being coerced.
    """
    if not isinstance(proposal_id, str) or not proposal_id.strip():
        raise WorktreeSpecError("proposal_id is required to derive a workspace id")
    match = _PROPOSAL_ID_RE.match(proposal_id.strip())
    if not match:
        raise WorktreeSpecError(
            f"cannot derive workspace id from non-canonical proposal_id: {proposal_id!r}"
        )
    return "wt-" + match.group(1)


def derive_branch_name(workspace_id: str) -> str:
    """
    Derive the deterministic local branch name for a workspace.

    ``"wt-8123ab91" -> "ibg-worktree/wt-8123ab91"``

    Namespaced under ``ibg-worktree/`` so a disposable proposal branch is never confused with the
    eventual PR branch carried on the proposal. Fail-closed on a malformed workspace id.
    """
    if not isinstance(workspace_id, str) or not _WORKSPACE_ID_RE.match(workspace_id.strip()):
        raise WorktreeSpecError(f"invalid workspace_id: {workspace_id!r}")
    return "ibg-worktree/" + workspace_id.strip()


def normalize_allowed_paths(paths: Iterable[str]) -> Tuple[str, ...]:
    """
    Normalize, validate, dedupe, and sort repo-relative allowed paths (posix).

    Mirrors ``ProposalTargetBinding._normalize_target_paths``: absolute paths and traversal
    segments are forbidden so the allowed set can only ever name locations inside the repo.
    Fail-closed on any malformed entry.
    """
    if paths is None:
        raise WorktreeSpecError("allowed_paths is required")
    materialized = list(paths)
    if not materialized:
        raise WorktreeSpecError("allowed_paths must be non-empty")
    normalized = set()
    for raw in materialized:
        if not isinstance(raw, str) or not raw.strip():
            raise WorktreeSpecError(f"invalid allowed path: {raw!r}")
        candidate = raw.strip().replace("\\", "/")
        if candidate.startswith("/") or _WINDOWS_DRIVE_RE.match(candidate):
            raise WorktreeSpecError(f"absolute allowed paths are forbidden: {raw!r}")
        if ".." in candidate.split("/"):
            raise WorktreeSpecError(f"path traversal is forbidden: {raw!r}")
        candidate = candidate.strip("/")
        if not candidate:
            raise WorktreeSpecError(f"empty allowed path after normalization: {raw!r}")
        normalized.add(candidate)
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class RepositoryWorktreeSpec:
    """
    Immutable descriptive spec for one disposable repository worktree.

    Deterministic (derived, never caller-timed):
        workspace_id, branch  — derived from proposal_id
    Descriptive context:
        proposal_id, repository_id, worktree_path, base_revision, allowed_paths, state
    """

    workspace_id: str
    proposal_id: str
    repository_id: str
    branch: str
    worktree_path: str
    base_revision: str
    allowed_paths: Tuple[str, ...] = field(default_factory=tuple)
    state: RepositoryWorktreeState = RepositoryWorktreeState.NEW

    def with_state(self, state: RepositoryWorktreeState) -> "RepositoryWorktreeSpec":
        """Return a copy in a new lifecycle state (the spec itself stays immutable)."""
        if not isinstance(state, RepositoryWorktreeState):
            raise WorktreeSpecError("state must be a RepositoryWorktreeState")
        return RepositoryWorktreeSpec(
            workspace_id=self.workspace_id,
            proposal_id=self.proposal_id,
            repository_id=self.repository_id,
            branch=self.branch,
            worktree_path=self.worktree_path,
            base_revision=self.base_revision,
            allowed_paths=self.allowed_paths,
            state=state,
        )

    def to_canonical_dict(self) -> dict:
        """Deterministic, byte-stable serialization for identical inputs (state as its value)."""
        return {
            "workspace_id": self.workspace_id,
            "proposal_id": self.proposal_id,
            "repository_id": self.repository_id,
            "branch": self.branch,
            "worktree_path": self.worktree_path,
            "base_revision": self.base_revision,
            "allowed_paths": list(self.allowed_paths),
            "state": self.state.value,
        }
