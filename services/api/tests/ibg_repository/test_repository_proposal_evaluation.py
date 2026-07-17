"""
Contract tests for the observational RepositoryProposalEvaluation (PR F).

These bind the contract's own guarantees: a content-addressed, byte-stable id; wall-clock excluded
from identity and canonical form; an auditable fixed-precision completeness score computed in decimal
(never binary float); ``not_applicable`` excluded from the score's denominator; deterministic finding
ordering; and a vocabulary that can express structural completeness but not approval.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.ibg_repository import (
    EVALUATION_CONSTITUTIONAL_CLASSIFICATION,
    EvaluationFinding,
    FINDING_CATEGORIES,
    FINDING_STATUSES,
    ProposalEvaluationError,
    READINESS_COMPLETE,
    READINESS_INCOMPLETE,
    READINESS_SUMMARIES,
    RepositoryProposalEvaluation,
    build_execution_plan,
    compute_completeness_score,
    evaluate_repository_proposal,
    sort_findings,
    summarize_findings,
)


def _finding(check_id="c.x", category="completeness", status="pass", detail="d"):
    return EvaluationFinding(check_id=check_id, category=category, status=status, detail=detail)


# --- completeness score: an auditable decimal ratio, not an invented metric ----------------------


@pytest.mark.parametrize(
    "passed, applicable, expected",
    [
        (9, 10, "0.90"),
        (10, 10, "1.00"),
        (0, 10, "0.00"),
        (1, 3, "0.33"),
        (2, 3, "0.67"),
        (1, 8, "0.13"),  # 0.125 -> ROUND_HALF_UP -> 0.13
        (1, 2, "0.50"),
        (7, 25, "0.28"),
    ],
)
def test_completeness_score_is_documented_fixed_precision_decimal(passed, applicable, expected):
    assert compute_completeness_score(passed, applicable) == expected


def test_completeness_score_is_a_string_not_a_float():
    """A binary float would make the canonical form — and thus the id — representation-dependent."""
    score = compute_completeness_score(1, 3)
    assert isinstance(score, str)
    # The exact decimal is preserved; a float round-trip would not be 0.33.
    assert Decimal(score) == Decimal("0.33")


def test_completeness_score_fails_closed_when_no_check_applies():
    """An empty denominator has no honest score, so construction fails rather than inventing one."""
    with pytest.raises(ProposalEvaluationError, match="no applicable checks"):
        compute_completeness_score(0, 0)


@pytest.mark.parametrize(
    "passed, applicable",
    [(-1, 10), (1, -10), (11, 10)],
)
def test_completeness_score_rejects_incoherent_counts(passed, applicable):
    with pytest.raises(ProposalEvaluationError):
        compute_completeness_score(passed, applicable)


@pytest.mark.parametrize("passed, applicable", [(True, 10), (1, True), ("1", 10), (1, 1.0)])
def test_completeness_score_rejects_non_int_counts(passed, applicable):
    with pytest.raises(ProposalEvaluationError):
        compute_completeness_score(passed, applicable)


# --- summarize_findings: not_applicable never enters the denominator -----------------------------


def test_not_applicable_is_excluded_from_the_applicable_denominator():
    findings = (
        _finding("a", status="pass"),
        _finding("b", status="fail"),
        _finding("c", status="not_applicable"),
        _finding("d", status="not_applicable"),
    )
    counts = summarize_findings(findings)
    assert counts == {"passed": 1, "failed": 1, "not_applicable": 2, "applicable": 2}
    # The two not_applicable checks neither reward nor penalize the score.
    assert compute_completeness_score(counts["passed"], counts["applicable"]) == "0.50"


def test_all_not_applicable_findings_yield_an_empty_denominator_that_fails_closed():
    counts = summarize_findings((_finding("a", status="not_applicable"),))
    assert counts["applicable"] == 0
    with pytest.raises(ProposalEvaluationError):
        compute_completeness_score(counts["passed"], counts["applicable"])


# --- deterministic ordering ----------------------------------------------------------------------


def test_findings_sort_by_category_then_check_id():
    unsorted = (
        _finding("z.2", category="invariant"),
        _finding("a.1", category="provenance"),
        _finding("a.2", category="provenance"),
        _finding("m.1", category="completeness"),
    )
    ordered = sort_findings(unsorted)
    assert [(f.category, f.check_id) for f in ordered] == [
        ("completeness", "m.1"),
        ("invariant", "z.2"),
        ("provenance", "a.1"),
        ("provenance", "a.2"),
    ]


def test_finding_order_is_not_incidental_evaluation_order():
    """Shuffled construction order must not change the canonical form or the id."""
    findings = (
        _finding("b.2", category="governance"),
        _finding("a.1", category="completeness"),
    )
    assert sort_findings(findings) == sort_findings(tuple(reversed(findings)))


# --- identity and serialization ------------------------------------------------------------------


def test_evaluation_id_is_content_addressed(evaluation_of):
    evaluation = evaluation_of()
    assert evaluation.evaluation_id.startswith("eval-")
    assert evaluation.evaluation_id == "eval-" + evaluation.compute_evaluation_hash()
    assert len(evaluation.evaluation_id) == len("eval-") + 16


def test_identical_artifacts_yield_byte_identical_evaluations(make_proposal, evaluation_of):
    proposal = make_proposal()
    first = evaluation_of(proposal=proposal)
    second = evaluation_of(proposal=proposal)
    assert first.evaluation_id == second.evaluation_id
    assert json.dumps(first.to_canonical_dict(), sort_keys=True) == json.dumps(
        second.to_canonical_dict(), sort_keys=True
    )


def test_canonical_dict_round_trips_through_json(evaluation_of):
    evaluation = evaluation_of()
    restored = json.loads(json.dumps(evaluation.to_canonical_dict()))
    assert restored == evaluation.to_canonical_dict()


def test_created_at_is_excluded_from_identity_and_canonical_form(make_proposal, evaluation_of):
    proposal = make_proposal()
    without = evaluation_of(proposal=proposal)
    with_stamp = evaluation_of(
        proposal=proposal, created_at=datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    )
    assert with_stamp.evaluation_id == without.evaluation_id
    assert with_stamp.to_canonical_dict() == without.to_canonical_dict()
    assert "created_at" not in with_stamp.to_canonical_dict()


def test_audit_dict_surfaces_the_informational_timestamp(evaluation_of):
    stamp = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    with_stamp = evaluation_of(created_at=stamp)
    assert with_stamp.to_audit_dict()["created_at"] == stamp.isoformat()
    assert evaluation_of().to_audit_dict()["created_at"] is None


def test_audit_dict_is_a_superset_of_the_canonical_dict(evaluation_of):
    evaluation = evaluation_of()
    audit = evaluation.to_audit_dict()
    for key, value in evaluation.to_canonical_dict().items():
        assert audit[key] == value


def test_canonical_dict_contains_no_wall_clock_or_environment_values(evaluation_of):
    serialized = json.dumps(evaluation_of().to_canonical_dict())
    assert "created_at" not in serialized
    assert "C:/" not in serialized and "/tmp/" not in serialized
    # An object repr would leak identity/address into the content hash.
    assert " object at 0x" not in serialized


def test_evaluation_is_frozen(evaluation_of):
    evaluation = evaluation_of()
    with pytest.raises(dataclasses.FrozenInstanceError):
        evaluation.readiness_summary = READINESS_INCOMPLETE  # type: ignore[misc]


def test_finding_is_frozen():
    finding = _finding()
    with pytest.raises(dataclasses.FrozenInstanceError):
        finding.status = "fail"  # type: ignore[misc]


def test_all_findings_returns_every_category_in_deterministic_order(evaluation_of):
    evaluation = evaluation_of()
    every = evaluation.all_findings()
    assert len(every) == (
        len(evaluation.completeness_findings)
        + len(evaluation.governance_findings)
        + len(evaluation.provenance_findings)
        + len(evaluation.execution_findings)
        + len(evaluation.invariant_results)
    )
    assert list(every) == sorted(every, key=lambda f: (f.category, f.check_id))


# --- vocabulary boundary --------------------------------------------------------------------------


def test_readiness_vocabulary_is_structural_only():
    assert READINESS_SUMMARIES == (READINESS_COMPLETE, READINESS_INCOMPLETE)
    assert READINESS_COMPLETE == "complete"
    assert READINESS_INCOMPLETE == "incomplete"


def test_finding_vocabulary_has_no_warn_state():
    assert FINDING_STATUSES == ("pass", "fail", "not_applicable")
    assert "warn" not in FINDING_STATUSES
    assert FINDING_CATEGORIES == (
        "completeness",
        "governance",
        "provenance",
        "execution",
        "invariant",
    )


def test_classification_declares_no_approval_authority():
    assert (
        EVALUATION_CONSTITUTIONAL_CLASSIFICATION
        == "observational_proposal_evaluation__no_approval_authority"
    )
    assert RepositoryProposalEvaluation.constitutional_classification == (
        EVALUATION_CONSTITUTIONAL_CLASSIFICATION
    )


@pytest.mark.parametrize(
    "forbidden",
    ["approve", "reject", "merge", "block", "authorize", "canonical", "unsafe", "ready to execute"],
)
def test_evaluation_never_speaks_in_decision_vocabulary(evaluation_of, forbidden):
    """The evaluator may say complete/incomplete/pass/fail — never a decision it has no authority to make."""
    evaluation = evaluation_of()
    serialized = json.dumps(evaluation.to_canonical_dict()).lower()
    # 'not an approval / not a rejection' disclaimers are the only legitimate use, and the summary
    # states them explicitly; assert the decision words never appear as an asserted verdict field.
    assert evaluation.readiness_summary in READINESS_SUMMARIES
    for finding in evaluation.all_findings():
        assert finding.status in FINDING_STATUSES
        assert forbidden not in finding.status
    assert f'"readiness_summary": "{forbidden}"' not in serialized


def test_evaluation_summary_is_a_deterministic_fact_only_template(make_proposal, evaluation_of):
    proposal = make_proposal()
    evaluation = evaluation_of(proposal=proposal)
    assert evaluation.evaluation_summary == evaluation_of(proposal=proposal).evaluation_summary
    assert evaluation.proposal_id in evaluation.evaluation_summary
    assert evaluation.execution_plan_id in evaluation.evaluation_summary
    assert evaluation.completeness_score in evaluation.evaluation_summary
    # It states the boundary rather than a recommendation.
    assert "not an approval" in evaluation.evaluation_summary


def test_evaluation_has_no_free_form_reviewer_notes_field(evaluation_of):
    """Free-form evaluator-authored prose invites interpretation and non-determinism; PR F has none."""
    assert not hasattr(evaluation_of(), "reviewer_notes")
