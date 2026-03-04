/**
 * Rosette Preset Library
 *
 * CRITICAL INSIGHT: Many "traditional" patterns (herringbone, spanish rope, wave)
 * are mathematically identical - they're all just repeating angular segments.
 *
 * Instead of duplicating patterns with different names, we define PATTERN FAMILIES
 * and generate variations parametrically.
 */

import type { RosettePattern, RosetteRingBand } from '@/models/rmos'

// ============================================================================
// PATTERN FAMILIES
// ============================================================================

export interface PatternFamily {
  id: string
  name: string
  description: string
  category: 'traditional' | 'modern' | 'geometric' | 'organic'
  baseTemplate: Omit<RosettePattern, 'id' | 'name'>
  variations: PatternVariation[]
}

export interface PatternVariation {
  name: string
  description: string
  params: PatternParams
  svgFile?: string // Filename of SVG in /assets/rosette-presets/ (e.g., 'herringbone-24.svg')
}

export interface PatternParams {
  segments: number // Number of angular divisions (affects slice_angle_deg)
  rings: number // Number of concentric bands
  ringWidths: number[] // Width of each ring in mm
  stripFamilies: string[] // Material IDs for each ring
  colorScheme: string[] // Color hints
  alternation?: 'none' | 'checkerboard' | 'spiral' | 'radial'
}

// ============================================================================
// UTILITY: Generate pattern from parameters
// ============================================================================

export function generatePattern(
  name: string,
  params: PatternParams,
  baseRadius = 95 // Standard soundhole radius
): Omit<RosettePattern, 'id'> {
  const sliceAngle = 360 / params.segments

  // Generate rings from inside out
  let currentRadius = baseRadius - params.ringWidths.reduce((sum, w) => sum + w, 0)

  const rings: RosetteRingBand[] = []

  for (let i = 0; i < params.rings; i++) {
    const width = params.ringWidths[i] || 3 // Default 3mm
    currentRadius += width

    // Apply alternation pattern
    let stripFamily = params.stripFamilies[i % params.stripFamilies.length]
    let colorHint = params.colorScheme[i % params.colorScheme.length]

    if (params.alternation === 'checkerboard' && i % 2 === 1) {
      // Alternate every other ring
      stripFamily = params.stripFamilies[(i + 1) % params.stripFamilies.length]
      colorHint = params.colorScheme[(i + 1) % params.colorScheme.length]
    }

    rings.push({
      id: `ring-${i}`,
      index: i,
      radius_mm: currentRadius,
      width_mm: width,
      color_hint: colorHint,
      strip_family_id: stripFamily,
      slice_angle_deg: sliceAngle,
      tile_length_override_mm: null,
    })
  }

  return {
    name,
    center_x_mm: 0,
    center_y_mm: 0,
    ring_bands: rings,
    default_slice_thickness_mm: 0.8,
    default_passes: 2,
    default_workholding: 'vacuum-table',
    default_tool_id: 'saw-thin-kerf',
  }
}

// ============================================================================
// PATTERN FAMILIES - MATHEMATICALLY DISTINCT
// ============================================================================

export const PATTERN_FAMILIES: Record<string, PatternFamily> = {
  // ---------------------------------------------------------------------------
  // FAMILY 1: SINGLE-RING REPEATING
  // The "herringbone/rope/wave" family - all mathematically identical
  // What makes them look different is just the segment count
  // ---------------------------------------------------------------------------
  repeating_single: {
    id: 'repeating_single',
    name: 'Repeating Single Ring',
    description: 'One ring with repeating angular segments. Traditional patterns like herringbone, rope, and wave all belong to this family.',
    category: 'traditional',
    baseTemplate: generatePattern('Base Single Ring', {
      segments: 12,
      rings: 1,
      ringWidths: [4],
      stripFamilies: ['maple-light', 'walnut-dark'],
      colorScheme: ['#f5deb3', '#3e2723'],
      alternation: 'checkerboard',
    }),
    variations: [
      {
        name: 'Herringbone (24 segments)',
        description: 'Traditional herringbone pattern - very fine, delicate segments',
        svgFile: 'herringbone-24.svg',
        params: {
          segments: 24,
          rings: 1,
          ringWidths: [3],
          stripFamilies: ['maple-light', 'walnut-dark'],
          colorScheme: ['#f5deb3', '#3e2723'],
        },
      },
      {
        name: 'Spanish Rope (16 segments)',
        description: 'Classic Spanish rope pattern - traditional proportions',
        svgFile: 'spanish-rope-16.svg',
        params: {
          segments: 16,
          rings: 1,
          ringWidths: [4],
          stripFamilies: ['maple-light', 'rosewood'],
          colorScheme: ['#f5deb3', '#5d4037'],
        },
      },
      {
        name: 'Wave Pattern (12 segments)',
        description: 'Wave or rope pattern - bold, visible segments',
        svgFile: 'wave-12.svg',
        params: {
          segments: 12,
          rings: 1,
          ringWidths: [5],
          stripFamilies: ['maple-light', 'ebony'],
          colorScheme: ['#f5deb3', '#000000'],
        },
      },
      {
        name: 'German Rope (8 segments)',
        description: 'German/Bavarian rope - strong octagonal segments',
        svgFile: 'german-rope-8.svg',
        params: {
          segments: 8,
          rings: 1,
          ringWidths: [6],
          stripFamilies: ['maple-light', 'padauk'],
          colorScheme: ['#f5deb3', '#d32f2f'],
        },
      },
      {
        name: 'Fine Herringbone (32 segments)',
        description: 'Extra fine herringbone - very delicate detail',
        svgFile: 'fine-herringbone-32.svg',
        params: {
          segments: 32,
          rings: 1,
          ringWidths: [2.5],
          stripFamilies: ['maple-light', 'walnut-dark'],
          colorScheme: ['#f5deb3', '#3e2723'],
        },
      },
      {
        name: 'Wide Rope (6 segments)',
        description: 'Bold hexagonal rope pattern',
        svgFile: 'wide-rope-6.svg',
        params: {
          segments: 6,
          rings: 1,
          ringWidths: [7],
          stripFamilies: ['maple-light', 'ebony'],
          colorScheme: ['#f5deb3', '#000000'],
        },
      },
    ],
  },

  // ---------------------------------------------------------------------------
  // FAMILY 2: MULTI-RING ALTERNATING
  // Truly different - multiple concentric rings with material alternation
  // ---------------------------------------------------------------------------
  multi_ring_alternating: {
    id: 'multi_ring_alternating',
    name: 'Multi-Ring Alternating',
    description: 'Multiple concentric rings with alternating materials. Creates complex depth and visual interest.',
    category: 'traditional',
    baseTemplate: generatePattern('Base Multi-Ring', {
      segments: 16,
      rings: 5,
      ringWidths: [2, 2, 2, 2, 2],
      stripFamilies: ['maple-light', 'walnut-dark'],
      colorScheme: ['#f5deb3', '#3e2723'],
      alternation: 'checkerboard',
    }),
    variations: [
      {
        name: 'Triple Ring Classic',
        description: '3 rings, high contrast',
        svgFile: 'triple-ring-classic.svg',
        params: {
          segments: 16,
          rings: 3,
          ringWidths: [4, 3, 4],
          stripFamilies: ['maple-light', 'walnut-dark'],
          colorScheme: ['#f5deb3', '#3e2723'],
          alternation: 'checkerboard',
        },
      },
      {
        name: 'Five Ring Delicate',
        description: '5 narrow rings, fine detail',
        svgFile: 'five-ring-delicate.svg',
        params: {
          segments: 20,
          rings: 5,
          ringWidths: [2, 2, 2, 2, 2],
          stripFamilies: ['maple-light', 'rosewood', 'mahogany'],
          colorScheme: ['#f5deb3', '#5d4037', '#bf360c'],
          alternation: 'checkerboard',
        },
      },
      {
        name: 'Seven Ring Complex',
        description: '7 rings with 3-wood alternation',
        svgFile: 'seven-ring-complex.svg',
        params: {
          segments: 24,
          rings: 7,
          ringWidths: [1.5, 2, 1.5, 2, 1.5, 2, 1.5],
          stripFamilies: ['maple-light', 'walnut-dark', 'padauk'],
          colorScheme: ['#f5deb3', '#3e2723', '#d32f2f'],
          alternation: 'checkerboard',
        },
      },
    ],
  },

  // ---------------------------------------------------------------------------
  // FAMILY 3: RADIAL STAR
  // Truly different - alternating segments radiate from center with no ring divisions
  // ---------------------------------------------------------------------------
  radial_star: {
    id: 'radial_star',
    name: 'Radial Star',
    description: 'Single continuous band divided only radially - creates star/sunburst effect.',
    category: 'geometric',
    baseTemplate: generatePattern('Base Radial', {
      segments: 12,
      rings: 1,
      ringWidths: [12],
      stripFamilies: ['maple-light', 'ebony'],
      colorScheme: ['#f5deb3', '#000000'],
    }),
    variations: [
      {
        name: '8-Point Star',
        description: 'Bold octagonal star',
        svgFile: 'star-8-point.svg',
        params: {
          segments: 8,
          rings: 1,
          ringWidths: [15],
          stripFamilies: ['maple-light', 'ebony'],
          colorScheme: ['#f5deb3', '#000000'],
        },
      },
      {
        name: '12-Point Star',
        description: 'Classic 12-point starburst',
        svgFile: 'star-12-point.svg',
        params: {
          segments: 12,
          rings: 1,
          ringWidths: [12],
          stripFamilies: ['maple-light', 'walnut-dark'],
          colorScheme: ['#f5deb3', '#3e2723'],
        },
      },
      {
        name: '16-Point Star',
        description: 'Fine detailed star',
        svgFile: 'star-16-point.svg',
        params: {
          segments: 16,
          rings: 1,
          ringWidths: [10],
          stripFamilies: ['maple-light', 'rosewood'],
          colorScheme: ['#f5deb3', '#5d4037'],
        },
      },
    ],
  },

  // ---------------------------------------------------------------------------
  // FAMILY 4: BORDERED FIELD
  // Truly different - solid center with decorative border
  // ---------------------------------------------------------------------------
  bordered_field: {
    id: 'bordered_field',
    name: 'Bordered Field',
    description: 'Solid center field surrounded by decorative border rings.',
    category: 'traditional',
    baseTemplate: generatePattern('Base Border', {
      segments: 1, // Solid center - no segments
      rings: 3,
      ringWidths: [20, 3, 3],
      stripFamilies: ['walnut-dark', 'maple-light', 'ebony'],
      colorScheme: ['#3e2723', '#f5deb3', '#000000'],
    }),
    variations: [
      {
        name: 'Simple Border',
        description: 'Dark center with light border',
        svgFile: 'simple-border.svg',
        params: {
          segments: 1,
          rings: 2,
          ringWidths: [18, 4],
          stripFamilies: ['ebony', 'maple-light'],
          colorScheme: ['#000000', '#f5deb3'],
        },
      },
      {
        name: 'Double Border',
        description: 'Center with two contrasting borders',
        svgFile: 'double-border.svg',
        params: {
          segments: 1,
          rings: 3,
          ringWidths: [15, 3, 3],
          stripFamilies: ['rosewood', 'maple-light', 'walnut-dark'],
          colorScheme: ['#5d4037', '#f5deb3', '#3e2723'],
        },
      },
      {
        name: 'Triple Border Complex',
        description: 'Center with three decorative rings',
        svgFile: 'triple-border-complex.svg',
        params: {
          segments: 1,
          rings: 4,
          ringWidths: [12, 2, 2, 2],
          stripFamilies: ['mahogany', 'maple-light', 'ebony', 'maple-light'],
          colorScheme: ['#bf360c', '#f5deb3', '#000000', '#f5deb3'],
        },
      },
    ],
  },

  // ---------------------------------------------------------------------------
  // FAMILY 5: CONCENTRIC ONLY
  // Truly different - multiple rings, all solid (no angular segments)
  // ---------------------------------------------------------------------------
  concentric_only: {
    id: 'concentric_only',
    name: 'Concentric Rings Only',
    description: 'Pure concentric circles with no angular divisions. Simple, elegant, modern.',
    category: 'modern',
    baseTemplate: generatePattern('Base Concentric', {
      segments: 1,
      rings: 4,
      ringWidths: [3, 3, 3, 3],
      stripFamilies: ['maple-light', 'walnut-dark', 'maple-light', 'ebony'],
      colorScheme: ['#f5deb3', '#3e2723', '#f5deb3', '#000000'],
    }),
    variations: [
      {
        name: 'Two-Tone Rings',
        description: 'Simple alternating light/dark',
        svgFile: 'two-tone-rings.svg',
        params: {
          segments: 1,
          rings: 5,
          ringWidths: [2, 2, 2, 2, 2],
          stripFamilies: ['maple-light', 'ebony'],
          colorScheme: ['#f5deb3', '#000000'],
          alternation: 'checkerboard',
        },
      },
      {
        name: 'Rainbow Gradient',
        description: '7 rings with color progression',
        svgFile: 'rainbow-gradient.svg',
        params: {
          segments: 1,
          rings: 7,
          ringWidths: [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
          stripFamilies: ['maple-light', 'cherry', 'mahogany', 'rosewood', 'walnut-dark', 'wenge', 'ebony'],
          colorScheme: ['#f5deb3', '#c62828', '#bf360c', '#5d4037', '#3e2723', '#424242', '#000000'],
        },
      },
      {
        name: 'Wide Band Minimalist',
        description: '3 wide bands, bold and simple',
        svgFile: 'wide-band-minimalist.svg',
        params: {
          segments: 1,
          rings: 3,
          ringWidths: [5, 5, 5],
          stripFamilies: ['walnut-dark', 'maple-light', 'walnut-dark'],
          colorScheme: ['#3e2723', '#f5deb3', '#3e2723'],
        },
      },
    ],
  },

  // ---------------------------------------------------------------------------
  // FAMILY 6: HYBRID RADIAL/CONCENTRIC
  // Truly different - inner rings segmented, outer rings solid (or vice versa)
  // ---------------------------------------------------------------------------
  hybrid: {
    id: 'hybrid',
    name: 'Hybrid Radial/Concentric',
    description: 'Combines segmented and solid rings for complex visual effect.',
    category: 'modern',
    baseTemplate: generatePattern('Base Hybrid', {
      segments: 16,
      rings: 4,
      ringWidths: [3, 3, 3, 3],
      stripFamilies: ['maple-light', 'walnut-dark'],
      colorScheme: ['#f5deb3', '#3e2723'],
    }),
    variations: [
      {
        name: 'Segmented Core',
        description: 'Inner ring segmented, outer rings solid',
        svgFile: 'segmented-core.svg',
        params: {
          segments: 12, // This would need special logic - different segments per ring
          rings: 3,
          ringWidths: [6, 4, 4],
          stripFamilies: ['maple-light', 'walnut-dark', 'ebony'],
          colorScheme: ['#f5deb3', '#3e2723', '#000000'],
        },
      },
      // Note: This pattern family needs special handling in the generator
      // to support different segment counts per ring
    ],
  },
}

// ============================================================================
// PRESET CATALOG
// ============================================================================

export interface PresetCatalog {
  families: PatternFamily[]
  totalPresets: number
  categories: string[]
}

export function getPresetCatalog(): PresetCatalog {
  const families = Object.values(PATTERN_FAMILIES)
  const totalPresets = families.reduce((sum, f) => sum + f.variations.length, 0)
  const categories = [...new Set(families.map(f => f.category))]

  return {
    families,
    totalPresets,
    categories,
  }
}

// ============================================================================
// HELPER: Create pattern from variation
// ============================================================================

export function createPatternFromVariation(
  family: PatternFamily,
  variation: PatternVariation,
  customName?: string
): Omit<RosettePattern, 'id'> {
  const name = customName || `${family.name} - ${variation.name}`
  return generatePattern(name, variation.params)
}
