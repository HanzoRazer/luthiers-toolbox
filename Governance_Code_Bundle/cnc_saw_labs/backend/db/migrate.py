from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.session import engine as default_engine


@dataclass(frozen=True)
class Migration:
    id: str          # e.g. "0001_init_workflow_sessions"
    filename: str    # e.g. "0001_init_workflow_sessions.sql"
    sql: str


def _migrations_dir() -> Path:
    # Keep it explicit + repo-local
    return Path(__file__).resolve().parents[2] / "workflow" / "db" / "migrations"


def _ensure_migrations_table(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
          id TEXT PRIMARY KEY,
          applied_utc TEXT NOT NULL
        );
    """))


def _load_migrations() -> List[Migration]:
    mig_dir = _migrations_dir()
    if not mig_dir.exists():
        raise FileNotFoundError(f"Migration directory not found: {mig_dir}")

    migrations: List[Migration] = []
    for p in sorted(mig_dir.glob("*.sql")):
        mid = p.stem
        migrations.append(Migration(id=mid, filename=p.name, sql=p.read_text(encoding="utf-8")))
    return migrations


def _is_applied(db: Session, migration_id: str) -> bool:
    row = db.execute(
        text("SELECT 1 FROM schema_migrations WHERE id = :id LIMIT 1"),
        {"id": migration_id},
    ).fetchone()
    return row is not None


def apply_migrations(*, engine: Engine = default_engine, dry_run: bool = False) -> List[Tuple[str, str]]:
    """
    Applies all pending SQL migrations in order.

    Returns list of (migration_id, status) where status is:
      - "APPLIED"
      - "SKIPPED"
      - "DRY_RUN"
    """
    migrations = _load_migrations()
    results: List[Tuple[str, str]] = []

    with Session(engine) as db:
        _ensure_migrations_table(db)

        for m in migrations:
            if _is_applied(db, m.id):
                results.append((m.id, "SKIPPED"))
                continue

            if dry_run:
                results.append((m.id, "DRY_RUN"))
                continue

            # Apply migration within transaction
            db.execute(text(m.sql))
            db.execute(
                text("INSERT INTO schema_migrations (id, applied_utc) VALUES (:id, datetime('now'))"),
                {"id": m.id},
            )
            db.commit()
            results.append((m.id, "APPLIED"))

    return results

2) Two tiny SQL migrations
Create directory:
services/api/app/workflow/db/migrations/
0001_init_workflow_sessions.sql
-- 0001_init_workflow_sessions.sql
-- Creates workflow_sessions table (JSON-payload storage) used by DbWorkflowSessionStore.

CREATE TABLE IF NOT EXISTS workflow_sessions (
  session_id TEXT PRIMARY KEY,
  mode TEXT NOT NULL,
  state TEXT NOT NULL,
  session_json TEXT NOT NULL,
  created_utc TEXT NOT NULL DEFAULT (datetime('now')),
  updated_utc TEXT NOT NULL DEFAULT (datetime('now')),
  tool_id TEXT NULL,
  material_id TEXT NULL,
  machine_id TEXT NULL,
  candidate_attempt_count INTEGER NOT NULL DEFAULT 0
);

-- Trigger to update updated_utc automatically on update (SQLite)
CREATE TRIGGER IF NOT EXISTS workflow_sessions_updated_utc
AFTER UPDATE ON workflow_sessions
BEGIN
  UPDATE workflow_sessions
  SET updated_utc = datetime('now')
  WHERE session_id = NEW.session_id;
END;
0002_add_indexes.sql
-- 0002_add_indexes.sql
-- Adds simple indexes for common lookup patterns.

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_state ON workflow_sessions(state);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_mode ON workflow_sessions(mode);

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_tool_id ON workflow_sessions(tool_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_material_id ON workflow_sessions(material_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_machine_id ON workflow_sessions(machine_id);

3) CLI upgrade script
services/api/scripts/upgrade_db.py
from __future__ import annotations

import argparse
import os

from app.db.session import engine
from app.db.migrate import apply_migrations


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply lightweight SQL migrations to the RMOS SQLite database.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be applied, without applying.")
    args = parser.parse_args()

    results = apply_migrations(engine=engine, dry_run=args.dry_run)

    print("RMOS DB Migration Results")
    print("------------------------")
    for mid, status in results:
        print(f"{status:8} {mid}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

4) Stop relying on create_all() in production
In app/main.py, replace your create_all() startup with migration apply:
from app.db.migrate import apply_migrations

@app.on_event("startup")
def _init_db():
    # Apply SQL migrations instead of create_all()
    apply_migrations(dry_run=False)