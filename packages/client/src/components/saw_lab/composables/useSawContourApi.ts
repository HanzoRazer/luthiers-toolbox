/**
 * Composable for contour API calls: validation, learned params, job logging.
 * Extracted from SawContourPanel.vue
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import type { SawBlade } from './useSawBladeRegistry'

// ==========================================================================
// Types
// ==========================================================================

export interface RadiusValidationResult {
  status: 'ok' | 'warn' | 'error'
  message: string
  min_radius?: number
  requested_radius?: number
  safety_margin?: number
}

export interface ValidationCheck {
  result: 'OK' | 'WARN' | 'ERROR'
  message: string
}

export interface ContourValidationResult {
  overall_result: 'OK' | 'WARN' | 'ERROR'
  checks: Record<string, ValidationCheck>
}

export interface MergedParams {
  rpm: number
  feed_ipm: number
  doc_mm: number
  safe_z?: number
}

export interface LaneKey {
  tool_id: string
  material: string
  mode: string
  machine_profile: string
}

export interface ContourApiState {
  /** Radius validation result */
  radiusValidation: Ref<RadiusValidationResult | null>
  /** Full contour validation result */
  validationResult: Ref<ContourValidationResult | null>
  /** Merged learned parameters */
  mergedParams: Ref<MergedParams | null>
  /** Run ID after job log submission */
  runId: Ref<string>
  /** Validate radius against blade diameter */
  validateRadius: (bladeDiameterMm: number, requestedRadiusMm: number) => Promise<void>
  /** Validate full contour operation */
  validateContour: (
    blade: SawBlade,
    materialFamily: string,
    rpm: number,
    feedIpm: number,
    docMm: number
  ) => Promise<void>
  /** Merge learned parameters for operation lane */
  mergeLearnedParams: (
    laneKey: LaneKey,
    baseline: { rpm: number; feed_ipm: number; doc_mm: number; safe_z: number }
  ) => Promise<MergedParams | null>
  /** Send contour job to job log */
  sendToJobLog: (payload: Record<string, unknown>) => Promise<string | null>
  /** Clear validation state */
  clearValidation: () => void
}

// ==========================================================================
// Composable
// ==========================================================================

export function useSawContourApi(): ContourApiState {
  const radiusValidation = ref<RadiusValidationResult | null>(null)
  const validationResult = ref<ContourValidationResult | null>(null)
  const mergedParams = ref<MergedParams | null>(null)
  const runId = ref('')

  // ==========================================================================
  // Methods
  // ==========================================================================

  async function validateRadius(bladeDiameterMm: number, requestedRadiusMm: number): Promise<void> {
    const payload = {
      blade_diameter_mm: bladeDiameterMm,
      requested_radius_mm: requestedRadiusMm,
    }

    try {
      const response = await api('/api/saw/validate/contour', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      radiusValidation.value = await response.json()
    } catch (err) {
      console.error('Radius validation failed:', err)
      radiusValidation.value = {
        status: 'error',
        message: 'Validation request failed',
      }
    }
  }

  async function validateContour(
    blade: SawBlade,
    materialFamily: string,
    rpm: number,
    feedIpm: number,
    docMm: number
  ): Promise<void> {
    const payload = {
      blade,
      op_type: 'contour',
      material_family: materialFamily,
      planned_rpm: rpm,
      planned_feed_ipm: feedIpm,
      planned_doc_mm: docMm,
    }

    try {
      const response = await api('/api/saw/validate/operation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      validationResult.value = await response.json()
    } catch (err) {
      console.error('Validation failed:', err)
      validationResult.value = {
        overall_result: 'ERROR',
        checks: {
          api_error: { result: 'ERROR', message: 'Validation request failed' },
        },
      }
    }
  }

  async function mergeLearnedParams(
    laneKey: LaneKey,
    baseline: { rpm: number; feed_ipm: number; doc_mm: number; safe_z: number }
  ): Promise<MergedParams | null> {
    try {
      const response = await api('/api/feeds/learned/merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lane_key: laneKey, baseline }),
      })
      const result = await response.json()
      mergedParams.value = result.merged
      return result.merged
    } catch (err) {
      console.error('Failed to merge learned params:', err)
      return null
    }
  }

  async function sendToJobLog(payload: Record<string, unknown>): Promise<string | null> {
    try {
      const response = await api('/api/saw/joblog/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const run = await response.json()
      runId.value = run.run_id
      return run.run_id
    } catch (err) {
      console.error('Failed to send to job log:', err)
      return null
    }
  }

  function clearValidation(): void {
    radiusValidation.value = null
    validationResult.value = null
    mergedParams.value = null
  }

  return {
    radiusValidation,
    validationResult,
    mergedParams,
    runId,
    validateRadius,
    validateContour,
    mergeLearnedParams,
    sendToJobLog,
    clearValidation,
  }
}
