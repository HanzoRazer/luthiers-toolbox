"""Core invariant tests for the observational ProposalEvaluator (PR F)."""

from __future__ import annotations

import dataclasses

import pytest

from app.ibg_repository import (
    ProposalEvaluationError,
    ProposalEvaluator,
    READINESS_COMPLETE,
    READINESS_INCOMPLETE,
    RepositoryProposalEvaluation,
    build_execution_plan,
    evaluate_execution_plan,
    evaluate_repository_proposal,
    proposal_evaluator,
    validate_repository_proposal_evaluation,
)
from .proposal_evaluator_helpers import _finding, _reseal_plan, _status

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
