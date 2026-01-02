/**
 * rmosConfidence.ts
 * Bundle 08: Centralized Confidence Heuristic for RMOS Compare
 *
 * Deterministic confidence mapping from compare deltas.
 * Used by SnapshotComparePanel and other compare components.
 */

export type ConfLevel = "HIGH" | "MED" | "LOW";
export type ConfTrend = "UP" | "FLAT" | "DOWN" | "NONE";

/**
 * Input metrics for confidence computation.
 */
export interface ConfidenceMetrics {
  /** Count of rings where |Δ| >= 0.15mm */
  hotRings: number;
  /** Count of structural pattern differences */
  patternChanges: number;
  /** Warning delta (right - left) */
  warningDelta: number;
}

/**
 * Convert confidence level to numeric rank for comparison.
 * HIGH=3, MED=2, LOW=1
 */
export function confidenceToRank(level: ConfLevel): number {
  if (level === "HIGH") return 3;
  if (level === "MED") return 2;
  return 1; // LOW
}

/**
 * Compute confidence level from compare metrics.
 *
 * HIGH: No hot rings, no pattern changes, warnings not worse
 * MED: Minor diffs (≤2 hot rings, ≤1 pattern change, warnings +2 max)
 * LOW: Significant differences
 */
export function computeConfidence(metrics: ConfidenceMetrics): ConfLevel {
  const { hotRings, patternChanges, warningDelta } = metrics;

  // HIGH: No hot rings, no pattern changes, warnings not worse
  if (hotRings === 0 && patternChanges === 0 && warningDelta <= 0) {
    return "HIGH";
  }

  // MED: Minor deltas (≤2 hot rings, ≤1 pattern change, warnings +2 max)
  if (hotRings <= 2 && patternChanges <= 1 && warningDelta <= 2) {
    return "MED";
  }

  // LOW: Significant differences
  return "LOW";
}

/**
 * Compute confidence trend vs previous confidence level.
 *
 * UP: Confidence improved
 * FLAT: Confidence unchanged
 * DOWN: Confidence decreased
 * NONE: No previous confidence to compare
 */
export function computeConfidenceTrend(
  current: ConfLevel,
  prev: ConfLevel | null
): ConfTrend {
  if (!prev) return "NONE";

  const d = confidenceToRank(current) - confidenceToRank(prev);
  if (d > 0) return "UP";
  if (d < 0) return "DOWN";
  return "FLAT";
}

/**
 * Get multi-line tooltip text explaining confidence heuristic.
 */
export function getConfidenceTooltipText(): string {
  return [
    "Confidence indicates how reliable the comparison is at a glance.",
    "",
    "HIGH: No hot rings (|Δ| < 0.15mm), no pattern changes, warnings not worse.",
    "MED: Minor diffs (≤2 hot rings, ≤1 pattern change, warnings +2 max).",
    "LOW: Significant differences, or no compare result yet.",
    "",
    "Trend (vs previous compare):",
    "↑ Confidence improved",
    "→ Confidence unchanged",
    "↓ Confidence decreased",
  ].join("\n");
}
