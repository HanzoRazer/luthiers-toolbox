/**
 * RMOS N10.2: Safety models for apprenticeship mode.
 * 
 * TypeScript interfaces matching backend schemas for safety policy system.
 */

export type SafetyMode = "unrestricted" | "apprentice" | "mentor_review";

export type ActionRiskLevel = "low" | "medium" | "high";
export type ActionDecision = "allow" | "require_override" | "deny";

export interface SafetyModeState {
  mode: SafetyMode;
  set_by?: string | null;
  set_at?: string | null;
}

export interface SafetyActionContext {
  action: string;
  lane?: string | null;
  fragility_score?: number | null;
  risk_grade?: string | null;
  preset_id?: string | null;
  job_id?: string | null;
}

export interface SafetyDecision {
  decision: ActionDecision;
  reason: string;
  mode: SafetyMode;
  risk_level: ActionRiskLevel;
  requires_override: boolean;
}

export interface OverrideToken {
  token: string;
  action: string;
  created_by?: string | null;
  created_at: string;
  expires_at?: string | null;
  used: boolean;
}

export interface EvaluateActionResponse {
  decision: SafetyDecision;
  valid_override_tokens: OverrideToken[];
}

/**
 * Helper to get CSS class for safety mode display.
 */
export function safeModeClass(mode: SafetyMode): string {
  switch (mode) {
    case "unrestricted":
      return "bg-green-50 border-green-200 text-green-900";
    case "apprentice":
      return "bg-yellow-50 border-yellow-300 text-yellow-900";
    case "mentor_review":
      return "bg-blue-50 border-blue-300 text-blue-900";
    default:
      return "bg-gray-50 border-gray-200 text-gray-800";
  }
}

/**
 * Helper to get human-readable label for safety mode.
 */
export function safeModeLabel(mode: SafetyMode): string {
  switch (mode) {
    case "unrestricted":
      return "Unrestricted";
    case "apprentice":
      return "Apprentice";
    case "mentor_review":
      return "Mentor Review";
    default:
      return mode;
  }
}

/**
 * Helper to get CSS class for risk level badge.
 */
export function riskLevelClass(level: ActionRiskLevel): string {
  switch (level) {
    case "low":
      return "bg-green-100 text-green-800 border border-green-300";
    case "medium":
      return "bg-yellow-100 text-yellow-800 border border-yellow-300";
    case "high":
      return "bg-red-100 text-red-800 border border-red-300";
    default:
      return "bg-gray-100 text-gray-800 border border-gray-300";
  }
}

/**
 * Helper to get CSS class for decision badge.
 */
export function decisionClass(decision: ActionDecision): string {
  switch (decision) {
    case "allow":
      return "bg-green-100 text-green-800 border border-green-300";
    case "require_override":
      return "bg-yellow-100 text-yellow-800 border border-yellow-300";
    case "deny":
      return "bg-red-100 text-red-800 border border-red-300";
    default:
      return "bg-gray-100 text-gray-800 border border-gray-300";
  }
}
