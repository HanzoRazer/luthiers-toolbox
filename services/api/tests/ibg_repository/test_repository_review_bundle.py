"""Tests for RepositoryReviewBundle — the derived review artifact + its input adapters."""

from __future__ import annotations

import pytest

from app.ibg_repository import (
    REVIEW_BUNDLE_CONSTITUTIONAL_CLASSIFICATION,
    REVIEW_BUNDLE_SCHEMA_VERSION,
    RepositoryReviewBundle,
    RepositoryReviewBundleError,
    build_draft_pull_request_package,
    build_review_bundle,
    normalize_workspace_metadata,
)


# --- helper fakes -------------------------------------------------------

class _FakeSpec:
    """Object exposing to_canonical_dict() like a RepositoryWorktreeSpec (no PR-B import)."""

    def __init__(self, proposal_id):
        self._d = {
            "workspace_id": "wt-abc123",
            "proposal_id": proposal_id,
            "repository_id": "luthiers-toolbox",
            "branch": "ibg-worktree/wt-abc123",
            "worktree_path": "C:/tmp/ltb-worktrees/wt-abc123",
            "base_revision": "a708259d",
            "allowed_paths": ["b/z.py", "a/y.py"],
            "state": "ready",
        }

    def to_canonical_dict(self):
        return dict(self._d)


class _FakeReviewPackage:
    def __init__(self, payload):
        self._p = payload

    def to_dict(self):
        return dict(self._p)


class _FakeProvenance:
    def __init__(self, h, payload):
        self._h = h
        self._p = payload

    def compute_provenance_hash(self):
        return self._h

    def to_dict(self):
        return dict(self._p)


# --- workspace metadata adapter ----------------------------------------

def test_workspace_none():
    assert normalize_workspace_metadata(None) is None


def test_workspace_mapping_drops_env_path_and_sorts(make_proposal):
    p = make_proposal()
    out = normalize_workspace_metadata(_FakeSpec(p.proposal_id).to_canonical_dict())
    assert "worktree_path" not in out  # environment path excluded
    assert out["allowed_paths"] == ["a/y.py", "b/z.py"]  # sorted
    assert list(out.keys()) == sorted(out.keys())


def test_workspace_object_with_to_canonical_dict(make_proposal):
    p = make_proposal()
    out = normalize_workspace_metadata(_FakeSpec(p.proposal_id))
    assert out["workspace_id"] == "wt-abc123"
    assert "worktree_path" not in out


def test_workspace_rejects_unrecognized_field():
    with pytest.raises(RepositoryReviewBundleError):
        normalize_workspace_metadata({"workspace_id": "wt-1", "rogue": "x"})


def test_workspace_rejects_non_string_key():
    with pytest.raises(RepositoryReviewBundleError):
        normalize_workspace_metadata({1: "x"})


def test_workspace_rejects_unsupported_object():
    with pytest.raises(RepositoryReviewBundleError):
        normalize_workspace_metadata(object())


def test_workspace_rejects_bad_to_canonical_return():
    class _Bad:
        def to_canonical_dict(self):
            return ["not", "a", "mapping"]

    with pytest.raises(RepositoryReviewBundleError):
        normalize_workspace_metadata(_Bad())


# --- bundle assembly ----------------------------------------------------

def test_bundle_minimal(make_proposal):
    p = make_proposal()
    b = build_review_bundle(proposal=p)
    assert isinstance(b, RepositoryReviewBundle)
    assert b.schema_version == REVIEW_BUNDLE_SCHEMA_VERSION
    assert b.proposal_id == p.proposal_id
    assert b.proposal == p.to_canonical_dict()  # embeds canonical, does not re-model
    assert b.constitutional_classification == REVIEW_BUNDLE_CONSTITUTIONAL_CLASSIFICATION
    assert b.review_package is None
    assert b.workspace_metadata is None
    assert b.provenance_lineage is None
    assert b.provenance_lineage_embedded is False


def test_bundle_provenance_reference_always_present(make_proposal):
    p = make_proposal()
    ref = build_review_bundle(proposal=p).provenance_reference
    assert ref == {
        "evidence_candidate_id": p.target.evidence_candidate_id,
        "evidence_provenance_hash": p.target.evidence_provenance_hash,
        "producing_subsystem": p.target.producing_subsystem,
        "source_authority_state": p.target.source_authority_state,
    }


def test_bundle_embeds_review_package(make_proposal):
    b = build_review_bundle(
        proposal=make_proposal(), review_package=_FakeReviewPackage({"k": "v"})
    )
    assert b.review_package == {"k": "v"}


def test_bundle_review_package_bad_type(make_proposal):
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=make_proposal(), review_package=object())


def test_bundle_embeds_verified_provenance(make_proposal):
    p = make_proposal()
    prov = _FakeProvenance(p.target.evidence_provenance_hash, {"lineage": [1, 2]})
    b = build_review_bundle(proposal=p, provenance=prov)
    assert b.provenance_lineage_embedded is True
    assert b.provenance_lineage == {"lineage": [1, 2]}


def test_bundle_rejects_provenance_hash_mismatch(make_proposal):
    p = make_proposal()
    prov = _FakeProvenance("deadbeefdeadbeef", {"lineage": []})
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=p, provenance=prov)


def test_bundle_rejects_provenance_missing_methods(make_proposal):
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=make_proposal(), provenance=object())


def test_bundle_with_workspace(make_proposal):
    p = make_proposal()
    b = build_review_bundle(proposal=p, workspace_metadata=_FakeSpec(p.proposal_id))
    assert b.workspace_metadata["workspace_id"] == "wt-abc123"


def test_bundle_accepts_prebuilt_draft(make_proposal):
    p = make_proposal()
    draft = build_draft_pull_request_package(p, target_branch="release")
    b = build_review_bundle(proposal=p, draft_pull_request=draft)
    assert b.draft_pull_request["target_branch"] == "release"


def test_bundle_rejects_mismatched_draft(make_proposal):
    p1 = make_proposal(files=("services/api/app/ibg_repository/proposal_target.py",))
    p2 = make_proposal(files=("services/api/app/ibg_repository/cbsp21_patch_adapter.py",))
    draft_for_p2 = build_draft_pull_request_package(p2)
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=p1, draft_pull_request=draft_for_p2)


def test_bundle_rejects_non_proposal():
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal={"proposal_id": "rcp-1"})


# --- regression: proposal not mutated / authority not promoted ---------

def test_bundle_does_not_mutate_or_promote_proposal(make_proposal):
    p = make_proposal()
    before = p.to_canonical_dict()
    before_authority = p.target.source_authority_state
    build_review_bundle(proposal=p)
    assert p.to_canonical_dict() == before
    assert p.target.source_authority_state == before_authority


def test_bundle_deterministic(make_proposal):
    p = make_proposal()
    a = build_review_bundle(proposal=p).to_canonical_dict()
    b = build_review_bundle(proposal=p).to_canonical_dict()
    assert a == b


# --- canonicalization + embed edge cases (defensive branches) ----------

def test_review_package_mapping_embedded(make_proposal):
    b = build_review_bundle(proposal=make_proposal(), review_package={"k": "v", "n": 1})
    assert b.review_package == {"k": "v", "n": 1}


def test_canonicalize_rejects_nested_non_string_key(make_proposal):
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=make_proposal(), review_package={"outer": {1: "x"}})


def test_canonicalize_rejects_unsupported_value_type(make_proposal):
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=make_proposal(), review_package={"bad": {1, 2, 3}})


def test_review_package_to_dict_non_mapping(make_proposal):
    class _Bad:
        def to_dict(self):
            return ["not", "a", "mapping"]

    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=make_proposal(), review_package=_Bad())


def test_provenance_to_dict_non_mapping(make_proposal):
    p = make_proposal()

    class _BadProv:
        def compute_provenance_hash(self):
            return p.target.evidence_provenance_hash

        def to_dict(self):
            return ["nope"]

    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=p, provenance=_BadProv())


def test_bundle_rejects_bad_draft_type(make_proposal):
    with pytest.raises(RepositoryReviewBundleError):
        build_review_bundle(proposal=make_proposal(), draft_pull_request="not a package")
