"""Contract tests for review-queue architecture readiness models."""

import pytest

from app.cam.review_queue_readiness import (
    ReadinessContractError,
    AggregateReadiness,
    ReadinessEvidence,
    ReadinessFinding,
    ReadinessRequirement,
    ReadinessSeverity,
    ReadinessStatus,
    ReviewQueueReadinessContext,
    ReviewQueueReadinessReport,
    VerificationMode,
)


def _req(rid="RQR-TEST", severity=ReadinessSeverity.BLOCKING):
    return ReadinessRequirement(
        requirement_id=rid,
        title="t",
        description="d",
        severity=severity,
        evidence_kind="k",
        verification_mode=VerificationMode.STATIC,
        authority_source="test",
    )


class TestAuthorizationInvariants:
    """The report must never be usable as permission."""

    def test_invariants_default_false(self):
        report = ReviewQueueReadinessReport(
            aggregate=AggregateReadiness.READY, findings=()
        )
        assert report.implementation_authorized is False
        assert report.execution_authorized is False
        assert report.machine_output_allowed is False

    @pytest.mark.parametrize(
        "field",
        ["implementation_authorized", "execution_authorized", "machine_output_allowed"],
    )
    def test_cannot_be_set_true(self, field):
        with pytest.raises(ReadinessContractError):
            ReviewQueueReadinessReport(
                aggregate=AggregateReadiness.READY, findings=(), **{field: True}
            )

    def test_report_carries_non_authorization_notice(self):
        report = ReviewQueueReadinessReport(
            aggregate=AggregateReadiness.READY, findings=()
        )
        assert "does not authorize" in report.notice


class TestNoCallerSettableReadiness:
    """The defect that made the historical TD-2 design unsound."""

    def test_report_has_no_ready_input_field(self):
        # A caller-settable `ready` field would let the caller declare the answer.
        import dataclasses
        names = {f.name for f in dataclasses.fields(ReviewQueueReadinessReport)}
        assert "ready" not in names

    def test_evidence_requires_a_citable_source(self):
        with pytest.raises(ReadinessContractError):
            ReadinessEvidence(evidence_kind="k", present=True, source="")


class TestContextValidation:
    def test_duplicate_requirement_ids_rejected(self):
        with pytest.raises(ReadinessContractError):
            ReviewQueueReadinessContext(
                requirements=(_req("DUP"), _req("DUP")), evidence=()
            )

    def test_distinct_requirement_ids_accepted(self):
        ctx = ReviewQueueReadinessContext(
            requirements=(_req("A"), _req("B")), evidence=()
        )
        assert len(ctx.requirements) == 2


class TestFindingClassification:
    def test_blocking_unsatisfied_is_blocking_failure(self):
        f = ReadinessFinding(
            requirement_id="R", title="t",
            status=ReadinessStatus.UNSATISFIED,
            severity=ReadinessSeverity.BLOCKING, detail="d",
        )
        assert f.is_blocking_failure is True

    def test_blocking_unresolved_is_also_a_blocking_failure(self):
        """An unverifiable blocking prerequisite is not a pass."""
        f = ReadinessFinding(
            requirement_id="R", title="t",
            status=ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED,
            severity=ReadinessSeverity.BLOCKING, detail="d",
        )
        assert f.is_blocking_failure is True

    def test_deferred_by_policy_is_not_a_failure(self):
        f = ReadinessFinding(
            requirement_id="R", title="t",
            status=ReadinessStatus.DEFERRED_BY_POLICY,
            severity=ReadinessSeverity.BLOCKING, detail="d",
        )
        assert f.is_blocking_failure is False


class TestEnumSerialization:
    @pytest.mark.parametrize("enum_cls", [ReadinessStatus, ReadinessSeverity,
                                          VerificationMode, AggregateReadiness])
    def test_values_are_stable_strings(self, enum_cls):
        for member in enum_cls:
            assert isinstance(member.value, str)
            assert member.value == member.value.upper()
