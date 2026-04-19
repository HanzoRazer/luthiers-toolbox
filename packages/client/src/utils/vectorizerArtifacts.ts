/**
 * Canonical Vectorizer Artifact Utilities
 * ========================================
 *
 * Centralized helpers for consuming canonical vectorizer responses.
 * Replaces legacy field access patterns for both photo and blueprint pipelines.
 *
 * Usage:
 *   import { getDimensions, getStatus, downloadDxfFromBase64 } from '@/utils/vectorizerArtifacts'
 *
 * Canonical fields consumed:
 *   - artifacts.svg.content
 *   - artifacts.dxf.base64
 *   - dimensions.*
 *   - selection.*
 *   - recommendation.*
 *   - metrics.*
 *
 * Legacy fields this replaces:
 *   - svg_path_d, svg_path, dxf_path
 *   - body_width_mm, body_height_mm
 *   - contour_count, line_count
 *   - export_blocked, export_block_reason
 */

import { downloadBlob } from './downloadBlob'

// ─── Canonical Response Types ───────────────────────────────────────────────

export interface VectorizerArtifacts {
  svg?: {
    present: boolean
    content: string
    path_count: number
  }
  dxf?: {
    present: boolean
    base64: string
    entity_count: number
    closed_contours: number
  }
}

export interface VectorizerDimensions {
  width_mm: number
  height_mm: number
  width_in?: number
  height_in?: number
  spec_match?: string | null
}

export interface VectorizerSelection {
  candidate_count: number
  selected_index: number | null
  selection_score: number
  runner_up_score: number
  winner_margin: number
  reasons?: string[]
}

export interface VectorizerRecommendation {
  action: 'accept' | 'review' | 'reject'
  confidence: number
  reasons: string[]
}

export interface VectorizerMetrics {
  processing_ms?: number
  scale_source?: string
  bg_method?: string
  perspective_corrected?: boolean
  // Blueprint-specific
  original_entities?: number
  cleaned_entities?: number
  contours_found?: number
}

export interface VectorizerResponse {
  ok: boolean
  processed?: boolean
  stage?: string
  error?: string
  warnings?: string[]
  artifacts?: VectorizerArtifacts
  dimensions?: VectorizerDimensions
  selection?: VectorizerSelection
  recommendation?: VectorizerRecommendation
  metrics?: VectorizerMetrics
}

// ─── Base64 Decoding ────────────────────────────────────────────────────────

/**
 * Decode base64 string to Blob for download or upload.
 *
 * @param base64 - Base64-encoded string (without data URL prefix)
 * @param mimeType - MIME type for the resulting Blob
 * @returns Blob containing decoded binary data
 */
export function decodeBase64ToBlob(base64: string, mimeType: string): Blob {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Blob([bytes], { type: mimeType })
}

// ─── Download Helpers ───────────────────────────────────────────────────────

/**
 * Download DXF from base64-encoded artifact content.
 *
 * @param base64 - Base64-encoded DXF content from artifacts.dxf.base64
 * @param filename - Download filename (default: 'export.dxf')
 */
export function downloadDxfFromBase64(base64: string, filename = 'export.dxf'): void {
  const blob = decodeBase64ToBlob(base64, 'application/dxf')
  downloadBlob(blob, filename)
}

/**
 * Download SVG from content string.
 *
 * @param svgContent - Full SVG content from artifacts.svg.content
 * @param filename - Download filename (default: 'export.svg')
 */
export function downloadSvgFromContent(svgContent: string, filename = 'export.svg'): void {
  const blob = new Blob([svgContent], { type: 'image/svg+xml' })
  downloadBlob(blob, filename)
}

/**
 * Get DXF as Blob for CAM handoff or other processing.
 *
 * @param base64 - Base64-encoded DXF content
 * @returns Blob suitable for FormData or further processing
 */
export function getDxfBlob(base64: string): Blob {
  return decodeBase64ToBlob(base64, 'application/dxf')
}

/**
 * Get SVG as Blob.
 *
 * @param svgContent - Full SVG content string
 * @returns Blob suitable for FormData or further processing
 */
export function getSvgBlob(svgContent: string): Blob {
  return new Blob([svgContent], { type: 'image/svg+xml' })
}

// ─── Response Accessors ─────────────────────────────────────────────────────

/**
 * Get normalized dimensions from canonical response.
 *
 * @param response - Canonical vectorizer response
 * @returns Normalized dimensions object with defaults
 */
export function getDimensions(response: VectorizerResponse): {
  widthMm: number
  heightMm: number
  widthIn: number
  heightIn: number
  specMatch: string | null
} {
  return {
    widthMm: response.dimensions?.width_mm ?? 0,
    heightMm: response.dimensions?.height_mm ?? 0,
    widthIn: response.dimensions?.width_in ?? 0,
    heightIn: response.dimensions?.height_in ?? 0,
    specMatch: response.dimensions?.spec_match ?? null,
  }
}

/**
 * Get recommendation status for UI rendering.
 *
 * @param response - Canonical vectorizer response
 * @returns Status object with action, booleans, reasons, and confidence
 */
export function getStatus(response: VectorizerResponse): {
  action: 'accept' | 'review' | 'reject'
  isAccepted: boolean
  isReview: boolean
  isRejected: boolean
  reasons: string[]
  confidence: number
} {
  const action = response.recommendation?.action ?? 'reject'
  return {
    action,
    isAccepted: action === 'accept',
    isReview: action === 'review',
    isRejected: action === 'reject',
    reasons: response.recommendation?.reasons ?? [],
    confidence: response.recommendation?.confidence ?? 0,
  }
}

/**
 * Get error message from canonical response.
 * Prefers recommendation reasons over raw error field.
 *
 * @param response - Canonical vectorizer response
 * @returns Human-readable error message
 */
export function getErrorMessage(response: VectorizerResponse): string {
  return (
    response.recommendation?.reasons?.[0] ??
    response.error ??
    'Unknown vectorizer error'
  )
}

/**
 * Check if SVG artifact is valid for use.
 *
 * @param response - Canonical vectorizer response
 * @returns true if SVG content is present and usable
 */
export function hasValidSvg(response: VectorizerResponse): boolean {
  return !!(
    response.artifacts?.svg?.present &&
    response.artifacts?.svg?.content?.length > 50
  )
}

/**
 * Check if DXF artifact is available for download/CAM.
 *
 * @param response - Canonical vectorizer response
 * @returns true if DXF base64 is present and usable
 */
export function hasValidDxf(response: VectorizerResponse): boolean {
  return !!(
    response.artifacts?.dxf?.present &&
    response.artifacts?.dxf?.base64?.length > 100
  )
}

/**
 * Get selection diagnostics for debugging/display.
 *
 * @param response - Canonical vectorizer response
 * @returns Selection metrics with defaults
 */
export function getSelection(response: VectorizerResponse): {
  candidateCount: number
  selectionScore: number
  runnerUpScore: number
  winnerMargin: number
} {
  return {
    candidateCount: response.selection?.candidate_count ?? 0,
    selectionScore: response.selection?.selection_score ?? 0,
    runnerUpScore: response.selection?.runner_up_score ?? 0,
    winnerMargin: response.selection?.winner_margin ?? 0,
  }
}

/**
 * Get metrics for UI display.
 *
 * @param response - Canonical vectorizer response
 * @returns Metrics object with defaults
 */
export function getMetrics(response: VectorizerResponse): {
  processingMs: number
  scaleSource: string
  bgMethod: string
  perspectiveCorrected: boolean
  entityCount: number
  closedContours: number
} {
  return {
    processingMs: response.metrics?.processing_ms ?? 0,
    scaleSource: response.metrics?.scale_source ?? 'unknown',
    bgMethod: response.metrics?.bg_method ?? 'unknown',
    perspectiveCorrected: response.metrics?.perspective_corrected ?? false,
    entityCount: response.artifacts?.dxf?.entity_count ?? 0,
    closedContours: response.artifacts?.dxf?.closed_contours ?? 0,
  }
}

// ─── SVG Content Helpers ────────────────────────────────────────────────────

/**
 * Create a data URL from SVG content for use in img src or CSS.
 *
 * @param svgContent - Full SVG content string
 * @returns Data URL string
 */
export function svgToDataUrl(svgContent: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgContent)}`
}

/**
 * Extract the first path d attribute from SVG content.
 * Only use this if a component truly cannot consume full SVG.
 *
 * @param svgContent - Full SVG content string
 * @returns Path d attribute string, or empty string if not found
 */
export function extractPathDFromSvg(svgContent: string): string {
  // Parse as DOM to safely extract path d
  const parser = new DOMParser()
  const doc = parser.parseFromString(svgContent, 'image/svg+xml')

  // Find first path element
  const path = doc.querySelector('path')
  if (path) {
    return path.getAttribute('d') ?? ''
  }

  return ''
}
