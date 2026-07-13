"""
Repository worktree lifecycle state.

A ``RepositoryWorktreeState`` describes *where a disposable workspace is in its lifecycle*, not
authority. It never grants the right to mutate a repository — it is descriptive metadata carried
on a ``RepositoryWorktreeSpec``. The states form a deliberately small, forward-only lifecycle:

    NEW -> CREATED -> READY
                   \-> FAILED
    (any created state) -> DISPOSED

``NEW``      planned/validated spec; nothing exists on disk yet.
``CREATED``  creation has begun and may have left a worktree behind (transient).
``READY``    the worktree is created and usable for proposal assembly.
``FAILED``   creation was attempted, did not complete cleanly, and may need operator review.
``DISPOSED`` the worktree was removed; the spec is a tombstone.
"""

from __future__ import annotations

from enum import Enum


class RepositoryWorktreeState(str, Enum):
    """Forward-only lifecycle state of a disposable repository worktree (descriptive only)."""

    NEW = "new"
    CREATED = "created"
    READY = "ready"
    FAILED = "failed"
    DISPOSED = "disposed"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value
