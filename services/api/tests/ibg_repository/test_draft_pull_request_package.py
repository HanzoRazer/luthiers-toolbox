"""Tests for DraftPullRequestPackage — advisory PR metadata, no git/network."""

from __future__ import annotations

import pytest

from app.ibg_repository import (
    DRAFT_PR_CONSTITUTIONAL_CLASSIFICATION,
    DraftPullRequestPackage,
    DraftPullRequestPackageError,
    build_draft_pull_request_package,
    compute_packet_hash,
)


def test_branch_name_is_proposed_branch(make_proposal):
    p = make_proposal(proposed_branch="feature/my-head")
    pkg = build_draft_pull_request_package(p)
    assert pkg.branch_name == "feature/my-head"  # the intended PR head, not a worktree branch
    assert pkg.target_branch == "main"  # default


def test_target_branch_caller_supplied(make_proposal):
    pkg = build_draft_pull_request_package(make_proposal(), target_branch="develop")
    assert pkg.target_branch == "develop"


def test_carries_proposal_facts(make_proposal):
    p = make_proposal()
    pkg = build_draft_pull_request_package(p)
    assert pkg.proposal_id == p.proposal_id
    assert pkg.changed_file_summary == p.changed_file_summary
    assert pkg.cbsp21_patch_id == str(p.cbsp21_packet["patch_id"])
    assert pkg.cbsp21_packet_hash == compute_packet_hash(p.cbsp21_packet)
    assert pkg.constitutional_classification == DRAFT_PR_CONSTITUTIONAL_CLASSIFICATION


def test_is_frozen(make_proposal):
    pkg = build_draft_pull_request_package(make_proposal())
    with pytest.raises(Exception):
        pkg.title = "x"  # type: ignore[misc]


def test_deterministic(make_proposal):
    p = make_proposal()
    a = build_draft_pull_request_package(p, target_branch="main").to_canonical_dict()
    b = build_draft_pull_request_package(p, target_branch="main").to_canonical_dict()
    assert a == b


@pytest.mark.parametrize(
    "bad", ["", "  ", " feature/x", "feature/x ", "a b", "-x", "/x", "x/", "a..b", "a~b", "a:b", "x.lock"]
)
def test_rejects_unsafe_target_branch(make_proposal, bad):
    with pytest.raises(DraftPullRequestPackageError):
        build_draft_pull_request_package(make_proposal(), target_branch=bad)


def test_rejects_non_proposal():
    with pytest.raises(DraftPullRequestPackageError):
        build_draft_pull_request_package({"proposal_id": "rcp-1"})


def test_custom_review_sections_used(make_proposal):
    pkg = build_draft_pull_request_package(
        make_proposal(), review_sections=[("Only", "one section")]
    )
    assert pkg.review_sections == ({"heading": "Only", "body": "one section"},)


def test_duplicate_custom_sections_rejected(make_proposal):
    with pytest.raises(Exception):
        build_draft_pull_request_package(
            make_proposal(), review_sections=[("Dup", "a"), ("dup", "b")]
        )


def test_to_canonical_dict_shape(make_proposal):
    d = build_draft_pull_request_package(make_proposal()).to_canonical_dict()
    assert set(d.keys()) == {
        "title",
        "summary",
        "proposal_id",
        "branch_name",
        "target_branch",
        "review_sections",
        "changed_file_summary",
        "constitutional_classification",
        "cbsp21_patch_id",
        "cbsp21_packet_hash",
    }
