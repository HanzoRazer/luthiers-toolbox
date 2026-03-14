/**
 * Rosette Wheel Designer SDK Endpoints
 *
 * Typed SDK helpers for the interactive rosette wheel designer API.
 * Replaces raw fetch() calls in useRosetteWheelStore.
 */

import { apiFetch } from "@/sdk/core/apiFetch";
import type {
  BomResponse,
  CellInfoResponse,
  MfgCheckResponse,
  PlaceTileRequest,
  PlaceTileResponse,
  PreviewRequest,
  PreviewResponse,
  RecipePreset,
  SymmetryCellsRequest,
  SymmetryCellsResponse,
  TileCatalogResponse,
} from "@/types/rosetteDesigner";

const BASE = "/api/art/rosette-designer";

// ── Catalog ─────────────────────────────────────────────────────

/**
 * Fetch full tile catalog, ring defs, segment options.
 */
export async function fetchCatalog(): Promise<TileCatalogResponse> {
  return apiFetch(`${BASE}/catalog`, { method: "GET" });
}

/**
 * Fetch all recipe presets.
 */
export async function fetchRecipes(): Promise<{ recipes: RecipePreset[] }> {
  return apiFetch(`${BASE}/recipes`, { method: "GET" });
}

/**
 * Fetch a single recipe by ID.
 */
export async function fetchRecipe(recipeId: string): Promise<RecipePreset> {
  return apiFetch(`${BASE}/recipes/${recipeId}`, { method: "GET" });
}

// ── Tile Operations ─────────────────────────────────────────────

/**
 * Place a tile respecting current symmetry mode.
 */
export async function placeTile(req: PlaceTileRequest): Promise<PlaceTileResponse> {
  return apiFetch(`${BASE}/place-tile`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Get symmetry cells for a given position.
 */
export async function getSymmetryCells(
  req: SymmetryCellsRequest
): Promise<SymmetryCellsResponse> {
  return apiFetch(`${BASE}/sym-cells`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Get cell info for hover tooltip.
 */
export async function getCellInfo(
  ri: number,
  si: number,
  numSegs: number,
  grid: Record<string, string>
): Promise<CellInfoResponse> {
  const gridParam = encodeURIComponent(JSON.stringify(grid));
  return apiFetch(
    `${BASE}/cell-info?ri=${ri}&si=${si}&num_segs=${numSegs}&grid=${gridParam}`,
    { method: "GET" }
  );
}

// ── BOM ─────────────────────────────────────────────────────────

interface BomRequest {
  num_segs: number;
  grid: Record<string, string>;
  ring_active: boolean[];
}

/**
 * Compute full bill of materials.
 */
export async function computeBom(req: BomRequest): Promise<BomResponse> {
  return apiFetch(`${BASE}/bom`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Export BOM as CSV string.
 */
export async function exportBomCsv(
  req: BomRequest & { design_name?: string }
): Promise<string> {
  const resp = await fetch(`${BASE}/bom/csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!resp.ok) {
    throw new Error(`BOM CSV export failed: ${resp.status}`);
  }
  return resp.text();
}

// ── MFG Checks ──────────────────────────────────────────────────

interface MfgCheckRequest {
  num_segs: number;
  grid: Record<string, string>;
  ring_active: boolean[];
}

/**
 * Run manufacturing intelligence checks.
 */
export async function runMfgCheck(req: MfgCheckRequest): Promise<MfgCheckResponse> {
  return apiFetch(`${BASE}/mfg-check`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Apply auto-fix for MFG issues.
 */
export async function applyMfgAutoFix(
  req: MfgCheckRequest
): Promise<{ grid: Record<string, string> }> {
  return apiFetch(`${BASE}/mfg-auto-fix`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ── Preview ─────────────────────────────────────────────────────

/**
 * Render SVG preview of the current design.
 */
export async function renderPreview(req: PreviewRequest): Promise<PreviewResponse> {
  return apiFetch(`${BASE}/preview`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Export design as downloadable SVG.
 */
export async function exportSvg(
  req: PreviewRequest & { design_name?: string; with_annotations?: boolean }
): Promise<Blob> {
  const resp = await fetch(`${BASE}/export/svg`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!resp.ok) {
    throw new Error(`SVG export failed: ${resp.status}`);
  }
  return resp.blob();
}
