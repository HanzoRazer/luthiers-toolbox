"""Tests for the fail-closed worktree validation gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ibg_repository import (
    RepositoryWorktreeSpec,
    RepositoryWorktreeState,
    WorktreeValidationError,
    normalize_workspace_path,
    validate_branch,
    validate_deterministic_naming,
    validate_worktree,
    verify_repository_root,
    verify_temp_root,
)

from fake_git_runner import FakeGitRunner


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    troot = tmp_path / "wts"
    troot.mkdir()
    return str(repo), str(troot)


def _spec(troot, **over):
    ws = over.pop("workspace_id", "wt-8123ab91")
    kwargs = dict(
        workspace_id=ws,
        proposal_id="rcp-8123ab91",
        repository_id="luthiers-toolbox",
        branch="ibg-worktree/" + ws,
        worktree_path=str(Path(troot) / ws),
        base_revision="a832d6e3",
        allowed_paths=("services/api/app/x.py",),
        state=RepositoryWorktreeState.NEW,
    )
    kwargs.update(over)
    return RepositoryWorktreeSpec(**kwargs)


# --- root verification --------------------------------------------------

def test_verify_temp_root_ok(env):
    _, troot = env
    assert verify_temp_root(troot)


@pytest.mark.parametrize("bad", ["", "   ", None])
def test_verify_temp_root_fail_closed(bad):
    with pytest.raises(WorktreeValidationError):
        verify_temp_root(bad)


def test_verify_temp_root_must_exist(tmp_path):
    with pytest.raises(WorktreeValidationError):
        verify_temp_root(str(tmp_path / "nope"))


def test_verify_repository_root_requires_git(tmp_path):
    with pytest.raises(WorktreeValidationError):
        verify_repository_root(str(tmp_path))


# --- path confinement ---------------------------------------------------

def test_normalize_workspace_path_confined(env):
    _, troot = env
    p = normalize_workspace_path(troot, str(Path(troot) / "wt-abc"))
    assert p.endswith("wt-abc") or "wt-abc" in p


def test_normalize_workspace_path_rejects_traversal(env):
    _, troot = env
    with pytest.raises(WorktreeValidationError):
        normalize_workspace_path(troot, str(Path(troot) / ".." / "escape"))


def test_normalize_workspace_path_rejects_outside(env):
    _, troot = env
    with pytest.raises(WorktreeValidationError):
        normalize_workspace_path(troot, "C:/somewhere/else/wt-x")


# --- deterministic naming ----------------------------------------------

def test_validate_deterministic_naming_ok(env):
    _, troot = env
    validate_deterministic_naming(_spec(troot))


def test_validate_deterministic_naming_rejects_mismatched_workspace_id(env):
    _, troot = env
    # workspace_id not derived from proposal_id
    spec = _spec(troot, workspace_id="wt-deadbeef", branch="ibg-worktree/wt-deadbeef",
                 worktree_path=str(Path(troot) / "wt-deadbeef"))
    with pytest.raises(WorktreeValidationError):
        validate_deterministic_naming(spec)


def test_validate_deterministic_naming_rejects_hand_edited_branch(env):
    _, troot = env
    spec = _spec(troot, branch="main")
    with pytest.raises(WorktreeValidationError):
        validate_deterministic_naming(spec)


# --- branch checks ------------------------------------------------------

def test_validate_branch_rejects_existing(env):
    _, troot = env
    spec = _spec(troot)
    runner = FakeGitRunner(temp_root=troot, existing_branches=(spec.branch,))
    with pytest.raises(WorktreeValidationError):
        validate_branch(spec, runner)


# --- full gate ----------------------------------------------------------

def test_validate_worktree_happy_path(env):
    _, troot = env
    runner = FakeGitRunner(temp_root=troot)
    validate_worktree(_spec(troot), runner, temp_root=troot)


def test_validate_worktree_rejects_dirty_repo(env):
    _, troot = env
    runner = FakeGitRunner(temp_root=troot, clean=False)
    with pytest.raises(WorktreeValidationError):
        validate_worktree(_spec(troot), runner, temp_root=troot)


def test_validate_worktree_dirty_override_allows(env):
    _, troot = env
    runner = FakeGitRunner(temp_root=troot, clean=False)
    validate_worktree(_spec(troot), runner, temp_root=troot, require_clean=False)


def test_validate_worktree_rejects_existing_worktree(env):
    _, troot = env
    spec = _spec(troot)
    runner = FakeGitRunner(temp_root=troot, existing_worktrees=(spec.worktree_path,))
    with pytest.raises(WorktreeValidationError):
        validate_worktree(spec, runner, temp_root=troot)


def test_validate_worktree_rejects_existing_branch(env):
    _, troot = env
    spec = _spec(troot)
    runner = FakeGitRunner(temp_root=troot, existing_branches=(spec.branch,))
    with pytest.raises(WorktreeValidationError):
        validate_worktree(spec, runner, temp_root=troot)


def test_validate_worktree_rejects_repo_without_revision(env):
    _, troot = env
    runner = FakeGitRunner(temp_root=troot, revision="")
    with pytest.raises(WorktreeValidationError):
        validate_worktree(_spec(troot), runner, temp_root=troot)


def test_validate_worktree_rejects_unresolvable_base_revision(env):
    _, troot = env
    runner = FakeGitRunner(
        temp_root=troot,
        known_revisions=("1111111111111111111111111111111111111111",),
    )
    with pytest.raises(WorktreeValidationError, match="base_revision"):
        validate_worktree(_spec(troot, base_revision="deadbeef"), runner, temp_root=troot)
