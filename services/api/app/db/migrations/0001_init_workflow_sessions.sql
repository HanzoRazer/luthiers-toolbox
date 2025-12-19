-- Migration: 0001_init_workflow_sessions
-- Description: Create workflow_sessions table for multi-step CNC workflow state
-- Date: December 19, 2025

CREATE TABLE IF NOT EXISTS workflow_sessions (
    -- Primary key
    session_id TEXT PRIMARY KEY,

    -- Session metadata
    created_at_utc TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at_utc TEXT NOT NULL DEFAULT (datetime('now')),

    -- Workflow state
    workflow_type TEXT NOT NULL,          -- 'fret_slotting', 'rosette', 'inlay', etc.
    current_step TEXT NOT NULL,           -- Current step in workflow
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'completed', 'cancelled', 'error'

    -- Context (JSON serialized)
    context_json TEXT,                    -- RmosContext as JSON

    -- Run linkage
    run_ids_json TEXT,                    -- Array of associated run_ids

    -- Machine/material context
    machine_id TEXT,
    material_id TEXT,
    tool_id TEXT,

    -- User tracking
    user_id TEXT,

    -- State data (JSON serialized)
    state_data_json TEXT,                 -- Workflow-specific state

    -- Error tracking
    error_message TEXT,
    error_details_json TEXT
);

-- Record migration
INSERT OR IGNORE INTO _migrations (migration_id, applied_at)
VALUES ('0001_init_workflow_sessions', datetime('now'));
