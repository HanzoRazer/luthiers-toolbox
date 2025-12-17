"""
Alembic Migration Environment for Luthier's ToolBox

Database-agnostic: Works with SQLite (dev) and Postgres (prod).
Uses RMOS_DB_URL environment variable or falls back to SQLite.

Key features:
- Autogenerate from SQLAlchemy models
- Batch operations for SQLite compatibility
- Online/offline migration modes
"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the declarative Base from the app
from app.db.base import Base

# ============================================================
# MODEL IMPORTS - Add all models here for autogenerate to work
# ============================================================
# Each import registers the model with Base.metadata

# Workflow models (governance)
from app.workflow.db.models import WorkflowSessionRow  # noqa: F401

# Add future models here as they're created:
# from app.rmos.db.models import RunArtifactRow  # noqa: F401
# from app.tools.db.models import ToolRow  # noqa: F401

# ============================================================
# ALEMBIC CONFIG
# ============================================================

# Alembic Config object (from alembic.ini)
config = context.config

# Interpret the config file for Python logging (if present)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# ============================================================
# DATABASE URL RESOLUTION
# ============================================================


def get_database_url() -> str:
    """
    Get database URL from environment or config.

    Priority:
    1. RMOS_DB_URL environment variable
    2. sqlalchemy.url from alembic.ini

    Examples:
        SQLite:   sqlite:///data/rmos.sqlite3
        Postgres: postgresql://user:pass@localhost:5432/rmos
    """
    # Check environment first (allows runtime override)
    url = os.getenv("RMOS_DB_URL")
    if url:
        return url

    # Fall back to alembic.ini config
    return config.get_main_option("sqlalchemy.url", "sqlite:///data/rmos.sqlite3")


def is_sqlite(url: str) -> bool:
    """Check if URL is for SQLite database."""
    return url.startswith("sqlite")


# ============================================================
# OFFLINE MODE (generate SQL without DB connection)
# ============================================================


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This generates SQL scripts without connecting to the database.
    Useful for generating migration SQL for review or manual execution.

    Usage:
        alembic upgrade head --sql > migration.sql
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite needs batch mode for ALTER TABLE operations
        render_as_batch=is_sqlite(url),
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MODE (connect to DB and run migrations)
# ============================================================


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    This is the normal mode for `alembic upgrade head`.
    """
    url = get_database_url()

    # Build engine configuration
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    # SQLite-specific: disable pooling (not needed for file-based DB)
    if is_sqlite(url):
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            connect_args={"check_same_thread": False},
        )
    else:
        # Postgres/other: use standard pooling
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite batch mode for ALTER TABLE compatibility
            render_as_batch=is_sqlite(url),
            # Compare types for autogenerate (catches type changes)
            compare_type=True,
            # Compare server defaults for autogenerate
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# ENTRY POINT
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
