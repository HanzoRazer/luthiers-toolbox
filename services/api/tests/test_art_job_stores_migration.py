"""Tests for the SQLite-backed art job stores + one-time JSON migration.

Covers services/api/app/services/art_job_store.py (singular: lane/payload) and
art_jobs_store.py (plural: job_type/rings/...), which historically parsed and
rewrote the whole data/art_jobs.json on every op. See PERFORMANCE_AUDIT N1.
"""

import json
import sqlite3
from pathlib import Path

import pytest

from app.core import rmos_db as rdb
import app.services.art_job_store as singular
import app.services.art_jobs_store as plural


@pytest.fixture
def isolated_stores(tmp_path, monkeypatch):
    """Fresh temp rmos.db + temp legacy JSON, with store module state reset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    rdb.reset_rmos_db()
    rdb.get_rmos_db(tmp_path / "rmos.db")  # prime singleton with temp path

    legacy = tmp_path / "art_jobs.json"
    monkeypatch.setattr(singular, "JOBS_PATH", legacy)
    singular._reset_for_tests()
    monkeypatch.setattr(plural, "JOBS_PATH", legacy)
    plural._reset_for_tests()
    yield legacy
    singular._reset_for_tests()
    plural._reset_for_tests()
    rdb.reset_rmos_db()


def _seed_legacy(path: Path):
    path.write_text(json.dumps([
        {"id": "rosette_A", "lane": "rosette", "created_at": "1767589161.9",
         "payload": {"job_id": "rosette_A", "name": "A"}},
        {"id": "plural_B", "job_type": "rosette_cam", "created_at": 111.0,
         "post_preset": "grbl", "rings": 3, "z_passes": 2, "length_mm": 50.0,
         "gcode_lines": 100, "meta": {"kind": "RosetteCam"}},
    ]), encoding="utf-8")


def test_singular_round_trip(isolated_stores):
    job = singular.create_art_job("rosette", {"job_id": "j1", "name": "N"}, job_id="j1")
    assert job.id == "j1" and job.lane == "rosette"
    got = singular.get_job("j1")
    assert got["payload"]["name"] == "N"
    assert singular.get_job("missing") is None
    assert any(j["id"] == "j1" for j in singular._load())


def test_singular_upsert_no_duplicates(isolated_stores):
    singular.create_art_job("rosette", {"name": "v1"}, job_id="dup")
    singular.create_art_job("rosette", {"name": "v2"}, job_id="dup")
    rows = [j for j in singular._load() if j["id"] == "dup"]
    assert len(rows) == 1
    assert rows[0]["payload"]["name"] == "v2"


def test_plural_round_trip(isolated_stores):
    job = plural.create_art_job("p1", "rosette_cam", post_preset="mach4", rings=5,
                                z_passes=3, length_mm=99.0, gcode_lines=200,
                                meta={"kind": "RosetteCam"})
    assert job.id == "p1" and job.job_type == "rosette_cam" and job.rings == 5
    got = plural.get_art_job("p1")
    assert got is not None and got.post_preset == "mach4" and got.meta == {"kind": "RosetteCam"}
    assert plural.get_art_job("missing") is None
    assert any(r["job_type"] == "rosette_cam" for r in plural._load_jobs())


def test_migration_by_shape_and_decoupling(isolated_stores):
    _seed_legacy(isolated_stores)
    # Singular store imports only the lane/payload row.
    sing_ids = {j["id"] for j in singular._load()}
    assert sing_ids == {"rosette_A"}
    assert singular.get_job("plural_B") is None  # plural-shaped row skipped
    # Plural store imports only the job_type row.
    plur_ids = {r["id"] for r in plural._load_jobs()}
    assert plur_ids == {"plural_B"}
    assert plural.get_art_job("rosette_A") is None  # singular-shaped row skipped


def test_singular_migration_handles_dirty_rows_without_data_loss(isolated_stores):
    isolated_stores.write_text(json.dumps([
        {"id": "dup", "lane": "rosette", "created_at": "bad",
         "payload": "not-json"},
        {"id": "dup", "lane": "rosette", "created_at": 999.0,
         "payload": {"name": "duplicate"}},
        {"id": "plural_skip", "job_type": "rosette_cam"},
        {"lane": "rosette", "payload": {"name": "missing id"}},
    ]), encoding="utf-8")

    rows = singular._load()

    assert [row["id"] for row in rows] == ["dup"]
    assert rows[0]["payload"] == {"_raw_payload": "not-json"}
    assert rows[0]["created_at"] > 0


def test_singular_load_order_is_newest_first(isolated_stores):
    singular.create_art_job("rosette", {"name": "old"}, job_id="old")
    singular.create_art_job("rosette", {"name": "new"}, job_id="new")

    db = rdb.get_rmos_db()
    db.execute_update("UPDATE art_studio_jobs SET created_at = ? WHERE id = ?", (10.0, "old"))
    db.execute_update("UPDATE art_studio_jobs SET created_at = ? WHERE id = ?", (20.0, "new"))

    assert [row["id"] for row in singular._load()] == ["new", "old"]


def test_singular_failed_migration_rolls_back_and_retries(isolated_stores, monkeypatch):
    isolated_stores.write_text(json.dumps([
        {"id": "retry", "lane": "rosette", "created_at": 1.0,
         "payload": {"name": "retry"}}
    ]), encoding="utf-8")
    real_execute = singular._execute

    def fail_after_insert(*args, **kwargs):
        real_execute(*args, **kwargs)
        raise sqlite3.OperationalError("simulated migration interruption")

    monkeypatch.setattr(singular, "_execute", fail_after_insert)
    with pytest.raises(sqlite3.OperationalError):
        singular._load()
    assert singular._initialized is False

    monkeypatch.setattr(singular, "_execute", real_execute)
    rows = singular._load()
    assert [row["id"] for row in rows] == ["retry"]


def test_plural_migration_handles_duplicates_and_preserves_created_at(isolated_stores):
    isolated_stores.write_text(json.dumps([
        {"id": "plural_dup", "job_type": "rosette_cam", "created_at": 111.0,
         "post_preset": "first", "rings": 3, "z_passes": 2, "length_mm": 50.0,
         "gcode_lines": 100, "meta": {"kind": "RosetteCam"}},
        {"id": "plural_dup", "job_type": "rosette_cam", "created_at": 222.0,
         "post_preset": "duplicate", "rings": 9},
        {"id": "singular_skip", "lane": "rosette", "payload": {"name": "skip"}},
        {"job_type": "rosette_cam", "post_preset": "missing id"},
    ]), encoding="utf-8")

    rows = plural._load_jobs()

    assert [row["id"] for row in rows] == ["plural_dup"]
    assert rows[0]["post_preset"] == "first"
    assert rows[0]["created_at"].startswith("1970-01-01T00:01:51")


def test_plural_create_upserts_existing_job(isolated_stores):
    plural.create_art_job("dup", "rosette_cam", post_preset="first", rings=1)
    plural.create_art_job("dup", "rosette_cam", post_preset="second", rings=2)

    rows = [row for row in plural._load_jobs() if row["id"] == "dup"]
    assert len(rows) == 1
    assert rows[0]["post_preset"] == "second"
    assert rows[0]["rings"] == 2


def test_store_globals_rebind_after_rmos_db_reset(isolated_stores, tmp_path, monkeypatch):
    singular.create_art_job("rosette", {"name": "old"}, job_id="old")
    plural.create_art_job("old_plural", "rosette_cam")

    rdb.reset_rmos_db()
    new_legacy = tmp_path / "second_art_jobs.json"
    new_legacy.write_text(json.dumps([
        {"id": "new_singular", "lane": "rosette", "created_at": 1.0,
         "payload": {"name": "new"}},
        {"id": "new_plural", "job_type": "rosette_cam", "created_at": 2.0,
         "post_preset": "new"},
    ]), encoding="utf-8")
    monkeypatch.setattr(singular, "JOBS_PATH", new_legacy)
    monkeypatch.setattr(plural, "JOBS_PATH", new_legacy)
    rdb.get_rmos_db(tmp_path / "second_rmos.db")

    assert singular.get_job("old") is None
    assert singular.get_job("new_singular")["payload"]["name"] == "new"
    assert plural.get_art_job("old_plural") is None
    assert plural.get_art_job("new_plural").post_preset == "new"


def test_migration_runs_once(isolated_stores):
    _seed_legacy(isolated_stores)
    singular._load()  # triggers migration
    # A subsequent create must not re-import the legacy rows.
    singular.create_art_job("rosette", {"name": "new"}, job_id="new")
    ids = {j["id"] for j in singular._load()}
    assert ids == {"rosette_A", "new"}
