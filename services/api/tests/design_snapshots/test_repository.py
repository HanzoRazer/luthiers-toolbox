"""Immutable publication, collision, corruption, and reopen."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.design_snapshots import (
    FileDesignSnapshotRepository,
    capture_design_snapshot,
    new_design_snapshot_id,
)
from app.design_snapshots import repository as repository_module
from app.design_snapshots.errors import (
    DesignSnapshotRepositoryError,
    DuplicateDesignSnapshot,
)
from app.design_snapshots.repository import canonical_record_text

from .conftest import T0

API_ROOT = Path(__file__).resolve().parents[2]


def _snap(state, snapshot_id="dsn-synth-0001"):
    return capture_design_snapshot(
        project_id="project-synth-0001", job_id="JOB-SYNTH-0001", design_state=state,
        captured_at=T0, captured_by="operator-synth", design_snapshot_id=snapshot_id,
    )


@pytest.mark.unit
def test_save_is_immutable_and_same_bytes_are_idempotent(tmp_path, baseline_state):
    repo = FileDesignSnapshotRepository(tmp_path)
    snap = _snap(baseline_state)
    repo.save(snap)
    repo.save(snap)
    stored = (tmp_path / "dsn-synth-0001.json").read_text(encoding="utf-8")
    assert stored == canonical_record_text(snap)
    assert repo.get("dsn-synth-0001").snapshot_digest == snap.snapshot_digest
    other = _snap(baseline_state, "dsn-synth-0001")
    other_payload = json.loads(json.dumps(baseline_state))
    other_payload["spec"]["scale_length_mm"] = 646.0
    changed = _snap(other_payload, "dsn-synth-0001")
    with pytest.raises(DuplicateDesignSnapshot):
        repo.save(changed)
    assert (tmp_path / "dsn-synth-0001.json").read_text(encoding="utf-8") == stored
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.unit
def test_reopen_in_a_new_process_keeps_bytes(tmp_path, baseline_state, golden_text):
    repo = FileDesignSnapshotRepository(tmp_path)
    repo.save(_snap(baseline_state))
    script = (
        "import sys; from pathlib import Path; "
        "from app.design_snapshots import FileDesignSnapshotRepository as R; "
        "from app.design_snapshots.repository import canonical_record_text as T; "
        "record = R(Path(sys.argv[1])).get('dsn-synth-0001'); "
        "print(record.design_payload_digest); print(record.snapshot_digest); print(T(record))"
    )
    out = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)], cwd=API_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    assert out[2] == golden_text
    assert out[0] in golden_text and out[1] in golden_text


@pytest.mark.unit
def test_corrupt_foreign_and_leaking_files_fail_closed(tmp_path, golden_text):
    repo = FileDesignSnapshotRepository(tmp_path)
    (tmp_path / "dsn-trunc.json").write_text("{", encoding="utf-8")
    with pytest.raises(DesignSnapshotRepositoryError) as truncated:
        repo.get("dsn-trunc")
    assert truncated.value.code == "MALFORMED"
    payload = json.loads(golden_text)
    payload["snapshot_digest"] = "0" * 64
    (tmp_path / "dsn-synth-0001.json").write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    with pytest.raises(DesignSnapshotRepositoryError) as mismatch:
        repo.get("dsn-synth-0001")
    assert mismatch.value.code == "DIGEST_MISMATCH"
    (tmp_path / "foreign.json").write_text('{"schema_id":"other"}', encoding="utf-8")
    with pytest.raises(DesignSnapshotRepositoryError) as foreign:
        repo.get("foreign")
    assert foreign.value.code == "MALFORMED"
    payload = json.loads(golden_text)
    payload["schema_version"] = "9.0"
    (tmp_path / "dsn-version.json").write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    with pytest.raises(DesignSnapshotRepositoryError) as version:
        repo.get("dsn-version")
    assert version.value.code == "UNKNOWN_SCHEMA_VERSION"


@pytest.mark.unit
def test_absolute_path_in_a_stored_file_fails_closed(tmp_path):
    leaked = _snap({"notes": "relative-note"})
    text = json.loads(canonical_record_text(leaked))
    text["design_payload"] = {"notes": "/tmp/private.dxf"}
    text["design_payload_digest"] = "b" * 64
    text["project_ref"]["source_state_digest"] = "b" * 64
    text["snapshot_digest"] = "c" * 64
    (tmp_path / "dsn-synth-0001.json").write_text(
        json.dumps(text, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    with pytest.raises(DesignSnapshotRepositoryError) as refused:
        FileDesignSnapshotRepository(tmp_path).get("dsn-synth-0001")
    assert refused.value.code == "ABSOLUTE_PATH"


@pytest.mark.unit
def test_failed_publish_removes_the_temp_file(tmp_path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise OSError("disk")

    monkeypatch.setattr(repository_module.os, "link", boom)
    repo = FileDesignSnapshotRepository(tmp_path)
    with pytest.raises(OSError):
        repo.save(_snap({}))
    assert list(tmp_path.glob("*.tmp")) == []
    assert not (tmp_path / "dsn-synth-0001.json").exists()


@pytest.mark.unit
def test_generated_ids_survive_a_frozen_clock_and_reopen(tmp_path, monkeypatch):
    frozen = 1_761_600_000.123
    monkeypatch.setattr("app.design_snapshots.contracts.time.time", lambda: frozen)
    sample = [new_design_snapshot_id() for _ in range(64)]
    assert len(set(sample)) == 64
    prefix = f"dsn_{int(frozen * 1000)}_"
    assert all(item.startswith(prefix) and len(item.removeprefix(prefix)) == 32 for item in sample)
    snap = capture_design_snapshot(
        project_id="project-synth-0001", job_id="JOB-SYNTH-0001", design_state={"schema_version": "1.1"},
        captured_at=T0, captured_by="operator-synth",
    )
    FileDesignSnapshotRepository(tmp_path).save(snap)
    again = FileDesignSnapshotRepository(tmp_path).get(snap.design_snapshot_id)
    assert again.design_snapshot_id == snap.design_snapshot_id
    assert again.snapshot_digest == snap.snapshot_digest
