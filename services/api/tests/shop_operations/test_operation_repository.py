"""Durable, append-only operation history. Reopen means a new object, and a new process."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from app.shop_operations import (
    DuplicateOperationRecord,
    FileShopOperationRepository,
    OperationRecordNotFound,
    OperationRepositoryError,
    OperationSequenceError,
    OperationStatus,
)

from .test_operation_record_v1 import T0, make_record, measured

API_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def ops_dir(tmp_path):
    # The repository owns its directory exclusively; tmp_path also holds the
    # global RMOS isolation files (e.g. learned_overrides.json).
    return tmp_path / "ops"


def _abort(**kw):
    base = dict(record_id="rec-abort", occurred_at=T0 + timedelta(minutes=5),
                material_usage=(), evidence_refs=(), readiness_refs=())
    base.update(kw)
    return make_record(OperationStatus.ABORTED, **base)


@pytest.mark.unit
def test_records_survive_a_new_repository_and_a_new_process(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    repo.save(make_record())
    repo.save(make_record(OperationStatus.COMPLETED))

    reopened = FileShopOperationRepository(ops_dir)
    assert [r.status for r in reopened.list_for_job("JOB-2026-0001")] == ["STARTED", "COMPLETED"]

    script = (
        "import sys; from pathlib import Path; "
        "from app.shop_operations import FileShopOperationRepository as R; "
        "r = R(Path(sys.argv[1])).get('rec-done'); "
        "print(r.measured_duration.minutes, r.human_completion.completed_by, r.job.verification)"
    )
    out = subprocess.run([sys.executable, "-c", script, str(ops_dir)], cwd=API_ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    assert out == ["42.5", "operator-1", "UNVERIFIED_EXTERNAL_REFERENCE"]


@pytest.mark.unit
def test_saving_the_same_record_twice_is_idempotent_but_different_bytes_are_refused(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    repo.save(make_record())
    repo.save(make_record())
    with pytest.raises(DuplicateOperationRecord):
        repo.save(make_record(recorded_by="someone-else"))
    assert len(list(ops_dir.glob("*.json"))) == 1


@pytest.mark.unit
def test_terminal_events_need_a_start_and_happen_once(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    with pytest.raises(OperationSequenceError, match="needs a STARTED event first"):
        repo.save(make_record(OperationStatus.COMPLETED))
    repo.save(make_record())
    with pytest.raises(OperationSequenceError, match="already started"):
        repo.save(make_record(record_id="rec-start-2"))
    with pytest.raises(OperationSequenceError, match="cannot precede"):
        repo.save(_abort(occurred_at=T0 - timedelta(minutes=1)))
    repo.save(make_record(OperationStatus.COMPLETED))
    with pytest.raises(OperationSequenceError, match="already COMPLETED"):
        repo.save(_abort())
    with pytest.raises(OperationSequenceError, match="already COMPLETED"):
        repo.save(make_record(OperationStatus.COMPLETED, record_id="rec-done-2"))


@pytest.mark.unit
def test_a_retry_after_abort_is_a_new_operation(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    repo.save(make_record())
    repo.save(_abort())
    repo.save(make_record(record_id="rec-start-retry", operation_id="top-thickness-pass-1-retry"))
    assert {r.operation_id for r in repo.effective_for_job("JOB-2026-0001")} == {
        "top-thickness-pass-1", "top-thickness-pass-1-retry"}


@pytest.mark.unit
def test_corrections_supersede_without_editing_and_only_the_latest_can_be_corrected(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    repo.save(make_record())
    repo.save(make_record(OperationStatus.COMPLETED))
    fixed = make_record(OperationStatus.COMPLETED, record_id="rec-done-fix", measured_duration=measured("47"),
                        supersedes_record_id="rec-done", correction_reason="stopwatch read 42.5; log says 47")
    repo.save(fixed)

    assert repo.get("rec-done").measured_duration.minutes == "42.5"  # original kept, not edited
    effective = repo.effective_for_job("JOB-2026-0001")
    assert [r.record_id for r in effective] == ["rec-start", "rec-done-fix"]
    assert len(repo.list_for_job("JOB-2026-0001")) == 3

    with pytest.raises(OperationSequenceError, match="already superseded"):
        repo.save(make_record(OperationStatus.COMPLETED, record_id="rec-done-fix-2",
                              supersedes_record_id="rec-done", correction_reason="again"))
    with pytest.raises(OperationSequenceError, match="must match"):
        repo.save(_abort(record_id="rec-x", supersedes_record_id="rec-done-fix", correction_reason="wrong"))
    with pytest.raises(OperationRecordNotFound):
        repo.save(make_record(OperationStatus.COMPLETED, record_id="rec-y",
                              supersedes_record_id="rec-missing", correction_reason="none"))


@pytest.mark.unit
def test_jobs_are_kept_apart(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    repo.save(make_record())
    repo.save(make_record(record_id="rec-other", job_id="JOB-2026-0002"))
    assert [r.record_id for r in repo.list_for_job("JOB-2026-0002")] == ["rec-other"]


@pytest.mark.unit
def test_corrupt_or_tampered_files_are_refused_on_read(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    repo.save(make_record())
    path = ops_dir / "rec-start.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["recorded_by"] = "someone-else"
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(OperationRepositoryError, match="DIGEST_MISMATCH"):
        repo.get("rec-start")
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(OperationRepositoryError, match="MALFORMED"):
        repo.get("rec-start")


@pytest.mark.unit
def test_record_ids_cannot_escape_the_directory(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    for bad in ("../outside", "con", "UPPER", ""):
        with pytest.raises(OperationRepositoryError):
            repo.get(bad)
