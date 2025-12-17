from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from app.db.migrate import apply_migrations


def _names(db, sql: str) -> set[str]:
    rows = db.execute(text(sql)).fetchall()
    return {r[0] for r in rows}


def test_apply_migrations_creates_tables_and_indexes(tmp_path):
    # Temp, file-backed SQLite DB (closest to real usage)
    db_path = tmp_path / "rmos_migrations_test.sqlite3"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    # Run migrations
    results = apply_migrations(engine=engine, dry_run=False)

    # At least 2 migrations should be applied on a fresh DB
    applied = [mid for (mid, status) in results if status == "APPLIED"]
    assert "0001_init_workflow_sessions" in applied
    assert "0002_add_indexes" in applied

    # Validate DB objects exist
    with engine.connect() as db:
        tables = _names(db, "SELECT name FROM sqlite_master WHERE type='table';")
        assert "schema_migrations" in tables
        assert "workflow_sessions" in tables

        # Trigger from 0001
        triggers = _names(db, "SELECT name FROM sqlite_master WHERE type='trigger';")
        assert "workflow_sessions_updated_utc" in triggers

        # Indexes from 0002
        indexes = _names(db, "SELECT name FROM sqlite_master WHERE type='index';")

        expected_indexes = {
            "idx_workflow_sessions_state",
            "idx_workflow_sessions_mode",
            "idx_workflow_sessions_tool_id",
            "idx_workflow_sessions_material_id",
            "idx_workflow_sessions_machine_id",
        }
        missing = expected_indexes - indexes
        assert not missing, f"Missing expected indexes: {sorted(missing)}"

        # Bonus: migrations ledger has rows for applied migrations
        mig_rows = db.execute(text("SELECT id FROM schema_migrations ORDER BY id;")).fetchall()
        mig_ids = [r[0] for r in mig_rows]
        assert "0001_init_workflow_sessions" in mig_ids
        assert "0002_add_indexes" in mig_ids