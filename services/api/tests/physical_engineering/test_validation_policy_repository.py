"""Durable policy files. Reopen, conflict, and corruption stay explicit."""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from app.physical_engineering.validation_policy_record_v1 import ValidationPolicyError
from app.physical_engineering.validation_policy_repository import (
    DuplicatePolicyContent,
    FileValidationPolicyRepository,
)
from .test_validation_policy_record_v1 import active_record, draft_record


def _directory(tmp_path):
    return tmp_path / "policies"


def test_save_and_reopen_preserves_the_digest(tmp_path):
    record = draft_record()
    directory = _directory(tmp_path)
    FileValidationPolicyRepository(directory).save(record)
    loaded = FileValidationPolicyRepository(directory).get(record.policy_id, record.policy_revision)
    assert loaded == record
    assert loaded.payload_digest == record.payload_digest


def test_identical_republish_is_idempotent(tmp_path):
    record = draft_record()
    repository = FileValidationPolicyRepository(_directory(tmp_path))
    repository.save(record)
    repository.save(record)
    assert repository.get(record.policy_id, record.policy_revision) == record


def test_different_bytes_for_the_same_revision_are_refused(tmp_path):
    repository = FileValidationPolicyRepository(_directory(tmp_path))
    repository.save(draft_record())
    with pytest.raises(DuplicatePolicyContent):
        repository.save(draft_record(max_test_removal_mm="1.5"))


def test_corrupt_json_is_a_structured_failure(tmp_path):
    directory = _directory(tmp_path)
    repository = FileValidationPolicyRepository(directory)
    (directory / "plate-review@1.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_MALFORMED"):
        repository.get("plate-review", "1")


def test_unknown_json_file_is_malformed(tmp_path):
    directory = _directory(tmp_path)
    repository = FileValidationPolicyRepository(directory)
    repository.save(draft_record())
    (directory / "notes.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_MALFORMED"):
        repository.list_records()


def test_extra_policy_field_is_refused(tmp_path):
    record = draft_record()
    directory = _directory(tmp_path)
    repository = FileValidationPolicyRepository(directory)
    repository.save(record)
    path = directory / f"{record.policy_id}@{record.policy_revision}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["policy_values"]["confidence"] = "high"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_INCOMPATIBLE"):
        repository.get(record.policy_id, record.policy_revision)


def test_edited_value_after_approval_fails_the_digest(tmp_path):
    record = active_record()
    directory = _directory(tmp_path)
    repository = FileValidationPolicyRepository(directory)
    repository.save(record)
    path = directory / f"{record.policy_id}@{record.policy_revision}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["policy_values"]["max_test_removal_mm"] = "9"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_DIGEST_MISMATCH"):
        repository.get(record.policy_id, record.policy_revision)


def test_temporary_file_is_removed_when_publish_fails(tmp_path, monkeypatch):
    directory = _directory(tmp_path)
    repository = FileValidationPolicyRepository(directory)

    def _fail_link(source, destination):
        raise OSError("link failed")

    monkeypatch.setattr(os, "link", _fail_link)
    with pytest.raises(OSError, match="link failed"):
        repository.save(draft_record())
    assert list(directory.glob("*.tmp")) == []
    assert list(directory.glob("*.json")) == []


def _concurrent_save(directory, record, barrier):
    barrier.wait()
    try:
        FileValidationPolicyRepository(directory).save(record)
        return "saved"
    except DuplicatePolicyContent:
        return "duplicate"


def test_concurrent_identical_publish_keeps_one_record(tmp_path):
    directory = _directory(tmp_path)
    barrier = Barrier(2)
    record = draft_record()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(
            pool.map(lambda _: _concurrent_save(directory, record, barrier), range(2))
        )
    assert results == ("saved", "saved")
    loaded = FileValidationPolicyRepository(directory).get(record.policy_id, record.policy_revision)
    assert loaded.payload_digest == record.payload_digest


def test_concurrent_conflicting_publish_keeps_exactly_one(tmp_path):
    directory = _directory(tmp_path)
    barrier = Barrier(2)
    records = (draft_record(), draft_record(max_test_removal_mm="1.5"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(lambda record: _concurrent_save(directory, record, barrier), records))
    assert sorted(results) == ["duplicate", "saved"]
    loaded = FileValidationPolicyRepository(directory).get("plate-review", "1")
    assert loaded.policy_values.max_test_removal_mm in {"1.25", "1.5"}
