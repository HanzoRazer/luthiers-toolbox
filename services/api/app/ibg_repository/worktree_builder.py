"""
Repository worktree builder — the one operational entry point that materializes a workspace.

The builder turns a governed ``RepositoryChangeProposal`` into a disposable, isolated worktree by
(1) deriving a deterministic spec, (2) running the full fail-closed validation gate, and (3)
creating exactly one worktree through the injected ``GitRunner``. It performs NO other mutation:
it never commits, pushes, checks out the active tree, or deletes a foreign worktree/branch.

Ownership is recorded: ``dispose()`` will only remove a worktree this builder instance created and
still tracks. A worktree it did not create — even one at a path under the same temp root — cannot
be removed through this builder. Ownership is the safety interlock between "prepare a workspace"
and "tear one down".
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from .git_runner import GitRunner
from .repository_change_proposal import RepositoryChangeProposal
from .worktree_spec import (
    RepositoryWorktreeSpec,
    derive_branch_name,
    derive_workspace_id,
    normalize_allowed_paths,
)
from .worktree_state import RepositoryWorktreeState
from .worktree_validator import (
    WorktreeValidationError,
    normalize_workspace_path,
    verify_repository_root,
    verify_temp_root,
    validate_worktree,
)


class WorktreeBuildError(Exception):
    """Raised when a worktree cannot be planned, created, or disposed safely."""

    def __init__(
        self,
        message: str,
        *,
        spec: Optional[RepositoryWorktreeSpec] = None,
    ) -> None:
        super().__init__(message)
        self.spec = spec


def _owner_key(worktree_path: str) -> str:
    import os

    return os.path.normcase(os.path.normpath(os.path.abspath(worktree_path)))


class RepositoryWorktreeBuilder:
    """
    Creates and disposes deterministic, isolated worktrees for repository proposals.

    Requires an explicit repository root and temp root at construction — neither defaults
    silently to a developer or production path. All git access flows through the injected
    ``GitRunner`` seam.
    """

    def __init__(
        self,
        runner: GitRunner,
        *,
        repository_root: str,
        temp_root: str,
        require_clean: bool = True,
    ) -> None:
        if runner is None:
            raise WorktreeBuildError("a GitRunner must be injected")
        self._runner = runner
        self._repository_root = verify_repository_root(repository_root)
        self._temp_root = verify_temp_root(temp_root)
        self._require_clean = require_clean
        self._owned: Dict[str, RepositoryWorktreeSpec] = {}

    @property
    def temp_root(self) -> str:
        return self._temp_root

    @property
    def repository_root(self) -> str:
        return self._repository_root

    def owned_workspaces(self) -> Tuple[RepositoryWorktreeSpec, ...]:
        """Snapshot of worktrees this builder created and still tracks."""
        return tuple(self._owned.values())

    # --- planning (pure: derives + confines, no git, no mutation) --------

    def plan(
        self,
        *,
        proposal_id: str,
        repository_id: str,
        base_revision: str,
        allowed_paths: Iterable[str],
    ) -> RepositoryWorktreeSpec:
        """Derive a deterministic ``RepositoryWorktreeSpec`` (state NEW). No git, no I/O writes."""
        if not isinstance(repository_id, str) or not repository_id.strip():
            raise WorktreeBuildError("repository_id is required")
        if not isinstance(base_revision, str) or not base_revision.strip():
            raise WorktreeBuildError("base_revision is required")

        workspace_id = derive_workspace_id(proposal_id)
        branch = derive_branch_name(workspace_id)
        worktree_path = str(Path(self._temp_root) / workspace_id)
        # Confinement is proven at plan time so a bad path never reaches create().
        normalize_workspace_path(self._temp_root, worktree_path)
        paths = normalize_allowed_paths(allowed_paths)

        return RepositoryWorktreeSpec(
            workspace_id=workspace_id,
            proposal_id=proposal_id.strip(),
            repository_id=repository_id.strip(),
            branch=branch,
            worktree_path=worktree_path,
            base_revision=base_revision.strip(),
            allowed_paths=paths,
            state=RepositoryWorktreeState.NEW,
        )

    def plan_from_proposal(
        self, proposal: RepositoryChangeProposal
    ) -> RepositoryWorktreeSpec:
        """Derive a spec from a governed proposal. Never mutates or promotes the proposal."""
        if not isinstance(proposal, RepositoryChangeProposal):
            raise WorktreeBuildError("proposal must be a RepositoryChangeProposal")
        return self.plan(
            proposal_id=proposal.proposal_id,
            repository_id=proposal.target.repository_id,
            base_revision=proposal.target.base_revision,
            allowed_paths=proposal.target.authorized_target_paths,
        )

    # --- lifecycle (the only sanctioned mutation: worktree add/remove) ---

    def create(self, spec: RepositoryWorktreeSpec) -> RepositoryWorktreeSpec:
        """
        Validate and materialize a worktree; return the spec advanced to READY.

        Runs the full fail-closed gate first. On any failure nothing is created and the error
        propagates. On success the worktree is recorded as owned so it can later be disposed.
        """
        if not isinstance(spec, RepositoryWorktreeSpec):
            raise WorktreeBuildError("spec must be a RepositoryWorktreeSpec")
        try:
            validate_worktree(
                spec,
                self._runner,
                temp_root=self._temp_root,
                require_clean=self._require_clean,
            )
        except WorktreeValidationError as exc:
            raise WorktreeBuildError(f"worktree validation failed: {exc}") from exc

        key = _owner_key(spec.worktree_path)
        if key in self._owned:
            raise WorktreeBuildError(
                f"builder already owns a worktree at {spec.worktree_path!r}"
            )

        created = spec.with_state(RepositoryWorktreeState.CREATED)
        try:
            self._runner.create_worktree(spec.worktree_path, spec.branch, spec.base_revision)
        except Exception as exc:
            failed = created.with_state(RepositoryWorktreeState.FAILED)
            cleanup_error = self._cleanup_partial_create(spec.worktree_path, key)
            if cleanup_error is not None:
                raise WorktreeBuildError(
                    "worktree creation failed and partial-create cleanup failed: "
                    f"{exc}; cleanup: {cleanup_error}",
                    spec=failed,
                ) from exc
            raise WorktreeBuildError(
                f"worktree creation failed: {exc}",
                spec=failed,
            ) from exc

        ready = created.with_state(RepositoryWorktreeState.READY)
        self._owned[key] = ready
        return ready

    def _cleanup_partial_create(self, worktree_path: str, key: str) -> Optional[Exception]:
        """
        Best-effort cleanup for a create failure that left a registered worktree behind.

        Branch deletion remains intentionally out of scope for this layer; if git created the
        branch before failing, the caller receives a FAILED spec and the branch stays visible for
        operator review.
        """
        try:
            existing = tuple(self._runner.list_worktrees())
            if any(_owner_key(path) == key for path in existing):
                self._runner.remove_worktree(worktree_path)
        except Exception as exc:  # pragma: no cover - exercised through caller behavior
            return exc
        return None

    def build_from_proposal(
        self, proposal: RepositoryChangeProposal
    ) -> RepositoryWorktreeSpec:
        """Convenience: ``plan_from_proposal`` then ``create``."""
        return self.create(self.plan_from_proposal(proposal))

    def dispose(self, spec: RepositoryWorktreeSpec) -> RepositoryWorktreeSpec:
        """
        Remove a worktree this builder created; return the spec advanced to DISPOSED.

        Fail-closed ownership interlock: only a worktree recorded as owned by THIS builder may be
        removed. A foreign or already-disposed worktree raises.
        """
        if not isinstance(spec, RepositoryWorktreeSpec):
            raise WorktreeBuildError("spec must be a RepositoryWorktreeSpec")
        key = _owner_key(spec.worktree_path)
        if key not in self._owned:
            raise WorktreeBuildError(
                f"refusing to dispose a worktree not owned by this builder: "
                f"{spec.worktree_path!r}"
            )
        self._runner.remove_worktree(spec.worktree_path)
        del self._owned[key]
        return spec.with_state(RepositoryWorktreeState.DISPOSED)
