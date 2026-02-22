/**
 * CamPipeline state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type {
  PipelineOpResult,
  PipelinePreset,
  MachineProfile,
  PostProfile,
  NormalizationEntry
} from './camPipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface CamPipelineStateReturn {
  // File and loading
  file: Ref<File | null>
  loading: Ref<boolean>
  error: Ref<string | null>

  // Pipeline parameters
  toolDia: Ref<number>
  units: Ref<'mm' | 'inch'>
  bridgeProfile: Ref<boolean>
  machineId: Ref<string | null>
  postId: Ref<string | null>

  // Results
  results: Ref<PipelineOpResult[] | null>
  summary: Ref<Record<string, any> | null>
  openPayloadIndex: Ref<number | null>

  // Presets
  presets: Ref<PipelinePreset[]>
  selectedPresetId: Ref<string | null>
  newPresetName: Ref<string>
  newPresetDesc: Ref<string>

  // Inspector
  inspectorMachine: Ref<MachineProfile | null>
  inspectorPost: Ref<PostProfile | null>

  // H7.2 Normalization
  strictNormalize: Ref<boolean>
  normalizationIssues: Ref<NormalizationEntry[]>

  // Computed
  selectedPreset: ComputedRef<PipelinePreset | null>
  summaryLabel: ComputedRef<string>
}

// ============================================================================
// Composable
// ============================================================================

export function useCamPipelineState(): CamPipelineStateReturn {
  // File and loading
  const file = ref<File | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Pipeline parameters
  const toolDia = ref(6.0)
  const units = ref<'mm' | 'inch'>('mm')
  const bridgeProfile = ref(false)
  const machineId = ref<string | null>(null)
  const postId = ref<string | null>(null)

  // Results
  const results = ref<PipelineOpResult[] | null>(null)
  const summary = ref<Record<string, any> | null>(null)
  const openPayloadIndex = ref<number | null>(null)

  // Presets
  const presets = ref<PipelinePreset[]>([])
  const selectedPresetId = ref<string | null>(null)
  const newPresetName = ref('')
  const newPresetDesc = ref('')

  // Inspector
  const inspectorMachine = ref<MachineProfile | null>(null)
  const inspectorPost = ref<PostProfile | null>(null)

  // H7.2 Normalization
  const strictNormalize = ref(false)
  const normalizationIssues = ref<NormalizationEntry[]>([])

  // Computed
  const selectedPreset = computed(() =>
    presets.value.find(p => p.id === selectedPresetId.value) ?? null
  )

  const summaryLabel = computed(() => {
    if (!summary.value) return ''
    const s = summary.value
    const time = (s.time_s ?? s.time_jerk_s ?? 0).toFixed(1)
    const moves = s.move_count ?? '—'
    return `time: ${time}s, moves: ${moves}`
  })

  return {
    // File and loading
    file,
    loading,
    error,

    // Pipeline parameters
    toolDia,
    units,
    bridgeProfile,
    machineId,
    postId,

    // Results
    results,
    summary,
    openPayloadIndex,

    // Presets
    presets,
    selectedPresetId,
    newPresetName,
    newPresetDesc,

    // Inspector
    inspectorMachine,
    inspectorPost,

    // H7.2 Normalization
    strictNormalize,
    normalizationIssues,

    // Computed
    selectedPreset,
    summaryLabel
  }
}
