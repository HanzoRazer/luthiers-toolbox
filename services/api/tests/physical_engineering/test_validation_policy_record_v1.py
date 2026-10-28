"""Policy record rules. Fixture numbers are not an approved production policy."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.physical_engineering.evidence_serialization import payload_digest
from app.physical_engineering.validation_policy_record_v1 import (
    PolicyStatus,
    ValidationPolicyError,
    digest_fields,
    make_validation_policy_record,
)
from app.physical_engineering.validation_policy_record_v1 import _parts, _unsigned_fields


def _arguments(**over):
    base = dict(
        policy_id="plate-review",
        policy_revision="1",
        status="DRAFT",
        subject_id="plate-007",
        action="remove_material",
        max_test_removal_mm="1.25",
        max_test_removal_unit="mm",
        min_test_remaining_thickness_mm="2",
        min_test_remaining_thickness_unit="mm",
        source_type="owner_worksheet",
        source_id="policy-field-authority",
        recorded_by="test-fixture",
    )
    base.update(over)
    return base


def draft_record(**over):
    return make_validation_policy_record(**_arguments(**over))


def _payload_digest(**over) -> str:
    args = _arguments(**over)
    applicability, values, provenance = _parts(
        args["subject_id"],
        args["action"],
        args["max_test_removal_mm"],
        args["max_test_removal_unit"],
        args["min_test_remaining_thickness_mm"],
        args["min_test_remaining_thickness_unit"],
        args["source_type"],
        args["source_id"],
        args["recorded_by"],
    )
    return payload_digest(
        _unsigned_fields(
            args["policy_id"],
            args["policy_revision"],
            args["status"],
            applicability,
            values,
            provenance,
        )
    )


def active_record(**over):
    args = _arguments()
    args.update(over)
    args["status"] = over.get("status", "ACTIVE")
    return make_validation_policy_record(
        **args,
        approved_by="test-fixture-owner",
        approved_at=datetime(2026, 10, 23, 22, 0, tzinfo=timezone.utc),
        approval_basis_refs=("owner-worksheet-incomplete",),
        approved_payload_digest=_payload_digest(**args),
    )


def test_complete_draft_is_valid_and_not_active():
    record = draft_record()
    assert record.status == PolicyStatus.DRAFT.value
    assert record.approval is None
    assert record.payload_digest == payload_digest(digest_fields(record))


def test_draft_digest_is_stable():
    record = draft_record()
    assert record.payload_digest == "d5ece888ec5757285891c17c05ca96069b86e9f4531c270afcc351c00fed08a7"
    assert record.payload_digest == draft_record().payload_digest


def test_active_record_without_approval_is_refused():
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_APPROVED"):
        make_validation_policy_record(**_arguments(status="ACTIVE"))


def test_approval_digest_must_match_the_payload():
    args = _arguments(status="ACTIVE")
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_DIGEST_MISMATCH"):
        make_validation_policy_record(
            **args,
            approved_by="test-fixture-owner",
            approved_at=datetime(2026, 10, 23, 22, 0, tzinfo=timezone.utc),
            approval_basis_refs=("owner-worksheet-incomplete",),
            approved_payload_digest="0" * 64,
        )


def test_unsupported_schema_version_is_refused():
    record = draft_record()
    fields = _constructor_kwargs(record)
    fields["schema_version"] = "9.0"
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_INCOMPATIBLE"):
        from app.physical_engineering.validation_policy_record_v1 import (
            LtbValidationPolicyRecordV1,
        )

        LtbValidationPolicyRecordV1(**fields)


def test_unknown_status_is_refused():
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_INCOMPATIBLE:status"):
        draft_record(status="PROPOSED")


def test_blank_policy_id_or_revision_is_refused():
    with pytest.raises(ValidationPolicyError, match="policy_id"):
        draft_record(policy_id=" ")
    with pytest.raises(ValidationPolicyError, match="policy_revision"):
        draft_record(policy_revision="")


def test_policy_id_must_be_a_portable_filename():
    for invalid in ("Plate", "con", "../escape"):
        with pytest.raises(ValidationPolicyError):
            draft_record(policy_id=invalid)


def test_missing_provenance_is_refused():
    with pytest.raises(ValidationPolicyError, match="source_id"):
        draft_record(source_id="")


def test_non_finite_or_non_positive_removal_is_refused():
    for value in ("nan", "inf", "0", "-1", "01"):
        with pytest.raises(ValidationPolicyError, match="max_test_removal_mm"):
            draft_record(max_test_removal_mm=value)


def test_wrong_or_absent_unit_is_refused():
    with pytest.raises(ValidationPolicyError, match="max_test_removal_unit"):
        draft_record(max_test_removal_unit="in")
    with pytest.raises(ValidationPolicyError, match="min_test_remaining_thickness_unit"):
        draft_record(min_test_remaining_thickness_unit="MM")


def test_naive_approval_time_is_refused():
    args = _arguments(status="ACTIVE")
    with pytest.raises(ValidationPolicyError, match="approved_at"):
        make_validation_policy_record(
            **args,
            approved_by="test-fixture-owner",
            approved_at=datetime(2026, 10, 23, 22, 0),
            approval_basis_refs=("owner-worksheet-incomplete",),
            approved_payload_digest=_payload_digest(**args),
        )


def test_active_record_binds_approval_to_the_payload_digest():
    record = active_record()
    assert record.approval is not None
    assert record.approval.approved_payload_digest == record.payload_digest
    assert record.approval.approved_by == "test-fixture-owner"


def _constructor_kwargs(record):
    return dict(
        schema_id=record.schema_id,
        schema_version=record.schema_version,
        policy_id=record.policy_id,
        policy_revision=record.policy_revision,
        status=record.status,
        applicability=record.applicability,
        policy_values=record.policy_values,
        provenance=record.provenance,
        approval=record.approval,
        payload_digest=record.payload_digest,
    )
