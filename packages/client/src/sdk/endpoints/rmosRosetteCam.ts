/**
 * RMOS Rosette CAM SDK Endpoints
 *
 * Typed SDK helpers for rosette CNC/CAM operations.
 * Endpoints are at /api/rmos/rosette/* (delegating to real CAM engines).
 *
 * This completes the rosette wheel → registry integration by exposing
 * the manufacturing-level endpoints alongside the design-level endpoints
 * in artRosetteWheel.ts.
 */

import { apiFetch } from "@/sdk/core/apiFetch";
import type {
  SegmentRingRequest,
  SegmentRingResponse,
  GenerateSlicesRequest,
  GenerateSlicesResponse,
  PreviewRosetteRequest,
  PreviewRosetteResponse,
  ExportCncRequest,
  ExportCncResponse,
  CncHistoryResponse,
  CncJobDetailResponse,
} from "@/types/rmosRosetteCam";

const BASE = "/api/rmos/rosette";

// ── Geometry Generation ─────────────────────────────────────────

/**
 * Generate rosette segment ring geometry.
 *
 * Computes tile segmentation with real trapezoid geometry for a single ring.
 * Used to preview ring breakdown before manufacturing.
 */
export async function segmentRing(
  req: SegmentRingRequest
): Promise<SegmentRingResponse> {
  return apiFetch(`${BASE}/segment-ring`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Generate rosette slices for manufacturing.
 *
 * Computes slice geometry from ring configuration for CNC cutting.
 */
export async function generateSlices(
  req: GenerateSlicesRequest
): Promise<GenerateSlicesResponse> {
  return apiFetch(`${BASE}/generate-slices`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Generate rosette preview data.
 *
 * Computes full preview including segmentation and slices for multiple rings.
 */
export async function previewRosette(
  req: PreviewRosetteRequest
): Promise<PreviewRosetteResponse> {
  return apiFetch(`${BASE}/preview`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ── CNC Export ──────────────────────────────────────────────────

/**
 * Export rosette to CNC-ready G-code format.
 *
 * Generates complete G-code for cutting a rosette ring on CNC.
 * Includes safety validation, runtime estimation, and machine-specific
 * post-processing (GRBL or FANUC).
 */
export async function exportCnc(
  req: ExportCncRequest
): Promise<ExportCncResponse> {
  return apiFetch(`${BASE}/export-cnc`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ── Job History ─────────────────────────────────────────────────

/**
 * Get CNC job history for rosettes.
 *
 * Returns recent rosette CNC jobs with optional filtering.
 */
export async function getCncHistory(
  limit: number = 50,
  jobType?: string
): Promise<CncHistoryResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  if (jobType) params.set("job_type", jobType);

  return apiFetch(`${BASE}/cnc-history?${params.toString()}`, {
    method: "GET",
  });
}

/**
 * Get CNC job details by ID.
 *
 * Returns full details for a specific rosette CNC job.
 */
export async function getCncJob(jobId: string): Promise<CncJobDetailResponse> {
  return apiFetch(`${BASE}/cnc-job/${encodeURIComponent(jobId)}`, {
    method: "GET",
  });
}
