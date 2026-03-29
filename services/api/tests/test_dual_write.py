"""Tests for DualWriteStore."""

from __future__ import annotations

import pytest

from app.db.dual_write import DualWriteStore


class _AsyncStore:
    def __init__(self, name: str):
        self.name = name
        self.writes: list = []
        self.deletes: list = []
        self._data: dict = {}
        self._fail_write = False
        self._fail_delete = False

    async def write(self, record):
        if self._fail_write:
            raise RuntimeError("simulated PG failure")
        self.writes.append(record)
        return record

    async def read(self, key):
        return self._data.get(key)

    async def delete(self, key):
        if self._fail_delete:
            raise RuntimeError("simulated PG delete failure")
        self.deletes.append(key)
        return self._data.pop(key, None)


@pytest.mark.asyncio
async def test_write_goes_to_both_stores():
    sqlite = _AsyncStore("sqlite")
    pg = _AsyncStore("pg")
    store = DualWriteStore(sqlite, pg)
    rec = {"id": 1}
    out = await store.write(rec)
    assert out == rec
    assert sqlite.writes == [rec]
    assert pg.writes == [rec]


@pytest.mark.asyncio
async def test_pg_failure_does_not_fail_request(caplog):
    sqlite = _AsyncStore("sqlite")
    pg = _AsyncStore("pg")
    pg._fail_write = True
    store = DualWriteStore(sqlite, pg)
    rec = {"id": 2}
    with caplog.at_level("ERROR"):
        out = await store.write(rec)
    assert out == rec
    assert sqlite.writes == [rec]
    assert pg.writes == []  # raised before append... actually write fails at start - pg.writes stays empty
    assert any("DualWrite" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_reads_from_primary():
    sqlite = _AsyncStore("sqlite")
    pg = _AsyncStore("pg")
    sqlite._data["k"] = "from_sqlite"
    pg._data["k"] = "from_pg"
    store = DualWriteStore(sqlite, pg)
    assert await store.read("k") == "from_sqlite"


@pytest.mark.asyncio
async def test_switch_reads_to_secondary():
    sqlite = _AsyncStore("sqlite")
    pg = _AsyncStore("pg")
    sqlite._data["k"] = "from_sqlite"
    pg._data["k"] = "from_pg"
    store = DualWriteStore(sqlite, pg)
    store.switch_reads_to_secondary()
    assert store.primary is pg
    assert store.secondary is sqlite
    assert await store.read("k") == "from_pg"


@pytest.mark.asyncio
async def test_disable_dual_write():
    sqlite = _AsyncStore("sqlite")
    pg = _AsyncStore("pg")
    store = DualWriteStore(sqlite, pg)
    store.disable_dual_write()
    rec = {"id": 3}
    await store.write(rec)
    assert sqlite.writes == [rec]
    assert pg.writes == []
