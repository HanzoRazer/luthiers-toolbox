import { computeDesignConfidence, type FeasibilityLike, type ConfidenceLevel } from "@/utils/designConfidence";

export type ConfidenceReasonCode =
  | "NO_FEASIBILITY"
  | "RISK_RED"
  | "LOW_SCORE"
  | "WARNINGS_PRESENT"
  | "RISK_YELLOW"
  | "STRONG_SCORE_LOW_WARNINGS"
  | "UNKNOWN";

export type ConfidenceReason = {
  level: ConfidenceLevel;
  code: ConfidenceReasonCode;
  short: string;  // one-line
  detail: string; // tooltip / expanded
};

function scoreOf(f?: FeasibilityLike | null): number {
  return (f?.overall_score ?? f?.overallScore ?? 0) as number;
}

function riskOf(f?: FeasibilityLike | null): string {
  return String(f?.risk_bucket ?? f?.riskBucket ?? "UNKNOWN");
}

function warnCountOf(f?: FeasibilityLike | null): number {
  return f?.warnings?.length ?? 0;
}

/**
 * Convert feasibility into a small, explainable "why" summary.
 * This is intentionally deterministic + shallow (no AI).
 */
export function getConfidenceReason(feasibility?: FeasibilityLike | null): ConfidenceReason {
  const level = computeDesignConfidence(feasibility);

  if (!feasibility) {
    return {
      level,
      code: "NO_FEASIBILITY",
      short: "No feasibility yet",
      detail: "Feasibility hasn't been computed for this snapshot/design.",
    };
  }

  const score = scoreOf(feasibility);
  const risk = riskOf(feasibility);
  const warnings = warnCountOf(feasibility);

  if (risk === "RED") {
    return {
      level,
      code: "RISK_RED",
      short: "RED risk",
      detail: "Manufacturing risk is RED. Resolve warnings before continuing.",
    };
  }

  if (score < 65) {
    return {
      level,
      code: "LOW_SCORE",
      short: `Low score (${Math.round(score)})`,
      detail: "Feasibility score is below the recommended threshold.",
    };
  }

  if (risk === "YELLOW") {
    // If we're yellow but not low score, it's usually warnings or risk flags
    return {
      level,
      code: "RISK_YELLOW",
      short: "YELLOW risk",
      detail: "Risk is YELLOW. The design is workable but may need refinement.",
    };
  }

  if (score >= 85 && warnings <= 1) {
    return {
      level,
      code: "STRONG_SCORE_LOW_WARNINGS",
      short: `Strong (${Math.round(score)})`,
      detail: "High feasibility score with minimal warnings.",
    };
  }

  if (warnings > 1) {
    return {
      level,
      code: "WARNINGS_PRESENT",
      short: `${warnings} warnings`,
      detail: "Warnings are present. Reduce warnings to raise confidence.",
    };
  }

  return {
    level,
    code: "UNKNOWN",
    short: "OK",
    detail: "Feasibility looks acceptable, but not strongly high-confidence yet.",
  };
}

/**
 * Compact "what changed?" between two feasibility points.
 * Used for "Confidence dropped/improved" peek.
 */
export function diffFeasibility(a?: FeasibilityLike | null, b?: FeasibilityLike | null) {
  const aScore = scoreOf(a);
  const bScore = scoreOf(b);
  const aRisk = riskOf(a);
  const bRisk = riskOf(b);
  const aWarn = warnCountOf(a);
  const bWarn = warnCountOf(b);

  return {
    scoreDelta: (bScore - aScore),
    aScore,
    bScore,
    aRisk,
    bRisk,
    aWarn,
    bWarn,
    warnDelta: (bWarn - aWarn),
    riskChanged: aRisk !== bRisk,
  };
}
