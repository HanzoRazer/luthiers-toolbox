/**
 * useStiffnessIndex — Tonewood Acoustic Index Calculator
 *
 * The Production Shop — Woodwork Calculator / Stiffness Index panel
 *
 * Calculates four acoustic quality indices from density + MOE + dimensions:
 *
 *   1. RADIATION RATIO (Schelleng c/ρ)
 *      c / ρ  where c = √(E/ρ) × 1000  (m/s / kg/m³ × 10⁶)
 *      The primary soundboard quality index. Higher = more projecting.
 *      Adirondack spruce ~11.7, Sitka ~11.4, Cedar ~12.4
 *      Reference: Schelleng J.C. (1963) — "The violin as a circuit"
 *
 *   2. SPECIFIC MOE (E/ρ)
 *      MOE (GPa) / density (kg/m³) × 10⁶
 *      Stiffness per unit mass — same parameter as c² / 10⁶.
 *      Used for comparing fretboards and braces where pure stiffness matters.
 *
 *   3. STIFFNESS INDEX — Ashby plate index (E^(1/3) / ρ)
 *      For plate bending (soundboard, back): the material index that governs
 *      deflection at minimum weight. Higher = stiffer plate per gram.
 *      Reference: Ashby M.F. "Materials Selection in Mechanical Design"
 *
 *   4. ACOUSTIC IMPEDANCE (ρ × c)
 *      Governs reflection at wood joints (top-back, neck joint, bridge plate).
 *      Matched impedance → better energy transfer across a joint.
 *      ρ × c in units of kg/m²·s × 10⁻³ (MRayl)
 *
 *   5. PLATE MASS (at given dimensions)
 *      density × thickness × width × length → grams
 *      Practical: what does this blank weigh at your target thickness?
 *
 * API integration (R-8):
 *   When GET /api/registry/tonewoods is available, replaces hardcoded set
 *   with full 71-species tonewood reference. Falls back to hardcoded silently.
 */

import { ref, computed, readonly } from 'vue'
import { api } from '@/services/apiBase'
import {
  HARDCODED_TONEWOODS,
  PART_GROUPS,
  apiRecordToEntry,
} from './tonewoodData'
import type {
  TonewoodEntry,
  TonewoodPart,
  TonewoodApiResponse,
} from './tonewoodData'

// ============================================================================
// ACOUSTIC INDEX CALCULATIONS
// ============================================================================

/**
 * Speed of sound (m/s) from MOE (GPa) and density (kg/m³).
 * c = √(E / ρ)  where E in Pa, ρ in kg/m³
 * E (GPa) → Pa: × 10⁹
 */
export function calcSpeedOfSound(moeGpa: number, densityKgM3: number): number {
  return Math.sqrt((moeGpa * 1e9) / densityKgM3)
}

/**
 * Radiation ratio (Schelleng c/ρ index).
 * c / ρ × 1000  (units: m⁴ / kg·s)
 * Higher = better soundboard radiator.
 */
export function calcRadiationRatio(speedMs: number, densityKgM3: number): number {
  return (speedMs / densityKgM3) * 1000
}

/**
 * Specific MOE (E/ρ index).
 * MOE (GPa) / density (kg/m³) × 10⁶  (units: m²/s²)
 * = c²  — identical to radiation ratio squared × 10⁻⁶
 */
export function calcSpecificMoe(moeGpa: number, densityKgM3: number): number {
  return (moeGpa * 1e9) / densityKgM3
}

/**
 * Ashby plate stiffness index.
 * E^(1/3) / ρ  — governs minimum-weight plate for given bending stiffness.
 * Units: GPa^(1/3) · m³/kg
 */
export function calcAshbyIndex(moeGpa: number, densityKgM3: number): number {
  return Math.pow(moeGpa, 1 / 3) / (densityKgM3 / 1000)
}

/**
 * Acoustic impedance (ρ × c), in MRayl (10⁶ Pa·s/m).
 */
export function calcAcousticImpedance(densityKgM3: number, speedMs: number): number {
  return (densityKgM3 * speedMs) / 1e6
}

/**
 * Plate mass in grams.
 * thickness (mm) × width (mm) × length (mm) × density (kg/m³) / 1e6
 */
export function calcPlateMass(
  thicknessMm: number,
  widthMm: number,
  lengthMm: number,
  densityKgM3: number
): number {
  const volumeMm3 = thicknessMm * widthMm * lengthMm
  return (volumeMm3 / 1e6) * densityKgM3 * 1000 // → grams
}

// ============================================================================
// PER-ENTRY COMPUTED INDICES
// ============================================================================

export interface TonewoodIndices {
  entry: TonewoodEntry
  speedMs: number | null       // computed if missing, from MOE+ρ
  radiationRatio: number | null
  specificMoe: number | null
  ashbyIndex: number | null
  acousticImpedance: number | null
  /** Qualitative soundboard rating based on radiation ratio */
  soundboardRating: string | null
}

export function computeIndices(entry: TonewoodEntry): TonewoodIndices {
  if (!entry.moeGpa) {
    return {
      entry,
      speedMs: entry.speedOfSoundMs,
      radiationRatio: null,
      specificMoe: null,
      ashbyIndex: null,
      acousticImpedance: entry.acousticImpedance,
      soundboardRating: null,
    }
  }

  const speed = entry.speedOfSoundMs ?? calcSpeedOfSound(entry.moeGpa, entry.densityKgM3)
  const rr = calcRadiationRatio(speed, entry.densityKgM3)
  const sMoe = calcSpecificMoe(entry.moeGpa, entry.densityKgM3)
  const ashby = calcAshbyIndex(entry.moeGpa, entry.densityKgM3)
  const ai = calcAcousticImpedance(entry.densityKgM3, speed)

  // Schelleng soundboard rating (c/ρ × 1000 thresholds — approximate)
  let soundboardRating: string | null = null
  if (entry.parts.includes('soundboard')) {
    if (rr >= 12.0) soundboardRating = 'Excellent'
    else if (rr >= 10.5) soundboardRating = 'Good'
    else if (rr >= 9.0) soundboardRating = 'Acceptable'
    else soundboardRating = 'Below average'
  }

  return {
    entry,
    speedMs: +speed.toFixed(0),
    radiationRatio: +rr.toFixed(3),
    specificMoe: +(sMoe / 1e6).toFixed(3),
    ashbyIndex: +ashby.toFixed(4),
    acousticImpedance: +ai.toFixed(3),
    soundboardRating,
  }
}

// ============================================================================
// COMPOSABLE
// ============================================================================

export function useStiffnessIndex() {

  // ---------- Species pool (hardcoded + optional API extension) ----------
  const apiSpecies = ref<TonewoodEntry[]>([])
  const apiLoading = ref(false)
  const apiError = ref<string | null>(null)
  const apiLoaded = ref(false)

  /** Combined pool: API species replace hardcoded ones by id if present */
  const allSpecies = computed<TonewoodEntry[]>(() => {
    if (!apiLoaded.value) return HARDCODED_TONEWOODS
    const apiIds = new Set(apiSpecies.value.map(s => s.id))
    const kept = HARDCODED_TONEWOODS.filter(s => !apiIds.has(s.id))
    return [...kept, ...apiSpecies.value]
  })

  /** Try to load full tonewood dataset from API (R-8 endpoint) */
  async function loadFromApi(): Promise<void> {
    if (apiLoaded.value || apiLoading.value) return
    apiLoading.value = true
    apiError.value = null
    try {
      const data = await api.get<TonewoodApiResponse>('/api/registry/tonewoods')
      const entries = [
        ...Object.values(data.tier_1),
        ...Object.values(data.tier_2),
      ].map(apiRecordToEntry)
      apiSpecies.value = entries
      apiLoaded.value = true
    } catch {
      // Silent fallback to hardcoded set — do not surface error to user
      apiError.value = 'API unavailable — using built-in species set'
    } finally {
      apiLoading.value = false
    }
  }

  // ---------- Filter state ----------
  const partFilter = ref<TonewoodPart | 'all'>('soundboard')
  const sortBy = ref<'name' | 'radiation_ratio' | 'ashby' | 'density' | 'moe'>('radiation_ratio')
  const showNoMoeSpecies = ref(false)

  // ---------- Filtered + sorted species with computed indices ----------
  const filteredIndices = computed<TonewoodIndices[]>(() => {
    let pool = allSpecies.value

    if (partFilter.value !== 'all') {
      pool = pool.filter(s => s.parts.includes(partFilter.value as TonewoodPart))
    }

    if (!showNoMoeSpecies.value) {
      pool = pool.filter(s => s.moeGpa !== null)
    }

    const withIndices = pool.map(computeIndices)

    withIndices.sort((a, b) => {
      switch (sortBy.value) {
        case 'radiation_ratio':
          return (b.radiationRatio ?? 0) - (a.radiationRatio ?? 0)
        case 'ashby':
          return (b.ashbyIndex ?? 0) - (a.ashbyIndex ?? 0)
        case 'density':
          return a.entry.densityKgM3 - b.entry.densityKgM3
        case 'moe':
          return (b.entry.moeGpa ?? 0) - (a.entry.moeGpa ?? 0)
        case 'name':
          return a.entry.name.localeCompare(b.entry.name)
        default:
          return 0
      }
    })

    return withIndices
  })

  // ---------- Plate mass calculator ----------
  const selectedSpeciesId = ref<string>('spruce_adirondack')
  const thicknessMm = ref(3.0)
  const widthMm = ref(200.0)
  const lengthMm = ref(500.0)

  const selectedEntry = computed(() =>
    allSpecies.value.find(s => s.id === selectedSpeciesId.value) ?? null
  )

  const plateMassGrams = computed(() => {
    if (!selectedEntry.value) return null
    return calcPlateMass(thicknessMm.value, widthMm.value, lengthMm.value, selectedEntry.value.densityKgM3)
  })

  const selectedIndices = computed(() =>
    selectedEntry.value ? computeIndices(selectedEntry.value) : null
  )

  // ---------- Comparison mode: two species side by side ----------
  const compareId = ref<string>('cedar_western_red')
  const compareEntry = computed(() =>
    allSpecies.value.find(s => s.id === compareId.value) ?? null
  )
  const compareIndices = computed(() =>
    compareEntry.value ? computeIndices(compareEntry.value) : null
  )

  // ---------- Expose ----------
  return {
    // Species pool
    allSpecies: readonly(allSpecies),
    apiLoaded: readonly(apiLoaded),
    apiLoading: readonly(apiLoading),
    apiError: readonly(apiError),
    loadFromApi,

    // Filter/sort
    partFilter,
    sortBy,
    showNoMoeSpecies,
    partGroups: PART_GROUPS,

    // Table
    filteredIndices: readonly(filteredIndices),

    // Plate mass calc
    selectedSpeciesId,
    thicknessMm,
    widthMm,
    lengthMm,
    selectedEntry: readonly(selectedEntry),
    selectedIndices: readonly(selectedIndices),
    plateMassGrams: readonly(plateMassGrams),

    // Comparison
    compareId,
    compareEntry: readonly(compareEntry),
    compareIndices: readonly(compareIndices),
  }
}
