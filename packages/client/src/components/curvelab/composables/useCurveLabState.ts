/**
 * CurveLab state management.
 */
import { ref, computed, watch } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import type {
  AutoFixOption,
  CurvePoint,
  CurvePreflightResponse,
  ValidationReport,
  CurveLabProps
} from './curveLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CurveLabStateReturn {
  // Parameters
  tolerance: Ref<number>
  layer: Ref<string>

  // Inline report state
  inlineBusy: Ref<boolean>
  inlineResponse: Ref<CurvePreflightResponse | null>
  inlineError: Ref<string | null>

  // File validation state
  fileBusy: Ref<boolean>
  fileResponse: Ref<ValidationReport | null>
  fileError: Ref<string | null>

  // Auto-fix state
  autoFixBusy: Ref<boolean>
  fixedDownload: Ref<string | null>
  selectedFixes: Ref<AutoFixOption[]>
  workingDxf: Ref<string | null>

  // Computed
  inlinePoints: ComputedRef<CurvePoint[]>
  hasInlineGeometry: ComputedRef<boolean>
  inlinePointCount: ComputedRef<number>
  hasDxf: ComputedRef<boolean>

  // CAM ready labels
  inlineCamReadyLabel: ComputedRef<string>
  inlineCamReadyClass: ComputedRef<string>
  fileCamReadyLabel: ComputedRef<string>
  fileCamReadyClass: ComputedRef<string>
}

// ============================================================================
// Composable
// ============================================================================

export function useCurveLabState(props: CurveLabProps): CurveLabStateReturn {
  // Parameters
  const tolerance = ref(0.1)
  const layer = ref(props.layer)

  // Inline report state
  const inlineBusy = ref(false)
  const inlineResponse = ref<CurvePreflightResponse | null>(null)
  const inlineError = ref<string | null>(null)

  // File validation state
  const fileBusy = ref(false)
  const fileResponse = ref<ValidationReport | null>(null)
  const fileError = ref<string | null>(null)

  // Auto-fix state
  const autoFixBusy = ref(false)
  const fixedDownload = ref<string | null>(null)
  const selectedFixes = ref<AutoFixOption[]>([])
  const workingDxf = ref<string | null>(props.dxfBase64)

  // Watchers
  watch(
    () => props.layer,
    (next) => {
      layer.value = next || 'CURVE'
    }
  )

  watch(
    () => props.dxfBase64,
    (next) => {
      workingDxf.value = next
      fixedDownload.value = null
    }
  )

  // Computed - inline
  const inlinePoints = computed<CurvePoint[]>(() =>
    (props.points || []).map(([x, y]) => ({ x, y }))
  )

  const hasInlineGeometry = computed(() => inlinePoints.value.length >= 2)
  const inlinePointCount = computed(() => inlinePoints.value.length)

  // Computed - file
  const hasDxf = computed(() => !!workingDxf.value)

  // CAM ready labels
  const inlineCamReadyLabel = computed(() => {
    if (!inlineResponse.value) return ''
    return inlineResponse.value.cam_ready ? 'CAM Ready' : 'Needs Attention'
  })

  const inlineCamReadyClass = computed(() =>
    inlineResponse.value?.cam_ready
      ? 'bg-emerald-100 text-emerald-700'
      : 'bg-amber-100 text-amber-700'
  )

  const fileCamReadyLabel = computed(() => {
    if (!fileResponse.value) return ''
    return fileResponse.value.cam_ready ? 'CAM Ready' : 'Needs Review'
  })

  const fileCamReadyClass = computed(() =>
    fileResponse.value?.cam_ready
      ? 'bg-emerald-100 text-emerald-700'
      : 'bg-amber-100 text-amber-700'
  )

  return {
    tolerance,
    layer,
    inlineBusy,
    inlineResponse,
    inlineError,
    fileBusy,
    fileResponse,
    fileError,
    autoFixBusy,
    fixedDownload,
    selectedFixes,
    workingDxf,
    inlinePoints,
    hasInlineGeometry,
    inlinePointCount,
    hasDxf,
    inlineCamReadyLabel,
    inlineCamReadyClass,
    fileCamReadyLabel,
    fileCamReadyClass
  }
}
