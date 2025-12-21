// packages/client/src/types/fretSlots.ts
/**
 * Shared types for Fret Slots CAM + RMOS Messages
 * 
 * Wave 6 Implementation (Fret Slots UI Overlay Bundle)
 */

export type RmosSeverity = "info" | "warning" | "error" | "fatal";

export interface RmosMessage {
  code: string;              // e.g. "CHIPLOAD_HIGH", "SLOT_DEPTH_EXCEEDS_TOOL"
  severity: RmosSeverity;
  message: string;
  context: Record<string, unknown>;
  hint?: string | null;
}

export interface FretSlot {
  fret: number;
  stringIndex: number;
  positionMm: number;
  widthMm: number;
  depthMm: number;
  angleRad?: number | null;
  isPerpendicular?: boolean;
}

export interface FretSlotsPreviewRequest {
  model_id: string;
  fret_count: number;
  slot_width_mm: number;
  slot_depth_mm: number;
  bit_diameter_mm: number;
  mode?: "standard" | "fan_fret";
  perpendicular_fret?: number | null;
  bass_scale_mm?: number;
  treble_scale_mm?: number;
}

export interface FretSlotsPreviewResponse {
  model_id: string;
  fret_count: number;
  slots: FretSlot[];
  messages: RmosMessage[];
  statistics?: {
    total_cutting_length_mm: number;
    estimated_time_min: number;
  };
}

export interface FretRiskSummary {
  fret: number;
  worstSeverity: RmosSeverity | null;
  messages: RmosMessage[];
}

export interface FretStringRisk {
  fret: number;
  stringIndex: number;
  severity: RmosSeverity | null;
  messages: RmosMessage[];
}

// Color mapping for severity levels
export const SEVERITY_COLORS: Record<RmosSeverity, string> = {
  info: "#3b82f6",      // blue-500
  warning: "#f59e0b",   // amber-500
  error: "#ef4444",     // red-500
  fatal: "#7f1d1d",     // red-900
};

export const SEVERITY_BG_COLORS: Record<RmosSeverity, string> = {
  info: "rgba(59, 130, 246, 0.2)",
  warning: "rgba(245, 158, 11, 0.3)",
  error: "rgba(239, 68, 68, 0.4)",
  fatal: "rgba(127, 29, 29, 0.5)",
};
