"""Finding-level ProposalEvaluator tests for governed defects and execution mismatches."""

from __future__ import annotations

import copy
import dataclasses

import pytest

from app.governance.authority_state import AuthorityState
from app.ibg_repository import (
    ExecutionGroup,
    GOVERNED_PROVENANCE_FIELDS,
    READINESS_INCOMPLETE,
    build_execution_plan,
    build_proposal_target_binding,
    build_repository_change_proposal,
    evaluate_repository_proposal,
    validate_repository_proposal_evaluation,
)
from .proposal_evaluator_helpers import (
    FILES,
    _finding,
    _packet,
    _proposal_with_packet,
    _reseal_plan,
    _reseal_proposal,
    _status,
)

# --- evaluable defects are REPORTED, never raised ---------------------------------------------------


def test_a_defect_is_reported_as_a_failed_finding_not_an_exception(make_proposal):
    """The whole point of the error/finding split: a readiness gap must reach the reviewer."""
    proposal = make_proposal()
    plan = _reseal_plan(
        dataclasses.replace(build_execution_plan(proposal), planning_summary="edited")
    )
    # Re-sealed, so the plan is self-consistent; now break provenance continuity.
    broken_reference = dataclasses.replace(plan.provenance_reference, producing_subsystem="forged")
    plan = _reseal_plan(dataclasses.replace(plan, provenance_reference=broken_reference))

    evaluation = evaluate_repository_proposal(proposal, plan)  # does NOT raise

    assert evaluation.readiness_summary == READINESS_INCOMPLETE
    assert _status(evaluation, "provenance.producing_subsystem_continuous") == "fail"
    assert "discontinuity" in _finding(evaluation, "provenance.producing_subsystem_continuous").detail


def test_missing_provenance_values_are_reported_not_repaired(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    emptied = dataclasses.replace(plan.provenance_reference, evidence_candidate_id="")
    plan = _reseal_plan(dataclasses.replace(plan, provenance_reference=emptied))

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "provenance.evidence_candidate_id_continuous") == "fail"
    # Never invented or back-filled from the proposal.
    assert plan.provenance_reference.evidence_candidate_id == ""


def test_absent_provenance_reference_is_reported_across_all_governed_fields(make_proposal):
    proposal = make_proposal()
    # Not resealed: a plan missing this record cannot hash itself, which is itself part of the defect.
    plan = dataclasses.replace(build_execution_plan(proposal), provenance_reference=None)

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.provenance_reference_present") == "fail"
    for field in GOVERNED_PROVENANCE_FIELDS:
        assert _status(evaluation, f"provenance.{field}_continuous") == "fail"


def test_provenance_continuity_requires_exact_equality(make_proposal):
    """Near-enough is not continuity: a single altered character is a discontinuity."""
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    original = plan.provenance_reference.evidence_provenance_hash
    tweaked = dataclasses.replace(
        plan.provenance_reference, evidence_provenance_hash=original + "0"
    )
    plan = _reseal_plan(dataclasses.replace(plan, provenance_reference=tweaked))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "provenance.evidence_provenance_hash_continuous") == "fail"


def test_an_authority_state_upgrade_is_reported(make_candidate):
    """An unrecognized/relabelled authority state is how an upgrade would be smuggled past review."""
    binding = build_proposal_target_binding(
        make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="58ffadeb",
        authorized_target_paths=list(FILES),
        change_intent="evaluate",
    )
    forged = dataclasses.replace(binding, source_authority_state="fully_canonical_trust_me")
    proposal = _reseal_proposal(
        dataclasses.replace(
            build_repository_change_proposal(
                target=binding,
                cbsp21_packet=_packet(),
                proposed_branch="feature/x",
            ),
            target=forged,
        )
    )
    evaluation = evaluate_repository_proposal(proposal, _reseal_plan(build_execution_plan(proposal)))

    assert _status(evaluation, "governance.authority_state_not_upgraded") == "fail"
    assert evaluation.readiness_summary == READINESS_INCOMPLETE


def test_a_recognized_authority_state_is_never_penalized_for_its_level(make_proposal):
    """The evaluator reports the state; it does not judge which recognized state evidence holds."""
    proposal = make_proposal()
    evaluation = evaluate_repository_proposal(proposal, build_execution_plan(proposal))

    assert _status(evaluation, "governance.authority_state_not_upgraded") == "pass"
    assert proposal.target.source_authority_state == AuthorityState.ADVISORY_CANDIDATE.value
    # Every state the governance enum recognizes passes: the check tests recognizability, not level.
    # Judging WHICH state evidence should hold would require the live candidate the evaluator, by
    # design, cannot see — so asserting a "correct" level would be an invented claim.
    for state in AuthorityState:
        forged = dataclasses.replace(proposal.target, source_authority_state=state.value)
        candidate_proposal = _reseal_proposal(dataclasses.replace(proposal, target=forged))
        plan = _reseal_plan(
            dataclasses.replace(
                build_execution_plan(candidate_proposal),
                proposal_id=candidate_proposal.proposal_id,
            )
        )
        assert (
            _status(
                evaluate_repository_proposal(candidate_proposal, plan),
                "governance.authority_state_not_upgraded",
            )
            == "pass"
        )
def test_unsupported_declared_risk_is_reported(make_candidate):
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = _reseal_plan(build_execution_plan(proposal))
    # The packet is edited after the plan is built, so the defect reaches the evaluator.
    packet = copy.deepcopy(proposal.cbsp21_packet)
    packet["risk_level"] = "spicy"
    proposal = _reseal_proposal(dataclasses.replace(proposal, cbsp21_packet=packet))
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "governance.declared_risk_supported") == "fail"


def test_invalid_cbsp21_content_is_reported(make_candidate):
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = _reseal_plan(build_execution_plan(proposal))
    packet = copy.deepcopy(proposal.cbsp21_packet)
    del packet["title"]
    proposal = _reseal_proposal(dataclasses.replace(proposal, cbsp21_packet=packet))
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "governance.cbsp21_packet_valid") == "fail"
    assert "title" in _finding(evaluation, "governance.cbsp21_packet_valid").detail


def test_unarticulated_behavior_change_is_reported(make_candidate):
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = _reseal_plan(build_execution_plan(proposal))
    packet = copy.deepcopy(proposal.cbsp21_packet)
    packet["behavior_change"] = "adds a runtime path"
    packet["diff_articulation"]["why_not_redundant"] = "short"
    proposal = _reseal_proposal(dataclasses.replace(proposal, cbsp21_packet=packet))
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "governance.behavior_change_articulated") == "fail"


def test_an_unreadable_packet_is_reported_without_crashing(make_candidate):
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = _reseal_plan(build_execution_plan(proposal))
    proposal = _reseal_proposal(dataclasses.replace(proposal, cbsp21_packet="not a packet"))
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.cbsp21_packet_readable") == "fail"
    assert _status(evaluation, "governance.cbsp21_packet_valid") == "fail"
    assert _status(evaluation, "governance.declared_risk_supported") == "fail"
    # Nothing can be said about a rule whose input cannot be read — that is not_applicable, not fail.
    assert _status(evaluation, "governance.behavior_change_articulated") == "not_applicable"
    assert _status(evaluation, "invariant.validation_sequence_matches_packet") == "not_applicable"


def test_files_outside_the_authorized_boundary_are_reported(make_candidate):
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = _reseal_plan(build_execution_plan(proposal))
    proposal = _reseal_proposal(
        dataclasses.replace(proposal, changed_file_summary=("etc/passwd",) + FILES)
    )
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "governance.changed_files_within_authorized_paths") == "fail"
    assert "etc/passwd" in _finding(
        evaluation, "governance.changed_files_within_authorized_paths"
    ).detail


def test_a_reclassified_proposal_is_reported(make_proposal):
    proposal = make_proposal()
    plan = _reseal_plan(build_execution_plan(proposal))
    proposal = _reseal_proposal(
        dataclasses.replace(proposal, constitutional_classification="canonical__with_authority")
    )
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "governance.proposal_classification_unchanged") == "fail"


def test_a_reclassified_plan_is_reported(make_proposal):
    proposal = make_proposal()
    plan = _reseal_plan(
        dataclasses.replace(
            build_execution_plan(proposal),
            constitutional_classification="executable_plan__with_repository_authority",
        )
    )
    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "execution.plan_classification_descriptive") == "fail"


def test_a_plan_whose_id_does_not_match_its_content_is_reported(make_proposal):
    proposal = make_proposal()
    # Deliberately NOT resealed: the plan was altered after it was built.
    plan = dataclasses.replace(build_execution_plan(proposal), planning_summary="edited after build")

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "execution.plan_id_matches_content_hash") == "fail"


def test_a_plan_group_referencing_an_unknown_file_is_reported(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    stray = ExecutionGroup(group_id="grp-99", path_prefix="x", files=("services/api/app/ghost.py",))
    plan = _reseal_plan(dataclasses.replace(plan, recommended_review_order=(stray,)))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "execution.plan_groups_internally_consistent") == "fail"
    assert "ghost.py" in _finding(evaluation, "execution.plan_groups_internally_consistent").detail


def test_a_plan_omitting_a_declared_file_is_reported(make_candidate):
    files = (
        "services/api/app/ibg_repository/proposal_target.py",
        "services/api/app/ibg_repository/git_runner.py",
    )
    proposal = _proposal_with_packet(make_candidate, _packet(files=files), files=files)
    plan = build_execution_plan(proposal)
    trimmed = tuple(
        dataclasses.replace(g, files=tuple(f for f in g.files if "git_runner" not in f))
        for g in plan.recommended_commit_sequence
    )
    plan = _reseal_plan(dataclasses.replace(plan, recommended_commit_sequence=trimmed))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "invariant.plan_covers_all_declared_files") == "fail"
    assert "git_runner" in _finding(evaluation, "invariant.plan_covers_all_declared_files").detail


def test_a_plan_inventing_an_undeclared_file_is_reported(make_proposal):
    """A plan may only describe work the proposal declares; an extra file is invented scope."""
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    inflated = tuple(
        dataclasses.replace(g, files=g.files + ("services/api/app/ibg_repository/invented.py",))
        for g in plan.recommended_commit_sequence
    )
    plan = _reseal_plan(dataclasses.replace(plan, recommended_commit_sequence=inflated))

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "invariant.plan_introduces_no_undeclared_files") == "fail"
    assert "invented.py" in _finding(
        evaluation, "invariant.plan_introduces_no_undeclared_files"
    ).detail


def test_a_validation_sequence_that_diverges_from_the_packet_is_reported(make_proposal):
    proposal = make_proposal()
    plan = _reseal_plan(
        dataclasses.replace(
            build_execution_plan(proposal), recommended_validation_sequence=("rm -rf /",)
        )
    )
    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "invariant.validation_sequence_matches_packet") == "fail"


def test_an_empty_validation_sequence_is_reported_when_the_packet_declares_commands(make_proposal):
    proposal = make_proposal()
    plan = _reseal_plan(
        dataclasses.replace(build_execution_plan(proposal), recommended_validation_sequence=())
    )
    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "completeness.validation_sequence_present") == "fail"


def test_a_missing_complexity_summary_is_reported(make_proposal):
    proposal = make_proposal()
    # Not resealed: a plan missing this record cannot hash itself, which is itself part of the defect.
    plan = dataclasses.replace(build_execution_plan(proposal), estimated_complexity=None)

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.complexity_summary_present") == "fail"
    # The unhashable plan is REPORTED, never allowed to crash the evaluation.
    assert _status(evaluation, "execution.plan_id_matches_content_hash") == "fail"
    assert "not canonically serializable" in _finding(
        evaluation, "execution.plan_id_matches_content_hash"
    ).detail


def test_an_empty_complexity_label_is_reported(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    blank = dataclasses.replace(plan.estimated_complexity, label="")
    plan = _reseal_plan(dataclasses.replace(plan, estimated_complexity=blank))
    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "completeness.complexity_summary_present") == "fail"


def test_absent_ids_are_reported(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    # Both ids emptied together, so the artifacts still describe the same (empty) proposal.
    proposal = dataclasses.replace(proposal, proposal_id="")
    plan = dataclasses.replace(plan, proposal_id="", execution_plan_id="")

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "completeness.proposal_id_present") == "fail"
    assert _status(evaluation, "completeness.execution_plan_id_present") == "fail"


def test_an_empty_changed_file_set_makes_grouping_checks_not_applicable(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal = _reseal_proposal(dataclasses.replace(proposal, changed_file_summary=()))
    plan = _reseal_plan(
        dataclasses.replace(plan, proposal_id=proposal.proposal_id, recommended_commit_sequence=())
    )

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.changed_file_summary_present") == "fail"
    # Nothing to group and nothing to place: a conditional check that cannot apply is excluded,
    # never failed.
    assert _status(evaluation, "completeness.execution_groups_present") == "not_applicable"
    assert _status(evaluation, "governance.changed_files_within_authorized_paths") == "not_applicable"


def test_not_applicable_checks_are_excluded_from_the_score_denominator(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal = _reseal_proposal(dataclasses.replace(proposal, changed_file_summary=()))
    plan = _reseal_plan(
        dataclasses.replace(plan, proposal_id=proposal.proposal_id, recommended_commit_sequence=())
    )

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert evaluation.checks_not_applicable > 0
    assert evaluation.checks_applicable == evaluation.checks_passed + evaluation.checks_failed
    assert evaluation.checks_applicable + evaluation.checks_not_applicable == len(
        evaluation.all_findings()
    )
    validate_repository_proposal_evaluation(evaluation)


def test_a_packet_that_legitimately_declares_no_commands_makes_validation_not_applicable(
    make_candidate,
):
    """A source that declares no verification cannot make the plan's empty sequence a defect."""
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = build_execution_plan(proposal)
    packet = copy.deepcopy(proposal.cbsp21_packet)
    packet["verification"]["commands_run"] = []
    proposal = _reseal_proposal(dataclasses.replace(proposal, cbsp21_packet=packet))
    plan = _reseal_plan(
        dataclasses.replace(
            plan, proposal_id=proposal.proposal_id, recommended_validation_sequence=()
        )
    )

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.validation_sequence_present") == "not_applicable"
    assert _status(evaluation, "invariant.validation_sequence_matches_packet") == "not_applicable"


def test_a_plan_inventing_commands_the_packet_never_declared_is_reported(make_candidate):
    """not_applicable applies only when the plan ALSO carries none; invented commands still fail."""
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = build_execution_plan(proposal)
    packet = copy.deepcopy(proposal.cbsp21_packet)
    packet["verification"]["commands_run"] = []
    proposal = _reseal_proposal(dataclasses.replace(proposal, cbsp21_packet=packet))
    plan = _reseal_plan(
        dataclasses.replace(
            plan, proposal_id=proposal.proposal_id, recommended_validation_sequence=("invented",)
        )
    )

    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "invariant.validation_sequence_matches_packet") == "fail"


@pytest.mark.parametrize(
    "mutate, cbsp21_status",
    [
        # verification is not an object at all -> the required field resolves to nothing -> invalid.
        pytest.param(
            lambda p: p.__setitem__("verification", "not an object"), "fail", id="verification"
        ),
        # A bare string is non-empty, so CBSP21 (which only requires presence) accepts it; it is
        # still not a readable command LIST. The two checks report different things, and both are
        # honest — this is precisely why the packet-validity verdict is not reused as the answer here.
        pytest.param(
            lambda p: p["verification"].__setitem__("commands_run", "pytest"), "pass", id="commands_run"
        ),
    ],
)
def test_an_unreadable_verification_block_is_not_applicable_never_a_crash(
    make_candidate, mutate, cbsp21_status
):
    proposal = _proposal_with_packet(make_candidate, _packet())
    plan = build_execution_plan(proposal)
    packet = copy.deepcopy(proposal.cbsp21_packet)
    mutate(packet)
    proposal = _reseal_proposal(dataclasses.replace(proposal, cbsp21_packet=packet))
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.validation_sequence_present") == "not_applicable"
    assert _status(evaluation, "invariant.validation_sequence_matches_packet") == "not_applicable"
    assert _status(evaluation, "governance.cbsp21_packet_valid") == cbsp21_status
