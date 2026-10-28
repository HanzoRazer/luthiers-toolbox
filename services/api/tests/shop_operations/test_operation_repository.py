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
    make_operation_record,
    MaterialUsage,
    OperationRecordError,
    OperationRecordNotFound,
    OperationRepositoryError,
    OperationSequenceError,
    OperationStatus,
    material_provenance_disposition,
)
from app.shop_operations.operation_record_v1 import _build_operation_record

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


_V1_0_DIGESTS = {
    "rec-start": "0502de2eb983486d7fdf336989d5de1febe60a97c6546c71fdd68bd907a08c18",
    "rec-done": "6de312e9279943d8ecfd113b93ec831226ecabe825465d440e448cfb6db3bf6f",
    "rec-abort": "1bebcdecf9fa8b005267a7e69d0e203ce7026882867c0925726a92d404e0e5be",
    "rec-done-fix": "092938283f071f241d3f9facf66bd6551bb6b5764247a6eb782f801002ed48ba",
}
_V1_0_FILES = {
    "pre_harden_002_started.json": "rec-start",
    "pre_harden_002_completed.json": "rec-done",
    "pre_harden_002_aborted.json": "rec-abort",
    "pre_harden_002_completed_supersession.json": "rec-done-fix",
}


def _place_v1_0(ops_dir: Path, names: dict[str, str] | None = None) -> dict[str, bytes]:
    fixtures = Path(__file__).parent / "fixtures"
    chosen = _V1_0_FILES if names is None else names
    ops_dir.mkdir(parents=True, exist_ok=True)
    raws = {}
    for filename, record_id in chosen.items():
        raw = (fixtures / filename).read_bytes()
        (ops_dir / f"{record_id}.json").write_bytes(raw)
        raws[record_id] = raw
    return raws


@pytest.mark.unit
def test_v1_0_goldens_reopen_without_rewrite_or_invented_provenance(ops_dir):
    raws = _place_v1_0(ops_dir)
    repo = FileShopOperationRepository(ops_dir)
    loaded = {record_id: repo.get(record_id) for record_id in _V1_0_DIGESTS}
    assert loaded["rec-start"].status == "STARTED" and loaded["rec-start"].material_usage == ()
    assert loaded["rec-done"].status == "COMPLETED"
    assert loaded["rec-abort"].status == "ABORTED"
    assert loaded["rec-done"].measured_duration.minutes == "42.5"
    assert loaded["rec-abort"].material_usage[0].unit == "g"
    for record_id, digest in _V1_0_DIGESTS.items():
        assert loaded[record_id].schema_version == "1.0"
        assert loaded[record_id].payload_digest == digest
        assert (ops_dir / f"{record_id}.json").read_bytes() == raws[record_id]
    for record in (loaded["rec-done"], loaded["rec-abort"]):
        line = record.material_usage[0]
        assert material_provenance_disposition(line) == "LEGACY_PROVENANCE_UNAVAILABLE"
        assert line.recorded_by is None and line.observed_at is None and line.source_ref is None


@pytest.mark.unit
def test_v1_0_effective_state_is_unchanged_and_resave_does_not_rewrite(ops_dir):
    raws = _place_v1_0(ops_dir)
    repo = FileShopOperationRepository(ops_dir)
    assert [r.record_id for r in repo.effective_for_job("JOB-2026-0001")] == [
        "rec-start", "rec-abort", "rec-done-fix",
    ]
    for record_id in _V1_0_DIGESTS:
        repo.save(repo.get(record_id))
        assert (ops_dir / f"{record_id}.json").read_bytes() == raws[record_id]


@pytest.mark.unit
def test_new_v1_0_write_is_refused_and_v1_1_provenance_survives_reopen(ops_dir):
    raws = _place_v1_0(ops_dir, {
        "pre_harden_002_started.json": "rec-start",
        "pre_harden_002_completed.json": "rec-done",
    })
    repo = FileShopOperationRepository(ops_dir)
    done = repo.get("rec-done")
    fresh = _build_operation_record(
        record_id="rec-legacy-copy",
        schema_version="1.0",
        job_id=done.job.job_id,
        operation_id=done.operation_id,
        status=OperationStatus.COMPLETED,
        occurred_at=T0 + timedelta(minutes=45),
        recorded_at=T0 + timedelta(minutes=46),
        recorded_by="operator-1",
        measured_duration=done.measured_duration,
        material_usage=(MaterialUsage("spruce-top-plate-007", "1", "piece"),),
        evidence_refs=done.evidence_refs,
        readiness_refs=done.readiness_refs,
        human_completion=done.human_completion,
        supersedes_record_id=None,
        correction_reason=None,
    )
    with pytest.raises(OperationRecordError) as refused:
        repo.save(fresh)
    assert refused.value.code == "NEW_WRITE_REQUIRES_SCHEMA_1_1"
    assert not (ops_dir / "rec-legacy-copy.json").exists()
    assert list(ops_dir.glob("*.tmp")) == []

    from .test_operation_record_v1 import consumed, make_record
    hardened = make_record(
        OperationStatus.COMPLETED,
        record_id="rec-hard",
        material_usage=(consumed(measurement_source="SCALE_READING", quantity="18.6", unit="g"),),
        supersedes_record_id="rec-done",
        correction_reason="scale reading replaced the piece count",
    )
    repo.save(hardened)
    reopened = FileShopOperationRepository(ops_dir).get("rec-hard")
    assert reopened.schema_version == "1.1"
    assert reopened.material_usage[0].measurement_source == "SCALE_READING"
    assert reopened.material_usage[0].quantity == "18.6"
    assert [r.record_id for r in repo.effective_for_job("JOB-2026-0001")] == ["rec-start", "rec-hard"]
    assert (ops_dir / "rec-done.json").read_bytes() == raws["rec-done"]

    script = (
        "import sys; from pathlib import Path; "
        "from app.shop_operations import FileShopOperationRepository as R, material_provenance_disposition as D; "
        "repo = R(Path(sys.argv[1])); "
        "old = repo.get('rec-done'); new = repo.get('rec-hard'); "
        "print(old.schema_version, old.payload_digest, D(old.material_usage[0])); "
        "print(new.schema_version, new.record_id, new.material_usage[0].measurement_source, new.material_usage[0].unit)"
    )
    out = subprocess.run(
        [sys.executable, "-c", script, str(ops_dir)], cwd=API_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    assert out[0] == f"1.0 {_V1_0_DIGESTS['rec-done']} LEGACY_PROVENANCE_UNAVAILABLE"
    assert out[1] == "1.1 rec-hard SCALE_READING g"


@pytest.mark.unit
def test_generated_id_reopens_under_the_same_id(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    record = make_operation_record(
        job_id="JOB-2026-0001", operation_id="top-thickness-pass-1",
        status=OperationStatus.STARTED, occurred_at=T0, recorded_at=T0, recorded_by="operator-1",
    )
    repo.save(record)
    again = FileShopOperationRepository(ops_dir).get(record.record_id)
    assert again.record_id == record.record_id
    assert again.schema_version == "1.1"
    assert again.payload_digest == record.payload_digest


@pytest.mark.unit
def test_record_ids_cannot_escape_the_directory(ops_dir):
    repo = FileShopOperationRepository(ops_dir)
    for bad in ("../outside", "con", "UPPER", ""):
        with pytest.raises(OperationRepositoryError):
            repo.get(bad)
