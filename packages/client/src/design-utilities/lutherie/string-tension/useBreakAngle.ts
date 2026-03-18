/**
 * useBreakAngle — Bridge Break Angle API Composable
 *
 * The Production Shop — String Tension Calculator
 *
 * Wraps POST /bridge/break-angle endpoint.
 *
 * v2 Corrected (R-7 remediation complete):
 *   - Backend now uses corrected geometry (bridge surface, string exit point)
 *   - Backend returns gate result (GREEN/YELLOW/RED) based on Carruth 6° minimum
 *   - Client-side Carruth interpretation removed — use gate from API directly
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
import { STEEP_MAX_DEG } from './types'

// ============================================================================
// GEOMETRY INPUT DEFAULTS (v2 corrected field names)
// ============================================================================

export interface BreakAngleGeometry {
  /** Height of saddle crown above bridge TOP SURFACE (mm). Typical: 2-4 mm */
  saddleProjectionMm: number
  /** Distance from bridge pin center to saddle slot (mm). Martin ~5.5, Gibson ~6.5 */
  pinToSaddleMm: number
  /** Offset from pin center to string exit point (mm). Default 1.25 (midpoint 1.0-1.5) */
  slotOffsetMm: number
  /** Total saddle slot depth (mm) */
  saddleSlotDepthMm: number
  /** Saddle blank total height (mm). Standard bone blank = 12 mm */
  saddleBlankHeightMm: number
}

const DEFAULT_GEOMETRY: BreakAngleGeometry = {
  saddleProjectionMm: 2.5,
  pinToSaddleMm: 5.5,
  slotOffsetMm: 1.25,
  saddleSlotDepthMm: 10.0,
  saddleBlankHeightMm: 12.0,
}

// ============================================================================
// COMPOSABLE
// ============================================================================

export function useBreakAngle() {

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

    // v2: Use gate from API directly (no client-side Carruth interpretation)
    const gate = apiResult.value?.gate ?? null

    // carruthAdequate derived from gate (GREEN = adequate)
    const carruthAdequate = gate === 'GREEN' ? true : gate === 'RED' ? false : null

    // Status label from API gate/rating
    let statusLabel: string
    if (mode.value === 'computed' && apiResult.value) {
      // Use gate for display
      if (apiResult.value.gate === 'GREEN') {
        statusLabel = 'Adequate'
      } else if (apiResult.value.gate === 'YELLOW') {
        statusLabel = 'Marginal'
      } else if (apiResult.value.rating === 'too_steep') {
        statusLabel = 'Too steep'
      } else {
        statusLabel = 'Too shallow'
      }
    } else if (deg >= STEEP_MAX_DEG) {
      statusLabel = 'Too steep'
    } else {
      statusLabel = 'Manual'
    }

    return {
      deg,
      mode: mode.value,
      carruthAdequate,
      gate,
      apiRating: apiResult.value?.rating ?? null,
      riskFlags: apiResult.value?.risk_flags ?? [],
      statusLabel,
    }
  })

  // --------------------------------------------------------------------------
  // API call (v2 corrected geometry)
  // --------------------------------------------------------------------------

  async function fetchBreakAngle(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      // v2: Uses corrected field names and geometry
      // - saddle_projection_mm: height above bridge TOP SURFACE
      // - pin_to_saddle_mm: distance from pin center to saddle
      // - slot_offset_mm: accounts for slotted pin hole
      const result = await api.post<BreakAngleApiResult>('/api/bridge/break-angle', {
        saddle_projection_mm: geometry.value.saddleProjectionMm,
        pin_to_saddle_mm: geometry.value.pinToSaddleMm,
        slot_offset_mm: geometry.value.slotOffsetMm,
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
