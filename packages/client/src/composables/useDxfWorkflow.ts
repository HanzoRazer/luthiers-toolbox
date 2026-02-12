/**
 * Composable for DXF to G-code workflow state management.
 * Extracted from DxfToGcodeView.vue
 */
import { ref, computed } from 'vue'

export type WorkflowStep = 'upload' | 'validate' | 'configure' | 'generate' | 'review' | 'export'

export interface DxfFile {
  name: string
  size: number
  content?: string
  validationResult?: ValidationResult
}

export interface ValidationResult {
  ok: boolean
  errors: string[]
  warnings: string[]
  entities: number
  layers: string[]
  bounds?: {
    minX: number
    minY: number
    maxX: number
    maxY: number
  }
}

export interface GenerationResult {
  ok: boolean
  gcode?: string
  runId?: string
  riskLevel?: 'GREEN' | 'YELLOW' | 'RED'
  errors?: string[]
  warnings?: string[]
}

export function useDxfWorkflow() {
  // Current step
  const currentStep = ref<WorkflowStep>('upload')

  // File state
  const dxfFile = ref<DxfFile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Validation state
  const validationResult = ref<ValidationResult | null>(null)
  const validating = ref(false)

  // Generation state
  const generationResult = ref<GenerationResult | null>(null)
  const generating = ref(false)

  // Step navigation
  const canProceed = computed(() => {
    switch (currentStep.value) {
      case 'upload':
        return dxfFile.value !== null
      case 'validate':
        return validationResult.value?.ok === true
      case 'configure':
        return true // Configuration always allows proceeding
      case 'generate':
        return generationResult.value?.ok === true
      case 'review':
        return generationResult.value?.riskLevel !== 'RED'
      case 'export':
        return true
      default:
        return false
    }
  })

  const canGoBack = computed(() => {
    return currentStep.value !== 'upload'
  })

  const stepOrder: WorkflowStep[] = ['upload', 'validate', 'configure', 'generate', 'review', 'export']

  function nextStep() {
    const idx = stepOrder.indexOf(currentStep.value)
    if (idx < stepOrder.length - 1 && canProceed.value) {
      currentStep.value = stepOrder[idx + 1]
    }
  }

  function prevStep() {
    const idx = stepOrder.indexOf(currentStep.value)
    if (idx > 0) {
      currentStep.value = stepOrder[idx - 1]
    }
  }

  function goToStep(step: WorkflowStep) {
    currentStep.value = step
  }

  // File handling
  function setFile(file: DxfFile) {
    dxfFile.value = file
    // Reset downstream state
    validationResult.value = null
    generationResult.value = null
    error.value = null
  }

  function clearFile() {
    dxfFile.value = null
    validationResult.value = null
    generationResult.value = null
    currentStep.value = 'upload'
    error.value = null
  }

  // Validation
  function setValidationResult(result: ValidationResult) {
    validationResult.value = result
    if (dxfFile.value) {
      dxfFile.value.validationResult = result
    }
  }

  // Generation
  function setGenerationResult(result: GenerationResult) {
    generationResult.value = result
  }

  // Reset entire workflow
  function reset() {
    currentStep.value = 'upload'
    dxfFile.value = null
    validationResult.value = null
    generationResult.value = null
    loading.value = false
    validating.value = false
    generating.value = false
    error.value = null
  }

  // Progress indicator
  const progress = computed(() => {
    const idx = stepOrder.indexOf(currentStep.value)
    return Math.round(((idx + 1) / stepOrder.length) * 100)
  })

  return {
    // State
    currentStep,
    dxfFile,
    loading,
    error,
    validationResult,
    validating,
    generationResult,
    generating,

    // Computed
    canProceed,
    canGoBack,
    progress,
    stepOrder,

    // Methods
    nextStep,
    prevStep,
    goToStep,
    setFile,
    clearFile,
    setValidationResult,
    setGenerationResult,
    reset,
  }
}
