/**
 * Composable for Bridge Lab workflow stage management.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface BridgeLabWorkflowState {
  currentStage: Ref<number>
  dxfFile: Ref<File | null>
  preflightResult: Ref<any>
  toolpathResult: Ref<any>
  exportedGcode: Ref<string | null>
  exportedFilename: Ref<string | null>
  gcodeFile: Ref<File | null>
  simResult: Ref<any>
  calculatorStatus: Ref<string | null>
  preflightPassed: ComputedRef<boolean>
  onDxfFileChanged: (file: File | null) => void
  onPreflightResult: (result: any) => void
  resetWorkflow: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useBridgeLabWorkflow(): BridgeLabWorkflowState {
  const currentStage = ref(1)
  const dxfFile = ref<File | null>(null)
  const preflightResult = ref<any>(null)
  const toolpathResult = ref<any>(null)
  const exportedGcode = ref<string | null>(null)
  const exportedFilename = ref<string | null>(null)
  const gcodeFile = ref<File | null>(null)
  const simResult = ref<any>(null)
  const calculatorStatus = ref<string | null>(null)

  const preflightPassed = computed(() => {
    return preflightResult.value?.passed === true
  })

  function onDxfFileChanged(file: File | null): void {
    dxfFile.value = file
    toolpathResult.value = null
    exportedGcode.value = null
    exportedFilename.value = null
    gcodeFile.value = null
    simResult.value = null
    currentStage.value = 1
    if (!file) {
      calculatorStatus.value = null
    }
  }

  function onPreflightResult(result: any): void {
    preflightResult.value = result
    if (result.passed) {
      currentStage.value = 2
    }
  }

  function resetWorkflow(): void {
    currentStage.value = 1
    dxfFile.value = null
    preflightResult.value = null
    toolpathResult.value = null
    exportedGcode.value = null
    exportedFilename.value = null
    gcodeFile.value = null
    simResult.value = null
    calculatorStatus.value = null
  }

  return {
    currentStage,
    dxfFile,
    preflightResult,
    toolpathResult,
    exportedGcode,
    exportedFilename,
    gcodeFile,
    simResult,
    calculatorStatus,
    preflightPassed,
    onDxfFileChanged,
    onPreflightResult,
    resetWorkflow
  }
}
