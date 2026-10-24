"""File-backed evidence repository.

Each record is one JSON file named by its evidence id. The directory is
exclusive to this repository: every JSON file in it is a record, and a file
that is not one is corruption. Writes use a temporary file and ``os.link``,
the same publish shape as the repository's other atomic artifact files.
Closing this object and opening another on the same directory reads those
files again. There is no in-memory fallback and no delete method.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from app.physical_engineering.errors import EvidenceDigestMismatch, EvidenceNotFound
from app.physical_engineering.evidence_artifact_v1 import (
    SCHEMA_ID,
    EvidenceProvenance,
    EvidenceRecordError,
    LtbStoredEvidenceArtifactV1,
    _require_evidence_id,
)
from app.physical_engineering.evidence_serialization import canonical_record


class EvidenceRepositoryError(RuntimeError):
    """The store could not accept or reread a record."""


class DuplicateEvidenceContent(EvidenceRepositoryError):
    """This evidence id is already stored with different bytes."""


class FileEvidenceRepository:
    def __init__(self, directory: Path):
        if not isinstance(directory, Path):
            raise EvidenceRepositoryError("repository directory is required")
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, record: LtbStoredEvidenceArtifactV1) -> None:
        if not isinstance(record, LtbStoredEvidenceArtifactV1):
            raise EvidenceRepositoryError("record type is not stored evidence")
        self._require_supersession_target(record)
        path = self._path_for(record.evidence_id)
        text = canonical_record_text(record)
        if path.is_file():
            self._require_same_bytes(path, text, record.evidence_id)
            return
        self._publish_new(path, text, record.evidence_id)

    def get(self, evidence_id: str) -> LtbStoredEvidenceArtifactV1:
        path = self._path_for(evidence_id)
        if not path.is_file():
            raise EvidenceNotFound(evidence_id)
        return self._read(path)

    def list_for_subject(
        self, subject_id: str, subject_revision: str
    ) -> tuple[LtbStoredEvidenceArtifactV1, ...]:
        found = []
        for path in sorted(self._directory.glob("*.json")):
            record = self._read(path)
            if record.subject_id == subject_id and record.subject_revision == subject_revision:
                found.append(record)
        found.sort(key=lambda record: record.evidence_id)
        return tuple(found)

    def _require_supersession_target(self, record: LtbStoredEvidenceArtifactV1) -> None:
        target_id = record.supersedes_evidence_id
        if target_id is None:
            return
        prior = self.get(target_id)
        same = (
            prior.subject_id == record.subject_id
            and prior.subject_revision == record.subject_revision
            and prior.region_id == record.region_id
            and prior.coordinate_frame == record.coordinate_frame
            and prior.quantity_name == record.quantity_name
            and prior.unit == record.unit
        )
        if not same:
            raise EvidenceRepositoryError("supersession target does not match the new record")

    def _path_for(self, evidence_id: str) -> Path:
        _require_evidence_id(evidence_id, "evidence_id")
        directory = self._directory.resolve()
        path = (directory / f"{evidence_id}.json").resolve()
        if path.parent != directory:
            raise EvidenceRepositoryError("evidence id escapes the repository")
        return path

    def _publish_new(self, path: Path, text: str, evidence_id: str) -> None:
        handle, tmp_name = tempfile.mkstemp(
            prefix=path.name + ".", suffix=".tmp", dir=self._directory
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as outfile:
                outfile.write(text)
                outfile.flush()
                os.fsync(outfile.fileno())
            try:
                os.link(tmp_path, path)
            except FileExistsError:
                self._require_same_bytes(path, text, evidence_id)
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    def _require_same_bytes(self, path: Path, text: str, evidence_id: str) -> None:
        existing = path.read_text(encoding="utf-8")
        if existing != text:
            raise DuplicateEvidenceContent(evidence_id)

    def _read(self, path: Path) -> LtbStoredEvidenceArtifactV1:
        raw = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EvidenceRepositoryError("MALFORMED") from exc
        if not isinstance(payload, dict) or payload.get("schema_id") != SCHEMA_ID:
            raise EvidenceRepositoryError("MALFORMED")
        try:
            record = _record_from_payload(payload)
        except EvidenceRecordError as exc:
            if str(exc) == "DIGEST_MISMATCH":
                raise EvidenceDigestMismatch(str(payload.get("evidence_id", path.stem))) from exc
            raise EvidenceRepositoryError("MALFORMED") from exc
        except (KeyError, TypeError) as exc:
            raise EvidenceRepositoryError("MALFORMED") from exc
        if canonical_record_text(record) != raw:
            raise EvidenceRepositoryError("MALFORMED")
        return record


def canonical_record_text(record: LtbStoredEvidenceArtifactV1) -> str:
    from app.physical_engineering.evidence_artifact_v1 import record_fields

    return canonical_record(record_fields(record))


def _record_from_payload(payload: dict) -> LtbStoredEvidenceArtifactV1:
    provenance = payload["provenance"]
    return LtbStoredEvidenceArtifactV1(
        schema_id=payload["schema_id"],
        schema_version=payload["schema_version"],
        evidence_id=payload["evidence_id"],
        evidence_type=payload["evidence_type"],
        evidence_kind=payload["evidence_kind"],
        subject_id=payload["subject_id"],
        subject_revision=payload["subject_revision"],
        region_id=payload["region_id"],
        coordinate_frame=payload["coordinate_frame"],
        quantity_name=payload["quantity_name"],
        quantity_value=payload["quantity_value"],
        unit=payload["unit"],
        uncertainty=payload["uncertainty"],
        observed_at=payload["observed_at"],
        recorded_at=payload["recorded_at"],
        provenance=EvidenceProvenance(
            source_type=provenance["source_type"],
            source_id=provenance["source_id"],
            operator_or_process=provenance["operator_or_process"],
        ),
        payload_digest=payload["payload_digest"],
        supersedes_evidence_id=payload["supersedes_evidence_id"],
    )
