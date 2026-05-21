/**
 * Topology Variant Utilities
 *
 * Dev Order 66: Experimental topology variant framework
 *
 * Observational only — no calibration authority, no prediction systems.
 * In-memory storage for Dev Order 66 (no persistence backend).
 */

import type {
  TopologyVariant,
  TopologyVariantCategory,
  TopologyVariantValidationResult,
  TopologyVariantSummary,
} from '@/types/acoustics/topologyVariant'

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
