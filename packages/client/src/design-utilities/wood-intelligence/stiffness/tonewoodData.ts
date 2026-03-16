/**
 * Tonewood Stiffness Index Data
 *
 * The Production Shop — Woodwork Calculator / Stiffness Index panel
 *
 * Hybrid approach:
 *   HARDCODED — primary and key established tonewoods used daily in guitar building.
 *               Pulled from luthier_tonewood_reference.json (v4.0.0) in the backend.
 *               Augmented with FPL / Wood Database values for species missing MOE in repo.
 *
 *   API        — full 71-species tonewood reference via GET /api/registry/tonewoods
 *               (endpoint to be added — R-8). When available, replaces hardcoded set.
 *
 * Sources:
 *   [REPO]  luthier_tonewood_reference.json v4.0.0 — derived from USDA FPL + Wood Database
 *   [FPL]   USDA FPL Wood Handbook GTR-282 — Table 5-1, 5-3
 *   [WDB]   The Wood Database (Eric Meier) — https://www.wood-database.com
 *   [CIRAD] CIRAD Wood Collection open data
 *
 * Acoustic indices used:
 *   radiation_ratio   = speed_of_sound / density           (Schelleng — soundboard quality proxy)
 *   stiffness_index   = MOE^(1/3) / density                (Ashby plate bending index)
 *   specific_MOE      = MOE / density                      (stiffness per unit mass)
 *   acoustic_impedance = density × speed_of_sound          (reflection coefficient at join)
 */

// ============================================================================
// TYPES
// ============================================================================

export type TonewoodPart =
  | 'soundboard'
  | 'back_sides'
  | 'neck'
  | 'fretboard'
  | 'body'
  | 'bracing'
  | 'bridge'
  | 'accent'

export type TonewoodSource = 'repo' | 'fpl' | 'wdb' | 'estimated'

export interface TonewoodEntry {
  id: string
  name: string
  scientificName: string
  /** kg/m³ at ~12% MC */
  densityKgM3: number
  /** Modulus of Elasticity, GPa, longitudinal, 12% MC */
  moeGpa: number | null
  /** Speed of sound, m/s, longitudinal — √(MOE/ρ) × 1000 */
  speedOfSoundMs: number | null
  /** Acoustic impedance = ρ × c (kg/m²·s × 10³) */
  acousticImpedance: number | null
  /** Modulus of Rupture, MPa — bending strength */
  morMpa: number | null
  parts: TonewoodPart[]
  toneCharacter: string
  sustainability: string
  /** Data source flag */
  source: TonewoodSource
  /** Note on data quality / estimation method */
  sourceNote?: string
  /** Whether this species is in the hardcoded set (true) or API-only (false) */
  hardcoded: boolean
}

// ============================================================================
// HARDCODED PRIMARY SET
// All values from [REPO] unless flagged
// ============================================================================

export const HARDCODED_TONEWOODS: TonewoodEntry[] = [

  // ---------- SOUNDBOARDS ----------

  {
    id: 'spruce_adirondack',
    name: 'Adirondack Spruce',
    scientificName: 'Picea rubens',
    densityKgM3: 435,
    moeGpa: 11.2,
    speedOfSoundMs: 5074,
    acousticImpedance: 2.21,
    morMpa: 74.0,
    parts: ['soundboard'],
    toneCharacter: 'Powerful, high headroom — the pre-war dreadnought standard',
    sustainability: 'Limited supply — slow-growing',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'spruce_european',
    name: 'European Spruce',
    scientificName: 'Picea abies',
    densityKgM3: 405,
    moeGpa: 9.5,
    speedOfSoundMs: 4843,
    acousticImpedance: 1.96,
    morMpa: null,
    parts: ['soundboard'],
    toneCharacter: 'Warm, complex, refined — the classical luthier\'s choice',
    sustainability: 'Sustainable (managed forests)',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'spruce_sitka',
    name: 'Sitka Spruce',
    scientificName: 'Picea sitchensis',
    densityKgM3: 425,
    moeGpa: 9.93,
    speedOfSoundMs: 4853,
    acousticImpedance: 2.06,
    morMpa: 68.1,
    parts: ['soundboard'],
    toneCharacter: 'Versatile, strong fundamental — the modern production standard',
    sustainability: 'Sustainable',
    source: 'fpl',
    sourceNote: 'MOE/MOR from FPL GTR-282 Table 5-1 (Picea sitchensis, 12% MC). SOS computed.',
    hardcoded: true,
  },
  {
    id: 'spruce_white',
    name: 'White Spruce',
    scientificName: 'Picea glauca',
    densityKgM3: 410,
    moeGpa: 9.7,
    speedOfSoundMs: 4864,
    acousticImpedance: 1.99,
    morMpa: null,
    parts: ['soundboard', 'bracing'],
    toneCharacter: 'Balanced, clear — good alternative to Sitka',
    sustainability: 'Sustainable',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'cedar_western_red',
    name: 'Western Red Cedar',
    scientificName: 'Thuja plicata',
    densityKgM3: 370,
    moeGpa: 7.78,
    speedOfSoundMs: 4586,
    acousticImpedance: 1.70,
    morMpa: null,
    parts: ['soundboard'],
    toneCharacter: 'Warm, dark, immediate response — less break-in than spruce',
    sustainability: 'Sustainable',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'cedar_spanish',
    name: 'Spanish Cedar',
    scientificName: 'Cedrela odorata',
    densityKgM3: 450,
    moeGpa: 9.7,
    speedOfSoundMs: 4643,
    acousticImpedance: 2.09,
    morMpa: null,
    parts: ['neck'],
    toneCharacter: 'Resonant, lightweight — traditional classical guitar neck',
    sustainability: 'CITES Appendix III — verify sourcing',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'redwood',
    name: 'Redwood',
    scientificName: 'Sequoia sempervirens',
    densityKgM3: 420,
    moeGpa: 8.55,
    speedOfSoundMs: 4512,
    acousticImpedance: 1.89,
    morMpa: null,
    parts: ['soundboard', 'body'],
    toneCharacter: 'Warm, balanced, cedar-like with more sustain',
    sustainability: 'Old-growth protected; salvage only',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'douglas_fir',
    name: 'Douglas Fir',
    scientificName: 'Pseudotsuga menziesii',
    densityKgM3: 530,
    moeGpa: 10.0,
    speedOfSoundMs: 4344,
    acousticImpedance: 2.30,
    morMpa: null,
    parts: ['soundboard', 'bracing'],
    toneCharacter: 'Stiff and punchy — emerging as a premium soundboard wood',
    sustainability: 'Sustainable',
    source: 'repo',
    hardcoded: true,
  },

  // ---------- BACK & SIDES ----------

  {
    id: 'mahogany_honduran',
    name: 'Honduran Mahogany',
    scientificName: 'Swietenia macrophylla',
    densityKgM3: 545,
    moeGpa: 11.97,
    speedOfSoundMs: 4687,
    acousticImpedance: 2.55,
    morMpa: null,
    parts: ['body', 'neck', 'back_sides'],
    toneCharacter: 'Warm, balanced, good sustain — the all-mahogany standard',
    sustainability: 'CITES Appendix II — verify sourcing',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'rosewood_east_indian',
    name: 'East Indian Rosewood',
    scientificName: 'Dalbergia latifolia',
    densityKgM3: 830,
    moeGpa: 11.5,
    speedOfSoundMs: 3724,
    acousticImpedance: 3.09,
    morMpa: null,
    parts: ['fretboard', 'back_sides', 'bridge'],
    toneCharacter: 'Rich, complex, warm lows — the modern rosewood standard',
    sustainability: 'CITES Appendix II — requires documentation',
    source: 'wdb',
    sourceNote: 'MOE from Wood Database (Dalbergia latifolia). SOS computed from MOE/ρ. Repo record has density but no MOE.',
    hardcoded: true,
  },
  {
    id: 'rosewood_brazilian',
    name: 'Brazilian Rosewood',
    scientificName: 'Dalbergia nigra',
    densityKgM3: 835,
    moeGpa: 12.0,
    speedOfSoundMs: 3791,
    acousticImpedance: 3.17,
    morMpa: null,
    parts: ['fretboard', 'back_sides'],
    toneCharacter: 'Full-spectrum, complex, warm and bright simultaneously',
    sustainability: 'CITES Appendix I — pre-ban only; heavily restricted',
    source: 'wdb',
    sourceNote: 'MOE estimated from Wood Database comparable Dalbergia species. Repo record has density only.',
    hardcoded: true,
  },
  {
    id: 'walnut_black',
    name: 'Black Walnut',
    scientificName: 'Juglans nigra',
    densityKgM3: 610,
    moeGpa: 11.34,
    speedOfSoundMs: 4312,
    acousticImpedance: 2.63,
    morMpa: null,
    parts: ['body', 'back_sides'],
    toneCharacter: 'Warm, rich mids — increasingly popular mahogany alternative',
    sustainability: 'Sustainable (North American)',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'sapele',
    name: 'Sapele',
    scientificName: 'Entandrophragma cylindricum',
    densityKgM3: 640,
    moeGpa: 12.04,
    speedOfSoundMs: 4337,
    acousticImpedance: 2.78,
    morMpa: null,
    parts: ['body', 'neck', 'back_sides'],
    toneCharacter: 'Bright, complex ribbon figure — mahogany-family response',
    sustainability: 'Sustainable (FSC available)',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'koa',
    name: 'Hawaiian Koa',
    scientificName: 'Acacia koa',
    densityKgM3: 625,
    moeGpa: 10.37,
    speedOfSoundMs: 4073,
    acousticImpedance: 2.55,
    morMpa: null,
    parts: ['body', 'back_sides', 'soundboard'],
    toneCharacter: 'Warm, balanced — opens up with age like rosewood',
    sustainability: 'Limited; Hawaiian endemic. Hawaii only.',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'cherry_black',
    name: 'Black Cherry',
    scientificName: 'Prunus serotina',
    densityKgM3: 560,
    moeGpa: 10.24,
    speedOfSoundMs: 4276,
    acousticImpedance: 2.39,
    morMpa: null,
    parts: ['body', 'back_sides'],
    toneCharacter: 'Warm, clear, rosewood-adjacent — growing in popularity',
    sustainability: 'Sustainable (North American)',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'tasmanian_blackwood',
    name: 'Tasmanian Blackwood',
    scientificName: 'Acacia melanoxylon',
    densityKgM3: 640,
    moeGpa: 11.82,
    speedOfSoundMs: 4298,
    acousticImpedance: 2.75,
    morMpa: null,
    parts: ['body', 'back_sides'],
    toneCharacter: 'Warm, balanced — koa relative, similar response',
    sustainability: 'Sustainable (Australian)',
    source: 'repo',
    hardcoded: true,
  },

  // ---------- NECKS ----------

  {
    id: 'maple_hard',
    name: 'Hard Maple',
    scientificName: 'Acer saccharum',
    densityKgM3: 705,
    moeGpa: 13.49,
    speedOfSoundMs: 4374,
    acousticImpedance: 3.08,
    morMpa: null,
    parts: ['neck', 'fretboard', 'body'],
    toneCharacter: 'Bright, articulate, snappy — the electric guitar neck standard',
    sustainability: 'Sustainable (North American)',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'wenge',
    name: 'Wenge',
    scientificName: 'Millettia laurentii',
    densityKgM3: 870,
    moeGpa: 14.75,
    speedOfSoundMs: 4118,
    acousticImpedance: 3.58,
    morMpa: null,
    parts: ['neck', 'fretboard'],
    toneCharacter: 'Stiff, punchy, tight lows — popular for 5-7 string bass necks',
    sustainability: 'Vulnerable — verify sourcing',
    source: 'repo',
    hardcoded: true,
  },

  // ---------- FRETBOARDS ----------

  {
    id: 'african_blackwood',
    name: 'African Blackwood',
    scientificName: 'Dalbergia melanoxylon',
    densityKgM3: 1270,
    moeGpa: 17.95,
    speedOfSoundMs: 3760,
    acousticImpedance: 4.77,
    morMpa: null,
    parts: ['fretboard', 'bridge'],
    toneCharacter: 'Dense, brilliant — the traditional classical fretboard wood',
    sustainability: 'Near threatened — CITES Appendix II',
    source: 'repo',
    hardcoded: true,
  },
  {
    id: 'ebony_african',
    name: 'African Ebony',
    scientificName: 'Diospyros crassiflora',
    densityKgM3: 1030,
    moeGpa: 17.0,
    speedOfSoundMs: 4062,
    acousticImpedance: 4.18,
    morMpa: null,
    parts: ['fretboard', 'bridge', 'nuts'],
    toneCharacter: 'Bright, snappy attack, glass-like — the premium fretboard standard',
    sustainability: 'CITES Appendix II — endangered; verify sourcing',
    source: 'wdb',
    sourceNote: 'MOE from Wood Database (Diospyros crassiflora). SOS computed. Repo has density only.',
    hardcoded: true,
  },
  {
    id: 'pau_ferro',
    name: 'Pau Ferro (Bolivian Rosewood)',
    scientificName: 'Machaerium scleroxylon',
    densityKgM3: 880,
    moeGpa: 14.0,
    speedOfSoundMs: 3989,
    acousticImpedance: 3.51,
    morMpa: null,
    parts: ['fretboard', 'back_sides'],
    toneCharacter: 'Bright, clear — common rosewood substitute',
    sustainability: 'CITES Appendix II',
    source: 'repo',
    hardcoded: true,
  },

  // ---------- BODIES ----------

  {
    id: 'alder',
    name: 'Red Alder',
    scientificName: 'Alnus rubra',
    densityKgM3: 420,
    moeGpa: null,
    speedOfSoundMs: null,
    acousticImpedance: null,
    morMpa: null,
    parts: ['body'],
    toneCharacter: 'Balanced, slightly bright — the Fender Strat/Tele body standard',
    sustainability: 'Sustainable, abundant',
    source: 'repo',
    sourceNote: 'MOE not in repo or FPL for Alnus rubra. Density only.',
    hardcoded: true,
  },
  {
    id: 'ash_swamp',
    name: 'Swamp Ash',
    scientificName: 'Fraxinus spp.',
    densityKgM3: 500,
    moeGpa: null,
    speedOfSoundMs: null,
    acousticImpedance: null,
    morMpa: null,
    parts: ['body'],
    toneCharacter: 'Bright, twangy, scooped mids — classic Fender body tone',
    sustainability: 'Declining (emerald ash borer)',
    source: 'repo',
    sourceNote: 'MOE not populated in repo. Density only.',
    hardcoded: true,
  },
  {
    id: 'basswood',
    name: 'American Basswood',
    scientificName: 'Tilia americana',
    densityKgM3: 415,
    moeGpa: 10.07,
    speedOfSoundMs: 4926,
    acousticImpedance: 2.04,
    morMpa: null,
    parts: ['body'],
    toneCharacter: 'Warm, even, pickup-forward — Japanese electric guitar standard',
    sustainability: 'Sustainable',
    source: 'repo',
    hardcoded: true,
  },
]

// ============================================================================
// PART GROUPS (for filtering UI)
// ============================================================================

export const PART_GROUPS: { id: TonewoodPart; label: string }[] = [
  { id: 'soundboard', label: 'Soundboard' },
  { id: 'back_sides', label: 'Back & Sides' },
  { id: 'neck',       label: 'Neck' },
  { id: 'fretboard',  label: 'Fretboard' },
  { id: 'body',       label: 'Body' },
  { id: 'bracing',    label: 'Bracing' },
  { id: 'bridge',     label: 'Bridge' },
]

// ============================================================================
// API RESPONSE TYPE (for GET /api/registry/tonewoods — R-8)
// ============================================================================

export interface TonewoodApiResponse {
  tier_1: Record<string, ApiTonewoodRecord>
  tier_2: Record<string, ApiTonewoodRecord>
}

export interface ApiTonewoodRecord {
  id: string
  name: string
  scientific_name: string
  guitar_relevance: string
  density_kg_m3: number
  modulus_of_elasticity_gpa: number | null
  speed_of_sound_m_s: number | null
  acoustic_impedance: number | null
  modulus_of_rupture_mpa: number | null
  typical_uses: string[]
  tone_character: string
  sustainability: string
}

/**
 * Convert API response record to TonewoodEntry.
 * Used when the full dataset is loaded from the API.
 */
export function apiRecordToEntry(r: ApiTonewoodRecord): TonewoodEntry {
  return {
    id: r.id,
    name: r.name,
    scientificName: r.scientific_name,
    densityKgM3: r.density_kg_m3,
    moeGpa: r.modulus_of_elasticity_gpa,
    speedOfSoundMs: r.speed_of_sound_m_s,
    acousticImpedance: r.acoustic_impedance,
    morMpa: r.modulus_of_rupture_mpa,
    parts: r.typical_uses as TonewoodPart[],
    toneCharacter: r.tone_character,
    sustainability: r.sustainability,
    source: 'repo',
    hardcoded: false,
  }
}
