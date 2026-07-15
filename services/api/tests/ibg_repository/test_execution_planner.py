"""
Invariant tests for the descriptive ExecutionPlanner (PR E).

These bind the ratified boundary: the planner DERIVES every field from the proposal + its CBSP21
packet, INVENTS no ordering/dependency/effort, PRESERVES provenance exactly, does NOT upgrade
authority or mutate the proposal, is DETERMINISTIC, and performs NO git / filesystem-mutation /
GitHub / network operation. Where the source lacks information, the plan says so structurally
(``structural_dependency_groups`` with ``declared_path_grouping``), never fabricating edges.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from pathlib import Path

import pytest

import app.ibg_repository as ibg_repo
from app.ibg_repository import (
    ComplexitySummary,
    DependencyGroup,
    ExecutionGroup,
    ExecutionPlanner,
    ExecutionPlanningError,
    ProvenanceReference,
    RepositoryExecutionPlan,
    SUPPORTED_RISK_LEVELS,
    build_cbsp21_patch_packet,
    build_execution_plan,
    build_proposal_target_binding,
    build_repository_change_proposal,
    execution_plan_builder,
    validate_execution_plan,
)


def _proposal(
    make_candidate,
    *,
    files,
    authorized=None,
    risk="low",
    verification=("pytest",),
    change_type="feat",
):
    authorized = list(authorized) if authorized is not None else list(files)
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
        change_type=change_type,
        behavior_change="none",
        risk_level=risk,
        paths_in_scope=authorized,
        files_expected_to_change=list(files),
        what_changed="adds modules",
        why_not_redundant="n/a",
        verification_commands=list(verification),
    )
    return build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/ibg-x"
    )


_DIR = "services/api/app/ibg_repository/"
_DOCS = "docs/architecture/"


# --- stable id + determinism -------------------------------------------

def test_stable_execution_plan_id(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    a = build_execution_plan(p)
    b = build_execution_plan(p)
    assert a.execution_plan_id == b.execution_plan_id
    assert a.execution_plan_id.startswith("rep-")
    assert a.to_canonical_dict() == b.to_canonical_dict()


def test_id_matches_content_hash(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    plan = build_execution_plan(p)
    assert plan.execution_plan_id == "rep-" + plan.compute_plan_hash()


def test_distinct_proposals_yield_distinct_plans(make_candidate):
    p1 = _proposal(make_candidate, files=(_DIR + "a.py",))
    p2 = _proposal(make_candidate, files=(_DIR + "a.py", _DIR + "b.py"))
    assert build_execution_plan(p1).execution_plan_id != build_execution_plan(p2).execution_plan_id


def test_audit_timestamp_excluded_from_identity(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    with_ts = build_execution_plan(p, created_at=datetime(2026, 7, 14, tzinfo=timezone.utc))
    without_ts = build_execution_plan(p, created_at=None)
    assert with_ts.execution_plan_id == without_ts.execution_plan_id
    assert with_ts.to_canonical_dict() == without_ts.to_canonical_dict()
    assert with_ts.to_audit_dict()["created_at"] == "2026-07-14T00:00:00+00:00"
    assert without_ts.to_audit_dict()["created_at"] is None


# --- provenance preserved + authority unchanged ------------------------

def test_provenance_reference_preserved_exactly(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    plan = build_execution_plan(p)
    t = p.target
    assert plan.provenance_reference == ProvenanceReference(
        evidence_candidate_id=t.evidence_candidate_id,
        evidence_provenance_hash=t.evidence_provenance_hash,
        producing_subsystem=t.producing_subsystem,
        source_authority_state=t.source_authority_state,
    )


def test_source_authority_unchanged(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    plan = build_execution_plan(p)
    assert plan.provenance_reference.source_authority_state == p.target.source_authority_state


def test_original_proposal_object_unchanged(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    before = p.to_canonical_dict()
    build_execution_plan(p)
    assert p.to_canonical_dict() == before  # planning never mutates its input


# --- validation sequence copied without invention ----------------------

def test_validation_sequence_copied_verbatim_in_order(make_candidate):
    cmds = ("pytest -q tests/ibg_repository", "ruff check services/api/app/ibg_repository")
    p = _proposal(make_candidate, files=(_DIR + "a.py",), verification=cmds)
    plan = build_execution_plan(p)
    assert plan.recommended_validation_sequence == cmds  # same order, nothing added or removed


# --- deterministic path grouping ---------------------------------------

def test_deterministic_path_grouping(make_candidate):
    files = (_DIR + "b.py", _DIR + "a.py", _DOCS + "x.md")
    p = _proposal(make_candidate, files=files, authorized=[_DIR, _DOCS])
    plan = build_execution_plan(p)
    # Two authorized-path groups, ordered by path_prefix; files within each group sorted.
    assert [g.path_prefix for g in plan.recommended_commit_sequence] == [
        "docs/architecture",
        "services/api/app/ibg_repository",
    ]
    assert plan.recommended_commit_sequence[0].files == ("docs/architecture/x.md",)
    assert plan.recommended_commit_sequence[1].files == (
        "services/api/app/ibg_repository/a.py",
        "services/api/app/ibg_repository/b.py",
    )
    # review order reuses the SAME evidence-backed groups in the SAME order (no inferred priority)
    assert [g.to_canonical_dict() for g in plan.recommended_review_order] == [
        g.to_canonical_dict() for g in plan.recommended_commit_sequence
    ]


def test_most_specific_prefix_wins_for_nested_authorized(make_candidate):
    # A file under a nested authorized path is assigned to the most specific group, deterministically.
    files = (_DIR + "sub/deep.py",)
    p = _proposal(make_candidate, files=files, authorized=[_DIR, _DIR + "sub/"])
    plan = build_execution_plan(p)
    assert [g.path_prefix for g in plan.recommended_commit_sequence] == [
        "services/api/app/ibg_repository/sub"
    ]


# --- no synthetic dependency edges -------------------------------------

def test_structural_dependency_groups_assert_no_edges(make_candidate):
    files = (_DIR + "a.py", _DOCS + "x.md")
    p = _proposal(make_candidate, files=files, authorized=[_DIR, _DOCS])
    plan = build_execution_plan(p)
    assert all(isinstance(d, DependencyGroup) for d in plan.structural_dependency_groups)
    assert all(d.relationship == "declared_path_grouping" for d in plan.structural_dependency_groups)
    # the grouping mirrors the commit groups; it introduces NO cross-group edge
    assert [d.files for d in plan.structural_dependency_groups] == [
        g.files for g in plan.recommended_commit_sequence
    ]
    # the honest field name is used; there is no fabricated "dependency_graph" of edges
    assert not hasattr(plan, "dependency_graph")


def test_summary_declares_no_dependency_evidence(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    plan = build_execution_plan(p)
    assert "no" in plan.planning_summary and "dependency" in plan.planning_summary
    assert "structural path-containment grouping" in plan.planning_summary


# --- deterministic complexity classification ---------------------------

@pytest.mark.parametrize(
    "n_files,risk,expected",
    [
        (1, "low", "low"),
        (2, "low", "low"),
        (3, "low", "medium"),
        (8, "low", "medium"),
        (9, "low", "high"),
        (1, "medium", "medium"),
        (1, "high", "high"),
        (1, "critical", "high"),
        (5, "high", "high"),
    ],
)
def test_deterministic_complexity_label(make_candidate, n_files, risk, expected):
    files = tuple(f"{_DIR}m{i:02d}.py" for i in range(n_files))
    p = _proposal(make_candidate, files=files, authorized=[_DIR], risk=risk)
    plan = build_execution_plan(p)
    assert plan.estimated_complexity == ComplexitySummary(
        label=expected,
        changed_file_count=n_files,
        authorized_path_count=1,
        declared_risk_level=risk,
    )


# --- fail-closed rejects (§6) ------------------------------------------

def test_reject_non_proposal():
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(object())  # type: ignore[arg-type]


def test_reject_empty_proposal_id(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    tampered = dataclasses.replace(p, proposal_id="")
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_empty_changed_files(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    tampered = dataclasses.replace(p, changed_file_summary=())
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_cbsp21_scope_summary_mismatch(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    tampered = dataclasses.replace(p, changed_file_summary=(_DIR + "unrelated.py",))
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_file_outside_authorized_paths(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    narrowed = dataclasses.replace(p.target, authorized_target_paths=("some/other/dir",))
    tampered = dataclasses.replace(p, target=narrowed)
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_missing_authorized_paths(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    tampered = dataclasses.replace(p, target=dataclasses.replace(p.target, authorized_target_paths=()))
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_missing_provenance_field(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    tampered = dataclasses.replace(p, target=dataclasses.replace(p.target, evidence_candidate_id=""))
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_unsupported_risk_level(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",), risk="exotic")
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(p)


def test_supported_risk_levels_surface():
    assert SUPPORTED_RISK_LEVELS == ("critical", "high", "low", "medium")


def test_reject_packet_missing_scope(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    tampered = dataclasses.replace(p, cbsp21_packet={"risk_level": "low", "verification": {"commands_run": ["pytest"]}})
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_packet_missing_verification(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    packet = {
        "risk_level": "low",
        "change_type": "feat",
        "scope": {"files_expected_to_change": [_DIR + "a.py"]},
    }
    tampered = dataclasses.replace(p, cbsp21_packet=packet)
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


def test_reject_non_dict_packet(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    tampered = dataclasses.replace(p, cbsp21_packet="not-a-dict")  # type: ignore[arg-type]
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(tampered)


# --- planner surface + convenience equivalence -------------------------

def test_planner_exposes_only_plan_no_execution_verb():
    public = [m for m in dir(ExecutionPlanner) if not m.startswith("_")]
    assert public == ["plan"]
    forbidden = ("execute", "commit", "push", "merge", "pull_request", "mutate", "apply", "git", "github")
    assert not any(tok in "plan" for tok in forbidden)


def test_builder_and_convenience_match(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    via_fn = build_execution_plan(p).to_canonical_dict()
    via_planner = ExecutionPlanner().plan(p).to_canonical_dict()
    via_factory = execution_plan_builder().plan(p).to_canonical_dict()
    assert via_fn == via_planner == via_factory


# --- validate_execution_plan -------------------------------------------

def test_validate_accepts_well_formed_plan(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py", _DOCS + "x.md"), authorized=[_DIR, _DOCS])
    plan = build_execution_plan(p)
    assert validate_execution_plan(plan) is plan


def test_validate_rejects_non_plan():
    with pytest.raises(ExecutionPlanningError):
        validate_execution_plan(object())  # type: ignore[arg-type]


def test_validate_rejects_tampered_id(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    plan = build_execution_plan(p)
    tampered = dataclasses.replace(plan, execution_plan_id="rep-deadbeefdeadbeef")
    with pytest.raises(ExecutionPlanningError):
        validate_execution_plan(tampered)


def test_validate_rejects_group_file_not_in_commit_sequence(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    plan = build_execution_plan(p)
    rogue = (DependencyGroup(group_id="grp-99", path_prefix=_DIR.strip("/"), files=("ghost.py",)),)
    tampered = dataclasses.replace(plan, structural_dependency_groups=rogue)
    # Re-derive the id so the content hash MATCHES — otherwise the id check would fire first and we
    # would never exercise the group/file consistency check this test targets.
    consistent = dataclasses.replace(tampered, execution_plan_id="rep-" + tampered.compute_plan_hash())
    with pytest.raises(ExecutionPlanningError):
        validate_execution_plan(consistent)


# --- defensive packet-shape branches (tampered packets) ----------------

def test_reject_scope_files_none(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    packet = {"risk_level": "low", "change_type": "feat", "scope": {"files_expected_to_change": None}, "verification": {"commands_run": ["pytest"]}}
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(dataclasses.replace(p, cbsp21_packet=packet))


def test_scope_files_bare_string_is_accepted(make_candidate):
    # A bare-string scope entry equal to the single declared file is coerced (not split into chars).
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    packet = {"risk_level": "low", "change_type": "feat", "scope": {"files_expected_to_change": _DIR + "a.py"}, "verification": {"commands_run": ["pytest"]}}
    plan = build_execution_plan(dataclasses.replace(p, cbsp21_packet=packet))
    assert plan.recommended_commit_sequence[0].files == (_DIR + "a.py",)


def test_reject_verification_not_a_list(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    packet = {"risk_level": "low", "change_type": "feat", "scope": {"files_expected_to_change": [_DIR + "a.py"]}, "verification": {"commands_run": "pytest"}}
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(dataclasses.replace(p, cbsp21_packet=packet))


def test_reject_blank_verification_command(make_candidate):
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    packet = {"risk_level": "low", "change_type": "feat", "scope": {"files_expected_to_change": [_DIR + "a.py"]}, "verification": {"commands_run": [""]}}
    with pytest.raises(ExecutionPlanningError):
        build_execution_plan(dataclasses.replace(p, cbsp21_packet=packet))


def test_empty_authorized_entry_is_skipped(make_candidate):
    # A blank authorized entry is skipped (not treated as matching everything); real prefix still wins.
    p = _proposal(make_candidate, files=(_DIR + "a.py",))
    widened = dataclasses.replace(p.target, authorized_target_paths=("", _DIR.strip("/")))
    plan = build_execution_plan(dataclasses.replace(p, target=widened))
    assert [g.path_prefix for g in plan.recommended_commit_sequence] == [_DIR.strip("/")]


# --- constitutional invariant: no git/filesystem/GitHub/network --------

def test_planning_modules_have_no_execution_capability():
    # Import-precise (AST): forbid the *imports*, so descriptive prose in docstrings is not a false
    # positive. Covers both PR-E modules (contract + planner).
    import ast

    pkg_dir = Path(ibg_repo.__file__).parent
    forbidden_top = {
        "subprocess",
        "os",
        "shutil",
        "tempfile",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "http",
        "pygithub",
        "github",
    }
    forbidden_local = ("git_runner", "worktree_builder", "worktree_validator", "worktree_spec", "worktree_state")
    for module_name in ("repository_execution_plan.py", "execution_planner.py"):
        src = (pkg_dir / module_name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = (node.module or "").split(".")[0]
                if base:
                    imported.add(base)
                if node.module:
                    for local in forbidden_local:
                        assert local not in node.module, f"{module_name} must not import PR-B {local}"
        leaked = imported & forbidden_top
        assert not leaked, f"{module_name} must not import {leaked}"
