"""
DB Migrations Startup Hook

Runs database migrations at FastAPI startup when enabled via environment variable.

Env vars:
    RUN_MIGRATIONS_ON_STARTUP=true|false  (default false)
    MIGRATIONS_DRY_RUN=true|false         (default false)
    MIGRATIONS_FAIL_HARD=true|false       (default true)
    RMOS_DB_PATH=... (or DATABASE_URL / SQLITE_PATH)

Usage:
    In main.py:
        from app.db.startup import run_migrations_on_startup

        @app.on_event("startup")
        def _startup_db_migrations() -> None:
            run_migrations_on_startup()
"""
from __future__ import annotations

import logging
import os
import sqlite3

from app.db.migrate_sqlite import _resolve_db_path, _connect, apply_migrations

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def run_migrations_on_startup() -> None:
    """
    Runs DB migrations if RUN_MIGRATIONS_ON_STARTUP is enabled.

    Env:
      RUN_MIGRATIONS_ON_STARTUP=true|false  (default false)
      MIGRATIONS_DRY_RUN=true|false         (default false)
      MIGRATIONS_FAIL_HARD=true|false       (default true)
      RMOS_DB_PATH=... (or DATABASE_URL / SQLITE_PATH)
    """
    if not _env_bool("RUN_MIGRATIONS_ON_STARTUP", False):
        logger.info("DB migrations: skipped (RUN_MIGRATIONS_ON_STARTUP not enabled)")
        return

    dry_run = _env_bool("MIGRATIONS_DRY_RUN", False)
    fail_hard = _env_bool("MIGRATIONS_FAIL_HARD", True)

    db_path = _resolve_db_path()
    logger.info(
        "DB migrations: starting",
        extra={"db_path": str(db_path), "dry_run": dry_run}
    )

    conn = _connect(db_path)
    try:
        applied, skipped, applied_ids = apply_migrations(conn, dry_run=dry_run)
        logger.info(
            "DB migrations: complete",
            extra={
                "db_path": str(db_path),
                "dry_run": dry_run,
                "applied": applied,
                "skipped": skipped,
                "applied_ids": applied_ids,
            },
        )
    except (OSError, sqlite3.Error, ValueError) as e:  # WP-1: narrowed from except Exception
        logger.exception(
            "DB migrations: FAILED",
            extra={"db_path": str(db_path), "dry_run": dry_run}
        )
        if fail_hard:
            raise
        logger.warning(
            "DB migrations: continuing despite failure (MIGRATIONS_FAIL_HARD=false)"
        )
    finally:
        conn.close()
