"""
Database session management for The Production Shop.

Supports:
- SQLite: file-backed storage (default for dev)
- PostgreSQL: production database with Supabase

Environment variables:
- DATABASE_URL: PostgreSQL connection string (takes precedence)
- RMOS_DB_URL: SQLite fallback for local development
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool


# Database URL priority: DATABASE_URL (production) > RMOS_DB_URL (dev) > default SQLite
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("RMOS_DB_URL", "sqlite:///data/rmos.sqlite3")

# Determine database type
_is_postgres = DATABASE_URL.startswith("postgresql")
_is_sqlite = DATABASE_URL.startswith("sqlite")

# Connection pooling configuration
# - PostgreSQL with pgbouncer: use NullPool (pgbouncer manages pooling)
# - PostgreSQL without pgbouncer: use QueuePool
# - SQLite: no pooling needed
_use_pgbouncer = os.getenv("USE_PGBOUNCER", "").lower() in ("1", "true", "yes")

if _is_postgres:
    # PostgreSQL engine configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool if _use_pgbouncer else QueuePool,
        pool_size=5 if not _use_pgbouncer else None,
        max_overflow=10 if not _use_pgbouncer else None,
        pool_pre_ping=True,  # Verify connections before use
        future=True,
    )
elif _is_sqlite:
    # SQLite engine configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # FastAPI runs with threads
        future=True,
    )
else:
    # Generic fallback (MySQL, etc.)
    engine = create_engine(
        DATABASE_URL,
        future=True,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Usage:
        with db_session() as db:
            db.query(Model).filter(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:  # WP-1: keep broad — SQLAlchemy transaction guard must catch all to rollback  # AUDITED 2026-03: re-raises after rollback
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:  # WP-1: keep broad — SQLAlchemy transaction guard must catch all to rollback  # AUDITED 2026-03: re-raises after rollback
        db.rollback()
        raise
    finally:
        db.close()
