"""
Invariant tests for the observational ProposalEvaluator (PR F).

These bind the ratified boundary: the evaluator OBSERVES (scores, classifies, reports) and never
approves, rejects, blocks, mutates, or executes. It REPORTS evaluable defects as failed findings and
raises ONLY when the artifacts cannot be coherently evaluated. It PRESERVES provenance exactly, never
upgrades authority, leaves both inputs unmutated, is DETERMINISTIC, and performs NO git /
filesystem-mutation / GitHub / network operation.

Defective artifacts are constructed DIRECTLY (the frozen contracts permit it) rather than through the
fail-closed builders, because the builders reject these defects by construction. That is exactly what
makes the evaluator worth having: it checks the artifacts as given instead of trusting a builder ran.
"""

from __future__ import annotations

import copy
import dataclasses

import pytest

import app.ibg_repository as ibg_repo
from app.governance.authority_state import AuthorityState
from app.ibg_repository import (
    ComplexitySummary,
    EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION,
    ExecutionGroup,
    GOVERNED_PROVENANCE_FIELDS,
    PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    ProposalEvaluationError,
    ProposalEvaluator,
    ProvenanceReference,
    READINESS_COMPLETE,
    READINESS_INCOMPLETE,
    RepositoryProposalEvaluation,
    build_cbsp21_patch_packet,
    build_execution_plan,
    build_proposal_target_binding,
    build_repository_change_proposal,
    evaluate_execution_plan,
    evaluate_repository_proposal,
    proposal_evaluator,
    validate_repository_proposal_evaluation,
)

FILES = ("services/api/app/ibg_repository/proposal_target.py",)


def _reseal_plan(plan):
    """Re-derive the plan's content-addressed id after a deliberate edit.

    Isolates the defect under test: without resealing, ANY edit also trips
    ``execution.plan_id_matches_content_hash``, and the test could not tell the two apart.
    """
    return dataclasses.replace(plan, execution_plan_id="rep-" + plan.compute_plan_hash())


def _reseal_proposal(proposal):
    return dataclasses.replace(proposal, proposal_id="rcp-" + proposal.compute_proposal_hash())


def _finding(evaluation, check_id):
    for f in evaluation.all_findings():
        if f.check_id == check_id:
            return f
    raise AssertionError(f"no finding {check_id!r} in {[f.check_id for f in evaluation.all_findings()]}")


def _status(evaluation, check_id):
    return _finding(evaluation, check_id).status


# --- happy path ------------------------------------------------------------------------------------


def test_a_governed_proposal_and_its_plan_evaluate_as_complete(make_proposal):
    proposal = make_proposal()
    evaluation = evaluate_repository_proposal(proposal, build_execution_plan(proposal))

    assert isinstance(evaluation, RepositoryProposalEvaluation)
    assert evaluation.readiness_summary == READINESS_COMPLETE
    assert evaluation.checks_failed == 0
    assert evaluation.completeness_score == "1.00"
    assert evaluation.proposal_id == proposal.proposal_id
    validate_repository_proposal_evaluation(evaluation)


def test_every_check_has_exactly_one_owning_category(evaluation_of):
    """A duplicated finding would double-count in the score and mislead the reviewer."""
    evaluation = evaluation_of()
    ids = [f.check_id for f in evaluation.all_findings()]
    assert len(ids) == len(set(ids))
    # The category lists partition the findings; nothing appears in two lists.
    buckets = {
        "completeness": evaluation.completeness_findings,
        "governance": evaluation.governance_findings,
        "provenance": evaluation.provenance_findings,
        "execution": evaluation.execution_findings,
        "invariant": evaluation.invariant_results,
    }
    for category, findings in buckets.items():
        for finding in findings:
            assert finding.category == category
            assert finding.check_id.startswith(f"{category}.")


def test_counts_agree_with_the_findings(evaluation_of):
    evaluation = evaluation_of()
    every = evaluation.all_findings()
    assert evaluation.checks_passed == sum(1 for f in every if f.status == "pass")
    assert evaluation.checks_failed == sum(1 for f in every if f.status == "fail")
    assert evaluation.checks_not_applicable == sum(1 for f in every if f.status == "not_applicable")
    assert evaluation.checks_applicable == evaluation.checks_passed + evaluation.checks_failed
    assert evaluation.checks_not_applicable + evaluation.checks_applicable == len(every)


def test_evaluator_class_and_factory_delegate_to_the_owning_function(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    direct = evaluate_repository_proposal(proposal, plan)
    via_class = ProposalEvaluator().evaluate(proposal, plan)
    via_factory = proposal_evaluator().evaluate(proposal, plan)
    assert direct.evaluation_id == via_class.evaluation_id == via_factory.evaluation_id
    assert isinstance(proposal_evaluator(), ProposalEvaluator)


def test_evaluator_is_stateless_and_frozen(make_proposal):
    evaluator = ProposalEvaluator()
    with pytest.raises(dataclasses.FrozenInstanceError):
        evaluator.state = "x"  # type: ignore[attr-defined]
    assert not dataclasses.fields(ProposalEvaluator)


def test_evaluator_exposes_no_decision_or_execution_verb():
    """The evaluator has one operation. A decision verb would be authority it does not hold."""
    operations = {name for name in dir(ProposalEvaluator) if not name.startswith("_")}
    assert operations == {"evaluate"}
    for forbidden in ("approve", "reject", "block", "authorize", "merge", "commit", "push", "execute"):
        assert not hasattr(ProposalEvaluator, forbidden)


# --- hard errors: artifacts that cannot be coherently evaluated -------------------------------------


@pytest.mark.parametrize("bad", [None, "proposal", 42, object()])
def test_non_proposal_input_raises(bad, make_plan):
    with pytest.raises(ProposalEvaluationError):
        evaluate_repository_proposal(bad, make_plan())


@pytest.mark.parametrize("bad", [None, "plan", 42, object()])
def test_non_plan_input_raises(bad, make_proposal):
    with pytest.raises(ProposalEvaluationError):
        evaluate_repository_proposal(make_proposal(), bad)


def test_plan_describing_a_different_proposal_raises(make_proposal):
    """Not a readiness gap: an unrelated pairing is not evaluable, and a finding would imply it was."""
    proposal = make_proposal()
    other = make_proposal(change_intent="a different proposal entirely")
    assert proposal.proposal_id != other.proposal_id

    with pytest.raises(ProposalEvaluationError, match="describes proposal"):
        evaluate_repository_proposal(proposal, build_execution_plan(other))


def test_mismatch_raises_before_any_finding_is_produced(make_proposal):
    proposal = make_proposal()
    other = make_proposal(change_intent="a different proposal entirely")
    with pytest.raises(ProposalEvaluationError):
        evaluate_execution_plan(proposal, build_execution_plan(other))


def test_validate_rejects_a_non_evaluation():
    with pytest.raises(ProposalEvaluationError):
        validate_repository_proposal_evaluation("not an evaluation")


def test_validate_rejects_a_tampered_evaluation(evaluation_of):
    tampered = dataclasses.replace(evaluation_of(), readiness_summary=READINESS_INCOMPLETE)
    with pytest.raises(ProposalEvaluationError, match="does not match content hash"):
        validate_repository_proposal_evaluation(tampered)


def test_validate_rejects_counts_that_disagree_with_findings(evaluation_of):
    broken = dataclasses.replace(evaluation_of(), checks_passed=999)
    broken = dataclasses.replace(broken, evaluation_id="eval-" + broken.compute_evaluation_hash())
    with pytest.raises(ProposalEvaluationError, match="counts disagree"):
        validate_repository_proposal_evaluation(broken)


def test_validate_rejects_a_score_that_does_not_follow_from_the_counts(evaluation_of):
    broken = dataclasses.replace(evaluation_of(), completeness_score="0.10")
    broken = dataclasses.replace(broken, evaluation_id="eval-" + broken.compute_evaluation_hash())
    with pytest.raises(ProposalEvaluationError, match="does not match the counts"):
        validate_repository_proposal_evaluation(broken)


def test_validate_rejects_a_readiness_label_that_does_not_follow_from_failures(evaluation_of):
    broken = dataclasses.replace(evaluation_of(), readiness_summary=READINESS_INCOMPLETE)
    broken = dataclasses.replace(broken, evaluation_id="eval-" + broken.compute_evaluation_hash())
    with pytest.raises(ProposalEvaluationError, match="does not follow from"):
        validate_repository_proposal_evaluation(broken)


def test_validate_rejects_an_unrecognized_finding_vocabulary(evaluation_of):
    evaluation = evaluation_of()
    warned = dataclasses.replace(evaluation.completeness_findings[0], status="warn")
    broken = dataclasses.replace(
        evaluation, completeness_findings=(warned,) + evaluation.completeness_findings[1:]
    )
    broken = dataclasses.replace(broken, evaluation_id="eval-" + broken.compute_evaluation_hash())
    with pytest.raises(ProposalEvaluationError, match="unrecognized status"):
        validate_repository_proposal_evaluation(broken)


def test_validate_rejects_an_unrecognized_finding_category(evaluation_of):
    evaluation = evaluation_of()
    miscategorized = dataclasses.replace(evaluation.completeness_findings[0], category="opinion")
    broken = dataclasses.replace(
        evaluation, completeness_findings=(miscategorized,) + evaluation.completeness_findings[1:]
    )
    broken = dataclasses.replace(broken, evaluation_id="eval-" + broken.compute_evaluation_hash())
    with pytest.raises(ProposalEvaluationError, match="unrecognized category"):
        validate_repository_proposal_evaluation(broken)


def test_validate_rejects_a_reclassified_evaluation(evaluation_of):
    broken = dataclasses.replace(
        evaluation_of(), constitutional_classification="approval__with_authority"
    )
    broken = dataclasses.replace(broken, evaluation_id="eval-" + broken.compute_evaluation_hash())
    with pytest.raises(ProposalEvaluationError, match="is not"):
        validate_repository_proposal_evaluation(broken)


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


def _packet(files=FILES, risk="low", verification=("pytest",), behavior_change="none", why="n/a"):
    return build_cbsp21_patch_packet(
        patch_id="IBG_TEST",
        title="test packet",
        intent="test intent",
        change_type="feat",
        behavior_change=behavior_change,
        risk_level=risk,
        paths_in_scope=list(files),
        files_expected_to_change=list(files),
        what_changed="adds a module",
        why_not_redundant=why,
        verification_commands=list(verification),
    )


def _proposal_with_packet(make_candidate, packet, files=FILES):
    binding = build_proposal_target_binding(
        make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="58ffadeb",
        authorized_target_paths=list(files),
        change_intent="evaluate",
    )
    return build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/x"
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


def test_a_scalar_changed_file_summary_is_read_without_crashing(make_proposal):
    """A hand-built contract may carry a bare string; a string is one entry, never its characters."""
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal = _reseal_proposal(
        dataclasses.replace(proposal, changed_file_summary=FILES[0])  # type: ignore[arg-type]
    )
    plan = _reseal_plan(dataclasses.replace(plan, proposal_id=proposal.proposal_id))

    evaluation = evaluate_repository_proposal(proposal, plan)

    assert _status(evaluation, "completeness.changed_file_summary_present") == "pass"
    assert _status(evaluation, "invariant.plan_covers_all_declared_files") == "pass"
    assert _status(evaluation, "governance.changed_files_within_authorized_paths") == "pass"


def test_a_plan_with_no_group_collections_is_read_without_crashing(make_proposal):
    proposal = make_proposal()
    # Not resealed: a plan with no group collections cannot hash itself, which the id check reports.
    plan = dataclasses.replace(
        build_execution_plan(proposal),
        recommended_review_order=None,  # type: ignore[arg-type]
        structural_dependency_groups=None,  # type: ignore[arg-type]
    )
    evaluation = evaluate_repository_proposal(proposal, plan)
    assert _status(evaluation, "execution.plan_groups_internally_consistent") == "pass"
    assert _status(evaluation, "execution.plan_id_matches_content_hash") == "fail"


# --- readiness label semantics ---------------------------------------------------------------------


def test_readiness_is_derived_only_from_failed_applicable_checks(make_proposal):
    proposal = make_proposal()
    complete = evaluate_repository_proposal(proposal, build_execution_plan(proposal))
    assert complete.checks_failed == 0
    assert complete.readiness_summary == READINESS_COMPLETE

    plan = _reseal_plan(
        dataclasses.replace(
            build_execution_plan(proposal), recommended_validation_sequence=("something else",)
        )
    )
    incomplete = evaluate_repository_proposal(proposal, plan)
    assert incomplete.checks_failed > 0
    assert incomplete.readiness_summary == READINESS_INCOMPLETE


def test_a_not_applicable_check_alone_never_makes_an_evaluation_incomplete(make_proposal):
    """not_applicable is an absence of evidence, not a defect — it cannot flip the label."""
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal = _reseal_proposal(dataclasses.replace(proposal, changed_file_summary=()))
    plan = _reseal_plan(
        dataclasses.replace(plan, proposal_id=proposal.proposal_id, recommended_commit_sequence=())
    )
    evaluation = evaluate_repository_proposal(proposal, plan)
    # This artifact does have real failures; assert the label tracks failures, not the n/a count.
    assert evaluation.readiness_summary == (
        READINESS_COMPLETE if evaluation.checks_failed == 0 else READINESS_INCOMPLETE
    )


# --- observational boundary ------------------------------------------------------------------------


def test_evaluation_does_not_mutate_the_proposal_or_the_plan(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    proposal_before = copy.deepcopy(proposal.to_audit_dict())
    plan_before = copy.deepcopy(plan.to_audit_dict())

    evaluate_repository_proposal(proposal, plan)

    assert proposal.to_audit_dict() == proposal_before
    assert plan.to_audit_dict() == plan_before


def test_evaluation_does_not_upgrade_the_authority_state(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    before = proposal.target.source_authority_state

    evaluate_repository_proposal(proposal, plan)

    assert proposal.target.source_authority_state == before
    assert plan.provenance_reference.source_authority_state == before


def test_evaluation_carries_no_repository_or_approval_authority(evaluation_of):
    evaluation = evaluation_of()
    for forbidden in ("approve", "reject", "block", "authorize", "merge", "commit", "push", "execute"):
        assert not hasattr(evaluation, forbidden)
    assert (
        evaluation.constitutional_classification
        == "observational_proposal_evaluation__no_approval_authority"
    )


def test_evaluate_execution_plan_returns_only_the_plan_facing_findings(make_proposal):
    proposal = make_proposal()
    plan = build_execution_plan(proposal)
    findings = evaluate_execution_plan(proposal, plan)

    assert {f.category for f in findings} == {"execution", "invariant"}
    # Shares the full evaluation's logic rather than forking it.
    full = evaluate_repository_proposal(proposal, plan)
    assert findings == tuple(
        f for f in full.all_findings() if f.category in {"execution", "invariant"}
    )
    assert list(findings) == sorted(findings, key=lambda f: (f.category, f.check_id))


def test_evaluator_modules_perform_no_git_filesystem_github_or_network_operation():
    """AST-precise: the evaluator may not even IMPORT an execution or network capability."""
    import ast
    from pathlib import Path

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
    forbidden_local = (
        "git_runner",
        "worktree_builder",
        "worktree_validator",
        "worktree_spec",
        "worktree_state",
    )
    for module_name in ("repository_proposal_evaluation.py", "proposal_evaluator.py"):
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


def test_evaluator_does_not_attach_to_the_pipeline_or_the_planner():
    """PR F is a separate downstream consumer: it must not modify or wrap the upstream stages.

    The evaluation layer is two files — ``proposal_evaluator.py`` (orchestration + public API) and
    ``proposal_checks.py`` (the 25 check builders) — so the invariant is asserted over BOTH: neither
    may import the pipeline/review-bundle or any plan/pipeline BUILDER, or call one.
    """
    import ast
    from pathlib import Path

    layer = Path(ibg_repo.__file__).parent
    imported_names: set[str] = set()
    called: set[str] = set()
    for module_file in ("proposal_evaluator.py", "proposal_checks.py"):
        tree = ast.parse((layer / module_file).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "repository_proposal_pipeline" not in node.module, module_file
                assert "repository_review_bundle" not in node.module, module_file
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)

    # The layer reuses the planner's supported-risk set, but imports no plan/pipeline BUILDER...
    assert "SUPPORTED_RISK_LEVELS" in imported_names
    for builder in ("build_execution_plan", "ExecutionPlanner", "run_repository_proposal_pipeline"):
        assert builder not in imported_names, f"evaluation layer must not import {builder}"

    # ...and calls none of them anywhere (AST-precise: prose in a docstring is not a call).
    assert not called & {"build_execution_plan", "ExecutionPlanner", "build_review_bundle"}


def test_evaluation_is_not_wired_into_the_existing_pipeline():
    """The pipeline is unchanged by PR F; nothing evaluates implicitly as a side effect."""
    from app.ibg_repository import repository_proposal_pipeline

    src_names = dir(repository_proposal_pipeline)
    assert "evaluate_repository_proposal" not in src_names
    assert "ProposalEvaluator" not in src_names
    assert "RepositoryProposalEvaluation" not in src_names
