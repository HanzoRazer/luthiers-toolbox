/**
 * RmosRunViewer type definitions.
 */

// ============================================================================
// Explanation Types
// ============================================================================

export interface AssistantExplanation {
  summary?: string | null
  operator_notes?: string[] | null
  suggested_actions?: string[] | null
  disclaimer?: string | null
}

// ============================================================================
// Attachment Types
// ============================================================================

export interface RunAttachment {
  sha256?: string
  kind?: string
  filename?: string
  mime?: string
  size_bytes?: number
}

// ============================================================================
// Rule Types
// ============================================================================

export interface ExplainedRule {
  rule_id: string
  level: string
  summary: string
  operator_hint?: string
}
