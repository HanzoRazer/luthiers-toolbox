"""Tests for RepositoryChangeProposal — deterministic, content-addressed, no authority."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.ibg_repository import (
    PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    RepositoryChangeProposalError,
    build_proposal_target_binding,
    build_repository_change_proposal,
)

# Authorize the package directory so the default packet's declared file
# (services/api/app/ibg_repository/proposal_target.py) falls within the boundary.
_PKG_DIR = "services/api/app/ibg_repository/"


def _binding(make_candidate, paths=(_PKG_DIR,)):
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
    binding = _binding(make_candidate, paths=("a", "b"))
    packet = make_packet(files=["b/z.py", "a/y.py"])
    p = build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/x"
    )
    assert p.changed_file_summary == ("a/y.py", "b/z.py")


def test_rejects_declared_file_outside_authorized_paths(make_candidate, make_packet):
    # A proposal may not declare a change outside its authorized boundary (fail-closed).
    binding = _binding(make_candidate, paths=("services/api/app/ibg_repository/",))
    packet = make_packet(files=["services/api/app/other/thing.py"])
    with pytest.raises(RepositoryChangeProposalError):
        build_repository_change_proposal(
            target=binding, cbsp21_packet=packet, proposed_branch="feature/x"
        )


@pytest.mark.parametrize(
    "bad_branch",
    ["", "   ", "has space", "-leading", "feature/x/", "feature/x.lock", "a..b", "a~b", "a:b"],
)
def test_rejects_invalid_branch(make_candidate, make_packet, bad_branch):
    binding = _binding(make_candidate)
    with pytest.raises(RepositoryChangeProposalError):
        build_repository_change_proposal(
            target=binding, cbsp21_packet=make_packet(), proposed_branch=bad_branch
        )


def test_proposal_id_independent_of_packet_key_order(make_candidate):
    # Content-addressing is over canonical (sorted-key) content, so dict key insertion
    # order must not change the id.
    binding = _binding(make_candidate)
    ordered = {
        "schema": "cbsp21_patch_input_v1",
        "schema_version": "cbsp21_patch_input_v1",
        "patch_id": "IBG_TEST",
        "title": "t",
        "intent": "i",
        "change_type": "feat",
        "behavior_change": "none",
        "risk_level": "low",
        "scope": {
            "paths_in_scope": ["services/api/app/ibg_repository/proposal_target.py"],
            "files_expected_to_change": ["services/api/app/ibg_repository/proposal_target.py"],
        },
        "diff_articulation": {"what_changed": "c", "why_not_redundant": "n/a"},
        "verification": {"commands_run": ["pytest"]},
    }
    reordered = dict(reversed(list(ordered.items())))
    p1 = build_repository_change_proposal(
        target=binding, cbsp21_packet=ordered, proposed_branch="feature/x"
    )
    p2 = build_repository_change_proposal(
        target=binding, cbsp21_packet=reordered, proposed_branch="feature/x"
    )
    assert p1.proposal_id == p2.proposal_id


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
        authorized_target_paths=[_PKG_DIR],
        change_intent="i",
    )
    p = build_repository_change_proposal(
        target=binding, cbsp21_packet=make_packet(), proposed_branch="feature/f"
    )
    assert p.target.source_authority_state == c.authority_state.value
    assert p.constitutional_classification == PROPOSAL_CONSTITUTIONAL_CLASSIFICATION


def test_different_target_changes_id(make_candidate, make_packet):
    # Two different authorized boundaries that both still cover the default packet file.
    p1 = build_repository_change_proposal(
        target=_binding(make_candidate, paths=("services/api",)),
        cbsp21_packet=make_packet(),
        proposed_branch="f",
    )
    p2 = build_repository_change_proposal(
        target=_binding(make_candidate, paths=("services/api/app",)),
        cbsp21_packet=make_packet(),
        proposed_branch="f",
    )
    assert p1.proposal_id != p2.proposal_id
