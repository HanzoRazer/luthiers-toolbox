"""Tests for PostgreSQL connection pool with SQLite fallback."""

import pytest
from unittest.mock import patch, AsyncMock

from app.db.pg_pool import create_engine, get_db


class TestCreateEngine:
    """Tests for engine creation."""

    def test_sqlite_engine_created_when_no_pg_url(self):
        """SQLite engine is created when DATABASE_URL is not set to PostgreSQL."""
        # Default URL is SQLite
        engine = create_engine("sqlite+aiosqlite:///test.db")

        # Verify it's a SQLite engine (no pool class for SQLite)
        assert engine is not None
        assert "sqlite" in str(engine.url)

    def test_postgres_engine_uses_pool(self):
        """PostgreSQL engine uses connection pooling."""
        pytest.importorskip("asyncpg", reason="asyncpg not installed")

        pg_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        engine = create_engine(pg_url)

        assert engine is not None
        assert "postgresql" in str(engine.url)
        # Pool settings are applied
        assert engine.pool.size() == 0  # No connections yet


class TestGetDb:
    """Tests for database session dependency."""

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """get_db yields an AsyncSession."""
        # Create a generator
        gen = get_db()

        # Get the session
        session = await gen.__anext__()

        # Verify it's an AsyncSession
        from sqlalchemy.ext.asyncio import AsyncSession
        assert isinstance(session, AsyncSession)

        # Clean up
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    @pytest.mark.asyncio
    async def test_get_db_rolls_back_on_error(self):
        """get_db rolls back the session on exception."""
        from sqlalchemy.ext.asyncio import AsyncSession

        # Mock session with rollback tracking
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # Patch AsyncSessionLocal to return our mock
        with patch("app.db.pg_pool.AsyncSessionLocal") as mock_factory:
            # Create an async context manager that returns our mock
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_cm

            # Import fresh to use patched version
            from app.db.pg_pool import get_db as get_db_patched

            gen = get_db_patched()
            session = await gen.__anext__()

            # Simulate an error by throwing into the generator
            try:
                await gen.athrow(ValueError("Test error"))
            except ValueError:
                pass

            # Verify rollback was called
            mock_session.rollback.assert_called_once()
