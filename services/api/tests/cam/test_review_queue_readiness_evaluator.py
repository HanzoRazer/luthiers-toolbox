"""Evaluator tests — pure policy, no repository or framework dependency."""

import pytest

from app.cam.review_queue_readiness import (
    AggregateReadiness,
    ReadinessEvaluationError,
    ReadinessEvidence,
    ReadinessSeverity,
    ReadinessStatus,
    ReadinessRequirement,
    ReviewQueueReadinessContext,
    VerificationMode,
)
from app.cam.review_queue_readiness_evaluator import (
    aggregate_readiness,
    evaluate_requirement,
    evaluate_review_queue_readiness,
)


def _req(rid="R", kind="k", severity=ReadinessSeverity.BLOCKING,
         mode=VerificationMode.STATIC, note=None):
    return ReadinessRequirement(
        requirement_id=rid, title=f"title-{rid}", description="d",
        severity=severity, evidence_kind=kind, verification_mode=mode,
        authority_source="test", runtime_validation_note=note,
    )


def _ev(kind="k", present=True, source="src", detail="detail"):
    return ReadinessEvidence(
        evidence_kind=kind, present=present, source=source, detail=detail
    )


class TestRequirementEvaluation:
    def test_satisfied_when_evidence_present(self):
        f = evaluate_requirement(_req(), (_ev(present=True),))
        assert f.status is ReadinessStatus.SATISFIED
        assert f.evidence_sources == ["src"]

    def test_unsatisfied_on_confirmed_absence(self):
        f = evaluate_requirement(_req(), (_ev(present=False),))
        assert f.status is ReadinessStatus.UNSATISFIED

    def test_unresolved_when_nothing_was_collected(self):
        """Absence of evidence is not evidence of absence."""
        f = evaluate_requirement(_req(), ())
        assert f.status is ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED

    def test_runtime_mode_is_unresolved_without_governed_evidence(self):
        f = evaluate_requirement(_req(mode=VerificationMode.RUNTIME), ())
        assert f.status is ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED

    def test_hybrid_present_declaration_is_still_unresolved(self):
        """A declaration does not prove runtime enforcement."""
        f = evaluate_requirement(
            _req(mode=VerificationMode.HYBRID, note="needs runtime proof"),
            (_ev(present=True),),
        )
        assert f.status is ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED
        assert "runtime" in f.detail.lower()

    def test_evidence_of_another_kind_does_not_satisfy(self):
        f = evaluate_requirement(_req(kind="wanted"), (_ev(kind="other", present=True),))
        assert f.status is not ReadinessStatus.SATISFIED


class TestAggregation:
    def test_all_satisfied_is_ready(self):
        assert aggregate_readiness(
            (evaluate_requirement(_req(), (_ev(),)),)
        ) is AggregateReadiness.READY

    def test_warning_only_is_ready_with_warnings(self):
        f = evaluate_requirement(
            _req(severity=ReadinessSeverity.WARNING), (_ev(present=False),)
        )
        assert aggregate_readiness((f,)) is AggregateReadiness.READY_WITH_WARNINGS

    def test_blocking_unsatisfied_is_not_ready(self):
        f = evaluate_requirement(_req(), (_ev(present=False),))
        assert aggregate_readiness((f,)) is AggregateReadiness.NOT_READY

    def test_blocking_unresolved_is_not_ready(self):
        f = evaluate_requirement(_req(mode=VerificationMode.RUNTIME), ())
        assert aggregate_readiness((f,)) is AggregateReadiness.NOT_READY


class TestDeterminism:
    def test_finding_order_is_independent_of_evidence_order(self):
        reqs = (_req("R-C", "c"), _req("R-A", "a"), _req("R-B", "b"))
        ev_fwd = (_ev("a"), _ev("b"), _ev("c"))
        ev_rev = tuple(reversed(ev_fwd))

        r1 = evaluate_review_queue_readiness(
            ReviewQueueReadinessContext(requirements=reqs, evidence=ev_fwd)
        )
        r2 = evaluate_review_queue_readiness(
            ReviewQueueReadinessContext(requirements=reqs, evidence=ev_rev)
        )
        assert [f.requirement_id for f in r1.findings] == [
            f.requirement_id for f in r2.findings
        ]
        assert r1.to_dict() == r2.to_dict()

    def test_blocking_failures_sort_first(self):
        reqs = (
            _req("R-OK", "ok"),
            _req("R-BAD", "bad"),
        )
        ev = (_ev("ok", present=True), _ev("bad", present=False))
        report = evaluate_review_queue_readiness(
            ReviewQueueReadinessContext(requirements=reqs, evidence=ev)
        )
        assert report.findings[0].requirement_id == "R-BAD"

    def test_repeated_evaluation_is_identical(self):
        ctx = ReviewQueueReadinessContext(requirements=(_req(),), evidence=(_ev(),))
        assert (
            evaluate_review_queue_readiness(ctx).to_dict()
            == evaluate_review_queue_readiness(ctx).to_dict()
        )


class TestEvaluatorErrors:
    def test_evaluator_failure_raises_typed_error(self):
        """A broken evaluator must not be reported as a readiness verdict."""

        class Exploding(tuple):
            def __iter__(self):
                raise RuntimeError("boom")

        ctx = ReviewQueueReadinessContext(requirements=(_req(),), evidence=())
        object.__setattr__(ctx, "requirements", Exploding())
        with pytest.raises(ReadinessEvaluationError):
            evaluate_review_queue_readiness(ctx)
