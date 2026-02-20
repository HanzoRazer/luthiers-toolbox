/**
 * usePipelineWorkflow - Stage workflow manager for multi-step pipelines
 *
 * Extracted from PipelineLab.vue to support decomposition.
 * Handles stage navigation, validation gates, and per-stage state tracking.
 *
 * @example
 * const {
 *   currentStage,
 *   stages,
 *   canAdvance,
 *   next,
 *   back,
 *   reset,
 *   setStageValid
 * } = usePipelineWorkflow({
 *   stages: ['Upload', 'Validate', 'Process', 'Export'],
 *   onStageChange: (from, to) => console.log(`Stage ${from} → ${to}`)
 * })
 */

import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface StageState {
  /** Stage has completed successfully */
  completed: boolean
  /** Stage is currently loading/processing */
  loading: boolean
  /** Stage has an error */
  error: string | null
  /** Stage result data (generic) */
  result: unknown
}

export interface PipelineWorkflowOptions {
  /** Stage labels */
  stages: string[]
  /** Initial stage index (default: 0) */
  initialStage?: number
  /** Callback when stage changes */
  onStageChange?: (fromStage: number, toStage: number) => void
  /** Callback when pipeline resets */
  onReset?: () => void
}

export interface PipelineWorkflowReturn {
  // --- State ---
  /** Current stage index (0-based) */
  currentStage: Ref<number>
  /** Stage labels */
  stages: Readonly<string[]>
  /** Per-stage state tracking */
  stageStates: Ref<StageState[]>

  // --- Computed ---
  /** Current stage label */
  currentStageLabel: ComputedRef<string>
  /** Can advance to next stage (current stage is valid) */
  canAdvance: ComputedRef<boolean>
  /** Can go back (not at first stage) */
  canGoBack: ComputedRef<boolean>
  /** Is at final stage */
  isLastStage: ComputedRef<boolean>
  /** Is at first stage */
  isFirstStage: ComputedRef<boolean>
  /** Overall progress (0-1) */
  progress: ComputedRef<number>

  // --- Actions ---
  /** Advance to next stage (if valid) */
  next: () => boolean
  /** Go back to previous stage */
  back: () => boolean
  /** Jump to specific stage (if reachable) */
  goTo: (stageIndex: number) => boolean
  /** Reset to initial stage */
  reset: () => void

  // --- Stage State Management ---
  /** Mark stage as completed/valid */
  setStageCompleted: (stageIndex: number, completed?: boolean) => void
  /** Set stage loading state */
  setStageLoading: (stageIndex: number, loading: boolean) => void
  /** Set stage error */
  setStageError: (stageIndex: number, error: string | null) => void
  /** Set stage result data */
  setStageResult: (stageIndex: number, result: unknown) => void
  /** Get stage state */
  getStageState: (stageIndex: number) => StageState
  /** Clear stage state (for retry) */
  clearStageState: (stageIndex: number) => void
}

// ============================================================================
// Composable
// ============================================================================

export function usePipelineWorkflow(
  options: PipelineWorkflowOptions
): PipelineWorkflowReturn {
  const { stages, initialStage = 0, onStageChange, onReset } = options

  // --- Core State ---
  const currentStage = ref(initialStage)

  // Initialize per-stage state
  const stageStates = ref<StageState[]>(
    stages.map(() => ({
      completed: false,
      loading: false,
      error: null,
      result: null,
    }))
  )

  // --- Computed ---
  const currentStageLabel = computed(() => stages[currentStage.value] ?? '')

  const canAdvance = computed(() => {
    const state = stageStates.value[currentStage.value]
    return state?.completed === true && !state?.loading && currentStage.value < stages.length - 1
  })

  const canGoBack = computed(() => currentStage.value > 0)

  const isLastStage = computed(() => currentStage.value === stages.length - 1)

  const isFirstStage = computed(() => currentStage.value === 0)

  const progress = computed(() => {
    if (stages.length <= 1) return 1
    return currentStage.value / (stages.length - 1)
  })

  // --- Watch for stage changes ---
  watch(currentStage, (newStage, oldStage) => {
    if (newStage !== oldStage && onStageChange) {
      onStageChange(oldStage, newStage)
    }
  })

  // --- Actions ---
  function next(): boolean {
    if (!canAdvance.value) return false
    currentStage.value++
    return true
  }

  function back(): boolean {
    if (!canGoBack.value) return false
    currentStage.value--
    return true
  }

  function goTo(stageIndex: number): boolean {
    if (stageIndex < 0 || stageIndex >= stages.length) return false

    // Can only go forward if all previous stages are completed
    if (stageIndex > currentStage.value) {
      for (let i = currentStage.value; i < stageIndex; i++) {
        if (!stageStates.value[i]?.completed) return false
      }
    }

    currentStage.value = stageIndex
    return true
  }

  function reset(): void {
    currentStage.value = initialStage
    // Reset all stage states
    stageStates.value = stages.map(() => ({
      completed: false,
      loading: false,
      error: null,
      result: null,
    }))
    onReset?.()
  }

  // --- Stage State Management ---
  function setStageCompleted(stageIndex: number, completed = true): void {
    if (stageIndex >= 0 && stageIndex < stages.length) {
      stageStates.value[stageIndex].completed = completed
    }
  }

  function setStageLoading(stageIndex: number, loading: boolean): void {
    if (stageIndex >= 0 && stageIndex < stages.length) {
      stageStates.value[stageIndex].loading = loading
    }
  }

  function setStageError(stageIndex: number, error: string | null): void {
    if (stageIndex >= 0 && stageIndex < stages.length) {
      stageStates.value[stageIndex].error = error
      if (error) {
        stageStates.value[stageIndex].completed = false
      }
    }
  }

  function setStageResult(stageIndex: number, result: unknown): void {
    if (stageIndex >= 0 && stageIndex < stages.length) {
      stageStates.value[stageIndex].result = result
    }
  }

  function getStageState(stageIndex: number): StageState {
    return (
      stageStates.value[stageIndex] ?? {
        completed: false,
        loading: false,
        error: null,
        result: null,
      }
    )
  }

  function clearStageState(stageIndex: number): void {
    if (stageIndex >= 0 && stageIndex < stages.length) {
      stageStates.value[stageIndex] = {
        completed: false,
        loading: false,
        error: null,
        result: null,
      }
    }
  }

  return {
    // State
    currentStage,
    stages,
    stageStates,

    // Computed
    currentStageLabel,
    canAdvance,
    canGoBack,
    isLastStage,
    isFirstStage,
    progress,

    // Actions
    next,
    back,
    goTo,
    reset,

    // Stage State Management
    setStageCompleted,
    setStageLoading,
    setStageError,
    setStageResult,
    getStageState,
    clearStageState,
  }
}

// ============================================================================
// Convenience Types for Consumers
// ============================================================================

/** Stage index type for PipelineLab (4 stages) */
export type PipelineLabStage = 0 | 1 | 2 | 3

/** Stage names for PipelineLab */
export const PIPELINE_LAB_STAGES = [
  'Upload DXF',
  'Preflight Check',
  'Reconstruct Contours',
  'Adaptive Pocket',
] as const

/** Create a PipelineLab-specific workflow instance */
export function usePipelineLabWorkflow(
  options?: Partial<Omit<PipelineWorkflowOptions, 'stages'>>
) {
  return usePipelineWorkflow({
    stages: [...PIPELINE_LAB_STAGES],
    ...options,
  })
}
