/**
 * Ring Focus Utilities - Bundle 32.3.1
 *
 * Defensive helpers for extracting ring index from diagnostic objects,
 * supporting both snake_case (backend) and camelCase (frontend) shapes.
 */

export type RingDiagnosticLike = {
  ring_index?: number;
  ringIndex?: number;
  risk_bucket?: string;
  riskBucket?: string;
};

/**
 * Extract ring index from a diagnostic object.
 * Returns null if neither ring_index nor ringIndex is a number.
 */
export function getRingIndex(diag: RingDiagnosticLike): number | null {
  if (typeof diag.ring_index === "number") return diag.ring_index;
  if (typeof diag.ringIndex === "number") return diag.ringIndex;
  return null;
}

/**
 * Extract risk bucket from a diagnostic object.
 * Returns null if neither risk_bucket nor riskBucket is a string.
 */
export function getRiskBucket(diag: RingDiagnosticLike): string | null {
  if (typeof diag.risk_bucket === "string") return diag.risk_bucket;
  if (typeof diag.riskBucket === "string") return diag.riskBucket;
  return null;
}
