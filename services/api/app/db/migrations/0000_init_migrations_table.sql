-- Migration: 0000_init_migrations_table
-- Description: Create migrations tracking table
-- Date: December 19, 2025
-- NOTE: This must be run first before any other migrations

CREATE TABLE IF NOT EXISTS _migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Record this migration
INSERT OR IGNORE INTO _migrations (migration_id, applied_at)
VALUES ('0000_init_migrations_table', datetime('now'));
