// packages/client/src/types/sawLab.ts
/**
 * Saw Lab Types
 * 
 * Types for saw operations and RMOS guard messages.
 * 
 * Wave 8 Implementation (Combined CAM Guard Wave)
 */

import type { RmosMessage, RmosSeverity } from "./fretSlots";

export type CutType = "rip" | "crosscut" | "miter" | "dado" | "rabbet";

export interface SawOperation {
  opId: string;
  cutType: CutType;
  bladeId: string;
  materialId: string;
  
  // Dimensions
  startMm: number;
  endMm: number;
  depthMm: number;
  widthMm: number;
  cutLengthMm: number;
  
  // Machine parameters
  bladeDiameterMm: number;
  toothCount: number;
  rpm: number;
  feedRateMmpm: number;
  
  // Guard output
  messages: RmosMessage[];
}

export interface SawPreviewRequest {
  operations: Array<{
    op_id: string;
    cut_type: CutType;
    blade_id: string;
    material_id: string;
    start_mm: number;
    end_mm: number;
    depth_mm: number;
    width_mm: number;
    cut_length_mm: number;
    blade_diameter_mm: number;
    tooth_count: number;
    rpm: number;
    feed_rate_mmpm: number;
  }>;
}

export interface SawPreviewResponse {
  operations: SawOperation[];
  messages: RmosMessage[];
  total_cut_length_mm: number;
  estimated_time_min: number;
}

export interface SawOperationRisk {
  opId: string;
  worstSeverity: RmosSeverity | null;
  messages: RmosMessage[];
}

// Board geometry for visualization
export interface SawBoardGeometry {
  widthMm: number;
  heightMm: number;
  thicknessMm?: number;
}

export interface CutGeometry {
  opId: string;
  cutType: CutType;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  depthMm: number;
  severity: RmosSeverity | null;
}
