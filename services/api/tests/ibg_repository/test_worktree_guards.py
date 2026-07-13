"""Fast guard-clause coverage for the worktree layer (no candidate fixture, no real git)."""

from __future__ import annotations

import pytest

from app.ibg_repository import (
    GitCommandError,
    LocalGitRunner,
    RepositoryWorktreeBuilder,
    WorktreeBuildError,
    WorktreeSpecError,
    WorktreeValidationError,
    normalize_allowed_paths,
    normalize_repository_path,
    validate_repository,
    verify_repository_root,
)

from fake_git_runner import FakeGitRunner


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    troot = tmp_path / "wts"
    troot.mkdir()
    return str(repo), str(troot)


# --- spec guards --------------------------------------------------------

def test_normalize_allowed_paths_none():
    with pytest.raises(WorktreeSpecError):
        normalize_allowed_paths(None)


# --- validator guards ---------------------------------------------------

def test_verify_repository_root_empty_string():
    with pytest.raises(WorktreeValidationError):
        verify_repository_root("")


def test_normalize_repository_path_roundtrip(env):
    repo, _ = env
    assert normalize_repository_path(repo)


def test_validate_repository_direct_ok(env):
    _, troot = env
    runner = FakeGitRunner(temp_root=troot)

    class _Spec:
        base_revision = "a832d6e3"

    validate_repository(_Spec(), runner)  # revision non-empty -> ok


def test_validate_repository_direct_empty_revision(env):
    _, troot = env
    runner = FakeGitRunner(temp_root=troot, revision="")
    with pytest.raises(WorktreeValidationError):
        validate_repository(object(), runner)


# --- builder guards -----------------------------------------------------

def test_builder_properties_and_plan_guards(env):
    repo, troot = env
    builder = RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot), repository_root=repo, temp_root=troot
    )
    assert builder.temp_root == troot
    assert builder.repository_root == repo
    with pytest.raises(WorktreeBuildError):
        builder.plan(proposal_id="rcp-abc123", repository_id="  ",
                     base_revision="rev", allowed_paths=["a/b.py"])
    with pytest.raises(WorktreeBuildError):
        builder.plan(proposal_id="rcp-abc123", repository_id="r",
                     base_revision="  ", allowed_paths=["a/b.py"])


def test_builder_create_and_dispose_reject_non_spec(env):
    repo, troot = env
    builder = RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot), repository_root=repo, temp_root=troot
    )
    with pytest.raises(WorktreeBuildError):
        builder.create({"not": "a spec"})
    with pytest.raises(WorktreeBuildError):
        builder.dispose({"not": "a spec"})


# --- git_runner guards --------------------------------------------------

def test_local_runner_properties_and_arg_guards(env):
    repo, troot = env

    class _Seam:
        def __call__(self, argv):
            from app.ibg_repository import CommandResult

            return CommandResult(0, "", "")

    runner = LocalGitRunner(repo, troot, command_seam=_Seam())
    assert runner.repository_root == repo
    assert runner.temp_root == troot
    with pytest.raises(GitCommandError):
        runner.create_worktree("", "b", "rev")  # empty worktree_path
    with pytest.raises(GitCommandError):
        runner.create_worktree(troot + "/wt-x", "  ", "rev")  # empty branch
    with pytest.raises(GitCommandError):
        runner.create_worktree(troot + "/wt-x", "b", "  ")  # empty base_revision
    with pytest.raises(GitCommandError):
        runner.branch_exists("  ")  # empty branch
