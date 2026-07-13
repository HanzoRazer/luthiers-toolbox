"""
Git execution abstraction for the repository worktree layer.

``GitRunner`` is the ONLY seam through which this subsystem may touch git. It is deliberately
narrow: it exposes exactly the read/worktree operations needed to prepare a disposable
workspace and nothing else. There is no ``commit``, ``push``, ``reset``, ``clean``, ``checkout``,
``fetch``, branch deletion, or GitHub/network operation anywhere in this interface — those
capabilities are constitutionally out of scope for this sprint and cannot be reached through it.

``LocalGitRunner`` is the real adapter. It:
  * requires an explicit repository root AND an explicit temporary worktree root (no silent
    default to a developer/production path);
  * runs git through an injected command seam using explicit ``argv`` lists (never a shell
    string), so there is no shell interpolation;
  * confines every worktree path it creates or removes to beneath the configured temp root;
  * fails closed — a non-zero git exit raises ``GitCommandError``.

Tests inject an in-memory fake ``GitRunner`` (see ``tests/ibg_repository/fake_git_runner.py``); a
single bounded integration test exercises ``LocalGitRunner`` against a throwaway repo under the
pytest temp directory.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable, List, Protocol, Sequence, Tuple, runtime_checkable


DEFAULT_GIT_TIMEOUT_SECONDS = 30


class GitRunnerError(Exception):
    """Base error for git runner operations."""


class GitCommandError(GitRunnerError):
    """Raised when a git command fails (non-zero exit) or is structurally rejected."""


class GitRunnerConfigError(GitRunnerError):
    """Raised when a runner is constructed with an invalid repository or temp root."""


@runtime_checkable
class GitRunner(Protocol):
    """The narrow, sanctioned git seam. Implementations MUST NOT expose any other git verb."""

    def list_worktrees(self) -> Tuple[str, ...]:
        """Return the absolute paths of existing worktrees."""

    def branch_exists(self, branch: str) -> bool:
        """True if a local branch already exists."""

    def repository_clean(self) -> bool:
        """True if the repository working tree has no uncommitted changes."""

    def current_revision(self) -> str:
        """Return the current HEAD revision (full sha)."""

    def resolve_revision(self, revision: str) -> str:
        """Resolve ``revision`` to a commit sha or raise if it cannot be used as a base."""

    def create_worktree(self, worktree_path: str, branch: str, base_revision: str) -> None:
        """Create a new worktree at ``worktree_path`` on a NEW ``branch`` from ``base_revision``."""

    def remove_worktree(self, worktree_path: str) -> None:
        """Remove a worktree previously created at ``worktree_path``."""


# A command seam: takes an argv list, returns (returncode, stdout, stderr). Injected so unit
# tests can assert the exact argv (no shell) without spawning git.
CommandSeam = Callable[[Sequence[str]], "CommandResult"]


class CommandResult:
    """Minimal result of a git invocation."""

    __slots__ = ("returncode", "stdout", "stderr")

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _default_command_seam(argv: Sequence[str]) -> CommandResult:
    """Real command seam: run git with an explicit argv list, no shell, capture output."""
    try:
        completed = subprocess.run(  # noqa: S603 - explicit argv, shell=False, fixed executable
            list(argv),
            capture_output=True,
            text=True,
            shell=False,
            timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        timeout_msg = f"git command timed out after {DEFAULT_GIT_TIMEOUT_SECONDS}s"
        return CommandResult(124, stdout, (stderr + "\n" + timeout_msg).strip())
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _norm(path: str) -> str:
    """Resolved, absolute, normalized, case-folded path for containment comparison."""
    return os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath(path))))


def _is_within(child: str, root: str) -> bool:
    """True if ``child`` is ``root`` itself or nested beneath it (no traversal escape)."""
    c, r = _norm(child), _norm(root)
    if c == r:
        return True
    return c.startswith(r + os.sep)


class LocalGitRunner:
    """
    Real ``GitRunner`` over local git. Confines all worktree paths beneath ``temp_root``.

    Only the sanctioned read/worktree operations are implemented; there is intentionally no method that
    commits, pushes, resets, cleans, checks out the active tree, deletes a branch, or talks to a
    remote. ``create_worktree``/``remove_worktree`` refuse any path outside ``temp_root``.
    """

    def __init__(
        self,
        repository_root: str,
        temp_root: str,
        *,
        git_executable: str = "git",
        command_seam: CommandSeam = _default_command_seam,
    ) -> None:
        if not isinstance(repository_root, str) or not repository_root.strip():
            raise GitRunnerConfigError("repository_root is required")
        if not isinstance(temp_root, str) or not temp_root.strip():
            raise GitRunnerConfigError("temp_root is required (no silent default)")
        repo = Path(repository_root)
        if not (repo / ".git").exists():
            raise GitRunnerConfigError(
                f"repository_root does not look like a git repository: {repository_root!r}"
            )
        troot = Path(temp_root)
        if not troot.exists() or not troot.is_dir():
            raise GitRunnerConfigError(
                f"temp_root must be an existing directory: {temp_root!r}"
            )
        self._repository_root = str(repo)
        self._temp_root = str(troot)
        self._git = git_executable
        self._seam = command_seam

    @property
    def repository_root(self) -> str:
        return self._repository_root

    @property
    def temp_root(self) -> str:
        return self._temp_root

    def _run(self, *args: str) -> CommandResult:
        argv: List[str] = [self._git, "-C", self._repository_root, *args]
        return self._seam(argv)

    def _run_checked(self, *args: str) -> CommandResult:
        result = self._run(*args)
        if result.returncode != 0:
            raise GitCommandError(
                f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
            )
        return result

    def _require_confined(self, worktree_path: str) -> str:
        if not isinstance(worktree_path, str) or not worktree_path.strip():
            raise GitCommandError("worktree_path is required")
        if not _is_within(worktree_path, self._temp_root):
            raise GitCommandError(
                f"refusing worktree path outside temp_root {self._temp_root!r}: {worktree_path!r}"
            )
        return worktree_path

    # --- read operations -------------------------------------------------

    def list_worktrees(self) -> Tuple[str, ...]:
        result = self._run_checked("worktree", "list", "--porcelain")
        paths: List[str] = []
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                paths.append(line[len("worktree "):].strip())
        return tuple(paths)

    def branch_exists(self, branch: str) -> bool:
        if not isinstance(branch, str) or not branch.strip():
            raise GitCommandError("branch is required")
        result = self._run("show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
        raise GitCommandError(
            f"git show-ref failed while checking branch {branch!r} "
            f"({result.returncode}): {result.stderr.strip()}"
        )

    def repository_clean(self) -> bool:
        result = self._run_checked("status", "--porcelain")
        return result.stdout.strip() == ""

    def current_revision(self) -> str:
        return self._run_checked("rev-parse", "HEAD").stdout.strip()

    def resolve_revision(self, revision: str) -> str:
        if not isinstance(revision, str) or not revision.strip():
            raise GitCommandError("revision is required")
        return self._run_checked(
            "rev-parse",
            "--verify",
            f"{revision.strip()}^{{commit}}",
        ).stdout.strip()

    # --- worktree mutations (the only sanctioned writes) -----------------

    def create_worktree(self, worktree_path: str, branch: str, base_revision: str) -> None:
        path = self._require_confined(worktree_path)
        if not isinstance(branch, str) or not branch.strip():
            raise GitCommandError("branch is required")
        if not isinstance(base_revision, str) or not base_revision.strip():
            raise GitCommandError("base_revision is required")
        self._run_checked("worktree", "add", "-b", branch, path, base_revision)

    def remove_worktree(self, worktree_path: str) -> None:
        path = self._require_confined(worktree_path)
        self._run_checked("worktree", "remove", path)
