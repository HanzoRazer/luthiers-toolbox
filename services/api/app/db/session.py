"""
Database session management for Luthier's ToolBox.

Provides SQLite connection with file-backed storage.
Environment variable RMOS_DB_URL can override default path.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


# File-backed SQLite by default
DATABASE_URL = os.getenv("RMOS_DB_URL", "sqlite:///data/rmos.sqlite3")

# For SQLite: check_same_thread=False is needed when FastAPI runs with threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
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
    except Exception:
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
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
