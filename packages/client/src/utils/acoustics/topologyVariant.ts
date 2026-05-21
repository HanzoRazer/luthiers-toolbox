/**
 * Topology Variant Utilities
 *
 * Dev Order 66: Experimental topology variant framework
 * Dev Order 67: QA hardening and linkage verification
 *
 * Observational only — no calibration authority, no prediction systems.
 * In-memory storage (no persistence backend).
 *
 * All functions are immutable — they never mutate input arrays or objects.
 */

import type {
  TopologyVariant,
  TopologyVariantCategory,
  TopologyVariantValidationResult,
  TopologyVariantSummary,
} from '@/types/acoustics/topologyVariant'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'

/**
 * Generate a topology variant ID with timestamp
 * Format: topology-variant-YYYYMMDD-HHmmss
 */
export function generateTopologyVariantId(): string {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const min = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  return `topology-variant-${yyyy}${mm}${dd}-${hh}${min}${ss}`
}

/**
 * Create a new topology variant with defaults
 */
export function createTopologyVariant(
  title: string,
  overrides?: Partial<Omit<TopologyVariant, 'schemaVersion' | 'variantId' | 'createdAtIso'>>
): TopologyVariant {
  return {
    schemaVersion: 'topology-variant.v1',
    variantId: generateTopologyVariantId(),
    title,
    createdAtIso: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * Validate topology variant structure
 */
export function validateTopologyVariant(data: unknown): TopologyVariantValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (!data || typeof data !== 'object') {
    return { valid: false, errors: ['Data must be an object'], warnings: [] }
  }

  const obj = data as Record<string, unknown>

  // Required fields
  if (obj.schemaVersion !== 'topology-variant.v1') {
    errors.push(`Invalid or missing schemaVersion (expected 'topology-variant.v1')`)
  }

  if (typeof obj.variantId !== 'string' || obj.variantId.trim() === '') {
    errors.push('Missing or invalid variantId')
  }

  if (typeof obj.title !== 'string' || obj.title.trim() === '') {
    errors.push('Missing or invalid title')
  }

  if (typeof obj.createdAtIso !== 'string') {
    errors.push('Missing createdAtIso timestamp')
  }

  // Optional field type checks
  if (obj.description !== undefined && typeof obj.description !== 'string') {
    errors.push('description must be a string')
  }

  if (obj.category !== undefined) {
    const validCategories: TopologyVariantCategory[] = [
      'body', 'shell', 'aperture', 'bracing', 'bridge', 'tornavoz', 'combined'
    ]
    if (!validCategories.includes(obj.category as TopologyVariantCategory)) {
      errors.push(`Invalid category: ${obj.category}`)
    }
  }

  const stringFields = [
    'shellFamily', 'bodyFamily', 'apertureStrategy', 'bracingStrategy',
    'bridgeStrategy', 'localContourStrategy', 'tornavozStrategy', 'notes'
  ]
  for (const field of stringFields) {
    if (obj[field] !== undefined && typeof obj[field] !== 'string') {
      errors.push(`${field} must be a string`)
    }
  }

  if (obj.experimentTags !== undefined) {
    if (!Array.isArray(obj.experimentTags)) {
      errors.push('experimentTags must be an array')
    } else if (!obj.experimentTags.every((t: unknown) => typeof t === 'string')) {
      errors.push('experimentTags must contain only strings')
    }
  }

  // Warnings for sparse variants
  const hasAnyStrategy = [
    obj.shellFamily, obj.bodyFamily, obj.apertureStrategy,
    obj.bracingStrategy, obj.bridgeStrategy, obj.localContourStrategy,
    obj.tornavozStrategy
  ].some(v => v !== undefined && v !== '')

  if (!hasAnyStrategy && !obj.description) {
    warnings.push('Variant has no strategy descriptors or description')
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  }
}

/**
 * Get display label for topology variant
 */
export function getTopologyVariantDisplayLabel(variant: TopologyVariant): string {
  if (variant.title) {
    return variant.title
  }
  return variant.variantId
}

/**
 * Get short summary of variant strategies
 */
export function getTopologyVariantStrategySummary(variant: TopologyVariant): string {
  const parts: string[] = []

  if (variant.bodyFamily) parts.push(variant.bodyFamily)
  if (variant.apertureStrategy) parts.push(variant.apertureStrategy)
  if (variant.bracingStrategy) parts.push(variant.bracingStrategy)
  if (variant.shellFamily) parts.push(variant.shellFamily)

  if (parts.length === 0) {
    if (variant.description) {
      return variant.description.slice(0, 50) + (variant.description.length > 50 ? '...' : '')
    }
    return 'No strategies defined'
  }

  return parts.join(' · ')
}

/**
 * Create summary for display/selection
 */
export function createTopologyVariantSummary(variant: TopologyVariant): TopologyVariantSummary {
  return {
    variantId: variant.variantId,
    title: variant.title,
    category: variant.category,
    tagCount: variant.experimentTags?.length ?? 0,
    hasDescription: !!variant.description,
  }
}

/**
 * Format variant timestamp for display
 */
export function formatVariantTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) {
      return 'Unknown'
    }
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return 'Unknown'
  }
}

/**
 * Check if two archives share the same topology variant
 */
export function checkSharedTopologyVariant(
  variantRefsA: string[] | undefined,
  variantRefsB: string[] | undefined
): { shared: boolean; sharedIds: string[] } {
  if (!variantRefsA?.length || !variantRefsB?.length) {
    return { shared: false, sharedIds: [] }
  }

  const setA = new Set(variantRefsA)
  const sharedIds = variantRefsB.filter(id => setA.has(id))

  return {
    shared: sharedIds.length > 0,
    sharedIds,
  }
}

/**
 * Get category display label
 */
export function getCategoryDisplayLabel(category: TopologyVariantCategory | undefined): string {
  if (!category) return 'Uncategorized'

  const labels: Record<TopologyVariantCategory, string> = {
    body: 'Body',
    shell: 'Shell/Radius',
    aperture: 'Aperture',
    bracing: 'Bracing',
    bridge: 'Bridge/Plate',
    tornavoz: 'Tornavoz/Liner',
    combined: 'Combined',
  }

  return labels[category] ?? category
}

/**
 * Sort variants by creation date (newest first)
 */
export function sortTopologyVariantsByDate(variants: TopologyVariant[]): TopologyVariant[] {
  return [...variants].sort((a, b) => {
    const dateA = new Date(a.createdAtIso).getTime()
    const dateB = new Date(b.createdAtIso).getTime()
    if (isNaN(dateA) && isNaN(dateB)) return 0
    if (isNaN(dateA)) return 1
    if (isNaN(dateB)) return -1
    return dateB - dateA
  })
}

/**
 * Filter variants by category
 */
export function filterVariantsByCategory(
  variants: TopologyVariant[],
  category: TopologyVariantCategory
): TopologyVariant[] {
  return variants.filter(v => v.category === category)
}

/**
 * Filter variants by experiment tag
 */
export function filterVariantsByTag(
  variants: TopologyVariant[],
  tag: string
): TopologyVariant[] {
  const lowerTag = tag.toLowerCase()
  return variants.filter(v =>
    v.experimentTags?.some(t => t.toLowerCase().includes(lowerTag))
  )
}

/**
 * Get all unique experiment tags from variants
 */
export function getAllExperimentTags(variants: TopologyVariant[]): string[] {
  const tags = new Set<string>()
  for (const v of variants) {
    if (v.experimentTags) {
      for (const tag of v.experimentTags) {
        tags.add(tag)
      }
    }
  }
  return Array.from(tags).sort()
}

// =============================================================================
// Dev Order 67: Hardening Utilities
// =============================================================================

/**
 * Type guard for TopologyVariant
 * Returns true if data has valid topology-variant.v1 schema structure
 */
export function isTopologyVariant(data: unknown): data is TopologyVariant {
  if (!data || typeof data !== 'object') return false
  const obj = data as Record<string, unknown>
  return (
    obj.schemaVersion === 'topology-variant.v1' &&
    typeof obj.variantId === 'string' &&
    obj.variantId.trim() !== '' &&
    typeof obj.title === 'string' &&
    typeof obj.createdAtIso === 'string'
  )
}

/**
 * Normalize a topology variant (immutable)
 * - Trims whitespace from string fields
 * - Removes empty optional string fields
 * - Normalizes empty tag arrays to undefined
 * - Preserves schema version and IDs
 * - Does NOT fix invalid schema versions
 */
export function normalizeTopologyVariant(variant: TopologyVariant): TopologyVariant {
  const trimOrUndefined = (val: string | undefined): string | undefined => {
    if (val === undefined) return undefined
    const trimmed = val.trim()
    return trimmed === '' ? undefined : trimmed
  }

  const normalizedTags = variant.experimentTags?.filter(t => t.trim() !== '').map(t => t.trim())

  return {
    schemaVersion: variant.schemaVersion,
    variantId: variant.variantId,
    title: variant.title.trim(),
    createdAtIso: variant.createdAtIso,
    description: trimOrUndefined(variant.description),
    category: variant.category,
    shellFamily: trimOrUndefined(variant.shellFamily),
    bodyFamily: trimOrUndefined(variant.bodyFamily),
    apertureStrategy: trimOrUndefined(variant.apertureStrategy),
    bracingStrategy: trimOrUndefined(variant.bracingStrategy),
    bridgeStrategy: trimOrUndefined(variant.bridgeStrategy),
    localContourStrategy: trimOrUndefined(variant.localContourStrategy),
    tornavozStrategy: trimOrUndefined(variant.tornavozStrategy),
    experimentTags: normalizedTags?.length ? normalizedTags : undefined,
    notes: trimOrUndefined(variant.notes),
  }
}

/**
 * Safely parse topology variant timestamp
 * Returns Date object or null if invalid
 */
export function safeParseTopologyVariantTimestamp(isoString: string | undefined): Date | null {
  if (!isoString) return null
  try {
    const date = new Date(isoString)
    return isNaN(date.getTime()) ? null : date
  } catch {
    return null
  }
}

/**
 * Check if archive has topology variant references
 */
export function hasTopologyVariantReferences(archive: MeasurementArchiveRecord): boolean {
  return Array.isArray(archive.topologyVariantReferences) &&
    archive.topologyVariantReferences.length > 0
}

/**
 * Deduplicate topology variant references (immutable)
 * Filters out empty strings and duplicates
 */
export function dedupeTopologyVariantReferences(refs: string[] | undefined): string[] {
  if (!refs || refs.length === 0) return []
  const seen = new Set<string>()
  const result: string[] = []
  for (const ref of refs) {
    const trimmed = ref.trim()
    if (trimmed !== '' && !seen.has(trimmed)) {
      seen.add(trimmed)
      result.push(trimmed)
    }
  }
  return result
}

/**
 * Filter archives by topology variant ID (immutable)
 * Returns archives that reference the given variant ID
 */
export function filterArchivesByTopologyVariant(
  archives: MeasurementArchiveRecord[],
  variantId: string
): MeasurementArchiveRecord[] {
  if (!variantId.trim()) return []
  return archives.filter(archive =>
    archive.topologyVariantReferences?.includes(variantId)
  )
}

/**
 * Group archives by topology variant (immutable)
 * Returns a map of variantId → archives
 * Archives with no variant refs are grouped under '__none__'
 * Archives with multiple refs appear in multiple groups
 */
export function groupArchivesByTopologyVariant(
  archives: MeasurementArchiveRecord[]
): Map<string, MeasurementArchiveRecord[]> {
  const groups = new Map<string, MeasurementArchiveRecord[]>()

  for (const archive of archives) {
    const refs = archive.topologyVariantReferences
    if (!refs || refs.length === 0) {
      const existing = groups.get('__none__') ?? []
      groups.set('__none__', [...existing, archive])
    } else {
      for (const ref of refs) {
        const existing = groups.get(ref) ?? []
        groups.set(ref, [...existing, archive])
      }
    }
  }

  return groups
}

/**
 * Validate that a variant ID reference exists in the variants list
 * Returns true if the reference is valid (exists or is empty)
 */
export function isValidVariantReference(
  variantId: string,
  variants: TopologyVariant[]
): boolean {
  if (!variantId.trim()) return false
  return variants.some(v => v.variantId === variantId)
}

/**
 * Filter out invalid variant references (immutable)
 * Removes refs that don't exist in the variants list
 */
export function filterValidVariantReferences(
  refs: string[] | undefined,
  variants: TopologyVariant[]
): string[] {
  if (!refs || refs.length === 0) return []
  const variantIds = new Set(variants.map(v => v.variantId))
  return refs.filter(ref => variantIds.has(ref))
}
