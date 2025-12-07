// packages/client/src/api/art-studio.ts
/**
 * Typed client for Art Studio API endpoints
 *
 * Provides TypeScript interfaces and functions for:
 * - Rosette channel calculation and DXF export
 * - Fretboard inlay pattern generation
 * - Bracing section calculations
 */

const base = (import.meta as any).env?.VITE_API_BASE || "/api";

// --------------------------------------------------------------------- //
// Rosette Types & API
// --------------------------------------------------------------------- //

export interface PurflingBand {
  material: string;
  width_mm: number;
}

export interface RosettePreviewRequest {
  soundhole_diameter_mm: number;
  central_band_mm: number;
  inner_purfling: PurflingBand[];
  outer_purfling: PurflingBand[];
  channel_depth_mm: number;
}

export interface RosetteStackItem {
  label: string;
  width_mm: number;
  inner_radius_mm: number;
  outer_radius_mm: number;
}

export interface RosetteCalcResult {
  soundhole_radius_mm: number;
  channel_inner_radius_mm: number;
  channel_outer_radius_mm: number;
  channel_width_mm: number;
  channel_depth_mm: number;
  stack: RosetteStackItem[];
}

export interface RosettePreviewResponse {
  result: RosetteCalcResult;
  preview_svg: string | null;
}

export interface RosetteDXFRequest extends RosettePreviewRequest {
  center_x_mm: number;
  center_y_mm: number;
  include_purfling_rings: boolean;
}

export interface RosettePresetInfo {
  name: string;
  description: string;
  soundhole_diameter_mm: number;
  central_band_mm: number;
  channel_depth_mm: number;
}

export async function previewRosette(
  req: RosettePreviewRequest
): Promise<RosettePreviewResponse> {
  const res = await fetch(`${base}/art-studio/rosette/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportRosetteDXF(req: RosetteDXFRequest): Promise<Blob> {
  const res = await fetch(`${base}/art-studio/rosette/export-dxf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}

export async function listRosettePresets(): Promise<RosettePresetInfo[]> {
  const res = await fetch(`${base}/art-studio/rosette/presets`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getRosettePreset(
  name: string
): Promise<RosettePreviewRequest> {
  const res = await fetch(
    `${base}/art-studio/rosette/presets/${encodeURIComponent(name)}`
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --------------------------------------------------------------------- //
// Inlay Types & API
// --------------------------------------------------------------------- //

export type InlayPatternType =
  | "dot"
  | "diamond"
  | "block"
  | "trapezoid"
  | "custom";

export interface InlayPreviewRequest {
  pattern_type: InlayPatternType;
  fret_positions: number[];
  scale_length_mm: number;
  fretboard_width_nut_mm: number;
  fretboard_width_body_mm: number;
  num_frets: number;
  inlay_size_mm: number;
  double_at_12: boolean;
  double_spacing_mm: number;
}

export interface InlayShape {
  fret: number;
  center_x_mm: number;
  center_y_mm: number;
  pattern_type: InlayPatternType;
  size_mm: number;
  vertices: number[][];
  is_double: boolean;
}

export interface InlayCalcResult {
  scale_length_mm: number;
  num_frets: number;
  inlays: InlayShape[];
  fret_positions_mm: number[];
}

export interface InlayPreviewResponse {
  result: InlayCalcResult;
  preview_svg: string | null;
}

export interface InlayDXFRequest extends InlayPreviewRequest {
  dxf_version: string;
  layer_prefix: string;
}

export interface InlayPresetInfo {
  name: string;
  description: string;
  pattern_type: InlayPatternType;
  fret_positions: number[];
}

export interface FretPositionResponse {
  scale_length_mm: number;
  positions: Array<{
    fret: number;
    position_mm: number;
    distance_from_previous_mm: number;
  }>;
}

export async function previewInlay(
  req: InlayPreviewRequest
): Promise<InlayPreviewResponse> {
  const res = await fetch(`${base}/art-studio/inlay/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportInlayDXF(req: InlayDXFRequest): Promise<Blob> {
  const res = await fetch(`${base}/art-studio/inlay/export-dxf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}

export async function listInlayPresets(): Promise<InlayPresetInfo[]> {
  const res = await fetch(`${base}/art-studio/inlay/presets`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getInlayPreset(
  name: string
): Promise<InlayPreviewRequest> {
  const res = await fetch(
    `${base}/art-studio/inlay/presets/${encodeURIComponent(name)}`
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getFretPositions(
  scaleLengthMm: number,
  numFrets: number = 24
): Promise<FretPositionResponse> {
  const params = new URLSearchParams({
    scale_length_mm: scaleLengthMm.toString(),
    num_frets: numFrets.toString(),
  });
  const res = await fetch(`${base}/art-studio/inlay/fret-positions?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --------------------------------------------------------------------- //
// Bracing Types & API
// --------------------------------------------------------------------- //

export type BraceProfileType =
  | "rectangular"
  | "triangular"
  | "parabolic"
  | "scalloped";

export interface BracingPreviewRequest {
  profile_type: BraceProfileType;
  width_mm: number;
  height_mm: number;
  length_mm: number;
  density_kg_m3: number;
}

export interface BraceSectionResult {
  area_mm2: number;
  centroid_y_mm: number;
  inertia_mm4: number;
  section_modulus_mm3: number;
  profile_type: string;
}

export interface BracingPreviewResponse {
  section: BraceSectionResult;
  mass_grams: number;
  stiffness_estimate: number | null;
}

export interface BracingBatchRequest {
  braces: BracingPreviewRequest[];
  name: string;
}

export interface BracingBatchResponse {
  name: string;
  total_mass_grams: number;
  total_stiffness: number;
  braces: BracingPreviewResponse[];
}

export interface BracingDXFRequest {
  braces: Array<{
    profile_type: BraceProfileType;
    width_mm: number;
    height_mm: number;
    length_mm: number;
    x_mm: number;
    y_mm: number;
    angle_deg: number;
  }>;
  dxf_version: string;
  include_centerlines: boolean;
  include_labels: boolean;
}

export interface BracingPresetInfo {
  name: string;
  description: string;
  profile_type: BraceProfileType;
  typical_wood: string;
}

export async function previewBracing(
  req: BracingPreviewRequest
): Promise<BracingPreviewResponse> {
  const res = await fetch(`${base}/art-studio/bracing/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function batchBracing(
  req: BracingBatchRequest
): Promise<BracingBatchResponse> {
  const res = await fetch(`${base}/art-studio/bracing/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportBracingDXF(req: BracingDXFRequest): Promise<Blob> {
  const res = await fetch(`${base}/art-studio/bracing/export-dxf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}

export async function listBracingPresets(): Promise<BracingPresetInfo[]> {
  const res = await fetch(`${base}/art-studio/bracing/presets`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --------------------------------------------------------------------- //
// Utility Functions
// --------------------------------------------------------------------- //

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export const COMMON_WOODS = [
  { name: "Sitka Spruce", density: 420 },
  { name: "Engelmann Spruce", density: 380 },
  { name: "Western Red Cedar", density: 350 },
  { name: "Adirondack Spruce", density: 450 },
  { name: "European Spruce", density: 430 },
  { name: "Maple", density: 650 },
  { name: "Mahogany", density: 530 },
  { name: "Rosewood", density: 850 },
  { name: "Ebony", density: 1100 },
] as const;

export const COMMON_SCALE_LENGTHS = [
  { name: 'Gibson (24.75")', mm: 628.65 },
  { name: 'Fender (25.5")', mm: 647.7 },
  { name: 'PRS (25")', mm: 635.0 },
  { name: "Classical (650mm)", mm: 650.0 },
  { name: 'Baritone (27")', mm: 685.8 },
] as const;

export const PURFLING_MATERIALS = [
  { code: "bwb", name: "Black-White-Black", width: 1.5 },
  { code: "wbw", name: "White-Black-White", width: 1.5 },
  { code: "rope", name: "Rope Binding", width: 2.0 },
  { code: "herringbone", name: "Herringbone", width: 6.0 },
  { code: "abalone", name: "Abalone", width: 2.5 },
  { code: "wood", name: "Wood Strip", width: 1.0 },
] as const;
