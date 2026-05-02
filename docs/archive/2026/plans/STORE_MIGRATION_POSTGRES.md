# Store Migration: SQLite → PostgreSQL

## Overview

The RMOS stores now support both SQLite and PostgreSQL backends. The backend is automatically selected based on the `DATABASE_URL` environment variable.

## Quick Start

### SQLite (Default - Development)

No configuration needed. SQLite is used by default:

```bash
# Default: uses services/api/data/rmos.db
python -m uvicorn app.main:app --reload
```

### PostgreSQL (Production)

Set `DATABASE_URL` to a PostgreSQL connection string:

```bash
# Railway, Heroku, Supabase, etc.
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
python -m uvicorn app.main:app
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Primary connection string | `postgresql://user:pass@host/db` |
| `RMOS_DB_PATH` | Legacy SQLite path (fallback) | `/data/rmos.db` |

**Priority**: `DATABASE_URL` > `RMOS_DB_PATH` > default SQLite path

## Backend Detection

```python
from app.core.rmos_db import get_rmos_db

db = get_rmos_db()
print(db.backend_type)  # "postgresql" or "sqlite"
```

## Affected Components

The following stores automatically use the configured backend:

| Store | Module |
|-------|--------|
| PatternStore | `app.stores.sqlite_pattern_store` |
| StripFamilyStore | `app.stores.sqlite_strip_family_store` |
| JobLogStore | `app.stores.sqlite_joblog_store` |
| WorkflowSessionStore | `app.workflow.sessions.store` |
| RMOSDatabase | `app.core.rmos_db` |

## Query Compatibility

The stores use `?` placeholders for parameters. These are automatically converted to `%s` for PostgreSQL:

```python
# Works with both SQLite and PostgreSQL
db.execute_query("SELECT * FROM patterns WHERE id = ?", (pattern_id,))
```

## Schema Differences

| SQLite | PostgreSQL |
|--------|------------|
| `TEXT` | `TEXT` |
| `REAL` | `DOUBLE PRECISION` |
| `DEFAULT CURRENT_TIMESTAMP` | `DEFAULT NOW()` |
| `INSERT OR IGNORE` | `ON CONFLICT DO NOTHING` |

## PostgreSQL Requirements

When using PostgreSQL, install `psycopg2-binary`:

```bash
pip install psycopg2-binary
```

## Testing Both Backends

```bash
# Test SQLite (default)
pytest tests/

# Test PostgreSQL
DATABASE_URL="postgresql://test:test@localhost:5432/test_db" pytest tests/
```

## Deployment Checklist

1. ✅ Set `DATABASE_URL` environment variable
2. ✅ Install `psycopg2-binary` in requirements
3. ✅ Run migrations (auto-created on first connection)
4. ✅ Verify with `db.backend_type`

## Rollback

To revert to SQLite-only:
1. Unset `DATABASE_URL`
2. The stores will automatically use SQLite

## Technical Notes

- **Connection pooling**: PostgreSQL uses RealDictCursor for dict-like row access
- **Transactions**: Both backends auto-commit on success, rollback on error
- **Schema migration**: Tables are created on first connection
- **Backup**: SQLite uses file copy, PostgreSQL should use `pg_dump`

## Files Modified

- `services/api/app/core/rmos_db.py` - Core database manager with dual-backend support
- `services/api/app/core/db_backend.py` - Backend abstraction layer (optional)
