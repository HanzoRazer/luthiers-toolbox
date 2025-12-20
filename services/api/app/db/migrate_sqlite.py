"""
DB Migration Runner (SQLite) - Pure SQLite, No ORM

Minimal, deterministic SQLite runner that:
- Applies migrations in filename order
- Tracks applied migrations in `_migrations` table
- Bootstraps automatically by running 0000_*.sql if tracking table doesn't exist
- Safe to run multiple times (skips already-applied)
- Each migration is transactional (per file)

Usage:
    cd services/api
    python -m app.db.migrate_sqlite

Env vars:
    RMOS_DB_PATH: preferred explicit path
    DATABASE_URL: accepts sqlite:///absolute/path or sqlite://relative/path
    SQLITE_PATH: fallback explicit path
    DRY_RUN: set to "1" or "true" for dry run mode
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class Migration:
    migration_id: str  # e.g. "0001_init_workflow_sessions"
    filename: str      # e.g. "0001_init_workflow_sessions.sql"
    path: Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_db_path() -> Path:
    """
    Resolve DB path for local/dev.

    Supported env vars:
      - RMOS_DB_PATH: preferred explicit path
      - DATABASE_URL: accepts sqlite:///absolute/path or sqlite://relative/path
      - SQLITE_PATH: fallback explicit path

    Default:
      services/api/.data/rmos.sqlite (relative to this file)
    """
    rmos_db_path = os.environ.get("RMOS_DB_PATH")
    if rmos_db_path:
        return Path(rmos_db_path).expanduser().resolve()

    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("sqlite://"):
        # sqlite:///abs/path OR sqlite://relative/path
        raw = db_url[len("sqlite://"):]
        # strip leading slashes only for the scheme separator case
        # sqlite:///C:/... => raw starts with "/C:/..."
        # sqlite:////tmp/x => raw starts with "//tmp/x"
        while raw.startswith("/") and len(raw) > 1 and raw[1] != "/":
            # keep Windows drive "C:/" intact when raw="/C:/..."
            break
        # normalize common sqlite URL forms
        if raw.startswith("///"):
            raw = raw[2:]  # "///abs" -> "/abs"
        return Path(raw).expanduser().resolve()

    sqlite_path = os.environ.get("SQLITE_PATH")
    if sqlite_path:
        return Path(sqlite_path).expanduser().resolve()

    # default: services/api/app/db/../../.data/rmos.sqlite
    here = Path(__file__).resolve()
    default_db = (here.parent.parent / ".data" / "rmos.sqlite").resolve()
    return default_db


def _migrations_dir() -> Path:
    return (Path(__file__).resolve().parent / "migrations").resolve()


def _discover_migrations() -> List[Migration]:
    mig_dir = _migrations_dir()
    if not mig_dir.exists():
        raise FileNotFoundError(f"migrations directory not found: {mig_dir}")

    migrations: List[Migration] = []
    for p in sorted(mig_dir.glob("*.sql")):
        stem = p.stem  # "0001_init_workflow_sessions"
        migrations.append(Migration(migration_id=stem, filename=p.name, path=p))

    if not migrations:
        raise FileNotFoundError(f"no .sql migrations found in: {mig_dir}")

    return migrations


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _ensure_db_parent(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _connect(db_path: Path) -> sqlite3.Connection:
    _ensure_db_parent(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def _read_applied(conn: sqlite3.Connection) -> List[str]:
    # Use _migrations table (existing in repo from 0000_init_migrations_table.sql)
    if not _table_exists(conn, "_migrations"):
        return []
    rows = conn.execute(
        "SELECT migration_id FROM _migrations ORDER BY migration_id ASC"
    ).fetchall()
    return [str(r["migration_id"]) for r in rows]


def _record_applied(conn: sqlite3.Connection, migration_id: str) -> None:
    # Use _migrations table (existing in repo from 0000_init_migrations_table.sql)
    conn.execute(
        "INSERT INTO _migrations (migration_id, applied_at) VALUES (?, ?)",
        (migration_id, _utc_now_iso()),
    )


def apply_migrations(
    conn: sqlite3.Connection,
    *,
    dry_run: bool = False,
) -> Tuple[int, int, List[str]]:
    """
    Apply pending migrations in filename order.

    Returns: (applied_count, skipped_count, applied_ids)

    Rules:
      - If _migrations table does not exist, we will apply 0000 first (required)
        then proceed with normal tracking.
      - Each migration runs in its own transaction.
      - Safe to run repeatedly: already-applied migrations are skipped.
    """
    migrations = _discover_migrations()

    # Bootstrap: ensure 0000 exists if table missing
    if not _table_exists(conn, "_migrations"):
        mig0 = next((m for m in migrations if m.migration_id.startswith("0000_")), None)
        if mig0 is None:
            raise RuntimeError(
                "_migrations table is missing and no 0000_*.sql migration was found."
            )
        if dry_run:
            # In dry-run mode, do not mutate; just report.
            applied = []
            already = set()
        else:
            sql = mig0.path.read_text(encoding="utf-8")
            with conn:
                conn.executescript(sql)
                # 0000 should create _migrations; record itself after it exists
                if not _table_exists(conn, "_migrations"):
                    raise RuntimeError(
                        "0000 migration ran, but _migrations table still does not exist."
                    )
                _record_applied(conn, mig0.migration_id)
            applied = [mig0.migration_id]
            already = set(applied)
    else:
        applied = []
        already = set(_read_applied(conn))

    applied_ids: List[str] = list(applied)

    # Re-read after bootstrap so we have authoritative applied set
    if _table_exists(conn, "_migrations"):
        already = set(_read_applied(conn))

    applied_count = 0
    skipped_count = 0

    for mig in migrations:
        if mig.migration_id in already:
            skipped_count += 1
            continue

        if dry_run:
            applied_ids.append(mig.migration_id)
            applied_count += 1
            continue

        sql = mig.path.read_text(encoding="utf-8")
        with conn:  # transaction per migration
            conn.executescript(sql)
            _record_applied(conn, mig.migration_id)

        applied_ids.append(mig.migration_id)
        applied_count += 1

    return applied_count, skipped_count, applied_ids


def run_migrations_from_env(*, dry_run: bool = False) -> int:
    """
    CLI entry: connects using env-derived DB path and applies migrations.
    Returns exit code.
    """
    db_path = _resolve_db_path()
    conn = _connect(db_path)
    try:
        applied, skipped, ids = apply_migrations(conn, dry_run=dry_run)
    finally:
        conn.close()

    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"[migrate] mode={mode} db={db_path}")
    print(f"[migrate] applied={applied} skipped={skipped}")
    if ids:
        print("[migrate] applied_ids:")
        for mid in ids:
            print(f"  - {mid}")
    return 0


if __name__ == "__main__":
    dry = os.environ.get("DRY_RUN", "").lower() in {"1", "true", "yes", "y"}
    raise SystemExit(run_migrations_from_env(dry_run=dry))
