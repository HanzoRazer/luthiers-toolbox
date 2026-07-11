"""Tests for RepositoryWorktreeSpec and its deterministic derivations."""

from __future__ import annotations

import pytest

from app.ibg_repository import (
    RepositoryWorktreeSpec,
    RepositoryWorktreeState,
    WorktreeSpecError,
    derive_branch_name,
    derive_workspace_id,
    normalize_allowed_paths,
)


def _spec(**over):
    kwargs = dict(
        workspace_id="wt-8123ab91",
        proposal_id="rcp-8123ab91",
        repository_id="luthiers-toolbox",
        branch="ibg-worktree/wt-8123ab91",
        worktree_path="C:/tmp/ltb-worktrees/wt-8123ab91",
        base_revision="a832d6e3",
        allowed_paths=("services/api/app/x.py",),
        state=RepositoryWorktreeState.NEW,
    )
    kwargs.update(over)
    return RepositoryWorktreeSpec(**kwargs)


# --- deterministic id derivation ---------------------------------------

@pytest.mark.parametrize(
    "proposal_id,expected",
    [
        ("rcp-8123ab91", "wt-8123ab91"),
        ("rcp-0011223344556677", "wt-0011223344556677"),
        ("  rcp-abcdef  ", "wt-abcdef"),
    ],
)
def test_derive_workspace_id_deterministic(proposal_id, expected):
    assert derive_workspace_id(proposal_id) == expected
    # idempotent / stable across calls
    assert derive_workspace_id(proposal_id) == expected


@pytest.mark.parametrize(
    "bad", ["", "   ", None, "rcp-", "8123ab91", "wt-8123ab91", "rcp-XYZ", "rcp-123!"]
)
def test_derive_workspace_id_fail_closed(bad):
    with pytest.raises(WorktreeSpecError):
        derive_workspace_id(bad)


def test_workspace_id_is_not_time_based():
    # Same proposal id -> identical workspace id on repeated derivation (no wall-clock component).
    a = derive_workspace_id("rcp-deadbeefcafe")
    b = derive_workspace_id("rcp-deadbeefcafe")
    assert a == b == "wt-deadbeefcafe"


# --- branch derivation --------------------------------------------------

def test_derive_branch_name():
    assert derive_branch_name("wt-8123ab91") == "ibg-worktree/wt-8123ab91"


@pytest.mark.parametrize("bad", ["", "   ", None, "8123ab91", "rcp-8123ab91", "wt-XYZ"])
def test_derive_branch_name_fail_closed(bad):
    with pytest.raises(WorktreeSpecError):
        derive_branch_name(bad)


# --- allowed path normalization ----------------------------------------

def test_normalize_allowed_paths_sorted_deduped():
    out = normalize_allowed_paths(["b/z.py", "a/y.py", "b/z.py", "a\\x.py"])
    assert out == ("a/x.py", "a/y.py", "b/z.py")


@pytest.mark.parametrize("bad", ["/etc/passwd", "C:/win", "../escape", "a/../b", "   "])
def test_normalize_allowed_paths_rejects_unsafe(bad):
    with pytest.raises(WorktreeSpecError):
        normalize_allowed_paths([bad])


def test_normalize_allowed_paths_rejects_empty():
    with pytest.raises(WorktreeSpecError):
        normalize_allowed_paths([])


# --- spec dataclass -----------------------------------------------------

def test_spec_is_frozen():
    s = _spec()
    with pytest.raises(Exception):
        s.repository_id = "other"  # type: ignore[misc]


def test_spec_default_state_is_new():
    s = RepositoryWorktreeSpec(
        workspace_id="wt-abc123",
        proposal_id="rcp-abc123",
        repository_id="r",
        branch="ibg-worktree/wt-abc123",
        worktree_path="C:/tmp/ltb-worktrees/wt-abc123",
        base_revision="rev",
    )
    assert s.state is RepositoryWorktreeState.NEW
    assert s.allowed_paths == ()


def test_with_state_returns_new_immutable_copy():
    s = _spec()
    ready = s.with_state(RepositoryWorktreeState.READY)
    assert ready is not s
    assert ready.state is RepositoryWorktreeState.READY
    assert s.state is RepositoryWorktreeState.NEW  # original unchanged
    # everything else identical
    assert ready.to_canonical_dict()["state"] == "ready"


def test_with_state_rejects_non_state():
    with pytest.raises(WorktreeSpecError):
        _spec().with_state("ready")  # type: ignore[arg-type]


def test_to_canonical_dict_deterministic_and_state_as_value():
    a = _spec().to_canonical_dict()
    b = _spec().to_canonical_dict()
    assert a == b
    assert a["state"] == "new"
    assert a["allowed_paths"] == ["services/api/app/x.py"]
    assert set(a.keys()) == {
        "workspace_id",
        "proposal_id",
        "repository_id",
        "branch",
        "worktree_path",
        "base_revision",
        "allowed_paths",
        "state",
    }


def test_state_enum_values_stable():
    assert [s.value for s in RepositoryWorktreeState] == [
        "new",
        "created",
        "ready",
        "failed",
        "disposed",
    ]
