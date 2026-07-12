"""Tests for the deterministic review export layer + PR-C constitutional invariants."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.ibg_repository as ibg_repo
from app.ibg_repository import (
    build_review_bundle,
    stable_review_hash,
    to_dict,
    to_json,
    to_markdown,
)


# --- dict / json --------------------------------------------------------

def test_to_dict_is_canonical(make_proposal):
    b = build_review_bundle(proposal=make_proposal())
    assert to_dict(b) == b.to_canonical_dict()


def test_to_dict_rejects_non_bundle():
    with pytest.raises(TypeError):
        to_dict({"not": "a bundle"})


def test_to_json_deterministic_and_valid(make_proposal):
    p = make_proposal()
    j1 = to_json(build_review_bundle(proposal=p))
    j2 = to_json(build_review_bundle(proposal=p))
    assert j1 == j2  # byte-stable
    parsed = json.loads(j1)
    assert parsed["schema_version"] == "ibg_repository_review_bundle_v1"


def test_to_json_sorted_keys(make_proposal):
    j = to_json(build_review_bundle(proposal=make_proposal()))
    top = json.loads(j)
    assert list(top.keys()) == sorted(top.keys())


# --- markdown -----------------------------------------------------------

def test_to_markdown_deterministic(make_proposal):
    p = make_proposal()
    m1 = to_markdown(build_review_bundle(proposal=p))
    m2 = to_markdown(build_review_bundle(proposal=p))
    assert m1 == m2  # byte-stable for identical inputs


def test_markdown_has_expected_sections(make_proposal):
    m = to_markdown(build_review_bundle(proposal=make_proposal()))
    for header in [
        "## Review sections",
        "## Changed files",
        "## CBSP21 evidence",
        "## Provenance",
        "## Workspace",
    ]:
        assert header in m
    assert "(no workspace metadata supplied)" in m  # None workspace path


def test_markdown_reflects_workspace_and_provenance(make_proposal):
    p = make_proposal()

    class _Spec:
        def to_canonical_dict(self):
            return {
                "workspace_id": "wt-abc123",
                "proposal_id": p.proposal_id,
                "repository_id": "luthiers-toolbox",
                "branch": "ibg-worktree/wt-abc123",
                "worktree_path": "C:/tmp/x/wt-abc123",
                "base_revision": "a708259d",
                "allowed_paths": ["a/y.py"],
                "state": "ready",
            }

    m = to_markdown(build_review_bundle(proposal=p, workspace_metadata=_Spec()))
    assert "workspace_id: wt-abc123" in m
    assert "worktree_path" not in m  # environment path excluded from export too
    assert "full_lineage_embedded: False" in m


# --- stable hash --------------------------------------------------------

def test_stable_review_hash_deterministic(make_proposal):
    p = make_proposal()
    assert stable_review_hash(build_review_bundle(proposal=p)) == stable_review_hash(
        build_review_bundle(proposal=p)
    )


def test_stable_review_hash_changes_with_proposal(make_proposal):
    h1 = stable_review_hash(build_review_bundle(proposal=make_proposal(change_intent="a")))
    h2 = stable_review_hash(build_review_bundle(proposal=make_proposal(change_intent="b")))
    assert h1 != h2


# --- determinism invariant: no wall-clock / no unordered ---------------

def test_no_timestamp_leakage(make_proposal):
    # Two bundles built "at different times" are identical -> no time entered the canonical form.
    p = make_proposal()
    assert to_json(build_review_bundle(proposal=p)) == to_json(
        build_review_bundle(proposal=p)
    )


# --- constitutional invariant: PR-C source imports nothing dangerous ---

def test_pr_c_modules_have_no_git_or_network_imports():
    pkg_dir = Path(ibg_repo.__file__).parent
    pr_c_files = [
        "review_summary_builder.py",
        "draft_pull_request_package.py",
        "repository_review_bundle.py",
        "repository_review_export.py",
    ]
    forbidden = ("subprocess", "requests", "httpx", "urllib", "socket", "os.system", "pygithub")
    for name in pr_c_files:
        src = (pkg_dir / name).read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in src, f"{name} must not reference {token!r}"
        # must not import PR-B worktree modules (soft dependency)
        assert "worktree_builder" not in src, f"{name} must not import PR-B builder"
        assert "git_runner" not in src, f"{name} must not import git runner"
