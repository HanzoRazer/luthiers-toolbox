from __future__ import annotations

import os
from contextlib import contextmanager
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
def db_session() -> Session:
    db = SessionLocal()