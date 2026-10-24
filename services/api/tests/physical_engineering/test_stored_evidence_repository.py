"""Durable evidence files. Reopen means a new repository object, and a new process."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.physical_engineering.errors import EvidenceDigestMismatch, EvidenceNotFound
from app.physical_engineering.evidence_serialization import canonical_record
from app.physical_engineering.evidence_artifact_v1 import record_fields
from app.physical_engineering.stored_evidence_repository import (
    DuplicateEvidenceContent,
    FileEvidenceRepository,
)
from .test_evidence_artifact_v1 import make_record


API_ROOT = Path(__file__).resolve().parents[2]


def _directory(tmp_path):
    """This store owns its directory. The suite fixture also writes JSON beside it."""
    return tmp_path / "evidence"


def test_save_then_retrieve_preserves_fields(tmp_path):
    record = make_record()
    directory = _directory(tmp_path)
    FileEvidenceRepository(directory).save(record)
    loaded = FileEvidenceRepository(directory).get(record.evidence_id)
    assert record_fields(loaded) == record_fields(record)


def test_reopen_reads_the_same_bytes(tmp_path):
    record = make_record()
    directory = _directory(tmp_path)
    FileEvidenceRepository(directory).save(record)
    text = (directory / f"{record.evidence_id}.json").read_text(encoding="utf-8")
    reopened = FileEvidenceRepository(directory).get(record.evidence_id)
    assert text == canonical_record(record_fields(reopened))


def test_new_process_reads_the_saved_record(tmp_path):
    record = make_record()
    directory = _directory(tmp_path)
    FileEvidenceRepository(directory).save(record)
    script = (
        "from pathlib import Path\n"
        "from app.physical_engineering.stored_evidence_repository import FileEvidenceRepository\n"
        f"record = FileEvidenceRepository(Path({str(directory)!r})).get({record.evidence_id!r})\n"
        "print(record.payload_digest)\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == record.payload_digest


def test_identical_replay_is_idempotent(tmp_path):
    record = make_record()
    repository = FileEvidenceRepository(_directory(tmp_path))
    repository.save(record)
    repository.save(record)
    assert repository.get(record.evidence_id).payload_digest == record.payload_digest


def test_same_id_with_different_payload_is_refused(tmp_path):
    repository = FileEvidenceRepository(_directory(tmp_path))
    repository.save(make_record())
    with pytest.raises(DuplicateEvidenceContent):
        repository.save(make_record(quantity_value="3.1"))


def test_missing_id_is_not_found(tmp_path):
    with pytest.raises(EvidenceNotFound):
        FileEvidenceRepository(_directory(tmp_path)).get("missing-evidence")


def test_payload_changed_after_digest_is_digest_mismatch(tmp_path):
    record = make_record()
    directory = _directory(tmp_path)
    repository = FileEvidenceRepository(directory)
    repository.save(record)
    path = directory / f"{record.evidence_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["quantity_value"] = "9.9"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(EvidenceDigestMismatch):
        repository.get(record.evidence_id)


def test_list_for_subject_is_sorted_and_scoped(tmp_path):
    repository = FileEvidenceRepository(_directory(tmp_path))
    repository.save(make_record(evidence_id="b-evidence"))
    repository.save(make_record(evidence_id="a-evidence", evidence_kind="modal_frequency", quantity_name="frequency", quantity_value="184.6", unit="hz", uncertainty="1.8"))
    repository.save(make_record(evidence_id="other-subject", subject_id="plate-008"))
    listed = repository.list_for_subject("plate-007", "rev-3")
    assert [record.evidence_id for record in listed] == ["a-evidence", "b-evidence"]
