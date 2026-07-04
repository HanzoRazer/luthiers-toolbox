"""Tests for the SQLite-backed art job stores + one-time JSON migration.

Covers services/api/app/services/art_job_store.py (singular: lane/payload) and
art_jobs_store.py (plural: job_type/rings/...), which historically parsed and
rewrote the whole data/art_jobs.json on every op. See PERFORMANCE_AUDIT N1.
"""

import json
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
    monkeypatch.setattr(singular, "_initialized", False)
    monkeypatch.setattr(plural, "JOBS_PATH", legacy)
    monkeypatch.setattr(plural, "_migrated", False)
    monkeypatch.setattr(plural, "_store", None)
    yield legacy
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


def test_migration_runs_once(isolated_stores):
    _seed_legacy(isolated_stores)
    singular._load()  # triggers migration
    # A subsequent create must not re-import the legacy rows.
    singular.create_art_job("rosette", {"name": "new"}, job_id="new")
    ids = {j["id"] for j in singular._load()}
    assert ids == {"rosette_A", "new"}
