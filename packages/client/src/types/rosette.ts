/**
 * Rosette Types - Bundle 31.0
 *
 * Core types for rosette designs in Design-First Mode.
 */

export type RingParam = {
  ring_index: number;
  width_mm: number;
  pattern_type: string;
  tile_length_mm?: number | null;
};

export type RosetteParamSpec = {
  outer_diameter_mm: number;
  inner_diameter_mm: number;
  ring_params: RingParam[];
};
