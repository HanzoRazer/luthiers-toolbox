"""Immutable file store for design snapshots.

One JSON file per ``design_snapshot_id``. Publication is a temp file plus
``os.link`` in the same directory, then the temp file is removed. The same
bytes may be saved again. Different bytes for an existing id are refused.
There is no update and no delete.

The directory is exclusive to this store. One writer at a time is the
concurrency model: nothing here locks against a second process.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .contracts import (
    SCHEMA_ID,
    ActorReferenceV1,
    ArtifactReferenceV1,
    ExternalJobReferenceV1,
    GeneratorReferenceV1,
    LtbDesignSnapshotV1,
    LtbProjectReferenceV1,
    require_snapshot_id,
    snapshot_fields,
)
from .errors import (
    DesignSnapshotError,
    DesignSnapshotNotFound,
    DesignSnapshotRepositoryError,
    DuplicateDesignSnapshot,
)
from .serialization import canonical_record


class FileDesignSnapshotRepository:
    def __init__(self, directory: Path):
        if not isinstance(directory, Path):
            raise DesignSnapshotRepositoryError("repository directory is required", code="DIRECTORY")
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, record: LtbDesignSnapshotV1) -> None:
        if not isinstance(record, LtbDesignSnapshotV1):
            raise DesignSnapshotRepositoryError("record type is not a design snapshot", code="RECORD_TYPE")
        path = self._path_for(record.design_snapshot_id)
        text = canonical_record_text(record)
        if path.is_file():
            self._require_same_bytes(path, text, record.design_snapshot_id)
            return
        self._publish_new(path, text, record.design_snapshot_id)

    def get(self, design_snapshot_id: str) -> LtbDesignSnapshotV1:
        path = self._path_for(design_snapshot_id)
        if not path.is_file():
            raise DesignSnapshotNotFound(design_snapshot_id)
        return self._read(path)

    def _path_for(self, design_snapshot_id: str) -> Path:
        try:
            require_snapshot_id(design_snapshot_id)
        except DesignSnapshotError as exc:
            raise DesignSnapshotRepositoryError(str(exc), code="SNAPSHOT_ID") from exc
        directory = self._directory.resolve()
        path = (directory / f"{design_snapshot_id}.json").resolve()
        if path.parent != directory:
            raise DesignSnapshotRepositoryError("snapshot id escapes the repository", code="SNAPSHOT_ID")
        return path

    def _publish_new(self, path: Path, text: str, snapshot_id: str) -> None:
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
                self._require_same_bytes(path, text, snapshot_id)
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    def _require_same_bytes(self, path: Path, text: str, snapshot_id: str) -> None:
        if path.read_text(encoding="utf-8") != text:
            raise DuplicateDesignSnapshot(snapshot_id)

    def _read(self, path: Path) -> LtbDesignSnapshotV1:
        raw = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DesignSnapshotRepositoryError("MALFORMED", code="MALFORMED") from exc
        if not isinstance(payload, dict) or payload.get("schema_id") != SCHEMA_ID:
            raise DesignSnapshotRepositoryError("MALFORMED", code="MALFORMED")
        try:
            record = snapshot_from_payload(payload)
        except DesignSnapshotError as exc:
            kept = exc.code if exc.code in {"DIGEST_MISMATCH", "ABSOLUTE_PATH", "UNKNOWN_SCHEMA_VERSION"} else "MALFORMED"
            raise DesignSnapshotRepositoryError(str(exc), code=kept) from exc
        except (KeyError, TypeError, AttributeError) as exc:
            raise DesignSnapshotRepositoryError("MALFORMED", code="MALFORMED") from exc
        if canonical_record_text(record) != raw:
            raise DesignSnapshotRepositoryError("MALFORMED", code="MALFORMED")
        return record


def canonical_record_text(record: LtbDesignSnapshotV1) -> str:
    return canonical_record(snapshot_fields(record))


def snapshot_from_payload(payload: dict) -> LtbDesignSnapshotV1:
    job = payload["external_job_ref"]
    project = payload["project_ref"]
    actor = payload["captured_by"]
    return LtbDesignSnapshotV1(
        schema_id=payload["schema_id"],
        schema_version=payload["schema_version"],
        design_snapshot_id=payload["design_snapshot_id"],
        external_job_ref=ExternalJobReferenceV1(**job),
        project_ref=LtbProjectReferenceV1(**project),
        captured_at=payload["captured_at"],
        captured_by=ActorReferenceV1(**actor),
        design_payload=payload["design_payload"],
        design_payload_digest=payload["design_payload_digest"],
        artifact_refs=tuple(ArtifactReferenceV1(**item) for item in payload["artifact_refs"]),
        generator_refs=tuple(GeneratorReferenceV1(**item) for item in payload["generator_refs"]),
        snapshot_digest=payload["snapshot_digest"],
    )
