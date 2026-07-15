"""
What the execution-plan contract ACCEPTS and REFUSES (PR E).

Split from ``test_execution_planner.py`` — which owns derivation, determinism, and the
fail-closed rejects — so both modules stay under the 500-line file-size gate. This module owns
the acceptance boundary:

  * scope agreement compares the declared file SET, never the spelling of a path;
  * plan identity has a single source of truth (the contract's own canonical content);
  * ``validate_execution_plan`` binds the PR-E boundary for plans built ELSEWHERE — hand
    constructed via the public frozen dataclasses, or revived from a serialized plan — where
    the content hash alone proves nothing, since it is derived from the plan it is checking.
"""

from __future__ import annotations

import copy
import dataclasses

import pytest

from app.ibg_repository import (
    DependencyGroup,
    ExecutionGroup,
    ExecutionPlanningError,
    build_cbsp21_patch_packet,
    build_execution_plan,
    build_proposal_target_binding,
    build_repository_change_proposal,
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


# --- scope agreement compares the file SET, not its formatting ---------
#
# ``build_repository_change_proposal`` derives ``changed_file_summary`` with sorted({str(f) ...}) —
# it does not normalize (only its boundary check does). A packet built by build_cbsp21_patch_packet
# is already normalized, but a RAW dict packet — the shape RepositoryProposalPipeline accepts and
# the shape a .cbsp21/patches/*.json file loads as — keeps its author's formatting. The planner must
# compare the declared file SET, not the spelling.

def _raw_scope_proposal(make_candidate, *, raw_files, authorized):
    """A real proposal whose packet is a RAW dict carrying unnormalized scope formatting."""
    binding = build_proposal_target_binding(
        make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="58ffadeb",
        authorized_target_paths=list(authorized),
        change_intent="plan the approved work",
    )
    packet = copy.deepcopy(
        build_cbsp21_patch_packet(
            patch_id="IBG_TEST",
            title="test packet",
            intent="test intent",
            change_type="feat",
            behavior_change="none",
            risk_level="low",
            paths_in_scope=list(authorized),
            files_expected_to_change=[_DIR + "a.py"],
            what_changed="adds modules",
            why_not_redundant="n/a",
            verification_commands=["pytest"],
        )
    )
    packet["scope"]["files_expected_to_change"] = list(raw_files)
    return build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/ibg-x"
    )


@pytest.mark.parametrize(
    "raw",
    [
        "services/api/app/ibg_repository" + chr(92) + "a.py",  # backslash separator
        _DIR + "a.py ",                                        # trailing whitespace
        "/" + _DIR + "a.py",                                   # leading slash
        _DIR + "a.py/",                                        # trailing slash
    ],
    ids=["backslash", "trailing-space", "leading-slash", "trailing-slash"],
)
def test_formatting_only_scope_difference_still_plans(make_candidate, raw):
    # The proposal and its packet agree on the file set and differ only in spelling. Rejecting this
    # would be a false negative: nothing about *what changes* is in dispute.
    p = _raw_scope_proposal(make_candidate, raw_files=[raw], authorized=[_DIR])
    assert p.changed_file_summary == (raw,)  # PR-A keeps the raw spelling
    plan = build_execution_plan(p)
    # The plan carries the canonical normalized form regardless of how the packet spelled it.
    assert plan.recommended_commit_sequence[0].files == (_DIR + "a.py",)
    assert validate_execution_plan(plan) is plan


def test_duplicate_after_normalization_collapses_to_one_file(make_candidate):
    p = _raw_scope_proposal(
        make_candidate, raw_files=[_DIR + "a.py", _DIR + "a.py/"], authorized=[_DIR]
    )
    plan = build_execution_plan(p)
    assert plan.recommended_commit_sequence[0].files == (_DIR + "a.py",)
    assert plan.estimated_complexity.changed_file_count == 1


def test_normalization_still_rejects_a_genuinely_different_file_set(make_candidate):
    # Tamper detection must survive normalization: a different SET is still a real disagreement.
    p = _raw_scope_proposal(make_candidate, raw_files=[_DIR + "a.py"], authorized=[_DIR])
    tampered = dataclasses.replace(p, changed_file_summary=(_DIR + "b.py",))
    with pytest.raises(ExecutionPlanningError, match="disagrees with CBSP21 scope"):
        build_execution_plan(tampered)


def test_normalization_is_a_noop_for_already_normalized_proposals(make_candidate):
    # Normalizing both sides must not churn ids for existing correct usage. The id is a pure
    # function of the plan's content, so showing normalization leaves the content byte-identical
    # for already-normalized input is exactly what "no id churn" means — and says it without
    # pinning a golden literal (make_candidate() is not guaranteed stable across calls).
    p = _proposal(make_candidate, files=(_DIR + "a.py", _DOCS + "x.md"), authorized=[_DIR, _DOCS])
    plan = build_execution_plan(p)
    planned = tuple(sorted(f for g in plan.recommended_commit_sequence for f in g.files))
    assert planned == tuple(sorted(p.changed_file_summary))
    assert validate_execution_plan(plan) is plan


# --- plan identity has a single source of truth ------------------------

def test_builder_output_always_satisfies_its_own_validator(make_candidate):
    # The builder content-addresses from the contract's own _canonical_content(), so the id can
    # never drift from compute_plan_hash() as fields are added.
    p = _proposal(make_candidate, files=(_DIR + "a.py", _DOCS + "x.md"), authorized=[_DIR, _DOCS])
    plan = build_execution_plan(p)
    assert plan.execution_plan_id == "rep-" + plan.compute_plan_hash()
    assert validate_execution_plan(plan) is plan


# --- validator binds the boundary for plans built ELSEWHERE ------------
#
# compute_plan_hash() is derived FROM the plan, so a self-consistent hand-built or deserialized
# plan always matches its own id. The hash detects tampering AFTER construction; it proves nothing
# about honesty at construction. These bind what the hash cannot.

def _reid(plan):
    """Self-consistently re-id a mutated plan, as a hand-builder/deserializer would."""
    return dataclasses.replace(plan, execution_plan_id="rep-" + plan.compute_plan_hash())


def test_validate_rejects_self_declared_authority(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(
        dataclasses.replace(plan, constitutional_classification="grants_repository_authority")
    )
    with pytest.raises(ExecutionPlanningError, match="constitutional_classification"):
        validate_execution_plan(rogue)


def test_validate_rejects_fabricated_dependency_relationship(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(
        dataclasses.replace(
            plan,
            structural_dependency_groups=tuple(
                dataclasses.replace(d, relationship="proven_build_dependency")
                for d in plan.structural_dependency_groups
            ),
        )
    )
    with pytest.raises(ExecutionPlanningError, match="declared_path_grouping"):
        validate_execution_plan(rogue)


@pytest.mark.parametrize("field", ["recommended_review_order", "structural_dependency_groups"])
def test_validate_rejects_dropped_group_coverage(make_candidate, field):
    # An emptied collection previously passed vacuously: every file in () is trivially in-scope.
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(dataclasses.replace(plan, **{field: ()}))
    with pytest.raises(ExecutionPlanningError, match="is empty"):
        validate_execution_plan(rogue)


def test_validate_rejects_partial_review_coverage(make_candidate):
    # Review order must cover the SAME declared files, not merely a subset of them.
    p = _proposal(make_candidate, files=(_DIR + "a.py", _DOCS + "x.md"), authorized=[_DIR, _DOCS])
    plan = build_execution_plan(p)
    rogue = _reid(dataclasses.replace(plan, recommended_review_order=plan.recommended_review_order[:1]))
    with pytest.raises(ExecutionPlanningError, match="does not cover the same declared files"):
        validate_execution_plan(rogue)


def test_validate_rejects_duplicate_file_within_a_group(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(
        dataclasses.replace(
            plan,
            recommended_commit_sequence=tuple(
                dataclasses.replace(g, files=g.files + g.files)
                for g in plan.recommended_commit_sequence
            ),
        )
    )
    with pytest.raises(ExecutionPlanningError, match="more than one group|partition"):
        validate_execution_plan(rogue)


def test_validate_rejects_duplicate_group_id(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    dup = plan.recommended_commit_sequence + tuple(
        dataclasses.replace(g, files=(_DIR + "z.py",)) for g in plan.recommended_commit_sequence
    )
    rogue = _reid(dataclasses.replace(plan, recommended_commit_sequence=dup))
    with pytest.raises(ExecutionPlanningError, match="duplicate group_id"):
        validate_execution_plan(rogue)


def test_validate_rejects_group_declaring_no_files(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(
        dataclasses.replace(
            plan,
            recommended_commit_sequence=(
                ExecutionGroup(group_id="grp-00", path_prefix=_DIR.strip("/"), files=()),
            ),
        )
    )
    with pytest.raises(ExecutionPlanningError, match="declares no files"):
        validate_execution_plan(rogue)


def test_validate_rejects_file_outside_its_group_prefix(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(
        dataclasses.replace(
            plan,
            recommended_commit_sequence=(
                ExecutionGroup(group_id="grp-00", path_prefix=_DIR.strip("/"), files=("ghost.py",)),
            ),
        )
    )
    with pytest.raises(ExecutionPlanningError, match="outside its path_prefix"):
        validate_execution_plan(rogue)


def test_validate_rejects_empty_planning_summary(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    with pytest.raises(ExecutionPlanningError, match="planning_summary"):
        validate_execution_plan(_reid(dataclasses.replace(plan, planning_summary="")))


def test_validate_rejects_empty_validation_sequence(make_candidate):
    # CBSP21 requires a non-empty verification.commands_run, so a real plan always carries one.
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(dataclasses.replace(plan, recommended_validation_sequence=()))
    with pytest.raises(ExecutionPlanningError, match="recommended_validation_sequence is empty"):
        validate_execution_plan(rogue)


def test_validate_rejects_blank_validation_command(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(dataclasses.replace(plan, recommended_validation_sequence=("  ",)))
    with pytest.raises(ExecutionPlanningError, match="recommended_validation_sequence entry"):
        validate_execution_plan(rogue)


def test_validate_rejects_provenance_stripped_after_construction(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(
        dataclasses.replace(
            plan,
            provenance_reference=dataclasses.replace(plan.provenance_reference, producing_subsystem=""),
        )
    )
    with pytest.raises(ExecutionPlanningError, match="producing_subsystem"):
        validate_execution_plan(rogue)


def test_validate_rejects_empty_proposal_id(make_candidate):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    with pytest.raises(ExecutionPlanningError, match="proposal_id"):
        validate_execution_plan(_reid(dataclasses.replace(plan, proposal_id="")))


@pytest.mark.parametrize(
    "mutation, match",
    [
        ({"changed_file_count": 999}, "changed_file_count"),
        ({"declared_risk_level": "banana"}, "unsupported declared risk_level"),
        ({"authorized_path_count": 0}, "authorized_path_count"),
        # Only the label is corrupted: its inputs stay consistent so the label-vs-table check is
        # what fires (1 file at risk "low" tabulates to "low", never "high").
        ({"label": "high"}, "documented table"),
    ],
    ids=["file-count", "risk-level", "path-count", "label-vs-table"],
)
def test_validate_rejects_complexity_contradicting_its_inputs(make_candidate, mutation, match):
    plan = build_execution_plan(_proposal(make_candidate, files=(_DIR + "a.py",)))
    rogue = _reid(
        dataclasses.replace(
            plan, estimated_complexity=dataclasses.replace(plan.estimated_complexity, **mutation)
        )
    )
    with pytest.raises(ExecutionPlanningError, match=match):
        validate_execution_plan(rogue)
