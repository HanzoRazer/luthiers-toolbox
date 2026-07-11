"""Tests for RepositoryChangeProposal — deterministic, content-addressed, no authority."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.ibg_repository import (
    PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    build_proposal_target_binding,
    build_repository_change_proposal,
)


def _binding(make_candidate, paths=("services/api/app/ibg_repository/x.py",)):
    return build_proposal_target_binding(
        make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="ac5a2d35",
        authorized_target_paths=list(paths),
        change_intent="add contracts",
    )


def test_proposal_deterministic_for_identical_inputs(make_candidate, make_packet):
    binding = _binding(make_candidate)
    packet = make_packet()
    p1 = build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/x"
    )
    p2 = build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/x"
    )
    assert p1.proposal_id == p2.proposal_id
    assert p1.compute_proposal_hash() == p2.compute_proposal_hash()
    assert p1.to_canonical_dict() == p2.to_canonical_dict()
    assert p1.proposal_id == "rcp-" + p1.compute_proposal_hash()


def test_created_at_excluded_from_canonical_and_id(make_candidate, make_packet):
    binding = _binding(make_candidate)
    ts = datetime(2026, 7, 10, tzinfo=timezone.utc)
    with_ts = build_repository_change_proposal(
        target=binding, cbsp21_packet=make_packet(), proposed_branch="feature/x", created_at=ts
    )
    without_ts = build_repository_change_proposal(
        target=binding, cbsp21_packet=make_packet(), proposed_branch="feature/x"
    )
    assert "created_at" not in with_ts.to_canonical_dict()
    assert with_ts.to_audit_dict()["created_at"] == ts.isoformat()
    assert with_ts.proposal_id == without_ts.proposal_id  # timestamp does not affect the id


def test_changed_file_summary_derived_and_sorted(make_candidate, make_packet):
    binding = _binding(make_candidate)
    packet = make_packet(files=["b/z.py", "a/y.py"])
    p = build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/x"
    )
    assert p.changed_file_summary == ("a/y.py", "b/z.py")


def test_rejects_invalid_packet(make_candidate):
    binding = _binding(make_candidate)
    with pytest.raises(Exception):
        build_repository_change_proposal(
            target=binding, cbsp21_packet={"bad": True}, proposed_branch="f"
        )


def test_does_not_upgrade_authority_state(make_candidate, make_packet):
    c = make_candidate()
    binding = build_proposal_target_binding(
        c,
        repository_id="r",
        base_revision="rev",
        authorized_target_paths=["a/b.py"],
        change_intent="i",
    )
    p = build_repository_change_proposal(
        target=binding, cbsp21_packet=make_packet(), proposed_branch="f"
    )
    assert p.target.source_authority_state == c.authority_state.value
    assert p.constitutional_classification == PROPOSAL_CONSTITUTIONAL_CLASSIFICATION


def test_different_target_changes_id(make_candidate, make_packet):
    p1 = build_repository_change_proposal(
        target=_binding(make_candidate, paths=("a/x.py",)),
        cbsp21_packet=make_packet(),
        proposed_branch="f",
    )
    p2 = build_repository_change_proposal(
        target=_binding(make_candidate, paths=("a/y.py",)),
        cbsp21_packet=make_packet(),
        proposed_branch="f",
    )
    assert p1.proposal_id != p2.proposal_id
