-- Migration: 0002_add_indexes
-- Description: Add performance indexes for common queries
-- Date: December 19, 2025

-- Workflow sessions indexes
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_status
    ON workflow_sessions(status);

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_workflow_type
    ON workflow_sessions(workflow_type);

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_created_at
    ON workflow_sessions(created_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_user_id
    ON workflow_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_machine_id
    ON workflow_sessions(machine_id);

-- Composite index for common filter pattern
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_status_type
    ON workflow_sessions(status, workflow_type);

-- Record migration
INSERT OR IGNORE INTO _migrations (migration_id, applied_at)
VALUES ('0002_add_indexes', datetime('now'));
