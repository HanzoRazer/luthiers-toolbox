/**
 * exportBlockReason.ts
 * Bundle 10: Centralized "why export is blocked" logic
 *
 * Computes export eligibility and generates human-readable reason text.
 * Policy: Export allowed only when ALL items are GREEN and not rejected/error.
 */

export type RiskLevel = "GREEN" | "YELLOW" | "RED" | "UNKNOWN";

export type ExportEligibilityInput = {
  /** Risk decision: null means undecided */
  decision?: RiskLevel | null;
  /** Whether item was rejected */
  rejected?: boolean;
  /** Whether item has an error */
  hasError?: boolean;
};

export type ExportEligibilityResult = {
  /** Whether export is allowed */
  allowed: boolean;
  /** Human-readable tooltip explaining status */
  reason: string;
  /** Breakdown of blocked counts by category */
  blockedCounts: Record<string, number>;
};

/**
 * Compute export eligibility from a list of items.
 *
 * @param items - Array of items with decision/rejected/hasError fields
 * @returns Eligibility result with allowed flag, reason string, and counts
 */
export function computeExportEligibility(
  items: ExportEligibilityInput[]
): ExportEligibilityResult {
  const counts: Record<string, number> = {
    total: items.length,
    undecided: 0,
    red: 0,
    unknown: 0,
    rejected: 0,
    error: 0,
    nonGreen: 0,
  };

  for (const it of items) {
    if (it.hasError) counts.error++;

    if (it.rejected) counts.rejected++;

    const d = it.decision ?? null;
    if (d === null) counts.undecided++;
    else if (d === "RED") counts.red++;
    else if (d === "UNKNOWN") counts.unknown++;
    else if (d !== "GREEN") counts.nonGreen++;
  }

  // Policy: Export allowed only when every item is GREEN and not rejected/error
  const allowed =
    counts.total > 0 &&
    counts.undecided === 0 &&
    counts.red === 0 &&
    counts.unknown === 0 &&
    counts.nonGreen === 0 &&
    counts.rejected === 0 &&
    counts.error === 0;

  if (allowed) {
    return {
      allowed: true,
      reason: "Export is allowed: all selected items are GREEN.",
      blockedCounts: counts,
    };
  }

  // Build a human explanation (keep short + actionable)
  const parts: string[] = [
    "Export blocked: only GREEN, decided items can be exported.",
  ];

  if (counts.undecided) parts.push(`${counts.undecided} undecided`);
  if (counts.unknown) parts.push(`${counts.unknown} UNKNOWN`);
  if (counts.red) parts.push(`${counts.red} RED`);
  if (counts.nonGreen) parts.push(`${counts.nonGreen} non-GREEN`);
  if (counts.rejected) parts.push(`${counts.rejected} rejected`);
  if (counts.error) parts.push(`${counts.error} error`);

  parts.push("Fix: decide remaining items (GREEN) and clear rejects/errors.");

  return {
    allowed: false,
    reason: parts.join(" • "),
    blockedCounts: counts,
  };
}
