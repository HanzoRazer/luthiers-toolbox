# Database Migrations

Alembic migrations for Luthier's ToolBox.

## Quick Start

```bash
cd services/api

# Generate a new migration from model changes
alembic revision --autogenerate -m "describe your changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Database Configuration

Uses `RMOS_DB_URL` environment variable:

| Environment | URL Example |
|-------------|-------------|
| Development | `sqlite:///data/rmos.sqlite3` (default) |
| Production  | `postgresql://user:pass@host:5432/rmos` |

## Adding New Models

1. Create your model in `app/<module>/db/models.py`
2. Import it in `app/db/migrations/env.py` (MODEL IMPORTS section)
3. Run: `alembic revision --autogenerate -m "add <model>"`
4. Review the generated migration in `versions/`
5. Apply: `alembic upgrade head`

## SQLite Compatibility

Migrations use batch mode for SQLite compatibility. This means:
- ALTER TABLE operations are supported
- Same migrations work on SQLite and Postgres
- No manual SQL needed for column changes

## Files

- `env.py` - Migration environment (imports models, configures DB)
- `script.py.mako` - Template for generated migrations
- `versions/` - Migration scripts (chronological)
