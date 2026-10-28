"""The shop-operation record states facts and refuses everything else."""
from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone

import pytest

from app.shop_operations import (
    CURRENT_WRITE_SCHEMA_VERSION,
    HumanCompletion,
    JobReference,
    MaterialMeasurementSource,
    MaterialUsage,
    MeasuredDuration,
    OperationRecordError,
    OperationStatus,
    ShopOperationRecordV1,
    make_operation_record,
    material_provenance_disposition,
    new_operation_record_id,
)
from app.shop_operations.operation_record_v1 import _build_operation_record
import app.shop_operations.operation_record_v1 as records
from app.shop_operations.operation_record_v1 import record_fields

T0 = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)


def measured(minutes: str = "42.5", **kw) -> MeasuredDuration:
    base = dict(minutes=minutes, basis="MEASURED", method="stopwatch",
                measured_by="operator-1", source_id="bench-log-2026-10-27")
    base.update(kw)
    return MeasuredDuration(**base)


def consumed(quantity: str = "1", unit: str = "piece", **kw) -> MaterialUsage:
    base = dict(
        material_ref="spruce-top-plate-007",
        quantity=quantity,
        unit=unit,
        measurement_source="COUNTED",
        recorded_by="operator-1",
        observed_at=(T0 + timedelta(minutes=45)).isoformat(),
        source_ref=None,
    )
    base.update(kw)
    return MaterialUsage(**base)


def make_record(status=OperationStatus.STARTED, **kw) -> ShopOperationRecordV1:
    base = dict(record_id="rec-start", job_id="JOB-2026-0001", operation_id="top-thickness-pass-1",
                status=status, occurred_at=T0, recorded_at=T0, recorded_by="operator-1")
    if status is OperationStatus.COMPLETED:
        base.update(record_id="rec-done", occurred_at=T0 + timedelta(minutes=45),
                    recorded_at=T0 + timedelta(minutes=46), measured_duration=measured(),
                    material_usage=(consumed(),),
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
def test_default_record_ids_are_collision_safe_and_caller_ids_still_work(monkeypatch):
    frozen = 1_761_500_000.123
    monkeypatch.setattr(records.time, "time", lambda: frozen)
    first = new_operation_record_id()
    second = new_operation_record_id()
    prefix = f"sop_{int(frozen * 1000)}_"
    assert first != second
    assert first.startswith(prefix) and second.startswith(prefix)
    assert len(first.removeprefix(prefix)) == 32
    generated = make_operation_record(
        job_id="JOB-2026-0001", operation_id="top-thickness-pass-1",
        status=OperationStatus.STARTED, occurred_at=T0, recorded_at=T0, recorded_by="operator-1",
    )
    assert generated.record_id.startswith(prefix)
    supplied = make_record()
    assert supplied.record_id == "rec-start"


@pytest.mark.unit
def test_new_material_line_requires_measurement_provenance_and_refuses_estimates():
    legacy = MaterialUsage("spruce-top-plate-007", "1", "piece")
    assert legacy.measurement_source is None
    with pytest.raises(OperationRecordError, match="provenance is required"):
        make_record(OperationStatus.COMPLETED, material_usage=(legacy,))
    for source in ("ESTIMATE", "DERIVED", "DERIVED_ESTIMATE", "MOVE_COUNT", "DEFAULT", "UNKNOWN", "BOM", "PLANNED"):
        with pytest.raises(OperationRecordError, match="not a measurement"):
            consumed(measurement_source=source)
    with pytest.raises(OperationRecordError, match="requires source_ref"):
        consumed(measurement_source="IMPORTED_MEASUREMENT", source_ref=None)
    with pytest.raises(OperationRecordError, match="incomplete"):
        consumed(recorded_by=None)
    imported = consumed(measurement_source="IMPORTED_MEASUREMENT", source_ref="scale-export-9")
    assert imported.measurement_source == MaterialMeasurementSource.IMPORTED_MEASUREMENT.value
    weighed = consumed(measurement_source="SCALE_READING", quantity="18.6", unit="g")
    assert weighed.source_ref is None
    assert weighed.quantity == "18.6" and weighed.unit == "g"


@pytest.mark.unit
def test_minutes_and_quantity_keep_their_decimal_strings():
    tiny = "0." + ("0" * 400) + "1"
    duration = measured(minutes=tiny)
    line = consumed(quantity="18.60", unit="g")
    assert duration.minutes == tiny
    assert line.quantity == "18.60"
    done = make_record(OperationStatus.COMPLETED, measured_duration=duration, material_usage=(line,))
    assert done.measured_duration.minutes == tiny
    assert done.material_usage[0].quantity == "18.60"
    assert done.material_usage[0].unit == "g"


@pytest.mark.unit
def test_unit_tokens_stay_explicit_and_are_not_a_closed_conversion_table():
    for unit in ("g", "kg", "mm", "cm2", "cm3", "piece", "board_feet"):
        assert consumed(unit=unit).unit == unit
    for unit in ("Piece", "mm thick", ""):
        with pytest.raises(OperationRecordError, match="material unit"):
            consumed(unit=unit)


@pytest.mark.unit
def test_record_carries_no_approval_release_or_cam_field():
    names = {f.name for f in fields(ShopOperationRecordV1)} | set(record_fields(make_record()))
    for cls in (JobReference, MeasuredDuration, MaterialUsage, HumanCompletion):
        names |= {f.name for f in fields(cls)}
    forbidden = ("approv", "authori", "release", "cam_", "manufactur", "design_", "fingerprint", "sha256")
    assert [n for n in names if any(word in n for word in forbidden)] == []


@pytest.mark.unit
def test_new_writes_are_schema_1_1_and_unknown_versions_fail():
    started = make_record()
    done = make_record(OperationStatus.COMPLETED)
    assert CURRENT_WRITE_SCHEMA_VERSION == "1.1"
    assert started.schema_version == CURRENT_WRITE_SCHEMA_VERSION
    assert done.schema_version == CURRENT_WRITE_SCHEMA_VERSION
    assert material_provenance_disposition(done.material_usage[0]) == "COUNTED"
    for version in ("1.2", "2.0", "0.9"):
        with pytest.raises(OperationRecordError) as refused:
            _build_operation_record(
                record_id="rec-start", schema_version=version, job_id="JOB-2026-0001",
                operation_id="top-thickness-pass-1", status=OperationStatus.STARTED,
                occurred_at=T0, recorded_at=T0, recorded_by="operator-1",
                measured_duration=None, material_usage=(), evidence_refs=(), readiness_refs=(),
                human_completion=None, supersedes_record_id=None, correction_reason=None,
            )
        assert refused.value.code == "UNKNOWN_SCHEMA_VERSION"


@pytest.mark.unit
def test_id_factory_is_injected_and_does_not_replace_a_caller_id(monkeypatch):
    frozen = 1_761_500_000.123
    monkeypatch.setattr(records.time, "time", lambda: frozen)
    sample = [new_operation_record_id() for _ in range(256)]
    assert len(set(sample)) == 256
    prefix = f"sop_{int(frozen * 1000)}_"
    assert all(item.startswith(prefix) and len(item.removeprefix(prefix)) == 32 for item in sample)

    ticks = iter(1_761_500_000.0 + i * 0.001 for i in range(4))
    monkeypatch.setattr(records.time, "time", lambda: next(ticks))
    ordered = [new_operation_record_id() for _ in range(4)]
    assert ordered == sorted(ordered)

    def boom() -> str:
        raise AssertionError("factory must not replace a caller id")

    kept = make_operation_record(
        record_id="rec-caller", id_factory=boom, job_id="JOB-2026-0001",
        operation_id="top-thickness-pass-1", status=OperationStatus.STARTED,
        occurred_at=T0, recorded_at=T0, recorded_by="operator-1",
    )
    assert kept.record_id == "rec-caller"
    injected = make_operation_record(
        id_factory=lambda: "rec-injected", job_id="JOB-2026-0001",
        operation_id="top-thickness-pass-1", status=OperationStatus.STARTED,
        occurred_at=T0, recorded_at=T0, recorded_by="operator-1",
    )
    assert injected.record_id == "rec-injected"
    for bad in ("CON", "../outside", "Has Space", ""):
        with pytest.raises(OperationRecordError):
            make_operation_record(
                record_id=bad, job_id="JOB-2026-0001", operation_id="top-thickness-pass-1",
                status=OperationStatus.STARTED, occurred_at=T0, recorded_at=T0, recorded_by="operator-1",
            )


@pytest.mark.unit
def test_allowed_material_sources_and_prohibited_sources_keep_their_codes():
    for source in ("MANUAL_MEASUREMENT", "SCALE_READING", "COUNTED"):
        line = consumed(measurement_source=source)
        done = make_record(OperationStatus.COMPLETED, material_usage=(line,))
        assert done.material_usage[0].measurement_source == source
        assert done.material_usage[0].source_ref is None
    imported = consumed(measurement_source="IMPORTED_MEASUREMENT", source_ref="scale-export-9")
    assert make_record(OperationStatus.COMPLETED, material_usage=(imported,)).material_usage[0].source_ref == "scale-export-9"
    for source in ("ESTIMATE", "DERIVED", "DEFAULT", "BOM", "PLANNED", "UNKNOWN"):
        with pytest.raises(OperationRecordError) as refused:
            consumed(measurement_source=source)
        assert refused.value.code == "PROHIBITED_MEASUREMENT_SOURCE"
    with pytest.raises(OperationRecordError, match="requires source_ref"):
        consumed(measurement_source="IMPORTED_MEASUREMENT", source_ref=None)
    with pytest.raises(OperationRecordError, match="recorded_by"):
        consumed(recorded_by=" ")
    with pytest.raises(OperationRecordError, match="timezone-aware"):
        consumed(observed_at="2026-10-27T14:45:00")
    for quantity in ("0", "-1", "NaN", "Infinity", "1e3"):
        with pytest.raises(OperationRecordError, match="positive decimal"):
            consumed(quantity=quantity)
    assert consumed(quantity="18.6", unit="g") != consumed(quantity="18.6", unit="kg")
