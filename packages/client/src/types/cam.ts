// src/types/cam.ts
/**
 * Shared CAM type definitions for backplot, pipeline, and simulation.
 */

export type BackplotPoint = [number, number];

export interface BackplotLoop {
  pts: BackplotPoint[];
}

export interface BackplotOverlay {
  type: string;
  x: number;
  y: number;
  radius?: number;
  severity?: "info" | "low" | "medium" | "high" | "critical";
  feed_pct?: number;
}

export interface BackplotMove {
  code: string;
  x?: number;
  y?: number;
  z?: number;
  f?: number;
  [key: string]: any;
}

export interface SimIssue {
  type: string;
  x: number;
  y: number;
  z?: number | null;
  severity: "info" | "low" | "medium" | "high" | "critical";
  note?: string | null;
  move_idx?: number | null;
}

export interface BackplotFocusPoint {
  x: number;
  y: number;
}

export interface AdaptiveStats {
  length_mm?: number;
  time_s?: number;
  time_jerk_s?: number;
  move_count?: number;
  area_mm2?: number;
  volume_mm3?: number;
  [key: string]: any;
}

export interface PipelinePreset {
  id: string;
  name: string;
  description?: string | null;
  units: "mm" | "inch";
  machine_id?: string | null;
  post_id?: string | null;
}

export interface PipelinePresetCreate {
  name: string;
  description?: string | null;
  units: "mm" | "inch";
  machine_id?: string | null;
  post_id?: string | null;
}
