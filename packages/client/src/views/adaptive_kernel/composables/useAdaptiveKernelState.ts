/**
 * AdaptiveKernelLab state composable.
 */
import { ref, type Ref } from 'vue'
import type { AdaptivePlanIn, AdaptivePlanOut } from '@/api/adaptive'

// ============================================================================
// Types
// ============================================================================

export interface AdaptiveKernelStateReturn {
  // Units and tool params
  units: Ref<'mm' | 'inch'>
  toolD: Ref<number>
  stepover: Ref<number>
  stepdown: Ref<number>
  margin: Ref<number>
  strategy: Ref<'Spiral' | 'Lanes'>
  feedXY: Ref<number>
  safeZ: Ref<number>
  zRough: Ref<number>

  // Corner and slowdown
  cornerRadiusMin: Ref<number>
  targetStepover: Ref<number>
  slowdownFeedPct: Ref<number>

  // Trochoid
  useTrochoids: Ref<boolean>
  trochoidRadius: Ref<number>
  trochoidPitch: Ref<number>

  // Input/output
  loopsText: Ref<string>
  lastRequest: Ref<AdaptivePlanIn | null>
  result: Ref<AdaptivePlanOut | null>
  errorMsg: Ref<string | null>
  busy: Ref<boolean>

  // UI state
  showPipelineSnippet: Ref<boolean>
  sentToPipeline: Ref<boolean>
  showToolpathPreview: Ref<boolean>
}

// ============================================================================
// Composable
// ============================================================================

export function useAdaptiveKernelState(): AdaptiveKernelStateReturn {
  // Units and tool params
  const units = ref<'mm' | 'inch'>('mm')
  const toolD = ref(6.0)
  const stepover = ref(0.45)
  const stepdown = ref(2.0)
  const margin = ref(0.5)
  const strategy = ref<'Spiral' | 'Lanes'>('Spiral')
  const feedXY = ref(1200)
  const safeZ = ref(5.0)
  const zRough = ref(-1.5)

  // Corner and slowdown
  const cornerRadiusMin = ref(1.0)
  const targetStepover = ref(0.45)
  const slowdownFeedPct = ref(60.0)

  // Trochoid
  const useTrochoids = ref(false)
  const trochoidRadius = ref(1.5)
  const trochoidPitch = ref(3.0)

  // Input/output
  const loopsText = ref<string>('')
  const lastRequest = ref<AdaptivePlanIn | null>(null)
  const result = ref<AdaptivePlanOut | null>(null)
  const errorMsg = ref<string | null>(null)
  const busy = ref(false)

  // UI state
  const showPipelineSnippet = ref(false)
  const sentToPipeline = ref(false)
  const showToolpathPreview = ref(true)

  return {
    units,
    toolD,
    stepover,
    stepdown,
    margin,
    strategy,
    feedXY,
    safeZ,
    zRough,
    cornerRadiusMin,
    targetStepover,
    slowdownFeedPct,
    useTrochoids,
    trochoidRadius,
    trochoidPitch,
    loopsText,
    lastRequest,
    result,
    errorMsg,
    busy,
    showPipelineSnippet,
    sentToPipeline,
    showToolpathPreview
  }
}
