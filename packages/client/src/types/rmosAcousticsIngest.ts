// packages/client/src/types/rmosAcousticsIngest.ts
/**
 * RMOS Acoustics Ingest Audit Types
 *
 * Types for browsing and retrieving ingest events (import-zip audit log).
 * Schema: acoustics_ingest_event_v1
 */

// ============================================================
// Error Payload
// ============================================================

export type IngestEventError = {
  code?: string;
  message?: string;
  detail?: unknown;
};

// ============================================================
// Validation Summary
// ============================================================

export type IngestEventValidation = {
  passed?: boolean;
  errors_count?: number;
  warnings_count?: number;
  reason?: string;
};

// ============================================================
// Event Summary (Browse List)
// ============================================================

export type IngestEventSummary = {
  event_id: string;
  created_at_utc: string;
  outcome: "accepted" | "rejected" | "quarantined";
  session_id?: string | null;
  batch_label?: string | null;
  uploader_filename?: string | null;
  zip_sha256?: string | null;
  zip_size_bytes?: number | null;
  http_status?: number | null;
  run_id?: string | null;
  error_code?: string | null;
  error_message?: string | null;
};

// ============================================================
// Event Detail
// ============================================================

export type IngestEventDetail = {
  schema_id: string;
  event_id: string;
  created_at_utc: string;
  outcome: "accepted" | "rejected" | "quarantined";
  session_id?: string | null;
  batch_label?: string | null;
  uploader_filename?: string | null;
  zip_sha256?: string | null;
  zip_size_bytes?: number | null;
  http_status?: number | null;
  error?: IngestEventError | null;
  validation?: IngestEventValidation | null;
  run_id?: string | null;
  bundle_id?: string | null;
  bundle_sha256?: string | null;
};

// ============================================================
// Browse Params & Response
// ============================================================

export type IngestEventsBrowseParams = {
  limit?: number;
  cursor?: string;
  outcome?: "accepted" | "rejected" | "quarantined";
};

export type IngestEventsBrowseResponse = {
  schema_version: string;
  count: number;
  limit: number;
  next_cursor: string | null;
  outcome_filter: string | null;
  entries: IngestEventSummary[];
};

// ============================================================
// Outcome Badge Helpers
// ============================================================

export type OutcomeStyle = {
  label: string;
  icon: string;
  color: "green" | "red" | "yellow";
  tooltip: string;
};

export const OUTCOME_STYLES: Record<string, OutcomeStyle> = {
  accepted: {
    label: "Accepted",
    icon: "check",
    color: "green",
    tooltip: "Pack imported successfully",
  },
  rejected: {
    label: "Rejected",
    icon: "x-circle",
    color: "red",
    tooltip: "Pack rejected (400/422)",
  },
  quarantined: {
    label: "Quarantined",
    icon: "alert-triangle",
    color: "yellow",
    tooltip: "Import failed (500) - may need investigation",
  },
};

export function getOutcomeStyle(outcome: string): OutcomeStyle {
  return (
    OUTCOME_STYLES[outcome.toLowerCase()] || {
      label: outcome,
      icon: "help-circle",
      color: "yellow",
      tooltip: "Unknown outcome",
    }
  );
}
