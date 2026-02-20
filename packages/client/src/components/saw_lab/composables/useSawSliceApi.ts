/**
 * Composable for Saw Slice API operations (validation, learned params, job log).
 * Extracted from SawSlicePanel.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import type { SawBlade } from './useSawBladeRegistry'

// ==========================================================================
// Types
// ==========================================================================

export interface ValidationCheck {
  result: 'OK' | 'WARN' | 'ERROR'
  message: string
}

export interface ValidationResult {
  overall_result: 'OK' | 'WARN' | 'ERROR'
  checks: Record<string, ValidationCheck>
}

export interface MergedParams {
  rpm: number
  feed_ipm: number
  doc_mm: number
  lane_scale?: number
}

export interface SliceApiState {
  /** Validation results from last check */
  validationResult: Ref<ValidationResult | null>
  /** Merged learned parameters */
  mergedParams: Ref<MergedParams | null>
  /** Run ID from job log */
  runId: Ref<string>
  /** Is validation result valid (not ERROR) */
  isValid: ComputedRef<boolean>
  /** Validate operation parameters */
  validateOperation: () => Promise<void>
  /** Fetch and merge learned parameters */
  mergeLearnedParams: () => Promise<MergedParams | null>
  /** Send operation to job log */
  sendToJobLog: () => Promise<string | null>
  /** Format check name for display */
  formatCheckName: (key: string) => string
  /** Clear validation state */
  clearValidation: () => void
}

export interface SliceApiDeps {
  getBlade: () => SawBlade | null
  getBladeId: () => string
  getMaterial: () => string
  getMachine: () => string
  getRpm: () => number
  getFeedIpm: () => number
  getDepthPerPass: () => number
  getSafeZ: () => number
  getDepthPasses: () => number
  getTotalLengthMm: () => number
  getStartX: () => number
  getStartY: () => number
  getEndX: () => number
  getEndY: () => number
}

// ==========================================================================
// Composable
// ==========================================================================

export function useSawSliceApi(
  deps: SliceApiDeps,
  onParamsUpdated?: (params: MergedParams) => void
): SliceApiState {
  const validationResult = ref<ValidationResult | null>(null)
  const mergedParams = ref<MergedParams | null>(null)
  const runId = ref<string>('')

  // ==========================================================================
  // Computed
  // ==========================================================================

  const isValid = computed(() => {
    return validationResult.value !== null && validationResult.value.overall_result !== 'ERROR'
  })

  // ==========================================================================
  // Methods
  // ==========================================================================

  async function validateOperation(): Promise<void> {
    const blade = deps.getBlade()
    if (!blade) return

    const payload = {
      blade,
      op_type: 'slice',
      material_family: deps.getMaterial(),
      planned_rpm: deps.getRpm(),
      planned_feed_ipm: deps.getFeedIpm(),
      planned_doc_mm: deps.getDepthPerPass(),
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
    }
  }

  async function mergeLearnedParams(): Promise<MergedParams | null> {
    const laneKey = {
      tool_id: deps.getBladeId(),
      material: deps.getMaterial(),
      mode: 'slice',
      machine_profile: deps.getMachine(),
    }

    const baseline = {
      rpm: deps.getRpm(),
      feed_ipm: deps.getFeedIpm(),
      doc_mm: deps.getDepthPerPass(),
      safe_z: deps.getSafeZ(),
    }

    try {
      const response = await api('/api/feeds/learned/merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lane_key: laneKey, baseline }),
      })
      const result = await response.json()
      mergedParams.value = result.merged
      onParamsUpdated?.(result.merged)
      return result.merged
    } catch (err) {
      console.error('Failed to merge learned params:', err)
      return null
    }
  }

  async function sendToJobLog(): Promise<string | null> {
    const payload = {
      op_type: 'slice',
      machine_profile: deps.getMachine(),
      material_family: deps.getMaterial(),
      blade_id: deps.getBladeId(),
      safe_z: deps.getSafeZ(),
      depth_passes: deps.getDepthPasses(),
      total_length_mm: deps.getTotalLengthMm(),
      planned_rpm: deps.getRpm(),
      planned_feed_ipm: deps.getFeedIpm(),
      planned_doc_mm: deps.getDepthPerPass(),
      operator_notes: `Slice from (${deps.getStartX()},${deps.getStartY()}) to (${deps.getEndX()},${deps.getEndY()})`,
    }

    try {
      const response = await api('/api/saw/joblog/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const run = await response.json()
      runId.value = run.run_id

      alert(
        `Job sent to log! Run ID: ${run.run_id}\n\nReady to execute. Telemetry will be captured automatically.`
      )
      return run.run_id
    } catch (err) {
      console.error('Failed to send to job log:', err)
      alert('Failed to send to job log')
      return null
    }
  }

  function formatCheckName(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  }

  function clearValidation() {
    validationResult.value = null
    mergedParams.value = null
  }

  return {
    validationResult,
    mergedParams,
    runId,
    isValid,
    validateOperation,
    mergeLearnedParams,
    sendToJobLog,
    formatCheckName,
    clearValidation,
  }
}
