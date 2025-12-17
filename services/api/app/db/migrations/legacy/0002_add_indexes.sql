-- 0002_add_indexes.sql
-- Adds simple indexes for common lookup patterns.
-- Part of Governance_Code_Bundle integration.

CREATE INDEX IF NOT EXISTS idx_workflow_sessions_state ON workflow_sessions(state);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_mode ON workflow_sessions(mode);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_tool_id ON workflow_sessions(tool_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_material_id ON workflow_sessions(material_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_machine_id ON workflow_sessions(machine_id);
