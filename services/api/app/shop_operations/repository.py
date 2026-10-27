"""File-backed, append-only store for shop-operation records.

Each record is one JSON file named by its record id. The directory is exclusive
to this repository: every JSON file in it is a record, and a file that is not
one is corruption. Writes publish a temporary file with ``os.link`` so a record
appears whole or not at all. A new repository object, or a new process, on the
same directory reads the same files. There is no delete and no in-place edit:
a correction is a new record that supersedes an earlier one.

Sequencing, per ``(job_id, operation_id)`` over the records not superseded:

* a STARTED event comes first, and only once
* at most one terminal event (COMPLETED or ABORTED) follows it, no earlier than
  the start; a second one is refused
* a retry after ABORTED is a new ``operation_id``
* a correction names an existing, not-yet-superseded record for the same job,
  operation and status

The sequencing check reads, then writes. It assumes one writer per directory.
That single-writer limit is a deployment constraint of this store.

A new file whose material line has no measurement provenance is refused.
A file stored before that rule, re-saved with the same bytes, is idempotent.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from app.shop_operations.errors import (
    DuplicateOperationRecord,
    OperationRecordError,
    OperationRecordNotFound,
    OperationRepositoryError,
    OperationSequenceError,
)
from app.shop_operations.operation_record_v1 import (
    SCHEMA_ID,
    TERMINAL_STATUSES,
    HumanCompletion,
    JobReference,
    MaterialUsage,
    MeasuredDuration,
    OperationStatus,
    ShopOperationRecordV1,
    parse_time,
    record_fields,
    require_new_material_provenance,
    require_record_id,
)
from app.shop_operations.serialization import canonical_record


class FileShopOperationRepository:
    def __init__(self, directory: Path):
        if not isinstance(directory, Path):
            raise OperationRepositoryError("repository directory is required")
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, record: ShopOperationRecordV1) -> None:
        if not isinstance(record, ShopOperationRecordV1):
            raise OperationRepositoryError("record type is not a shop-operation record")
        path = self._path_for(record.record_id)
        text = canonical_record_text(record)
        if path.is_file():
            if path.read_text(encoding="utf-8") != text:
                raise DuplicateOperationRecord(record.record_id)
            return
        require_new_material_provenance(record)
        self._require_sequence(record)
        self._publish_new(path, text, record.record_id)

    def get(self, record_id: str) -> ShopOperationRecordV1:
        path = self._path_for(record_id)
        if not path.is_file():
            raise OperationRecordNotFound(record_id)
        return self._read(path)

    def list_for_job(self, job_id: str) -> tuple[ShopOperationRecordV1, ...]:
        """Every stored record for the job, superseded ones included, in event order."""
        found = [r for r in self._all() if r.job.job_id == job_id]
        found.sort(key=lambda r: (parse_time(r.occurred_at), r.record_id))
        return tuple(found)

    def effective_for_job(self, job_id: str) -> tuple[ShopOperationRecordV1, ...]:
        """The job's records with every superseded record removed."""
        records = self.list_for_job(job_id)
        superseded = {r.supersedes_record_id for r in records if r.supersedes_record_id}
        return tuple(r for r in records if r.record_id not in superseded)

    def _require_sequence(self, record: ShopOperationRecordV1) -> None:
        if record.supersedes_record_id is not None:
            self._require_correction_target(record)
            return
        history = [
            r for r in self.effective_for_job(record.job.job_id)
            if r.operation_id == record.operation_id
        ]
        starts = [r for r in history if r.status == OperationStatus.STARTED.value]
        terminals = [r for r in history if r.status in TERMINAL_STATUSES]
        if record.status == OperationStatus.STARTED.value:
            if starts:
                raise OperationSequenceError("operation already started; a retry is a new operation_id")
            return
        if not starts:
            raise OperationSequenceError(f"{record.status} needs a STARTED event first")
        if terminals:
            raise OperationSequenceError(f"operation already {terminals[0].status}")
        if parse_time(record.occurred_at) < parse_time(starts[0].occurred_at):
            raise OperationSequenceError(f"{record.status} cannot precede its STARTED event")

    def _require_correction_target(self, record: ShopOperationRecordV1) -> None:
        prior = self.get(record.supersedes_record_id)
        same = (
            prior.job.job_id == record.job.job_id
            and prior.operation_id == record.operation_id
            and prior.status == record.status
        )
        if not same:
            raise OperationSequenceError("a correction must match the job, operation and status it supersedes")
        if any(r.supersedes_record_id == prior.record_id for r in self._all()):
            raise OperationSequenceError("that record is already superseded; correct the latest record")

    def _all(self) -> list[ShopOperationRecordV1]:
        return [self._read(path) for path in sorted(self._directory.glob("*.json"))]

    def _path_for(self, record_id: str) -> Path:
        try:
            require_record_id(record_id, "record_id")
        except OperationRecordError as exc:
            raise OperationRepositoryError(str(exc)) from exc
        directory = self._directory.resolve()
        path = (directory / f"{record_id}.json").resolve()
        if path.parent != directory:
            raise OperationRepositoryError("record id escapes the repository")
        return path

    def _publish_new(self, path: Path, text: str, record_id: str) -> None:
        handle, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=self._directory)
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as outfile:
                outfile.write(text)
                outfile.flush()
                os.fsync(outfile.fileno())
            try:
                os.link(tmp_path, path)
            except FileExistsError:
                if path.read_text(encoding="utf-8") != text:
                    raise DuplicateOperationRecord(record_id) from None
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    def _read(self, path: Path) -> ShopOperationRecordV1:
        raw = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OperationRepositoryError("MALFORMED") from exc
        if not isinstance(payload, dict) or payload.get("schema_id") != SCHEMA_ID:
            raise OperationRepositoryError("MALFORMED")
        try:
            record = record_from_payload(payload)
        except OperationRecordError as exc:
            raise OperationRepositoryError(str(exc) if str(exc) == "DIGEST_MISMATCH" else "MALFORMED") from exc
        except (KeyError, TypeError, AttributeError) as exc:
            raise OperationRepositoryError("MALFORMED") from exc
        if canonical_record_text(record) != raw:
            raise OperationRepositoryError("MALFORMED")
        return record


def canonical_record_text(record: ShopOperationRecordV1) -> str:
    return canonical_record(record_fields(record))


def record_from_payload(payload: dict) -> ShopOperationRecordV1:
    duration, completion = payload["measured_duration"], payload["human_completion"]
    return ShopOperationRecordV1(
        schema_id=payload["schema_id"],
        schema_version=payload["schema_version"],
        record_id=payload["record_id"],
        job=JobReference(**payload["job"]),
        operation_id=payload["operation_id"],
        status=payload["status"],
        occurred_at=payload["occurred_at"],
        recorded_at=payload["recorded_at"],
        recorded_by=payload["recorded_by"],
        measured_duration=None if duration is None else MeasuredDuration(**duration),
        material_usage=tuple(MaterialUsage(**line) for line in payload["material_usage"]),
        evidence_refs=tuple(payload["evidence_refs"]),
        readiness_refs=tuple(payload["readiness_refs"]),
        human_completion=None if completion is None else HumanCompletion(**completion),
        supersedes_record_id=payload["supersedes_record_id"],
        correction_reason=payload["correction_reason"],
        payload_digest=payload["payload_digest"],
    )
