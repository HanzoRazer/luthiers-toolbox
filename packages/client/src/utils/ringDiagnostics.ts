/**
 * Ring Diagnostics Utility - Bundle 31.0.7
 *
 * UI-only fallback for deriving per-ring hints from global feasibility.
 * This does NOT perform physics - only maps global warnings to ring hints.
 */

import type { RiskBucket, RingFeasibilityDiagnostic, RosetteFeasibilitySummary } from "../types/feasibility";
import type { RosetteParamSpec } from "../types/rosette";

export function deriveRingHintsFromSummary(
  spec: RosetteParamSpec,
  summary: RosetteFeasibilitySummary | null
): RingFeasibilityDiagnostic[] {
  const rings = spec.ring_params || [];
  const baseRisk: RiskBucket = summary?.risk_bucket || "YELLOW";
  const warnings = summary?.warnings || [];

  // Find narrowest ring for heuristics
  const widths = rings.map((r) => Number(r.width_mm || 0));
  const minW = widths.length ? Math.min(...widths) : 0;

  // Parse warning keywords
  const kw = warnings.join(" | ").toLowerCase();
  const heat = kw.includes("heat");
  const defl = kw.includes("deflection");
  const chip = kw.includes("chipload");
  const rim = kw.includes("rim");

  return rings.map((r, idx) => {
    const w = Number(r.width_mm || 0);
    const pattern = String(r.pattern_type || "SOLID");
    const narrow = minW > 0 && w <= minW * 1.15;

    let risk: RiskBucket = "GREEN";
    if (!summary) risk = "YELLOW";
    else if (baseRisk === "GREEN") risk = narrow ? "YELLOW" : "GREEN";
    else if (baseRisk === "YELLOW") risk = narrow ? "YELLOW" : "YELLOW";
    else risk = narrow ? "RED" : "YELLOW";

    // If there are "hard" warnings, bump the narrow rings
    if (baseRisk === "RED" && (heat || defl || chip || rim) && narrow) risk = "RED";

    const ringWarnings: string[] = [];
    if (narrow) ringWarnings.push("Narrow ring (hint): consider increasing width.");
    if (heat) ringWarnings.push("Global heat warning (hint): reduce RPM or increase feed.");
    if (defl) ringWarnings.push("Global deflection warning (hint): reduce engagement/stickout.");
    if (chip) ringWarnings.push("Global chipload warning (hint): adjust feed/RPM.");
    if (rim) ringWarnings.push("Global rim-speed warning (hint): reduce RPM or tool diameter.");

    return {
      ring_index: idx,
      label: `Ring ${idx} - ${pattern} - ${w.toFixed(2)}mm`,
      risk_bucket: risk,
      score: null,
      warnings: ringWarnings,
      metrics: { width_mm: w, pattern_type: pattern, derived: true },
    };
  });
}
