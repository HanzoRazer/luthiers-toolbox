"""Tests for RepositoryProposalReviewPackage — wraps the existing IBG review, adds repo facts."""

from __future__ import annotations

import pytest

from app.ibg_repository import (
    RepositoryReviewPackageError,
    build_proposal_target_binding,
    build_repository_change_proposal,
    build_repository_proposal_review_package,
    compute_packet_hash,
)


def _proposal(make_candidate, make_packet):
    binding = build_proposal_target_binding(
        make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="ac5a2d35",
        authorized_target_paths=["services/api/app/ibg_repository/x.py"],
        change_intent="add",
    )
    return build_repository_change_proposal(
        target=binding, cbsp21_packet=make_packet(), proposed_branch="feature/x"
    )


def test_wraps_repo_facts_without_evidence_review(make_candidate, make_packet):
    p = _proposal(make_candidate, make_packet)
    rp = build_repository_proposal_review_package(proposal=p)
    assert rp.proposal_id == p.proposal_id
    assert rp.repository_id == "luthiers-toolbox"
    assert rp.base_revision == "ac5a2d35"
    assert rp.proposed_branch == "feature/x"
    assert rp.cbsp21_packet_hash == compute_packet_hash(p.cbsp21_packet)
    assert rp.evidence_review is None


def test_embeds_real_ibg_review_package(make_candidate, make_packet):
    # Proves reuse of the harvested review package, not a parallel model.
    from app.instrument_geometry.body.ibg.workflow.review_package import ReviewPackage

    p = _proposal(make_candidate, make_packet)
    real = ReviewPackage(package_id="rp_real", created_at="2026-07-10T00:00:00Z")
    rp = build_repository_proposal_review_package(proposal=p, evidence_review_package=real)
    assert rp.evidence_review["package_id"] == "rp_real"


def test_rejects_non_proposal():
    with pytest.raises(RepositoryReviewPackageError):
        build_repository_proposal_review_package(proposal={"x": 1})


def test_rejects_review_without_to_dict(make_candidate, make_packet):
    p = _proposal(make_candidate, make_packet)
    with pytest.raises(RepositoryReviewPackageError):
        build_repository_proposal_review_package(proposal=p, evidence_review_package=object())


def test_canonical_dict_stable(make_candidate, make_packet):
    p = _proposal(make_candidate, make_packet)
    rp = build_repository_proposal_review_package(proposal=p)
    assert rp.to_canonical_dict() == rp.to_canonical_dict()
