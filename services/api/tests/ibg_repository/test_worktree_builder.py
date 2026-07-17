"""Tests for RepositoryWorktreeBuilder — planning, lifecycle, and the ownership interlock."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ibg_repository import (
    RepositoryWorktreeBuilder,
    RepositoryWorktreeState,
    WorktreeBuildError,
    build_proposal_target_binding,
    build_repository_change_proposal,
    derive_workspace_id,
)

from .fake_git_runner import FakeGitRunner


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    troot = tmp_path / "wts"
    troot.mkdir()
    return str(repo), str(troot)


@pytest.fixture
def make_proposal(make_candidate, make_packet):
    """Build a real, governed RepositoryChangeProposal from the shared candidate fixture."""

    def _make(files=("services/api/app/ibg_repository/proposal_target.py",)):
        binding = build_proposal_target_binding(
            make_candidate(),
            repository_id="luthiers-toolbox",
            base_revision="a832d6e3",
            authorized_target_paths=list(files),
            change_intent="assemble a repository proposal",
        )
        packet = make_packet(files=files)
        return build_repository_change_proposal(
            target=binding,
            cbsp21_packet=packet,
            proposed_branch="feature/ibg-proposal",
        )

    return _make


def _builder(env, **over):
    repo, troot = env
    return RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot, **over.pop("runner_kwargs", {})),
        repository_root=repo,
        temp_root=troot,
        **over,
    )


# --- construction fail-closed ------------------------------------------

def test_builder_requires_runner(env):
    repo, troot = env
    with pytest.raises(WorktreeBuildError):
        RepositoryWorktreeBuilder(None, repository_root=repo, temp_root=troot)


def test_builder_requires_existing_temp_root(env):
    repo, troot = env
    with pytest.raises(Exception):
        RepositoryWorktreeBuilder(
            FakeGitRunner(temp_root=troot), repository_root=repo, temp_root=troot + "/nope"
        )


# --- planning is pure ---------------------------------------------------

def test_plan_from_proposal_derives_deterministic_spec(env, make_proposal):
    builder = _builder(env)
    p = make_proposal()
    spec = builder.plan_from_proposal(p)
    assert spec.state is RepositoryWorktreeState.NEW
    assert spec.workspace_id == derive_workspace_id(p.proposal_id)
    assert spec.branch == "ibg-worktree/" + spec.workspace_id
    assert spec.repository_id == p.target.repository_id
    assert spec.base_revision == p.target.base_revision
    assert spec.allowed_paths == p.target.authorized_target_paths
    _, troot = env
    assert Path(spec.worktree_path).parent == Path(troot)


def test_plan_is_deterministic(env, make_proposal):
    builder = _builder(env)
    p = make_proposal()
    assert builder.plan_from_proposal(p).to_canonical_dict() == (
        builder.plan_from_proposal(p).to_canonical_dict()
    )


def test_plan_does_not_mutate_proposal(env, make_proposal):
    builder = _builder(env)
    p = make_proposal()
    before = p.to_canonical_dict()
    before_authority = p.target.source_authority_state
    builder.plan_from_proposal(p)
    assert p.to_canonical_dict() == before
    assert p.target.source_authority_state == before_authority  # never promoted


def test_plan_from_proposal_rejects_non_proposal(env):
    builder = _builder(env)
    with pytest.raises(WorktreeBuildError):
        builder.plan_from_proposal({"proposal_id": "rcp-1"})


# --- create lifecycle ---------------------------------------------------

def test_create_happy_path_records_ownership(env, make_proposal):
    builder = _builder(env)
    spec = builder.plan_from_proposal(make_proposal())
    ready = builder.create(spec)
    assert ready.state is RepositoryWorktreeState.READY
    assert ready.worktree_path == spec.worktree_path
    assert len(builder.owned_workspaces()) == 1
    # the runner was actually asked to create exactly this worktree
    assert builder._runner.created == [spec.worktree_path]  # noqa: SLF001 (test introspection)


def test_create_rejects_dirty_repo(env, make_proposal):
    repo, troot = env
    builder = RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot, clean=False), repository_root=repo, temp_root=troot
    )
    spec = builder.plan_from_proposal(make_proposal())
    with pytest.raises(WorktreeBuildError):
        builder.create(spec)
    assert builder.owned_workspaces() == ()


def test_create_dirty_override(env, make_proposal):
    repo, troot = env
    builder = RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot, clean=False),
        repository_root=repo,
        temp_root=troot,
        require_clean=False,
    )
    ready = builder.create(builder.plan_from_proposal(make_proposal()))
    assert ready.state is RepositoryWorktreeState.READY


def test_create_rejects_existing_branch(env, make_proposal):
    repo, troot = env
    proposal = make_proposal()  # build ONCE (candidate id is not deterministic across calls)
    spec_ws = derive_workspace_id(proposal.proposal_id)
    builder = RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot, existing_branches=("ibg-worktree/" + spec_ws,)),
        repository_root=repo,
        temp_root=troot,
    )
    with pytest.raises(WorktreeBuildError):
        builder.create(builder.plan_from_proposal(proposal))


def test_create_is_idempotent_guard(env, make_proposal):
    builder = _builder(env)
    spec = builder.plan_from_proposal(make_proposal())
    builder.create(spec)
    # second create of the same spec must be refused (already owned)
    with pytest.raises(WorktreeBuildError):
        builder.create(spec)


def test_create_cleans_up_registered_worktree_after_partial_failure(env, make_proposal):
    repo, troot = env
    runner = FakeGitRunner(temp_root=troot, fail_create_after_add=True)
    builder = RepositoryWorktreeBuilder(runner, repository_root=repo, temp_root=troot)
    spec = builder.plan_from_proposal(make_proposal())

    with pytest.raises(WorktreeBuildError) as err:
        builder.create(spec)

    assert err.value.spec.state is RepositoryWorktreeState.FAILED
    assert runner.created == [spec.worktree_path]
    assert runner.removed == [spec.worktree_path]
    assert builder.owned_workspaces() == ()
    assert spec.worktree_path not in runner.list_worktrees()


def test_build_from_proposal_convenience(env, make_proposal):
    builder = _builder(env)
    ready = builder.build_from_proposal(make_proposal())
    assert ready.state is RepositoryWorktreeState.READY


# --- dispose ownership interlock ---------------------------------------

def test_dispose_only_owned(env, make_proposal):
    builder = _builder(env)
    ready = builder.build_from_proposal(make_proposal())
    disposed = builder.dispose(ready)
    assert disposed.state is RepositoryWorktreeState.DISPOSED
    assert builder.owned_workspaces() == ()
    assert builder._runner.removed == [ready.worktree_path]  # noqa: SLF001


def test_dispose_refuses_foreign_worktree(env, make_proposal):
    builder = _builder(env)
    # a spec the builder never created
    foreign = builder.plan_from_proposal(make_proposal())
    with pytest.raises(WorktreeBuildError):
        builder.dispose(foreign)


def test_dispose_twice_refused(env, make_proposal):
    builder = _builder(env)
    ready = builder.build_from_proposal(make_proposal())
    builder.dispose(ready)
    with pytest.raises(WorktreeBuildError):
        builder.dispose(ready)  # no longer owned


def test_two_builders_do_not_share_ownership(env, make_proposal):
    repo, troot = env
    b1 = RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot), repository_root=repo, temp_root=troot
    )
    ready = b1.build_from_proposal(make_proposal())
    b2 = RepositoryWorktreeBuilder(
        FakeGitRunner(temp_root=troot), repository_root=repo, temp_root=troot
    )
    with pytest.raises(WorktreeBuildError):
        b2.dispose(ready)  # b2 never created it
