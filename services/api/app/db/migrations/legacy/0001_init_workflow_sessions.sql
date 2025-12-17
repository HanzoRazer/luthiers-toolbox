-- 0001_init_workflow_sessions.sql
-- Creates workflow_sessions table (JSON-payload storage) used by DbWorkflowSessionStore.
-- Part of Governance_Code_Bundle integration.

CREATE TABLE IF NOT EXISTS workflow_sessions (
  session_id TEXT PRIMARY KEY,
  mode TEXT NOT NULL,
  state TEXT NOT NULL,
  session_json TEXT NOT NULL,
  created_utc TEXT NOT NULL DEFAULT (datetime('now')),
  updated_utc TEXT NOT NULL DEFAULT (datetime('now')),
  tool_id TEXT NULL,
  material_id TEXT NULL,
  machine_id TEXT NULL,
  candidate_attempt_count INTEGER NOT NULL DEFAULT 0
);

-- Trigger to update updated_utc automatically on update (SQLite)
CREATE TRIGGER IF NOT EXISTS workflow_sessions_updated_utc
AFTER UPDATE ON workflow_sessions
BEGIN
  UPDATE workflow_sessions
  SET updated_utc = datetime('now')
  WHERE session_id = NEW.session_id;
END;
