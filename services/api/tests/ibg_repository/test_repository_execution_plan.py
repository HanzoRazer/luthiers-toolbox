"""
Serialization + determinism tests for the RepositoryExecutionPlan contract (PR E).

Bind the contract-level guarantees independent of the planner: byte-stable canonical serialization,
JSON round-trip safety, the informational timestamp excluded from identity, content-addressed id,
frozen immutability, and the honest child-record shapes.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone

import pytest

from app.ibg_repository import (
    ComplexitySummary,
    DependencyGroup,
    EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION,
    ExecutionGroup,
    ProvenanceReference,
    RepositoryExecutionPlan,
    STRUCTURAL_GROUPING_RELATIONSHIP,
    build_cbsp21_patch_packet,
    build_execution_plan,
    build_proposal_target_binding,
    build_repository_change_proposal,
)

_DIR = "services/api/app/ibg_repository/"
_DOCS = "docs/architecture/"


def _make_proposal(make_candidate):
    files = (_DIR + "a.py", _DIR + "b.py", _DOCS + "x.md")
    authorized = [_DIR, _DOCS]
    binding = build_proposal_target_binding(
        make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="58ffadeb",
        authorized_target_paths=authorized,
        change_intent="plan the approved work",
    )
    packet = build_cbsp21_patch_packet(
        patch_id="IBG_TEST",
        title="test packet",
        intent="test intent",
        change_type="feat",
        behavior_change="none",
        risk_level="medium",
        paths_in_scope=authorized,
        files_expected_to_change=list(files),
        what_changed="adds modules",
        why_not_redundant="n/a",
        verification_commands=["pytest -q", "ruff check"],
    )
    return build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/ibg-x"
    )


def _plan(make_candidate, *, created_at=None):
    return build_execution_plan(_make_proposal(make_candidate), created_at=created_at)


# --- child record shapes -----------------------------------------------

def test_execution_group_canonical_shape():
    g = ExecutionGroup(group_id="grp-00", path_prefix="p", files=("p/a.py",))
    assert g.to_canonical_dict() == {"group_id": "grp-00", "path_prefix": "p", "files": ["p/a.py"]}


def test_dependency_group_default_relationship():
    d = DependencyGroup(group_id="grp-00", path_prefix="p", files=("p/a.py",))
    assert d.relationship == STRUCTURAL_GROUPING_RELATIONSHIP == "declared_path_grouping"
    assert d.to_canonical_dict()["relationship"] == "declared_path_grouping"


def test_complexity_summary_keeps_raw_inputs_visible():
    c = ComplexitySummary(label="medium", changed_file_count=3, authorized_path_count=2, declared_risk_level="medium")
    assert c.to_canonical_dict() == {
        "label": "medium",
        "changed_file_count": 3,
        "authorized_path_count": 2,
        "declared_risk_level": "medium",
    }


def test_provenance_reference_shape():
    r = ProvenanceReference(
        evidence_candidate_id="c",
        evidence_provenance_hash="h",
        producing_subsystem="s",
        source_authority_state="a",
    )
    assert set(r.to_canonical_dict()) == {
        "evidence_candidate_id",
        "evidence_provenance_hash",
        "producing_subsystem",
        "source_authority_state",
    }


# --- plan-level serialization ------------------------------------------

def test_canonical_serialization_byte_stable(make_candidate):
    # Identical proposal -> identical plan (planned twice from the SAME proposal).
    proposal = _make_proposal(make_candidate)
    a = build_execution_plan(proposal)
    b = build_execution_plan(proposal)
    assert json.dumps(a.to_canonical_dict(), sort_keys=True) == json.dumps(
        b.to_canonical_dict(), sort_keys=True
    )


def test_canonical_dict_json_round_trip(make_candidate):
    plan = _plan(make_candidate)
    canonical = plan.to_canonical_dict()
    assert json.loads(json.dumps(canonical)) == canonical  # JSON-safe, no non-serializable values


def test_canonical_excludes_created_at(make_candidate):
    plan = _plan(make_candidate, created_at=datetime(2026, 7, 14, tzinfo=timezone.utc))
    assert "created_at" not in plan.to_canonical_dict()


def test_audit_dict_includes_created_at(make_candidate):
    ts = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
    plan = _plan(make_candidate, created_at=ts)
    audit = plan.to_audit_dict()
    assert audit["created_at"] == ts.isoformat()
    # audit is a superset of canonical (only adds created_at)
    canonical = plan.to_canonical_dict()
    assert {k: audit[k] for k in canonical} == canonical


def test_id_matches_content_hash(make_candidate):
    plan = _plan(make_candidate)
    assert plan.execution_plan_id == "rep-" + plan.compute_plan_hash()
    assert len(plan.compute_plan_hash()) == 16


def test_created_at_does_not_change_identity(make_candidate):
    proposal = _make_proposal(make_candidate)
    a = build_execution_plan(proposal, created_at=None)
    b = build_execution_plan(proposal, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert a.execution_plan_id == b.execution_plan_id


def test_constitutional_classification_default(make_candidate):
    plan = _plan(make_candidate)
    assert plan.constitutional_classification == EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION
    assert "no_repository_authority" in plan.constitutional_classification


# --- immutability -------------------------------------------------------

def test_plan_is_frozen(make_candidate):
    plan = _plan(make_candidate)
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.planning_summary = "mutated"  # type: ignore[misc]


def test_child_records_are_frozen(make_candidate):
    plan = _plan(make_candidate)
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.estimated_complexity.label = "high"  # type: ignore[misc]
