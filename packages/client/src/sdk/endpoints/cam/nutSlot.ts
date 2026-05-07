/**
 * Nut Slot CAM Preview SDK
 *
 * Typed helper for nut slot toolpath preview:
 *   POST /api/cam/nut-slot/preview
 *
 * Returns toolpath JSON for visualization (no G-code, no export).
 * CAM Dev Order 2A: Frontend preview only.
 */

import { apiFetch } from "@/sdk/core/apiFetch";

// ---------------------------------------------------------------------------
// Gate Type
// ---------------------------------------------------------------------------

export type CamGate = "green" | "yellow" | "red";

// ---------------------------------------------------------------------------
// Request
// ---------------------------------------------------------------------------

export interface NutSlotPreviewRequest {
  nut_width_mm: number;
  num_strings: number;
  edge_offset_bass_mm: number;
  edge_offset_treble_mm: number;
  string_positions_x_mm?: number[] | null;
  slot_length_mm: number;
  slot_depth_mm: number;
  slot_width_mm: number;
  stock_thickness_mm: number;
  tool_diameter_mm: number;
  safe_z_mm?: number;
}

// ---------------------------------------------------------------------------
// Response Types
// ---------------------------------------------------------------------------

export interface ToolpathMove {
  type: "rapid" | "plunge" | "linear" | "retract";
  x: number;
  y: number;
  z: number;
}

export interface SlotToolpath {
  slot_index: number;
  string_number: number;
  x_mm: number;
  slot_width_mm: number;
  slot_depth_mm: number;
  moves: ToolpathMove[];
}

export interface CoordinateSystem {
  origin: string;
  z_zero: string;
  x_axis: string;
  y_axis: string;
}

export interface ToolMetadata {
  diameter_mm: number;
}

export interface PreviewStatistics {
  total_slots: number;
  max_depth_mm: number;
  estimated_time_s: number | null;
}

export interface NutSlotPreviewResponse {
  operation: string;
  status: string;
  gate: CamGate;
  units: string;
  coordinate_system: CoordinateSystem;
  machine_profile: string;
  tool: ToolMetadata;
  toolpaths: SlotToolpath[];
  warnings: string[];
  errors: string[];
  statistics: PreviewStatistics;
}

// ---------------------------------------------------------------------------
// API Function
// ---------------------------------------------------------------------------

/**
 * Generate nut slot CAM preview.
 *
 * Returns toolpath JSON for visualization.
 * Gate indicates safety status: green (safe), yellow (warnings), red (blocked).
 */
export async function previewNutSlots(
  request: NutSlotPreviewRequest
): Promise<NutSlotPreviewResponse> {
  return apiFetch<NutSlotPreviewResponse>("/api/cam/nut-slot/preview", {
    method: "POST",
    body: JSON.stringify(request),
    headers: { "Content-Type": "application/json" },
  });
}
