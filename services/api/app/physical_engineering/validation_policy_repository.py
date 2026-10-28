"""File-backed validation-policy repository.

One JSON file per policy id and revision. The directory is exclusive: every
JSON file in it is a policy record. Publication uses a temporary file,
``fsync``, and ``os.link``, so an existing revision is not replaced. There is
no default directory, no in-memory fallback, and no delete method.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from app.physical_engineering.validation_policy_record_v1 import (
    SCHEMA_ID,
    PolicyApplicability,
    PolicyApproval,
    PolicyProvenance,
    PolicyValues,
    LtbValidationPolicyRecordV1,
    ValidationPolicyError,
)
from app.physical_engineering.validation_policy_serialization import canonical_policy_text


class DuplicatePolicyContent(ValidationPolicyError):
    """This policy id and revision are already stored with different bytes."""

    def __init__(self, detail: str):
        super().__init__("VALIDATION_POLICY_CONFLICT", detail)


class FileValidationPolicyRepository:
    def __init__(self, directory: Path):
        if not isinstance(directory, Path):
            raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "directory")
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, record: LtbValidationPolicyRecordV1) -> None:
        if not isinstance(record, LtbValidationPolicyRecordV1):
            raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "record")
        path = self._path_for(record.policy_id, record.policy_revision)
        text = canonical_policy_text(record)
        if path.is_file():
            self._require_same_bytes(path, text, record.policy_id)
            return
        self._publish_new(path, text, record.policy_id)

    def get(self, policy_id: str, policy_revision: str) -> LtbValidationPolicyRecordV1:
        path = self._path_for(policy_id, policy_revision)
        if not path.is_file():
            raise ValidationPolicyError("VALIDATION_POLICY_NOT_FOUND", policy_id)
        return self._read(path)

    def list_records(self) -> tuple[LtbValidationPolicyRecordV1, ...]:
        found = [self._read(path) for path in sorted(self._directory.glob("*.json"))]
        found.sort(key=lambda record: (record.policy_id, record.policy_revision))
        return tuple(found)

    def _path_for(self, policy_id: str, policy_revision: str) -> Path:
        from app.physical_engineering.validation_policy_record_v1 import _identifier

        _identifier(policy_id, "policy_id")
        _identifier(policy_revision, "policy_revision")
        directory = self._directory.resolve()
        name = f"{policy_id}@{policy_revision}.json"
        path = (directory / name).resolve()
        if path.parent != directory:
            raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "policy_id")
        return path

    def _publish_new(self, path: Path, text: str, policy_id: str) -> None:
        handle, tmp_name = tempfile.mkstemp(
            prefix=path.name + ".", suffix=".tmp", dir=self._directory
        )
        tmp_path = Path(tmp_name)
        try:
            self._write_temp(handle, tmp_path, text)
            self._link_new(tmp_path, path, text, policy_id)
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    def _write_temp(self, handle: int, tmp_path: Path, text: str) -> None:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as outfile:
            outfile.write(text)
            outfile.flush()
            os.fsync(outfile.fileno())

    def _link_new(self, tmp_path: Path, path: Path, text: str, policy_id: str) -> None:
        try:
            os.link(tmp_path, path)
        except FileExistsError:
            self._require_same_bytes(path, text, policy_id)

    def _require_same_bytes(self, path: Path, text: str, policy_id: str) -> None:
        if path.read_text(encoding="utf-8") != text:
            raise DuplicatePolicyContent(policy_id)

    def _read(self, path: Path) -> LtbValidationPolicyRecordV1:
        raw = path.read_text(encoding="utf-8")
        payload = _load_json(raw, path.name)
        try:
            record = _record_from_payload(payload)
        except ValidationPolicyError:
            raise
        except (KeyError, TypeError) as exc:
            raise ValidationPolicyError("VALIDATION_POLICY_MALFORMED", path.name) from exc
        if canonical_policy_text(record) != raw:
            raise ValidationPolicyError("VALIDATION_POLICY_MALFORMED", path.name)
        return record


def _load_json(raw: str, name: str) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationPolicyError("VALIDATION_POLICY_MALFORMED", name) from exc
    if not isinstance(payload, dict) or payload.get("schema_id") != SCHEMA_ID:
        raise ValidationPolicyError("VALIDATION_POLICY_MALFORMED", name)
    return payload


def _record_from_payload(payload: dict) -> LtbValidationPolicyRecordV1:
    _reject_unknown(
        payload,
        {
            "schema_id",
            "schema_version",
            "policy_id",
            "policy_revision",
            "status",
            "applicability",
            "policy_values",
            "provenance",
            "approval",
            "payload_digest",
        },
        "record",
    )
    applicability = payload["applicability"]
    values = payload["policy_values"]
    provenance = payload["provenance"]
    _reject_unknown(applicability, {"subject_id", "action"}, "applicability")
    _reject_unknown(
        values,
        {
            "max_test_removal_mm",
            "max_test_removal_unit",
            "min_test_remaining_thickness_mm",
            "min_test_remaining_thickness_unit",
        },
        "policy_values",
    )
    _reject_unknown(provenance, {"source_type", "source_id", "recorded_by"}, "provenance")
    return LtbValidationPolicyRecordV1(
        schema_id=payload["schema_id"],
        schema_version=payload["schema_version"],
        policy_id=payload["policy_id"],
        policy_revision=payload["policy_revision"],
        status=payload["status"],
        applicability=PolicyApplicability(applicability["subject_id"], applicability["action"]),
        policy_values=PolicyValues(
            values["max_test_removal_mm"],
            values["max_test_removal_unit"],
            values["min_test_remaining_thickness_mm"],
            values["min_test_remaining_thickness_unit"],
        ),
        provenance=PolicyProvenance(
            provenance["source_type"],
            provenance["source_id"],
            provenance["recorded_by"],
        ),
        approval=_approval_from_payload(payload["approval"]),
        payload_digest=payload["payload_digest"],
    )


def _approval_from_payload(payload) -> PolicyApproval | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValidationPolicyError("VALIDATION_POLICY_MALFORMED", "approval")
    _reject_unknown(
        payload,
        {
            "approved_by",
            "approved_at",
            "approval_basis_refs",
            "approved_payload_digest",
        },
        "approval",
    )
    refs = payload["approval_basis_refs"]
    if not isinstance(refs, list):
        raise ValidationPolicyError("VALIDATION_POLICY_MALFORMED", "approval_basis_refs")
    return PolicyApproval(
        approved_by=payload["approved_by"],
        approved_at=payload["approved_at"],
        approval_basis_refs=tuple(refs),
        approved_payload_digest=payload["approved_payload_digest"],
    )


def _reject_unknown(payload: dict, allowed: set[str], label: str) -> None:
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", label)
