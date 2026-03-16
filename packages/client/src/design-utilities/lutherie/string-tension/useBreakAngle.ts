/**
 * useBreakAngle — Bridge Break Angle API Composable
 *
 * The Production Shop — String Tension Calculator
 *
 * Wraps POST /bridge/break-angle endpoint.
 *
 * ⚠️  KNOWN DEBT — R-7:
 *   The endpoint currently implements v1 geometry (wrong reference surfaces,
 *   AI-fabricated thresholds 18°/23–31°/38°). The corrected v2 spec is
 *   documented in bridge_break_angle_derivation.md and the remediation doc.
 *
 *   This composable:
 *   - Calls the v1 endpoint as-is
 *   - Applies v2 Carruth thresholds CLIENT-SIDE for display (when instrumentType
 *     has useCarruthThresholds = true), ignoring the v1 API rating
 *   - Surfaces the v1 rating separately as apiRating for traceability
 *   - Will be simplified once R-7 corrects the backend
 *
 * Two modes:
 *   'computed'  — resolves from API using geometry inputs
 *   'manual'    — user enters break angle directly (no API call)
 */

import { ref, computed, readonly } from 'vue'
import { api } from '@/services/apiBase'
import type {
  BreakAngleMode,
  BreakAngleApiResult,
  ResolvedBreakAngle,
} from './types'
import { CARRUTH_MIN_DEG, STEEP_MAX_DEG } from './types'

// ============================================================================
// GEOMETRY INPUT DEFAULTS
// ============================================================================

export interface BreakAngleGeometry {
  /** Distance from bridge pin center to saddle crown center (mm). Martin ~5.5, Gibson ~6.5 */
  pinToSaddleCenterMm: number
  /** Height of saddle crown above bridge top surface (mm). Note: v1 endpoint uses plate surface — see R-7 */
  saddleProtrusionMm: number
  /** Total saddle slot depth (mm) */
  saddleSlotDepthMm: number
  /** Saddle blank total height (mm). Standard bone blank = 12 mm */
  saddleBlankHeightMm: number
}

const DEFAULT_GEOMETRY: BreakAngleGeometry = {
  pinToSaddleCenterMm: 5.5,
  saddleProtrusionMm: 3.0,
  saddleSlotDepthMm: 10.0,
  saddleBlankHeightMm: 12.0,
}

// ============================================================================
// COMPOSABLE
// ============================================================================

export function useBreakAngle(useCarruthThresholds: { value: boolean }) {

  // --------------------------------------------------------------------------
  // State
  // --------------------------------------------------------------------------

  const mode = ref<BreakAngleMode>('manual')
  const manualDeg = ref(20.0)
  const geometry = ref<BreakAngleGeometry>({ ...DEFAULT_GEOMETRY })
  const apiResult = ref<BreakAngleApiResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // --------------------------------------------------------------------------
  // Resolved break angle (used downstream by useTension)
  // --------------------------------------------------------------------------

  const resolved = computed<ResolvedBreakAngle>(() => {
    const deg = mode.value === 'computed' && apiResult.value !== null
      ? apiResult.value.break_angle_deg
      : manualDeg.value

    // Carruth adequacy — only meaningful for acoustic pin-bridge
    let carruthAdequate: boolean | null = null
    if (useCarruthThresholds.value) {
      carruthAdequate = deg >= CARRUTH_MIN_DEG && deg < STEEP_MAX_DEG
    }

    // Client-side v2 rating (overrides v1 API rating for display when Carruth applies)
    let statusLabel: string
    if (deg >= STEEP_MAX_DEG) {
      statusLabel = 'Too steep'
    } else if (useCarruthThresholds.value && deg < CARRUTH_MIN_DEG) {
      statusLabel = 'Too shallow (Carruth)'
    } else if (useCarruthThresholds.value) {
      statusLabel = 'Adequate'
    } else if (mode.value === 'computed' && apiResult.value) {
      // For non-Carruth instruments, surface v1 rating as-is
      statusLabel = {
        optimal: 'Optimal',
        acceptable: 'Acceptable',
        too_shallow: 'Too shallow',
        too_steep: 'Too steep',
      }[apiResult.value.rating] ?? apiResult.value.rating
    } else {
      statusLabel = 'Manual'
    }

    return {
      deg,
      mode: mode.value,
      carruthAdequate,
      apiRating: apiResult.value?.rating ?? null,
      riskFlags: apiResult.value?.risk_flags ?? [],
      statusLabel,
    }
  })

  // --------------------------------------------------------------------------
  // API call
  // --------------------------------------------------------------------------

  async function fetchBreakAngle(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      // ⚠️ v1 endpoint — uses pin_to_saddle_center_mm (not corrected d_effective)
      // and measures saddle protrusion above bridge plate (not bridge top surface).
      // See R-7 for v2 correction plan.
      const result = await api.post<BreakAngleApiResult>('/api/bridge/break-angle', {
        pin_to_saddle_center_mm: geometry.value.pinToSaddleCenterMm,
        saddle_protrusion_mm: geometry.value.saddleProtrusionMm,
        saddle_slot_depth_mm: geometry.value.saddleSlotDepthMm,
        saddle_blank_height_mm: geometry.value.saddleBlankHeightMm,
      })
      apiResult.value = result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Break angle API call failed'
      apiResult.value = null
    } finally {
      loading.value = false
    }
  }

  // --------------------------------------------------------------------------
  // Actions
  // --------------------------------------------------------------------------

  function setMode(m: BreakAngleMode): void {
    mode.value = m
    if (m === 'computed' && apiResult.value === null) {
      fetchBreakAngle()
    }
  }

  function updateGeometry(patch: Partial<BreakAngleGeometry>): void {
    geometry.value = { ...geometry.value, ...patch }
  }

  function resetToManual(): void {
    mode.value = 'manual'
    apiResult.value = null
    error.value = null
  }

  // --------------------------------------------------------------------------
  // Expose
  // --------------------------------------------------------------------------

  return {
    mode,
    manualDeg,
    geometry,
    apiResult: readonly(apiResult),
    loading: readonly(loading),
    error: readonly(error),
    resolved: readonly(resolved),

    setMode,
    updateGeometry,
    fetchBreakAngle,
    resetToManual,
  }
}
