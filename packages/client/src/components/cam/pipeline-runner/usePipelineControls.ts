/**
 * Composable for pipeline control state (file, tool, units, etc).
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { PipelineOpResult } from './pipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface PipelineControlsState {
  file: Ref<File | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  toolDia: Ref<number>
  units: Ref<'mm' | 'inch'>
  bridgeProfile: Ref<boolean>
  machineId: Ref<string | null>
  postId: Ref<string | null>
  results: Ref<PipelineOpResult[] | null>
  summary: Ref<Record<string, any> | null>
  openPayloadIndex: Ref<number | null>
  summaryLabel: ComputedRef<string>
  onFileChange: (ev: Event) => void
  togglePayload: (idx: number) => void
  formatPayload: (payload: any) => string
  resetResults: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function usePipelineControls(): PipelineControlsState {
  const file = ref<File | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const toolDia = ref(6.0)
  const units = ref<'mm' | 'inch'>('mm')
  const bridgeProfile = ref(false)
  const machineId = ref<string | null>(null)
  const postId = ref<string | null>(null)

  const results = ref<PipelineOpResult[] | null>(null)
  const summary = ref<Record<string, any> | null>(null)
  const openPayloadIndex = ref<number | null>(null)

  const summaryLabel = computed(() => {
    if (!summary.value) return ''
    const s = summary.value
    const time = (s.time_s ?? s.time_jerk_s ?? 0).toFixed(1)
    const moves = s.move_count ?? '—'
    return `time: ${time}s, moves: ${moves}`
  })

  function onFileChange(ev: Event) {
    const input = ev.target as HTMLInputElement
    const f = input.files?.[0]
    if (f) file.value = f
  }

  function togglePayload(idx: number) {
    openPayloadIndex.value = openPayloadIndex.value === idx ? null : idx
  }

  function formatPayload(payload: any): string {
    try {
      return JSON.stringify(payload, null, 2)
    } catch {
      return String(payload)
    }
  }

  function resetResults() {
    results.value = null
    summary.value = null
    openPayloadIndex.value = null
  }

  return {
    file,
    loading,
    error,
    toolDia,
    units,
    bridgeProfile,
    machineId,
    postId,
    results,
    summary,
    openPayloadIndex,
    summaryLabel,
    onFileChange,
    togglePayload,
    formatPayload,
    resetResults
  }
}
