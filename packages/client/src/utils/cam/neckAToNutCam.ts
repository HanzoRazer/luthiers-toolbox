/**
 * NECK-A to Nut Slot CAM Adapter
 *
 * CAM Dev Order 3B: One-way handoff from NECK-A setup workflow to CAM prefill.
 *
 * Rules:
 *   - Pure function, no side effects
 *   - No API calls
 *   - Does not mutate NECK-A store
 *   - Does not mutate CAM store
 *   - Returns partial prefill values only
 *
 * Direction: NECK-A → CAM (one-way only)
 */

import type { NutSlotPreviewRequest } from "@/sdk/endpoints/cam";

/**
 * NECK-A state subset needed for CAM prefill.
 * Mirrors relevant fields from instrumentGeometryStore.
 */
export interface NeckANutState {
  nutClearancesMm: number[];
  nutWidthMm: number;
}

/**
 * Conservative defaults when NECK-A does not provide values.
 */
const SAFE_DEFAULTS = {
  slot_depth_mm: 1.5,
  slot_length_mm: 3.0,
  stock_thickness_mm: 5.0,
  edge_offset_mm: 3.5,
  slot_width_mm: 0.56,
  tool_diameter_mm: 0.5,
  safe_z_mm: 5.0,
} as const;

/**
 * Build CAM prefill values from NECK-A setup workflow state.
 *
 * This is advisory only. CAM validation still runs after prefill.
 * Does not auto-preview or auto-export.
 *
 * @param neckAState - Current NECK-A nut workflow state
 * @returns Partial prefill for NutSlotPreviewRequest
 */
export function buildNutCamPrefillFromNeckA(
  neckAState: NeckANutState
): Partial<NutSlotPreviewRequest> {
  const numStrings = neckAState.nutClearancesMm.length;

  return {
    nut_width_mm: neckAState.nutWidthMm,
    num_strings: numStrings > 0 ? numStrings : 6,
    edge_offset_bass_mm: SAFE_DEFAULTS.edge_offset_mm,
    edge_offset_treble_mm: SAFE_DEFAULTS.edge_offset_mm,
    string_positions_x_mm: null,
    slot_depth_mm: SAFE_DEFAULTS.slot_depth_mm,
    slot_length_mm: SAFE_DEFAULTS.slot_length_mm,
    slot_width_mm: SAFE_DEFAULTS.slot_width_mm,
    stock_thickness_mm: SAFE_DEFAULTS.stock_thickness_mm,
    tool_diameter_mm: SAFE_DEFAULTS.tool_diameter_mm,
    safe_z_mm: SAFE_DEFAULTS.safe_z_mm,
  };
}
