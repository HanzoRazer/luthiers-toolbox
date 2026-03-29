from __future__ import annotations
import os
import logging
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///app/data/rmos.sqlite3"
)

# PostgreSQL URL format for when PG is provisioned:
# postgresql+asyncpg://user:password@host:5432/dbname

def create_engine(url: str | None = None):
    db_url = url or DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")

    if is_sqlite:
        logger.info("pg_pool: using SQLite (PostgreSQL not configured)")
        return create_async_engine(db_url, echo=False)

    logger.info("pg_pool: using PostgreSQL connection pool")
    return create_async_engine(
        db_url,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )

engine = create_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
