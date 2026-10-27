"""MAINT-DEFER-019: art preset and art job ids must not collide within one millisecond.

The ids were ``{lane}_preset_{epoch_ms}`` / ``{lane}_job_{epoch_ms}``. Two calls in
the same millisecond produced the same id, which surfaced three ways:

* SQLite preset store: ``UNIQUE constraint failed: art_presets.id`` (CI flake in
  ``test_sqlite_art_stores.py``)
* JSON preset store (served by ``root_art_router``): two rows with one id, so
  ``get_preset`` returns whichever comes first
* singular art job store, fallback id: ``ON CONFLICT(id) DO UPDATE`` silently
  overwrites the earlier job

Each test freezes ``time.time`` so the collision is forced, not left to timing.
"""
from __future__ import annotations

import time

import pytest

from app.core import rmos_db as rdb

FROZEN = 1_761_500_000.123


@pytest.fixture
def frozen_clock(monkeypatch):
    monkeypatch.setattr(time, "time", lambda: FROZEN)


@pytest.mark.unit
def test_sqlite_preset_store_same_millisecond_ids_are_distinct(tmp_path, frozen_clock):
    from app.stores.sqlite_art_presets_store import SQLiteArtPresetsStore

    rdb.reset_rmos_db()
    store = SQLiteArtPresetsStore(rdb.RMOSDatabase(tmp_path / "rmos.db"))
    a = store.create_preset("rosette", "A", {})
    b = store.create_preset("rosette", "B", {})

    assert a["id"] != b["id"]
    assert a["id"].startswith(f"rosette_preset_{int(FROZEN * 1000)}_")
    assert len(store.list_by_lane("rosette")) == 2
    rdb.reset_rmos_db()


@pytest.mark.unit
def test_json_preset_store_same_millisecond_ids_are_distinct(tmp_path, monkeypatch, frozen_clock):
    import app.services.art_presets_store as json_store

    monkeypatch.setattr(json_store, "PRESETS_PATH", tmp_path / "art_presets.json")
    a = json_store.create_preset("rosette", "A", {})
    b = json_store.create_preset("rosette", "B", {})

    assert a.id != b.id
    assert json_store.get_preset(b.id)["name"] == "B"


@pytest.mark.unit
def test_art_job_fallback_id_does_not_upsert_over_another_job(tmp_path, monkeypatch, frozen_clock):
    import app.services.art_job_store as singular

    monkeypatch.delenv("DATABASE_URL", raising=False)
    rdb.reset_rmos_db()
    rdb.get_rmos_db(tmp_path / "rmos.db")
    monkeypatch.setattr(singular, "JOBS_PATH", tmp_path / "art_jobs.json")
    singular._reset_for_tests()
    try:
        first = singular.create_art_job("rosette", {"name": "first"})
        second = singular.create_art_job("rosette", {"name": "second"})

        assert first.id != second.id
        assert {row["payload"]["name"] for row in singular._load()} == {"first", "second"}
    finally:
        singular._reset_for_tests()
        rdb.reset_rmos_db()
