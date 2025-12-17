"""
Lightweight SQL migration system for Luthier's ToolBox.

Applies SQL files from migrations directory in alphabetical order.
Tracks applied migrations in schema_migrations table.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .session import engine as default_engine


@dataclass(frozen=True)
class Migration:
    """A single SQL migration."""
    id: str          # e.g. "0001_init_workflow_sessions"
    filename: str    # e.g. "0001_init_workflow_sessions.sql"
    sql: str


def _migrations_dir() -> Path:
    """Return path to migrations directory."""
    return Path(__file__).resolve().parent / "migrations"


def _ensure_migrations_table(db: Session) -> None:
    """Create schema_migrations table if it doesn't exist."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
          id TEXT PRIMARY KEY,
          applied_utc TEXT NOT NULL
        );
    """))
    db.commit()


def _load_migrations() -> List[Migration]:
    """Load all SQL migration files from migrations directory."""
    mig_dir = _migrations_dir()
    if not mig_dir.exists():
        # No migrations directory yet - return empty list
        return []

    migrations: List[Migration] = []
    for p in sorted(mig_dir.glob("*.sql")):
        mid = p.stem
        migrations.append(Migration(id=mid, filename=p.name, sql=p.read_text(encoding="utf-8")))
    return migrations


def _is_applied(db: Session, migration_id: str) -> bool:
    """Check if a migration has already been applied."""
    row = db.execute(
        text("SELECT 1 FROM schema_migrations WHERE id = :id LIMIT 1"),
        {"id": migration_id},
    ).fetchone()
    return row is not None


def apply_migrations(*, engine: Engine = default_engine, dry_run: bool = False) -> List[Tuple[str, str]]:
    """
    Apply all pending SQL migrations in order.

    Returns list of (migration_id, status) where status is:
      - "APPLIED"
      - "SKIPPED"
      - "DRY_RUN"
    """
    migrations = _load_migrations()
    results: List[Tuple[str, str]] = []

    if not migrations:
        return results

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
