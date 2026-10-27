"""LTB shop-operation record (SHOP-OP-RECORD-001).

One record is one event in the life of one operation on one job: it started,
it completed, or it was aborted. The record states facts only:

* which job and operation (the CNC-Production-Shop ``job_id`` is the governing
  key, owner ruling R1/R5, 2026-10-26)
* the event status
* a measured duration and how it was measured
* material used, with quantity and unit. A new line also records how that
  quantity was measured. A line stored before SHOP-OP-RECORD-HARDEN-002 may
  omit that provenance; it stays readable and is not rewritten
* evidence references and readiness references, kept apart
* who completed the operation

It carries no approval, release or CAM field and grants no manufacturing
authority (owner ruling R4). Human completion records that a person finished
the work; it does not authorize anything.

LTB cannot verify a CNC-Production-Shop ``job_id``: no resolver or contract
exists. Every job reference therefore says so, as
``UNVERIFIED_EXTERNAL_REFERENCE``, and no other verification state is accepted.

A derived or estimated duration is never an actual (owner ruling R7). The only
duration basis is ``MEASURED``; an unmeasured operation simply has no duration.
Minutes stay a positive decimal string. That string is the precision, and the
unit stays minutes. The value is not converted to seconds or to a binary float.

A derived, estimated, planned, or BOM quantity is never material consumption.
New material lines name a measurement source. Historical lines without that
source remain valid on read.

Design fingerprints are deliberately absent: pinning a design revision to the
job belongs to MVS step S4, not to this record.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
import re
import time
from types import SimpleNamespace
import uuid

from app.shop_operations.errors import OperationRecordError
from app.shop_operations.serialization import payload_digest


SCHEMA_ID = "ltb_shop_operation_record"
SCHEMA_VERSION = "1.0"
JOB_SYSTEM = "CNC-Production-Shop"

_RECORD_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9_-])?$")
_WINDOWS_RESERVED_NAMES = {
    "aux", "clock$", "con", "nul", "prn",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
}
_UNIT = re.compile(r"^[a-z][a-z0-9_]*$")
_POSITIVE_DECIMAL = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
_EXTERNAL_ID_MAX = 200


class OperationStatus(str, Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class JobReferenceVerification(str, Enum):
    """How far LTB has verified a job reference. Only one state exists today."""

    UNVERIFIED_EXTERNAL_REFERENCE = "UNVERIFIED_EXTERNAL_REFERENCE"


class DurationBasis(str, Enum):
    """Why a duration is an actual. Derived estimates have no member here."""

    MEASURED = "MEASURED"


class MaterialMeasurementSource(str, Enum):
    """How a consumed quantity was measured. Estimates have no member here."""

    MANUAL_MEASUREMENT = "MANUAL_MEASUREMENT"
    SCALE_READING = "SCALE_READING"
    COUNTED = "COUNTED"
    IMPORTED_MEASUREMENT = "IMPORTED_MEASUREMENT"


TERMINAL_STATUSES = frozenset({OperationStatus.COMPLETED.value, OperationStatus.ABORTED.value})


def text_token(value: object) -> bool:
    """True for a non-blank string with no leading or trailing space."""
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _require_positive_decimal(value: object, message: str) -> None:
    """Accept the decimal string as written. Refuse zero, negatives, and non-decimals."""
    if not isinstance(value, str) or _POSITIVE_DECIMAL.fullmatch(value) is None:
        raise OperationRecordError(message)
    if Decimal(value) <= 0:
        raise OperationRecordError(message)


@dataclass(frozen=True)
class JobReference:
    system: str
    job_id: str
    verification: str

    def __post_init__(self) -> None:
        if self.system != JOB_SYSTEM:
            raise OperationRecordError(f"job reference system must be {JOB_SYSTEM}")
        job_id = self.job_id
        if not text_token(job_id) or len(job_id) > _EXTERNAL_ID_MAX or not job_id.isprintable():
            raise OperationRecordError("job_id is required")
        if self.verification != JobReferenceVerification.UNVERIFIED_EXTERNAL_REFERENCE.value:
            raise OperationRecordError(
                "no job resolver exists; a job reference can only be UNVERIFIED_EXTERNAL_REFERENCE"
            )


@dataclass(frozen=True)
class MeasuredDuration:
    minutes: str
    basis: str
    method: str
    measured_by: str
    source_id: str

    def __post_init__(self) -> None:
        if self.basis != DurationBasis.MEASURED.value:
            raise OperationRecordError("a derived or estimated duration is never an actual")
        _require_positive_decimal(self.minutes, "minutes must be a positive decimal string")
        for name in ("method", "measured_by", "source_id"):
            if not text_token(getattr(self, name)):
                raise OperationRecordError(f"duration {name} is required")


@dataclass(frozen=True)
class MaterialUsage:
    """One consumed quantity.

    ``measurement_source``, ``recorded_by``, ``observed_at``, and ``source_ref``
    are absent together on a line stored before provenance was required. A new
    line carries the first three, and ``source_ref`` when the source is
    ``IMPORTED_MEASUREMENT``. Units stay the caller's token. Nothing converts them.
    """

    material_ref: str
    quantity: str
    unit: str
    measurement_source: str | None = None
    recorded_by: str | None = None
    observed_at: str | None = None
    source_ref: str | None = None

    def __post_init__(self) -> None:
        if not text_token(self.material_ref):
            raise OperationRecordError("material_ref is required")
        _require_positive_decimal(self.quantity, "material quantity must be a positive decimal string")
        if not isinstance(self.unit, str) or not _UNIT.fullmatch(self.unit):
            raise OperationRecordError("material unit must be an explicit lowercase identifier")
        _validate_material_provenance(self)


def _validate_material_provenance(line: MaterialUsage) -> None:
    if (
        line.measurement_source is None
        and line.recorded_by is None
        and line.observed_at is None
        and line.source_ref is None
    ):
        return
    if line.measurement_source is None or line.recorded_by is None or line.observed_at is None:
        raise OperationRecordError("material measurement provenance is incomplete")
    try:
        source = MaterialMeasurementSource(line.measurement_source)
    except ValueError:
        raise OperationRecordError("material measurement source is not a measurement") from None
    object.__setattr__(line, "measurement_source", source.value)
    if not text_token(line.recorded_by):
        raise OperationRecordError("material recorded_by is required")
    require_time(line.observed_at, "material observed_at")
    if source is MaterialMeasurementSource.IMPORTED_MEASUREMENT:
        if not text_token(line.source_ref):
            raise OperationRecordError("imported material measurement requires source_ref")
        return
    if line.source_ref is not None and not text_token(line.source_ref):
        raise OperationRecordError("material source_ref is required")


@dataclass(frozen=True)
class HumanCompletion:
    completed_by: str
    completed_at: str

    def __post_init__(self) -> None:
        if not text_token(self.completed_by):
            raise OperationRecordError("completed_by is required")
        require_time(self.completed_at, "completed_at")


@dataclass(frozen=True)
class ShopOperationRecordV1:
    schema_id: str
    schema_version: str
    record_id: str
    job: JobReference
    operation_id: str
    status: str
    occurred_at: str
    recorded_at: str
    recorded_by: str
    measured_duration: MeasuredDuration | None
    material_usage: tuple[MaterialUsage, ...]
    evidence_refs: tuple[str, ...]
    readiness_refs: tuple[str, ...]
    human_completion: HumanCompletion | None
    supersedes_record_id: str | None
    correction_reason: str | None
    payload_digest: str

    def __post_init__(self) -> None:
        _require_identity(self)
        _require_status_fields(self)
        _require_references(self)
        _require_correction(self)
        if payload_digest(record_fields(self)) != self.payload_digest:
            raise OperationRecordError("DIGEST_MISMATCH")


def record_fields(record: ShopOperationRecordV1) -> dict[str, object]:
    duration = record.measured_duration
    completion = record.human_completion
    return {
        "schema_id": record.schema_id,
        "schema_version": record.schema_version,
        "record_id": record.record_id,
        "job": {
            "system": record.job.system,
            "job_id": record.job.job_id,
            "verification": record.job.verification,
        },
        "operation_id": record.operation_id,
        "status": record.status,
        "occurred_at": record.occurred_at,
        "recorded_at": record.recorded_at,
        "recorded_by": record.recorded_by,
        "measured_duration": None if duration is None else {
            "minutes": duration.minutes,
            "basis": duration.basis,
            "method": duration.method,
            "measured_by": duration.measured_by,
            "source_id": duration.source_id,
        },
        "material_usage": [material_line_fields(m) for m in record.material_usage],
        "evidence_refs": list(record.evidence_refs),
        "readiness_refs": list(record.readiness_refs),
        "human_completion": None if completion is None else {
            "completed_by": completion.completed_by,
            "completed_at": completion.completed_at,
        },
        "supersedes_record_id": record.supersedes_record_id,
        "correction_reason": record.correction_reason,
        "payload_digest": record.payload_digest,
    }


def material_line_fields(line: MaterialUsage) -> dict[str, object]:
    """Canonical material object. Historical lines keep their three stored keys."""
    fields: dict[str, object] = {
        "material_ref": line.material_ref,
        "quantity": line.quantity,
        "unit": line.unit,
    }
    if line.measurement_source is None:
        return fields
    fields["measurement_source"] = line.measurement_source
    fields["recorded_by"] = line.recorded_by
    fields["observed_at"] = line.observed_at
    fields["source_ref"] = line.source_ref
    return fields


def new_operation_record_id() -> str:
    """Collision-safe default id: millisecond prefix, then ``uuid4().hex``.

    Same shape as the MAINT-DEFER-019 art-id repair: the clock prefix keeps the
    id time-led, and the uuid keeps two calls in one millisecond distinct.
    Caller-supplied ids that pass ``require_record_id`` stay valid.
    """
    return f"sop_{int(time.time() * 1000)}_{uuid.uuid4().hex}"


def require_new_material_provenance(record: ShopOperationRecordV1) -> None:
    """Refuse a new write whose material line omits measurement provenance.

    A file already stored without provenance still loads and may be saved again
    when the bytes are unchanged. That path does not call this function.
    """
    for line in record.material_usage:
        if line.measurement_source is None:
            raise OperationRecordError("material measurement provenance is required")


def make_operation_record(
    *,
    record_id: str | None = None,
    job_id: str,
    operation_id: str,
    status: OperationStatus | str,
    occurred_at: datetime,
    recorded_at: datetime,
    recorded_by: str,
    measured_duration: MeasuredDuration | None = None,
    material_usage: tuple[MaterialUsage, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    readiness_refs: tuple[str, ...] = (),
    human_completion: HumanCompletion | None = None,
    supersedes_record_id: str | None = None,
    correction_reason: str | None = None,
) -> ShopOperationRecordV1:
    """Build a record and attach the digest of its canonical payload."""
    record = _build_operation_record(
        record_id=record_id,
        job_id=job_id,
        operation_id=operation_id,
        status=status,
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        recorded_by=recorded_by,
        measured_duration=measured_duration,
        material_usage=material_usage,
        evidence_refs=evidence_refs,
        readiness_refs=readiness_refs,
        human_completion=human_completion,
        supersedes_record_id=supersedes_record_id,
        correction_reason=correction_reason,
    )
    require_new_material_provenance(record)
    return record


def _build_operation_record(
    *,
    record_id: str | None,
    job_id: str,
    operation_id: str,
    status: OperationStatus | str,
    occurred_at: datetime,
    recorded_at: datetime,
    recorded_by: str,
    measured_duration: MeasuredDuration | None,
    material_usage: tuple[MaterialUsage, ...],
    evidence_refs: tuple[str, ...],
    readiness_refs: tuple[str, ...],
    human_completion: HumanCompletion | None,
    supersedes_record_id: str | None,
    correction_reason: str | None,
) -> ShopOperationRecordV1:
    """Digest-valid record with no new-write provenance gate.

    The repository reader rebuilds historical files through ``ShopOperationRecordV1``.
    Tests that must persist a pre-provenance shape use this builder. New callers
    use ``make_operation_record``.
    """
    status_value = status.value if isinstance(status, OperationStatus) else status
    draft = dict(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        record_id=new_operation_record_id() if record_id is None else record_id,
        job=JobReference(
            system=JOB_SYSTEM,
            job_id=job_id,
            verification=JobReferenceVerification.UNVERIFIED_EXTERNAL_REFERENCE.value,
        ),
        operation_id=operation_id,
        status=status_value,
        occurred_at=stamp(occurred_at, "occurred_at"),
        recorded_at=stamp(recorded_at, "recorded_at"),
        recorded_by=recorded_by,
        measured_duration=measured_duration,
        material_usage=tuple(material_usage),
        evidence_refs=tuple(evidence_refs),
        readiness_refs=tuple(readiness_refs),
        human_completion=human_completion,
        supersedes_record_id=supersedes_record_id,
        correction_reason=correction_reason,
    )
    # record_fields only reads attributes, so a namespace carries the draft to it.
    digest = payload_digest(record_fields(SimpleNamespace(**draft, payload_digest="")))
    return ShopOperationRecordV1(**draft, payload_digest=digest)


def require_record_id(value: object, name: str) -> None:
    valid = isinstance(value, str) and _RECORD_ID.fullmatch(value) is not None
    if not valid or value.split(".", 1)[0] in _WINDOWS_RESERVED_NAMES:
        raise OperationRecordError(f"{name} is required")


def require_time(value: object, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise OperationRecordError(f"{name} must be timezone-aware")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        raise OperationRecordError(f"{name} must be timezone-aware") from None
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        raise OperationRecordError(f"{name} must be timezone-aware")


def stamp(value: datetime, name: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OperationRecordError(f"{name} must be timezone-aware")
    return value.isoformat()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)


def _require_identity(record: ShopOperationRecordV1) -> None:
    if record.schema_id != SCHEMA_ID or record.schema_version != SCHEMA_VERSION:
        raise OperationRecordError("schema identity is not the LTB shop-operation record")
    require_record_id(record.record_id, "record_id")
    if not isinstance(record.job, JobReference):
        raise OperationRecordError("job reference is required")
    for name in ("operation_id", "recorded_by"):
        if not text_token(getattr(record, name)):
            raise OperationRecordError(f"{name} is required")
    require_time(record.occurred_at, "occurred_at")
    require_time(record.recorded_at, "recorded_at")


def _require_status_fields(record: ShopOperationRecordV1) -> None:
    try:
        status = OperationStatus(record.status)
    except ValueError:
        raise OperationRecordError("unknown operation status") from None
    if status is OperationStatus.STARTED:
        if record.measured_duration is not None or record.material_usage:
            raise OperationRecordError("a STARTED event has no duration or material usage yet")
    if (record.human_completion is not None) != (status is OperationStatus.COMPLETED):
        raise OperationRecordError("human completion is required on COMPLETED and only there")
    if record.measured_duration is not None and not isinstance(record.measured_duration, MeasuredDuration):
        raise OperationRecordError("duration must be a MeasuredDuration")
    if not all(isinstance(m, MaterialUsage) for m in record.material_usage):
        raise OperationRecordError("material usage lines must be MaterialUsage")


def _require_references(record: ShopOperationRecordV1) -> None:
    for name in ("evidence_refs", "readiness_refs"):
        refs = getattr(record, name)
        if not isinstance(refs, tuple) or not all(text_token(ref) for ref in refs):
            raise OperationRecordError(f"{name} must be a tuple of references")
        if len(set(refs)) != len(refs):
            raise OperationRecordError(f"{name} repeats a reference")
    if set(record.evidence_refs) & set(record.readiness_refs):
        raise OperationRecordError("a reference cannot be both evidence and readiness")


def _require_correction(record: ShopOperationRecordV1) -> None:
    target, reason = record.supersedes_record_id, record.correction_reason
    if (target is None) != (reason is None):
        raise OperationRecordError("a correction needs both supersedes_record_id and correction_reason")
    if target is None:
        return
    require_record_id(target, "supersedes_record_id")
    if target == record.record_id:
        raise OperationRecordError("a record cannot supersede itself")
    if not text_token(reason):
        raise OperationRecordError("correction_reason is required")
