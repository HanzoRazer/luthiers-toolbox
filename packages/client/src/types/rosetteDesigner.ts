/**
 * Rosette Designer Types — Interactive Wheel Designer
 *
 * Mirrors services/api/app/art_studio/schemas/rosette_designer.py
 */

// ── Enums ──────────────────────────────────────────────────────

export type SymmetryMode = 'none' | 'rotational' | 'bilateral' | 'quadrant';

export type MfgSeverity = 'error' | 'warning' | 'info';

export type TileType =
  | 'solid' | 'abalone' | 'mop' | 'burl' | 'herringbone'
  | 'checker' | 'celtic' | 'diagonal' | 'dots'
  | 'stripes' | 'stripes2' | 'stripes3' | 'clear';

// ── Tile ───────────────────────────────────────────────────────

export interface TileDef {
  id: string;
  name: string;
  type: TileType;
  color?: string;
}

export interface TileCategory {
  label: string;
  tiles: string[];
}

// ── Ring ───────────────────────────────────────────────────────

export interface RingDef {
  label: string;
  r1: number;
  r2: number;
  color: string;
  dot_color: string;
  inch1: string;
  inch2: string;
  has_tabs: boolean;
  tab_inner_r: number;
  tab_outer_r: number;
  tab_ang_width: number;
  tab_fill_even: string;
  tab_fill_odd: string;
}

// ── Design state ──────────────────────────────────────────────

export interface RosetteDesignState {
  version: number;
  design_name: string;
  num_segs: number;
  sym_mode: SymmetryMode;
  grid: Record<string, string>;
  ring_active: boolean[];
  show_tabs: boolean;
  show_annotations: boolean;
}

// ── Place tile ────────────────────────────────────────────────

export interface PlaceTileRequest {
  ring_idx: number;
  seg_idx: number;
  tile_id: string;
  num_segs: number;
  sym_mode: SymmetryMode;
  grid: Record<string, string>;
  ring_active: boolean[];
}

export interface PlaceTileResponse {
  grid: Record<string, string>;
  affected_cells: string[];
}

// ── Symmetry cells ────────────────────────────────────────────

export interface SymmetryCellsRequest {
  ring_idx: number;
  seg_idx: number;
  sym_mode: SymmetryMode;
  num_segs: number;
}

export interface SymmetryCellsResponse {
  cells: number[][];
}

// ── Cell info ─────────────────────────────────────────────────

export interface CellInfoResponse {
  zone: string;
  seg: string;
  angle: string;
  depth_inches: string;
  arc_len_inches: string;
  r1_inches: string;
  r2_inches: string;
  tile_name: string | null;
  tile_id: string | null;
}

// ── BOM ───────────────────────────────────────────────────────

export interface BomPerRingDetail {
  ring_label: string;
  count: number;
  arc_total_inches: number;
  inner_arc_inches: number;
  outer_arc_inches: number;
  depth_inches: number;
  mid_arc_inches: number;
}

export interface BomMaterialEntry {
  tile_id: string;
  tile_name: string;
  tile_color_hex: string;
  pieces: number;
  arc_total_inches: number;
  per_ring: BomPerRingDetail[];
  procurement_strips: string[];
}

export interface BomRingEntry {
  label: string;
  dot_color: string;
  depth_inches: number;
  r1_inches: string;
  r2_inches: string;
  filled: number;
  total_cells: number;
  material_names: string[];
  arc_total_inches: number;
}

export interface BomResponse {
  filled_cells: number;
  total_cells: number;
  material_count: number;
  total_pieces: number;
  total_arc_inches: number;
  fill_percent: number;
  materials: BomMaterialEntry[];
  rings: BomRingEntry[];
}

// ── MFG ───────────────────────────────────────────────────────

export interface MfgFlagCellRef {
  ri: number;
  si: number;
  key: string;
  label: string;
  val: number;
}

export interface MfgFlag {
  id: string;
  sev: MfgSeverity;
  title: string;
  desc: string;
  cells: MfgFlagCellRef[];
  fix?: string;
  has_auto_fix: boolean;
}

export interface MfgCheckResponse {
  score: number;
  score_class: string;
  error_count: number;
  warning_count: number;
  info_count: number;
  passing_count: number;
  flags: MfgFlag[];
}

// ── Recipes ───────────────────────────────────────────────────

export interface RecipePreset {
  id: string;
  name: string;
  desc: string;
  tags: string[];
  num_segs: number;
  sym_mode: SymmetryMode;
  ring_active: boolean[];
  grid: Record<string, string>;
}

// ── Preview / Export ──────────────────────────────────────────

export interface PreviewRequest {
  num_segs: number;
  grid: Record<string, string>;
  ring_active: boolean[];
  show_tabs: boolean;
  show_annotations: boolean;
  width: number;
  height: number;
}

export interface PreviewResponse {
  svg: string;
}

// ── Catalog ───────────────────────────────────────────────────

export interface TileCatalogResponse {
  tile_map: Record<string, TileDef>;
  categories: TileCategory[];
  ring_defs: RingDef[];
  seg_options: number[];
}
