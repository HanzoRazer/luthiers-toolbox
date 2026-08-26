"""Read-only Git adapter tests using a real temporary repository."""

from __future__ import annotations

import subprocess

import pytest

from tools.grounding_agent.adapters.git_repo import GitRepoAdapter


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


@pytest.fixture
def temp_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "first.txt").write_text("one\n")
    _git(root, "add", "first.txt")
    _git(root, "commit", "-q", "-m", "first")
    first = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    (root / "second.txt").write_text("two\n")
    _git(root, "add", "second.txt")
    _git(root, "commit", "-q", "-m", "second")
    second = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    return root, first, second


def test_resolve_ref(temp_repo):
    root, first, second = temp_repo
    adapter = GitRepoAdapter(str(root))
    assert adapter.resolve_ref("HEAD") == second
    assert adapter.resolve_ref(first) == first


def test_resolve_ref_unknown(temp_repo):
    root, _first, _second = temp_repo
    adapter = GitRepoAdapter(str(root))
    assert adapter.resolve_ref("does-not-exist") is None


def test_is_ancestor_true_and_false(temp_repo):
    root, first, second = temp_repo
    adapter = GitRepoAdapter(str(root))
    assert adapter.is_ancestor(first, "HEAD") is True
    assert adapter.is_ancestor(second, first) is False


def test_is_ancestor_unknown_commit_returns_none(temp_repo):
    root, _first, _second = temp_repo
    adapter = GitRepoAdapter(str(root))
    assert adapter.is_ancestor("deadbeef", "HEAD") is None


def test_file_exists_at_ref(temp_repo):
    root, first, _second = temp_repo
    adapter = GitRepoAdapter(str(root))
    assert adapter.file_exists_at_ref("HEAD", "second.txt") is True
    # second.txt did not exist at the first commit.
    assert adapter.file_exists_at_ref(first, "second.txt") is False
    assert adapter.file_exists_at_ref("HEAD", "first.txt") is True


def test_file_exists_at_unknown_ref_returns_none(temp_repo):
    root, _first, _second = temp_repo
    adapter = GitRepoAdapter(str(root))
    assert adapter.file_exists_at_ref("no-such-ref", "first.txt") is None


def test_worktree_status_clean(temp_repo):
    root, _first, _second = temp_repo
    adapter = GitRepoAdapter(str(root))
    status = adapter.worktree_status()
    assert status is not None
    assert status.tracked_dirty is False
    assert status.untracked is False


def test_worktree_status_tracked_dirty_vs_untracked(temp_repo):
    root, _first, _second = temp_repo
    adapter = GitRepoAdapter(str(root))
    # Modify a tracked file -> tracked_dirty
    (root / "first.txt").write_text("one-changed\n")
    status = adapter.worktree_status()
    assert status.tracked_dirty is True
    assert status.untracked is False
    # Add an untracked file -> untracked, still tracked_dirty from above
    (root / "brand_new.txt").write_text("hi\n")
    status = adapter.worktree_status()
    assert status.tracked_dirty is True
    assert status.untracked is True
    assert "brand_new.txt" in status.untracked_files


def test_repository_root(temp_repo):
    root, _first, _second = temp_repo
    adapter = GitRepoAdapter(str(root))
    resolved = adapter.repository_root()
    assert resolved is not None
    assert resolved.endswith("repo")
