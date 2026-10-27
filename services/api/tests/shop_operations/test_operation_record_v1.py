"""The shop-operation record states facts and refuses everything else."""
from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone

import pytest

from app.shop_operations import (
    HumanCompletion,
    JobReference,
    MaterialUsage,
    MeasuredDuration,
    OperationRecordError,
    OperationStatus,
    ShopOperationRecordV1,
    make_operation_record,
)
from app.shop_operations.operation_record_v1 import record_fields

T0 = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)


def measured(minutes: str = "42.5", **kw) -> MeasuredDuration:
    base = dict(minutes=minutes, basis="MEASURED", method="stopwatch",
                measured_by="operator-1", source_id="bench-log-2026-10-27")
    base.update(kw)
    return MeasuredDuration(**base)


def make_record(status=OperationStatus.STARTED, **kw) -> ShopOperationRecordV1:
    base = dict(record_id="rec-start", job_id="JOB-2026-0001", operation_id="top-thickness-pass-1",
                status=status, occurred_at=T0, recorded_at=T0, recorded_by="operator-1")
    if status is OperationStatus.COMPLETED:
        base.update(record_id="rec-done", occurred_at=T0 + timedelta(minutes=45),
                    recorded_at=T0 + timedelta(minutes=46), measured_duration=measured(),
                    material_usage=(MaterialUsage("spruce-top-plate-007", "1", "piece"),),
                    evidence_refs=("ev-thickness-map-007",), readiness_refs=("rd-acoustic-top-review",),
                    human_completion=HumanCompletion("operator-1", (T0 + timedelta(minutes=45)).isoformat()))
    base.update(kw)
    return make_operation_record(**base)


@pytest.mark.unit
def test_started_and_completed_records_build_and_digest_their_fields():
    started = make_record()
    done = make_record(OperationStatus.COMPLETED)
    assert started.job.verification == "UNVERIFIED_EXTERNAL_REFERENCE"
    assert started.job.system == "CNC-Production-Shop"
    assert done.measured_duration.basis == "MEASURED"
    assert len(done.payload_digest) == 64 and done.payload_digest != started.payload_digest


@pytest.mark.unit
def test_job_reference_cannot_claim_verification_or_another_system():
    with pytest.raises(OperationRecordError, match="UNVERIFIED_EXTERNAL_REFERENCE"):
        JobReference("CNC-Production-Shop", "JOB-1", "VERIFIED")
    with pytest.raises(OperationRecordError, match="must be CNC-Production-Shop"):
        JobReference("luthiers-toolbox", "JOB-1", "UNVERIFIED_EXTERNAL_REFERENCE")
    for bad in ("", " JOB-1", "JOB\n1", "J" * 201):
        with pytest.raises(OperationRecordError, match="job_id"):
            JobReference("CNC-Production-Shop", bad, "UNVERIFIED_EXTERNAL_REFERENCE")


@pytest.mark.unit
def test_a_derived_duration_is_never_an_actual():
    for basis in ("DERIVED_ESTIMATE", "ESTIMATED", "CALCULATED", ""):
        with pytest.raises(OperationRecordError, match="never an actual"):
            measured(basis=basis)
    for minutes in ("0", "-5", "1e3", "NaN", "12,5", ""):
        with pytest.raises(OperationRecordError, match="positive decimal"):
            measured(minutes=minutes)
    with pytest.raises(OperationRecordError, match="method"):
        measured(method="")


@pytest.mark.unit
def test_status_decides_which_facts_may_be_present():
    with pytest.raises(OperationRecordError, match="STARTED event has no duration"):
        make_record(measured_duration=measured())
    with pytest.raises(OperationRecordError, match="STARTED event has no duration"):
        make_record(material_usage=(MaterialUsage("spruce", "1", "piece"),))
    with pytest.raises(OperationRecordError, match="human completion"):
        make_record(OperationStatus.COMPLETED, human_completion=None)
    with pytest.raises(OperationRecordError, match="human completion"):
        make_record(OperationStatus.ABORTED, record_id="rec-abort",
                    human_completion=HumanCompletion("operator-1", T0.isoformat()))
    unmeasured = make_record(OperationStatus.COMPLETED, measured_duration=None)
    assert unmeasured.measured_duration is None  # "No actual recorded", never a guess
    with pytest.raises(OperationRecordError, match="unknown operation status"):
        make_record(status="APPROVED")


@pytest.mark.unit
def test_material_lines_need_explicit_quantity_and_unit():
    for qty, unit in (("0", "piece"), ("1", ""), ("1", "Piece"), ("one", "piece"), ("1", "mm thick")):
        with pytest.raises(OperationRecordError, match="material"):
            MaterialUsage("spruce", qty, unit)


@pytest.mark.unit
def test_evidence_and_readiness_references_stay_separate():
    with pytest.raises(OperationRecordError, match="both evidence and readiness"):
        make_record(OperationStatus.COMPLETED, readiness_refs=("ev-thickness-map-007",))
    with pytest.raises(OperationRecordError, match="repeats"):
        make_record(OperationStatus.COMPLETED, evidence_refs=("ev-a", "ev-a"))


@pytest.mark.unit
def test_correction_needs_target_and_reason_and_cannot_be_self():
    with pytest.raises(OperationRecordError, match="both supersedes_record_id and correction_reason"):
        make_record(OperationStatus.COMPLETED, supersedes_record_id="rec-old")
    with pytest.raises(OperationRecordError, match="supersede itself"):
        make_record(OperationStatus.COMPLETED, supersedes_record_id="rec-done", correction_reason="typo")


@pytest.mark.unit
def test_times_must_be_timezone_aware():
    with pytest.raises(OperationRecordError, match="timezone-aware"):
        make_record(occurred_at=datetime(2026, 10, 27, 14, 0))
    with pytest.raises(OperationRecordError, match="timezone-aware"):
        HumanCompletion("operator-1", "2026-10-27T14:00:00")


@pytest.mark.unit
def test_tampered_field_breaks_the_digest():
    done = make_record(OperationStatus.COMPLETED)
    with pytest.raises(OperationRecordError, match="DIGEST_MISMATCH"):
        replace(done, measured_duration=measured(minutes="10"))


@pytest.mark.unit
def test_record_carries_no_approval_release_or_cam_field():
    names = {f.name for f in fields(ShopOperationRecordV1)} | set(record_fields(make_record()))
    for cls in (JobReference, MeasuredDuration, MaterialUsage, HumanCompletion):
        names |= {f.name for f in fields(cls)}
    forbidden = ("approv", "authori", "release", "cam_", "manufactur", "design_", "fingerprint", "sha256")
    assert [n for n in names if any(word in n for word in forbidden)] == []
