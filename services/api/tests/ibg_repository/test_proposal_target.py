"""Tests for ProposalTargetBinding — the constitutional evidence-input adapter."""

from __future__ import annotations

import pytest

from app.ibg_repository import (
    EvidenceContractError,
    InvalidTargetPathError,
    build_proposal_target_binding,
    normalize_producing_subsystem,
)


def _build(candidate, **over):
    kwargs = dict(
        repository_id="luthiers-toolbox",
        base_revision="ac5a2d35",
        authorized_target_paths=["services/api/app/x.py"],
        change_intent="do x",
    )
    kwargs.update(over)
    return build_proposal_target_binding(candidate, **kwargs)


def test_derives_evidence_owned_fields(make_candidate):
    c = make_candidate()
    b = _build(c)
    assert b.evidence_candidate_id == c.candidate_id
    assert b.evidence_provenance_hash == c.provenance.compute_provenance_hash()
    assert b.producing_subsystem == "body_isolation"  # normalized from system:body_isolation
    assert b.source_authority_state == c.authority_state.value


def test_rejects_untyped_dict_evidence():
    with pytest.raises(EvidenceContractError):
        build_proposal_target_binding(
            {"candidate_id": "x"},
            repository_id="r",
            base_revision="rev",
            authorized_target_paths=["a/b.py"],
            change_intent="i",
        )


def test_rejects_missing_provenance(make_candidate):
    c = make_candidate()
    c.provenance = None
    with pytest.raises(EvidenceContractError):
        _build(c)


@pytest.mark.parametrize("bad", ["/etc/passwd", "C:/win", "../escape", "a/../b", "   "])
def test_rejects_bad_paths(make_candidate, bad):
    with pytest.raises(InvalidTargetPathError):
        _build(make_candidate(), authorized_target_paths=[bad])


def test_rejects_empty_path_list(make_candidate):
    with pytest.raises(InvalidTargetPathError):
        _build(make_candidate(), authorized_target_paths=[])


def test_paths_normalized_sorted_deduped(make_candidate):
    b = _build(
        make_candidate(),
        authorized_target_paths=["b/z.py", "a/y.py", "b/z.py", "a\\x.py"],
    )
    assert b.authorized_target_paths == ("a/x.py", "a/y.py", "b/z.py")


def test_does_not_upgrade_or_mutate_candidate(make_candidate):
    c = make_candidate()
    before = c.authority_state
    _build(c)
    assert c.authority_state == before


def test_binding_is_frozen(make_candidate):
    b = _build(make_candidate())
    with pytest.raises(Exception):
        b.repository_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "actor,expected",
    [
        ("system:body_isolation", "body_isolation"),
        ("human:Reviewer Name", "reviewer_name"),
        ("system:create_candidate", "create_candidate"),
    ],
)
def test_normalize_producing_subsystem_ok(actor, expected):
    assert normalize_producing_subsystem(actor) == expected


@pytest.mark.parametrize("bad", ["", "   ", "system:", ":", None, "system::x"])
def test_normalize_producing_subsystem_fail_closed(bad):
    with pytest.raises(EvidenceContractError):
        normalize_producing_subsystem(bad)
