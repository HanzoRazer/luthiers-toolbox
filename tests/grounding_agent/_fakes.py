"""Importable in-memory fakes shared by engine and historical-fixture tests."""

from __future__ import annotations

import os
import sys
from typing import Dict, Optional, Tuple

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.grounding_agent.adapters.git_repo import (  # noqa: E402
    GitAdapterError,
    WorktreeStatus,
)


class FakeGit:
    """In-memory read-only git adapter."""

    def __init__(
        self,
        *,
        refs: Optional[Dict[str, str]] = None,
        ancestry: Optional[Dict[Tuple[str, str], Optional[bool]]] = None,
        files: Optional[Dict[Tuple[str, str], Optional[bool]]] = None,
        worktree: Optional[WorktreeStatus] = None,
        raise_error: bool = False,
    ) -> None:
        self._refs = refs or {}
        self._ancestry = ancestry or {}
        self._files = files or {}
        self._worktree = worktree
        self._raise_error = raise_error

    def resolve_ref(self, ref: str) -> Optional[str]:
        if self._raise_error:
            raise GitAdapterError("git unavailable")
        return self._refs.get(ref)

    def is_ancestor(self, commit: str, ref: str) -> Optional[bool]:
        if self._raise_error:
            raise GitAdapterError("git unavailable")
        return self._ancestry.get((commit, ref))

    def file_exists_at_ref(self, ref: str, path: str) -> Optional[bool]:
        if self._raise_error:
            raise GitAdapterError("git unavailable")
        return self._files.get((ref, path))

    def worktree_status(self) -> Optional[WorktreeStatus]:
        if self._raise_error:
            raise GitAdapterError("git unavailable")
        return self._worktree

    def repository_root(self) -> Optional[str]:
        return "/fake/repo"


class FakeGitHub:
    """In-memory read-only GitHub adapter.

    Values in ``prs``/``refs`` may be either a dict (returned) or an Exception
    instance (raised), which lets tests model auth/unavailable/not-found.
    """

    def __init__(
        self,
        *,
        prs: Optional[Dict[Tuple[str, int], object]] = None,
        refs: Optional[Dict[Tuple[str, str], object]] = None,
    ) -> None:
        self._prs = prs or {}
        self._refs = refs or {}

    def get_pull_request(self, repo: str, number: int) -> dict:
        value = self._prs.get((repo, number))
        if isinstance(value, Exception):
            raise value
        if value is None:
            raise KeyError(f"test did not configure PR {repo}#{number}")
        return value

    def get_ref(self, repo: str, ref: str) -> dict:
        value = self._refs.get((repo, ref))
        if isinstance(value, Exception):
            raise value
        if value is None:
            raise KeyError(f"test did not configure ref {repo}@{ref}")
        return value


class FakeFS:
    """In-memory read-only filesystem adapter."""

    def __init__(self, *, paths: Optional[Dict[str, bool]] = None) -> None:
        self._paths = paths or {}

    def local_path_exists(self, path: str) -> bool:
        return self._paths.get(path, False)

    def repo_path_exists(self, root: str, path: str) -> bool:
        return self._paths.get(os.path.join(root, path), False)
