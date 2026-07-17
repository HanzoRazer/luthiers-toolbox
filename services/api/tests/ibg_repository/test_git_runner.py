"""
Tests for the GitRunner abstraction.

Three layers:
  1. the in-memory FakeGitRunner behaves as a GitRunner;
  2. LocalGitRunner builds explicit argv lists (no shell) and confines worktree paths — asserted
     through an injected recording command seam, no real git spawned;
  3. ONE bounded integration test drives LocalGitRunner against a throwaway git repo created under
     the pytest tmp directory (skipped if git is unavailable).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from app.ibg_repository import (
    CommandResult,
    GitCommandError,
    GitRunner,
    GitRunnerConfigError,
    LocalGitRunner,
)
from app.ibg_repository.git_runner import (
    DEFAULT_GIT_TIMEOUT_SECONDS,
    _default_command_seam,
)

from .fake_git_runner import FakeGitRunner


# --- layer 1: fake conforms to the protocol -----------------------------

def test_fake_is_a_git_runner(tmp_path):
    fake = FakeGitRunner(temp_root=str(tmp_path))
    assert isinstance(fake, GitRunner)  # runtime_checkable structural check


def test_fake_create_and_remove_roundtrip(tmp_path):
    fake = FakeGitRunner(temp_root=str(tmp_path))
    wt = str(tmp_path / "wt-abc123")
    fake.create_worktree(wt, "ibg-worktree/wt-abc123", "rev")
    assert wt in fake.created
    assert fake.branch_exists("ibg-worktree/wt-abc123")
    assert any(Path(p) == Path(wt) for p in fake.list_worktrees())
    fake.remove_worktree(wt)
    assert wt in fake.removed


def test_fake_resolves_known_revision_prefix(tmp_path):
    fake = FakeGitRunner(
        temp_root=str(tmp_path),
        revision="a832d6e3a832d6e3a832d6e3a832d6e3a832d6e3",
    )
    assert fake.resolve_revision("a832d6e3").startswith("a832d6e3")
    with pytest.raises(GitCommandError):
        fake.resolve_revision("deadbeef")


def test_fake_rejects_path_outside_temp_root(tmp_path):
    fake = FakeGitRunner(temp_root=str(tmp_path))
    with pytest.raises(GitCommandError):
        fake.create_worktree("C:/somewhere/else", "b", "rev")


# --- layer 2: LocalGitRunner argv seam (no real git) --------------------

class RecordingSeam:
    def __init__(self, result=None):
        self.calls = []
        self._result = result or CommandResult(0, "", "")

    def __call__(self, argv):
        self.calls.append(list(argv))
        return self._result


@pytest.fixture
def fake_repo(tmp_path):
    """A directory that *looks* like a repo (has .git) plus a temp root, no real git needed."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    troot = tmp_path / "wts"
    troot.mkdir()
    return str(repo), str(troot)


def test_local_runner_requires_explicit_roots(tmp_path):
    with pytest.raises(GitRunnerConfigError):
        LocalGitRunner("", str(tmp_path))
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(GitRunnerConfigError):
        LocalGitRunner(str(repo), "")  # no silent temp-root default


def test_local_runner_rejects_non_repo(tmp_path):
    troot = tmp_path / "wts"
    troot.mkdir()
    with pytest.raises(GitRunnerConfigError):
        LocalGitRunner(str(tmp_path / "not-a-repo"), str(troot))


def test_local_runner_rejects_missing_temp_root(fake_repo):
    repo, _ = fake_repo
    with pytest.raises(GitRunnerConfigError):
        LocalGitRunner(repo, repo + "/does-not-exist")


def test_create_worktree_uses_explicit_argv_no_shell(fake_repo):
    repo, troot = fake_repo
    seam = RecordingSeam()
    runner = LocalGitRunner(repo, troot, command_seam=seam)
    wt = str(Path(troot) / "wt-abc123")
    runner.create_worktree(wt, "ibg-worktree/wt-abc123", "a832d6e3")
    assert seam.calls == [
        ["git", "-C", repo, "worktree", "add", "-b", "ibg-worktree/wt-abc123", wt, "a832d6e3"]
    ]
    # argv is a list of discrete tokens — no single shell string, no interpolation surface.
    assert all(isinstance(tok, str) for tok in seam.calls[0])


def test_remove_worktree_argv(fake_repo):
    repo, troot = fake_repo
    seam = RecordingSeam()
    runner = LocalGitRunner(repo, troot, command_seam=seam)
    wt = str(Path(troot) / "wt-abc123")
    runner.remove_worktree(wt)
    assert seam.calls == [["git", "-C", repo, "worktree", "remove", wt]]


def test_create_worktree_confined_to_temp_root(fake_repo):
    repo, troot = fake_repo
    seam = RecordingSeam()
    runner = LocalGitRunner(repo, troot, command_seam=seam)
    with pytest.raises(GitCommandError):
        runner.create_worktree(repo + "/inside-repo", "b", "rev")  # outside temp_root
    assert seam.calls == []  # rejected before any command was issued


def test_branch_exists_returns_false_when_branch_missing(fake_repo):
    repo, troot = fake_repo
    runner = LocalGitRunner(repo, troot, command_seam=RecordingSeam(CommandResult(1)))
    assert runner.branch_exists("whatever") is False


def test_branch_exists_raises_on_unexpected_git_error(fake_repo):
    repo, troot = fake_repo
    runner = LocalGitRunner(repo, troot, command_seam=RecordingSeam(CommandResult(128, "", "broken")))
    with pytest.raises(GitCommandError):
        runner.branch_exists("whatever")


def test_resolve_revision_uses_commitish_verification(fake_repo):
    repo, troot = fake_repo
    seam = RecordingSeam(CommandResult(0, "a832d6e3\n", ""))
    runner = LocalGitRunner(repo, troot, command_seam=seam)
    assert runner.resolve_revision("a832d6e3") == "a832d6e3"
    assert seam.calls == [
        ["git", "-C", repo, "rev-parse", "--verify", "a832d6e3^{commit}"]
    ]


def test_repository_clean_reflects_porcelain(fake_repo):
    repo, troot = fake_repo
    dirty = LocalGitRunner(repo, troot, command_seam=RecordingSeam(CommandResult(0, " M x")))
    clean = LocalGitRunner(repo, troot, command_seam=RecordingSeam(CommandResult(0, "")))
    assert dirty.repository_clean() is False
    assert clean.repository_clean() is True


def test_checked_command_raises_on_failure(fake_repo):
    repo, troot = fake_repo
    runner = LocalGitRunner(repo, troot, command_seam=RecordingSeam(CommandResult(128, "", "boom")))
    with pytest.raises(GitCommandError):
        runner.current_revision()


def test_default_command_seam_returns_timeout_result(monkeypatch):
    calls = {}

    def _timeout(*args, **kwargs):
        calls["timeout"] = kwargs.get("timeout")
        raise subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=kwargs.get("timeout"),
            output="stdout-before-timeout",
            stderr="stderr-before-timeout",
        )

    monkeypatch.setattr(subprocess, "run", _timeout)
    result = _default_command_seam(["git", "status"])
    assert calls["timeout"] == DEFAULT_GIT_TIMEOUT_SECONDS
    assert result.returncode == 124
    assert "timed out" in result.stderr


# --- layer 3: one bounded real-git integration test ---------------------

def _git_available() -> bool:
    return shutil.which("git") is not None


@pytest.mark.skipif(not _git_available(), reason="git not on PATH")
def test_local_runner_real_worktree_bounded(tmp_path):
    """Fully isolated under tmp_path: init a repo, add + list + remove a worktree via the runner."""
    repo = tmp_path / "repo"
    repo.mkdir()

    def g(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)

    g("init")
    g("config", "user.email", "t@example.com")
    g("config", "user.name", "t")
    g("commit", "--allow-empty", "-m", "root")

    troot = tmp_path / "wts"
    troot.mkdir()
    runner = LocalGitRunner(str(repo), str(troot))

    assert runner.repository_clean() is True
    rev = runner.current_revision()
    assert len(rev) >= 7
    assert runner.resolve_revision(rev) == rev
    assert runner.branch_exists("ibg-worktree/wt-real01") is False

    wt = str(troot / "wt-real01")
    runner.create_worktree(wt, "ibg-worktree/wt-real01", rev)
    assert Path(wt).is_dir()
    assert runner.branch_exists("ibg-worktree/wt-real01") is True
    assert any(Path(p) == Path(wt) for p in runner.list_worktrees())

    runner.remove_worktree(wt)
    assert not Path(wt).exists()
