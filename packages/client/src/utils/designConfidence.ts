/**
 * Design Confidence Utility
 *
 * Computes a confidence level from feasibility data.
 * Used by ConfidenceBadge and ConfidenceDetails components.
 */

export type ConfidenceLevel = "high" | "medium" | "low" | "none";

export type FeasibilityLike = {
  overall_score?: number;
  overallScore?: number;
  risk_bucket?: string;
  riskBucket?: string;
  warnings?: string[];
};

/**
 * Compute confidence level from feasibility data.
 * Returns "none" if no feasibility, otherwise "high", "medium", or "low".
 */
export function computeDesignConfidence(feasibility?: FeasibilityLike | null): ConfidenceLevel {
  if (!feasibility) return "none";

  const score = (feasibility.overall_score ?? feasibility.overallScore ?? 0) as number;
  const risk = String(feasibility.risk_bucket ?? feasibility.riskBucket ?? "UNKNOWN");
  const warnings = feasibility.warnings?.length ?? 0;

  // RED risk = always low
  if (risk === "RED") return "low";

  // High confidence: score >= 85, risk GREEN, <= 1 warning
  if (score >= 85 && risk === "GREEN" && warnings <= 1) return "high";

  // Medium confidence: score >= 65 and not RED
  if (score >= 65) return "medium";

  // Otherwise low
  return "low";
}

/**
 * Get color for confidence level (for badges/indicators).
 */
export function confidenceColor(level: ConfidenceLevel): string {
  switch (level) {
    case "high":
      return "#22c55e"; // green
    case "medium":
      return "#eab308"; // yellow
    case "low":
      return "#ef4444"; // red
    case "none":
    default:
      return "#9ca3af"; // gray
  }
}

/**
 * Get label for confidence level.
 */
export function confidenceLabel(level: ConfidenceLevel): string {
  switch (level) {
    case "high":
      return "High";
    case "medium":
      return "Medium";
    case "low":
      return "Low";
    case "none":
    default:
      return "None";
  }
}
