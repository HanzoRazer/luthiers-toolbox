/**
 * Feasibility Rule Registry (Client-side)
 *
 * Phase 3.3: Static mirror of backend rule_registry.py
 * Deterministic: no API call required for explainability.
 *
 * Rules are lookup-only. Logic lives in backend.
 */

export type FeasibilityRuleLevel = "RED" | "YELLOW"

export interface FeasibilityRuleMeta {
  rule_id: string
  level: FeasibilityRuleLevel
  summary: string
  description?: string
  operator_hint?: string
}

/**
 * Client-side mirror of backend FEASIBILITY_RULES.
 * Keep in sync with: services/api/app/rmos/feasibility/rule_registry.py
 */
export const FEASIBILITY_RULES: Record<string, FeasibilityRuleMeta> = {
  // RED — blocking rules
  F001: {
    rule_id: "F001",
    level: "RED",
    summary: "Invalid tool diameter",
    description: "tool_d must be greater than 0",
    operator_hint: "Check tool definition; diameter must be positive",
  },
  F002: {
    rule_id: "F002",
    level: "RED",
    summary: "Invalid stepover ratio",
    description: "Stepover must be between 0 and 1 (exclusive)",
    operator_hint: "Reduce stepover to less than 100% of tool diameter",
  },
  F003: {
    rule_id: "F003",
    level: "RED",
    summary: "Invalid stepdown",
    description: "Stepdown must be greater than 0",
    operator_hint: "Set a positive stepdown value",
  },
  F004: {
    rule_id: "F004",
    level: "RED",
    summary: "Invalid cutting depth",
    description: "Target depth must be negative (below surface)",
    operator_hint: "Verify z_rough is negative for material removal",
  },
  F005: {
    rule_id: "F005",
    level: "RED",
    summary: "Invalid safe Z height",
    description: "Safe Z must be greater than 0",
    operator_hint: "Set safe_z to a positive clearance height",
  },
  F006: {
    rule_id: "F006",
    level: "RED",
    summary: "No closed geometry",
    description: "At least one closed loop is required for pocketing",
    operator_hint: "Ensure DXF contains closed polylines or regions",
  },
  F007: {
    rule_id: "F007",
    level: "RED",
    summary: "No closed loops detected",
    description: "Geometry parser found no valid closed loops",
    operator_hint: "Check DXF layer and ensure geometry is closed",
  },

  // YELLOW — warning rules
  F010: {
    rule_id: "F010",
    level: "YELLOW",
    summary: "Tool may be too large",
    description: "Tool diameter exceeds smallest feature dimension",
    operator_hint: "Consider smaller tool or verify geometry tolerances",
  },
  F011: {
    rule_id: "F011",
    level: "YELLOW",
    summary: "Plunge feed too high",
    description: "Plunge feed rate exceeds lateral feed rate",
    operator_hint: "Reduce feed_z or increase feed_xy",
  },
  F012: {
    rule_id: "F012",
    level: "YELLOW",
    summary: "Large stepdown",
    description: "Stepdown exceeds 50% of tool diameter",
    operator_hint: "Consider reducing stepdown for tool life",
  },
  F013: {
    rule_id: "F013",
    level: "YELLOW",
    summary: "High loop count",
    description: "Geometry contains many loops which may slow processing",
    operator_hint: "Simplify geometry if possible or expect longer processing",
  },
}

/**
 * Look up rule metadata by ID.
 * Returns unknown fallback if rule not found.
 */
export function explainRule(ruleId: string): FeasibilityRuleMeta {
  const rid = String(ruleId || "").trim().toUpperCase()
  return (
    FEASIBILITY_RULES[rid] ?? {
      rule_id: rid || "UNKNOWN",
      level: "YELLOW",
      summary: "Unknown feasibility rule",
      description: "Rule ID not found in registry",
      operator_hint: "Contact support if this persists",
    }
  )
}

/**
 * Look up multiple rules at once.
 */
export function explainRules(ruleIds: string[]): FeasibilityRuleMeta[] {
  return (ruleIds || []).map((rid) => explainRule(rid))
}

/**
 * Get all known rule IDs.
 */
export function getAllRuleIds(): string[] {
  return Object.keys(FEASIBILITY_RULES)
}
