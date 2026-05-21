/**
 * Topology Variant Types
 *
 * Dev Order 66: Experimental topology variant framework
 *
 * Topology = the experimental acoustic configuration being measured.
 * Includes body family, shell/radius, aperture, bracing, bridge/plate,
 * local contouring, tornavoz/liner treatment.
 *
 * Schema: topology-variant.v1
 * Storage: in-memory only (no persistence backend for Dev Order 66)
 */

/**
 * Category of acoustic configuration element
 */
export type TopologyVariantCategory =
  | 'body'
  | 'shell'
  | 'aperture'
  | 'bracing'
  | 'bridge'
  | 'tornavoz'
  | 'combined'

/**
 * Core topology variant descriptor
 *
 * Lightweight descriptor for experimental acoustic configurations.
 * NOT a geometry schema — no numeric dimensions.
 */
export interface TopologyVariant {
  /** Schema version for future portability */
  schemaVersion: 'topology-variant.v1'

  /** Unique identifier: topology-variant-YYYYMMDD-HHmmss */
  variantId: string

  /** Human-readable title (required) */
  title: string

  /** Optional description of the configuration */
  description?: string

  /** Primary category of the variant */
  category?: TopologyVariantCategory

  /** Shell/radius family descriptor (e.g., "32/8 reflective shell") */
  shellFamily?: string

  /** Body family descriptor (e.g., "Carlos Jumbo", "J-45") */
  bodyFamily?: string

  /** Aperture strategy descriptor (e.g., "dual-spiral", "triple treble spiral with domed island") */
  apertureStrategy?: string

  /** Bracing strategy descriptor (e.g., "minimal A-frame", "X-brace") */
  bracingStrategy?: string

  /** Bridge/plate strategy descriptor */
  bridgeStrategy?: string

  /** Local contouring descriptor */
  localContourStrategy?: string

  /** Tornavoz/liner treatment descriptor (e.g., "Selmer-hybrid tornavoz variant") */
  tornavozStrategy?: string

  /** Freeform experiment tags for filtering/grouping */
  experimentTags?: string[]

  /** Freeform notes */
  notes?: string

  /** ISO timestamp when variant was created */
  createdAtIso: string
}

/**
 * Validation result for topology variant
 */
export interface TopologyVariantValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

/**
 * Summary of topology variant for display
 */
export interface TopologyVariantSummary {
  variantId: string
  title: string
  category?: TopologyVariantCategory
  tagCount: number
  hasDescription: boolean
}
