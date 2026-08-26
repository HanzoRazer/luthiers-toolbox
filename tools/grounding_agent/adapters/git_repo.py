"""Read-only Git adapter.

Only a fixed allowlist of non-mutating plumbing/porcelain read commands is
ever invoked, each through ``subprocess.run`` with an explicit argument array
and ``shell=False``. There is deliberately no public ``run_git`` method, so
callers cannot smuggle in a mutation such as ``commit``/``push``/``checkout``.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

# The complete set of git subcommands this adapter may run. Every entry is
# read-only. Adding a mutating subcommand here would be caught by the
# anti-mutation guard test.
_READ_ONLY_SUBCOMMANDS = frozenset(
    {
        "rev-parse",
        "merge-base",
        "status",
        "cat-file",
        "show-ref",
        "rev-list",
    }
)


@dataclass
class WorktreeStatus:
    """Working-tree state, keeping tracked and untracked strictly separate."""

    tracked_dirty: bool
    untracked: bool
    tracked_files: List[str]
    untracked_files: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "tracked_dirty": self.tracked_dirty,
            "untracked": self.untracked,
            "tracked_files": self.tracked_files,
            "untracked_files": self.untracked_files,
        }


class GitAdapterError(RuntimeError):
    """Raised when git itself cannot be executed (not for expected non-zero exits)."""


class GitRepoAdapter:
    """Read-only access to a local git checkout."""

    def __init__(self, repo_root: str = ".") -> None:
        self._repo_root = repo_root

    # -- internal ---------------------------------------------------------

    def _run(self, subcommand: str, *args: str) -> subprocess.CompletedProcess:
        """Run one allowlisted read-only git subcommand.

        Private by design: there is no public path to run an arbitrary command.
        """
        if subcommand not in _READ_ONLY_SUBCOMMANDS:
            # Defensive: this is a programming error, never reachable from input.
            raise GitAdapterError(f"git subcommand not permitted: {subcommand}")
        cmd = ["git", "-C", self._repo_root, subcommand, *args]
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
        except FileNotFoundError as exc:  # git not installed
            raise GitAdapterError("git executable not found") from exc

    # -- read operations --------------------------------------------------

    def repository_root(self) -> Optional[str]:
        proc = self._run("rev-parse", "--show-toplevel")
        if proc.returncode != 0:
            return None
        return proc.stdout.strip() or None

    def resolve_ref(self, ref: str) -> Optional[str]:
        """Resolve a ref/branch/SHA to a full commit SHA, or None if unknown."""
        proc = self._run("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if proc.returncode != 0:
            return None
        sha = proc.stdout.strip()
        return sha or None

    def is_ancestor(self, commit: str, ref: str) -> Optional[bool]:
        """True/False if ``commit`` is an ancestor of ``ref``; None if undeterminable.

        Both endpoints are resolved first so an unknown commit yields ``None``
        (INSUFFICIENT_EVIDENCE) rather than a misleading ``False``.
        """
        if self.resolve_ref(commit) is None or self.resolve_ref(ref) is None:
            return None
        proc = self._run("merge-base", "--is-ancestor", commit, ref)
        if proc.returncode == 0:
            return True
        if proc.returncode == 1:
            return False
        return None

    def file_exists_at_ref(self, ref: str, path: str) -> Optional[bool]:
        """Whether ``path`` exists in the tree at ``ref``. None if ref unknown.

        Uses ``git cat-file -e`` against ``<ref>:<path>`` so the answer is
        ref-aware repository evidence, not a working-tree check.
        """
        if self.resolve_ref(ref) is None:
            return None
        proc = self._run("cat-file", "-e", f"{ref}:{path}")
        return proc.returncode == 0

    def worktree_status(self) -> Optional[WorktreeStatus]:
        """Current checkout state, distinguishing tracked-dirty from untracked."""
        proc = self._run("status", "--porcelain")
        if proc.returncode != 0:
            return None
        tracked_files: List[str] = []
        untracked_files: List[str] = []
        for line in proc.stdout.splitlines():
            if not line:
                continue
            code = line[:2]
            name = line[3:]
            if code == "??":
                untracked_files.append(name)
            else:
                tracked_files.append(name)
        return WorktreeStatus(
            tracked_dirty=bool(tracked_files),
            untracked=bool(untracked_files),
            tracked_files=tracked_files,
            untracked_files=untracked_files,
        )
