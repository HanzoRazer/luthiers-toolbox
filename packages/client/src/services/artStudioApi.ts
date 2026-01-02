/**
 * Art Studio API Service
 * ======================
 * 
 * Centralized API for rosette design, geometry generation, and export.
 * 
 * Canonical paths (Art Studio owns rosette):
 *   /api/art/rosette/geometry   - Generate rosette geometry
 *   /api/art/rosette/export     - Export rosette to DXF/SVG
 *   /api/art/rosette/render     - Render rosette preview
 *   /api/art/rosette/patterns   - List available patterns
 * 
 * Legacy paths (maintained for compatibility):
 *   /api/rosette/*              - Old rosette endpoints
 * 
 * Wave 20: Option C API Restructuring - Art Studio canonical ownership
 */

import { apiFetchWithFallback, buildUrl } from './apiBase';

// =============================================================================
// TYPES
// =============================================================================

export type PatternType = 
  | 'herringbone'
  | 'celtic'
  | 'greek_key'
  | 'rope'
  | 'purfling'
  | 'mosaic'
  | 'custom';

export interface RosetteParams {
  pattern_type: PatternType;
  outer_radius_mm: number;
  inner_radius_mm: number;
  ring_count?: number;
  colors?: string[];
  line_width_mm?: number;
  repeat_count?: number;
  options?: Record<string, unknown>;
}

export interface RosetteGeometry {
  ok: boolean;
  pattern_type: PatternType;
  outer_radius_mm: number;
  inner_radius_mm: number;
  paths: Array<{
    id: string;
    type: 'polyline' | 'arc' | 'circle';
    points: Array<[number, number]>;
    closed: boolean;
    layer?: string;
  }>;
  metadata: {
    generated_at: string;
    complexity_level: number;
    estimated_cut_time_minutes?: number;
  };
}

export interface RosetteExportResult {
  ok: boolean;
  format: 'dxf' | 'svg' | 'nc';
  filename: string;
  download_url: string;
  file_size_bytes: number;
}

export interface RosettePreviewResult {
  ok: boolean;
  svg_data: string;
  width_mm: number;
  height_mm: number;
}

export interface PatternInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  default_repeat_count: number;
  thumbnail_url?: string;
}

// =============================================================================
// PATH BUILDERS
// =============================================================================

/**
 * Build canonical Art Studio rosette URL.
 * 
 * @example
 * buildRosetteUrl('geometry') → '/api/art/rosette/geometry'
 * buildRosetteUrl() → '/api/art/rosette/'
 */
export function buildRosetteUrl(endpoint?: string): string {
  if (!endpoint) {
    return buildUrl('api', 'art', 'rosette');
  }
  return buildUrl('api', 'art', 'rosette', endpoint);
}

/**
 * Build legacy rosette URL (for fallback).
 */
export function buildLegacyRosetteUrl(endpoint: string): string {
  return buildUrl('api', 'rosette', endpoint);
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Generate rosette geometry from parameters.
 */
export async function generateRosetteGeometry(
  params: RosetteParams
): Promise<RosetteGeometry> {
  const canonicalUrl = buildRosetteUrl('geometry');
  const legacyUrl = buildLegacyRosetteUrl('geometry');
  
  return apiFetchWithFallback<RosetteGeometry>(canonicalUrl, legacyUrl, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/**
 * Export rosette to specified format (DXF/SVG/NC).
 */
export async function exportRosette(
  params: RosetteParams & { format: 'dxf' | 'svg' | 'nc' }
): Promise<RosetteExportResult> {
  const canonicalUrl = buildRosetteUrl('export');
  const legacyUrl = buildLegacyRosetteUrl('export');
  
  return apiFetchWithFallback<RosetteExportResult>(canonicalUrl, legacyUrl, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/**
 * Render rosette preview as inline SVG.
 */
export async function renderRosettePreview(
  params: RosetteParams
): Promise<RosettePreviewResult> {
  const canonicalUrl = buildRosetteUrl('render');
  const legacyUrl = buildLegacyRosetteUrl('render');
  
  return apiFetchWithFallback<RosettePreviewResult>(canonicalUrl, legacyUrl, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/**
 * List all available rosette patterns.
 */
export async function fetchRosettePatterns(): Promise<{
  ok: boolean;
  patterns: PatternInfo[];
  categories: string[];
}> {
  const canonicalUrl = buildRosetteUrl('patterns');
  const legacyUrl = buildLegacyRosetteUrl('patterns');
  
  return apiFetchWithFallback(canonicalUrl, legacyUrl);
}

/**
 * Get details about a specific pattern.
 */
export async function fetchPatternInfo(patternId: string): Promise<PatternInfo> {
  const canonicalUrl = buildRosetteUrl(`patterns/${patternId}`);
  const legacyUrl = buildLegacyRosetteUrl(`patterns/${patternId}`);
  
  return apiFetchWithFallback<PatternInfo>(canonicalUrl, legacyUrl);
}

// =============================================================================
// CAM INTEGRATION
// =============================================================================

export interface RosetteCamParams extends RosetteParams {
  tool_diameter_mm: number;
  step_over_percent?: number;
  cut_depth_mm?: number;
  feed_rate_mm_min?: number;
  plunge_rate_mm_min?: number;
  post_processor?: string;
}

export interface RosetteCamResult {
  ok: boolean;
  gcode: string;
  estimated_time_minutes: number;
  tool_path_length_mm: number;
  warnings: string[];
}

/**
 * Generate CAM toolpath for rosette (advanced).
 * 
 * Uses canonical CAM path: /api/cam/art/rosette
 */
export async function generateRosetteCam(
  params: RosetteCamParams
): Promise<RosetteCamResult> {
  // CAM operations live under /api/cam axis
  const canonicalUrl = buildUrl('api', 'cam', 'art', 'rosette', 'toolpath');
  const legacyUrl = buildLegacyRosetteUrl('cam');
  
  return apiFetchWithFallback<RosetteCamResult>(canonicalUrl, legacyUrl, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

// =============================================================================
// PATTERN DEFAULTS
// =============================================================================

/**
 * Default parameters by pattern type.
 * Used for UI initialization and preview.
 */
export const PATTERN_DEFAULTS: Record<PatternType, Partial<RosetteParams>> = {
  herringbone: {
    ring_count: 3,
    line_width_mm: 0.5,
    repeat_count: 36,
  },
  celtic: {
    ring_count: 2,
    line_width_mm: 0.8,
    repeat_count: 8,
  },
  greek_key: {
    ring_count: 1,
    line_width_mm: 1.0,
    repeat_count: 12,
  },
  rope: {
    ring_count: 2,
    line_width_mm: 0.6,
    repeat_count: 24,
  },
  purfling: {
    ring_count: 5,
    line_width_mm: 0.3,
    repeat_count: 1,
  },
  mosaic: {
    ring_count: 4,
    line_width_mm: 0.4,
    repeat_count: 48,
  },
  custom: {
    ring_count: 1,
    line_width_mm: 0.5,
    repeat_count: 16,
  },
};
