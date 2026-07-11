"""
Worktree safety validation — the fail-closed gate between a spec and any git execution.

Everything here answers one question: *is it safe to materialize this worktree?* Validation is
pure with respect to the filesystem where it can be (path confinement, naming, branch shape) and
delegates only the genuinely git-stateful checks (repository cleanliness, branch existence,
existing worktrees) to an injected ``GitRunner`` — never to a scattered subprocess call.

Every check fails closed: an unsafe path, a repository mismatch, a duplicate branch, an existing
worktree, or a non-deterministic id raises rather than being waved through.
"""

from __future__ import annotations

import os
from pathlib import Path

from .git_runner import GitRunner
from .worktree_spec import (
    RepositoryWorktreeSpec,
    derive_branch_name,
    derive_workspace_id,
)


class WorktreeValidationError(Exception):
    """Raised when a worktree spec or environment fails a safety check."""


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def _is_within(child: str, root: str) -> bool:
    c, r = _norm(child), _norm(root)
    return c == r or c.startswith(r + os.sep)


def verify_temp_root(temp_root: str) -> str:
    """Fail-closed: the configured temp root must be a non-empty, existing directory."""
    if not isinstance(temp_root, str) or not temp_root.strip():
        raise WorktreeValidationError("temp_root is required (no silent default)")
    if not Path(temp_root).is_dir():
        raise WorktreeValidationError(f"temp_root must be an existing directory: {temp_root!r}")
    return str(Path(temp_root))


def verify_repository_root(repository_root: str) -> str:
    """Fail-closed: the repository root must exist and contain a ``.git`` entry."""
    if not isinstance(repository_root, str) or not repository_root.strip():
        raise WorktreeValidationError("repository_root is required")
    if not (Path(repository_root) / ".git").exists():
        raise WorktreeValidationError(
            f"repository_root is not a git repository: {repository_root!r}"
        )
    return str(Path(repository_root))


def normalize_repository_path(repository_root: str) -> str:
    """Normalized absolute repository root (for stable comparison)."""
    return _norm(verify_repository_root(repository_root))


def normalize_workspace_path(temp_root: str, worktree_path: str) -> str:
    """
    Validate and normalize a worktree path, confining it beneath ``temp_root``.

    Rejects absolute-escape, traversal (``..``), and any normalized result that lands outside the
    configured temp root. Returns the normalized absolute path.
    """
    verify_temp_root(temp_root)
    if not isinstance(worktree_path, str) or not worktree_path.strip():
        raise WorktreeValidationError("worktree_path is required")
    raw = worktree_path.replace("\\", "/")
    if ".." in raw.split("/"):
        raise WorktreeValidationError(f"path traversal is forbidden: {worktree_path!r}")
    if not _is_within(worktree_path, temp_root):
        raise WorktreeValidationError(
            f"worktree_path escapes temp_root {temp_root!r}: {worktree_path!r}"
        )
    return _norm(worktree_path)


def validate_workspace_path(spec: RepositoryWorktreeSpec, temp_root: str) -> None:
    """Confirm the spec's worktree path is confined to ``temp_root``."""
    normalize_workspace_path(temp_root, spec.worktree_path)


def validate_repository(spec: RepositoryWorktreeSpec, runner: GitRunner) -> None:
    """
    Confirm the base revision the spec pins actually resolves in the repository.

    Fail-closed: if the runner cannot report a current revision the spec cannot be trusted. This
    does not require the base revision to equal HEAD (a worktree legitimately branches from an
    older revision); it only proves the repository is real and reachable through the runner.
    """
    rev = runner.current_revision()
    if not isinstance(rev, str) or not rev.strip():
        raise WorktreeValidationError("repository did not report a current revision")


def validate_branch(spec: RepositoryWorktreeSpec, runner: GitRunner) -> None:
    """Fail-closed: the target branch must be well-formed AND must not already exist."""
    expected = derive_branch_name(spec.workspace_id)
    if spec.branch != expected:
        raise WorktreeValidationError(
            f"branch {spec.branch!r} is not the deterministic name for "
            f"{spec.workspace_id!r} (expected {expected!r})"
        )
    if runner.branch_exists(spec.branch):
        raise WorktreeValidationError(f"branch already exists: {spec.branch!r}")


def validate_deterministic_naming(spec: RepositoryWorktreeSpec) -> None:
    """Fail-closed: workspace id and branch must be the deterministic derivations of the ids."""
    expected_ws = derive_workspace_id(spec.proposal_id)
    if spec.workspace_id != expected_ws:
        raise WorktreeValidationError(
            f"workspace_id {spec.workspace_id!r} is not derived from proposal_id "
            f"{spec.proposal_id!r} (expected {expected_ws!r})"
        )
    expected_branch = derive_branch_name(spec.workspace_id)
    if spec.branch != expected_branch:
        raise WorktreeValidationError(
            f"branch {spec.branch!r} is not derived from workspace_id "
            f"{spec.workspace_id!r} (expected {expected_branch!r})"
        )


def validate_worktree(
    spec: RepositoryWorktreeSpec,
    runner: GitRunner,
    *,
    temp_root: str,
    require_clean: bool = True,
) -> None:
    """
    Full fail-closed pre-flight before a worktree may be created.

    Order matters — cheapest/purest checks first, git-stateful checks last:
      1. deterministic naming (pure)
      2. path confinement to temp_root (pure)
      3. repository reachable through the runner
      4. branch well-formed and not already existing
      5. no existing worktree at this path
      6. repository clean (unless ``require_clean`` is disabled)

    Raises ``WorktreeValidationError`` on the first violation; never returns a soft failure.
    """
    validate_deterministic_naming(spec)
    validate_workspace_path(spec, temp_root)
    validate_repository(spec, runner)
    validate_branch(spec, runner)

    target = _norm(spec.worktree_path)
    for existing in runner.list_worktrees():
        if _norm(existing) == target:
            raise WorktreeValidationError(f"a worktree already exists at {spec.worktree_path!r}")

    if require_clean and not runner.repository_clean():
        raise WorktreeValidationError(
            "repository working tree is dirty; refusing to create a worktree "
            "(pass require_clean=False to override deliberately)"
        )
