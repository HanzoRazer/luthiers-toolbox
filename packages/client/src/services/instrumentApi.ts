/**
 * Instrument API Service
 * ======================
 * 
 * Centralized API for instrument models, specs, and geometry.
 * 
 * Canonical paths (Option C):
 *   /api/instruments/guitar/           - List all models
 *   /api/instruments/guitar/{model}/spec - Model specifications
 *   /api/instruments/guitar/{model}/geometry - Body geometry
 *   /api/instruments/guitar/{model}/info - Model overview
 *   /api/instruments/guitar/{model}/assets - Asset files (if available)
 * 
 * Legacy paths (fallback):
 *   /api/instrument/geometry/* - Old instrument geometry endpoints
 * 
 * Wave 20: Option C API Restructuring
 */

import { apiFetch, apiFetchWithFallback, buildUrl } from './apiBase';

// =============================================================================
// TYPES
// =============================================================================

export interface InstrumentModel {
  model_id: string;
  display_name: string;
  category: string;
  status: 'STUB' | 'ASSETS_ONLY' | 'COMPLETE';
}

export interface InstrumentModelList {
  ok: boolean;
  total_models: number;
  models: InstrumentModel[];
  by_category: Record<string, string[]>;
  hierarchy?: Record<string, { display_name: string; variants: InstrumentModel[] }>;
}

export interface InstrumentSpec {
  model_id: string;
  display_name: string;
  category: string;
  status: string;
  scale_length_mm: number;
  scale_length_inches: number;
  fret_count: number;
  string_count: number;
  manufacturer: string;
  year_introduced: number;
  description: string;
  features: string[];
}

export interface InstrumentGeometry {
  model_id: string;
  category: string;
  scale_length_mm: number;
  body_length_mm: number;
  body_width_mm: number;
  body_depth_mm?: number;
  neck_pocket_length_mm?: number;
  notes: string;
}

export interface InstrumentInfo {
  model_id: string;
  display_name: string;
  category: string;
  status: string;
  description: string;
  manufacturer: string;
  year_introduced: number;
  has_assets: boolean;
  asset_count: number;
  endpoints: {
    spec: string;
    geometry: string;
    assets: string | null;
    cam: string;
  };
}

// =============================================================================
// PATH BUILDERS
// =============================================================================

/**
 * Build canonical instrument API URL.
 * 
 * @example
 * buildInstrumentUrl('stratocaster', 'spec') → '/api/instruments/guitar/stratocaster/spec'
 * buildInstrumentUrl() → '/api/instruments/guitar/'
 */
export function buildInstrumentUrl(modelId?: string, endpoint?: string): string {
  if (!modelId) {
    return buildUrl('api', 'instruments', 'guitar');
  }
  if (!endpoint) {
    return buildUrl('api', 'instruments', 'guitar', modelId);
  }
  return buildUrl('api', 'instruments', 'guitar', modelId, endpoint);
}

/**
 * Build legacy instrument API URL (for fallback).
 */
export function buildLegacyInstrumentUrl(endpoint: string): string {
  return buildUrl('api', 'instrument', 'geometry', endpoint);
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Fetch all available instrument models from registry.
 * 
 * Replaces hardcoded INSTRUMENT_MODELS array.
 */
export async function fetchInstrumentModels(): Promise<InstrumentModelList> {
  const url = buildInstrumentUrl();
  return apiFetch<InstrumentModelList>(url);
}

/**
 * Fetch specifications for a specific model.
 */
export async function fetchInstrumentSpec(modelId: string): Promise<InstrumentSpec> {
  const url = buildInstrumentUrl(modelId, 'spec');
  return apiFetch<InstrumentSpec>(url);
}

/**
 * Fetch geometry estimates for a model.
 */
export async function fetchInstrumentGeometry(modelId: string): Promise<InstrumentGeometry> {
  const url = buildInstrumentUrl(modelId, 'geometry');
  return apiFetch<InstrumentGeometry>(url);
}

/**
 * Fetch model overview/info for UI display.
 */
export async function fetchInstrumentInfo(modelId: string): Promise<InstrumentInfo> {
  const url = buildInstrumentUrl(modelId, 'info');
  return apiFetch<InstrumentInfo>(url);
}

/**
 * Fetch models that have actual asset files (for CAM operations).
 */
export async function fetchModelsWithAssets(): Promise<{
  ok: boolean;
  total_with_assets: number;
  models: Array<{
    model_id: string;
    display_name: string;
    status: string;
    asset_count: number;
    asset_types: string[];
  }>;
}> {
  const url = buildUrl('api', 'instruments', 'guitar', 'with-assets');
  return apiFetch(url);
}

// =============================================================================
// LEGACY COMPATIBILITY (Fretboard Geometry)
// =============================================================================

export interface FretboardParams {
  scale_length_mm: number;
  num_frets: number;
  nut_width_mm?: number;
  bridge_width_mm?: number;
  base_radius_inches?: number;
  end_radius_inches?: number;
}

export interface FretPosition {
  fret_number: number;
  position_mm: number;
  distance_from_previous_mm: number;
}

/**
 * Calculate fret positions (uses legacy endpoint with fallback).
 * 
 * This is the geometry calculation, not model-specific.
 */
export async function calculateFretPositions(
  params: FretboardParams
): Promise<{ frets: FretPosition[] }> {
  const canonicalUrl = buildUrl('api', 'instruments', 'geometry', 'frets');
  const legacyUrl = buildLegacyInstrumentUrl('frets');
  
  return apiFetchWithFallback(canonicalUrl, legacyUrl, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/**
 * Generate fretboard geometry (uses legacy endpoint with fallback).
 */
export async function generateFretboard(
  params: FretboardParams
): Promise<{ geometry: unknown }> {
  const canonicalUrl = buildUrl('api', 'instruments', 'geometry', 'fretboard');
  const legacyUrl = buildLegacyInstrumentUrl('fretboard');
  
  return apiFetchWithFallback(canonicalUrl, legacyUrl, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

// =============================================================================
// FALLBACK MODELS (offline/error state only)
// =============================================================================

/**
 * Fallback model list for offline/error states.
 * NOT the source of truth - always try API first.
 */
export const FALLBACK_MODELS: InstrumentModel[] = [
  { model_id: 'stratocaster', display_name: 'Fender Stratocaster', category: 'electric_guitar', status: 'STUB' },
  { model_id: 'telecaster', display_name: 'Fender Telecaster', category: 'electric_guitar', status: 'STUB' },
  { model_id: 'les_paul', display_name: 'Gibson Les Paul', category: 'electric_guitar', status: 'STUB' },
  { model_id: 'benedetto_17', display_name: 'Benedetto 17"', category: 'archtop', status: 'COMPLETE' },
  { model_id: 'smart_guitar', display_name: 'Smart Guitar', category: 'electric_guitar', status: 'COMPLETE' },
];
