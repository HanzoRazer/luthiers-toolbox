"""
In-memory ``GitRunner`` fake for worktree tests.

Records calls and maintains in-memory worktree/branch state so builder and validator tests never
touch a real repository or the filesystem. It intentionally mirrors ``LocalGitRunner``'s temp-root
confinement so tests exercise the same fail-closed boundary the real adapter enforces.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from app.ibg_repository.git_runner import GitCommandError


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath(path))))


class FakeGitRunner:
    """Deterministic in-memory GitRunner. Satisfies the GitRunner protocol structurally."""

    def __init__(
        self,
        *,
        temp_root: str,
        revision: str = "a832d6e3a832d6e3a832d6e3a832d6e3a832d6e3",
        clean: bool = True,
        existing_branches: Optional[Tuple[str, ...]] = None,
        existing_worktrees: Optional[Tuple[str, ...]] = None,
        known_revisions: Optional[Tuple[str, ...]] = None,
        fail_create_after_add: bool = False,
    ) -> None:
        self._temp_root = temp_root
        self._revision = revision
        self._clean = clean
        self._branches = set(existing_branches or ())
        self._worktrees: List[str] = list(existing_worktrees or ())
        self._known_revisions = set(known_revisions or (revision, "a832d6e3"))
        self._fail_create_after_add = fail_create_after_add
        self.calls: List[Tuple[str, tuple]] = []

    # --- introspection helpers for assertions ---------------------------
    @property
    def created(self) -> List[str]:
        return [args[0] for name, args in self.calls if name == "create_worktree"]

    @property
    def removed(self) -> List[str]:
        return [args[0] for name, args in self.calls if name == "remove_worktree"]

    def set_clean(self, clean: bool) -> None:
        self._clean = clean

    # --- GitRunner protocol ---------------------------------------------
    def list_worktrees(self) -> Tuple[str, ...]:
        self.calls.append(("list_worktrees", ()))
        return tuple(self._worktrees)

    def branch_exists(self, branch: str) -> bool:
        self.calls.append(("branch_exists", (branch,)))
        return branch in self._branches

    def repository_clean(self) -> bool:
        self.calls.append(("repository_clean", ()))
        return self._clean

    def current_revision(self) -> str:
        self.calls.append(("current_revision", ()))
        return self._revision

    def resolve_revision(self, revision: str) -> str:
        self.calls.append(("resolve_revision", (revision,)))
        if not isinstance(revision, str) or not revision.strip():
            raise GitCommandError("revision is required")
        requested = revision.strip()
        for known in self._known_revisions:
            if known == requested or known.startswith(requested):
                return known
        raise GitCommandError(f"unknown revision: {revision!r}")

    def create_worktree(self, worktree_path: str, branch: str, base_revision: str) -> None:
        self.calls.append(("create_worktree", (worktree_path, branch, base_revision)))
        if not _within(worktree_path, self._temp_root):
            raise GitCommandError(f"path outside temp_root: {worktree_path!r}")
        if _norm(worktree_path) in {_norm(w) for w in self._worktrees}:
            raise GitCommandError(f"worktree already exists: {worktree_path!r}")
        if branch in self._branches:
            raise GitCommandError(f"branch already exists: {branch!r}")
        self._worktrees.append(worktree_path)
        self._branches.add(branch)
        if self._fail_create_after_add:
            raise GitCommandError("simulated failure after worktree add")

    def remove_worktree(self, worktree_path: str) -> None:
        self.calls.append(("remove_worktree", (worktree_path,)))
        target = _norm(worktree_path)
        before = len(self._worktrees)
        self._worktrees = [w for w in self._worktrees if _norm(w) != target]
        if len(self._worktrees) == before:
            raise GitCommandError(f"no such worktree: {worktree_path!r}")


def _within(child: str, root: str) -> bool:
    c, r = _norm(child), _norm(root)
    return c == r or c.startswith(r + os.sep)
