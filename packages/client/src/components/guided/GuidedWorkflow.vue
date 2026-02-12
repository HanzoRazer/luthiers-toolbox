<script setup lang="ts">
/**
 * GuidedWorkflow - Step-by-step workflow container
 *
 * Provides navigation, progress tracking, and consistent UX
 * for multi-step operations like DXF → G-code conversion.
 */
import { ref, computed, provide } from 'vue'
import StepIndicator, { type Step } from './StepIndicator.vue'

export interface WorkflowStep extends Step {
  component?: any // Vue component for the step content
  validate?: () => boolean | Promise<boolean>
  onEnter?: () => void | Promise<void>
  onLeave?: () => void | Promise<void>
}

const props = defineProps<{
  steps: WorkflowStep[]
  title?: string
  subtitle?: string
  allowSkip?: boolean
  showSummaryOnComplete?: boolean
}>()

const emit = defineEmits<{
  (e: 'complete', data: Record<string, any>): void
  (e: 'cancel'): void
  (e: 'step-change', step: number): void
}>()

// State
const currentStep = ref(0)
const completedSteps = ref<number[]>([])
const stepData = ref<Record<string, any>>({})
const isValidating = ref(false)
const error = ref<string | null>(null)

// Computed
const currentStepConfig = computed(() => props.steps[currentStep.value])
const isFirstStep = computed(() => currentStep.value === 0)
const isLastStep = computed(() => currentStep.value === props.steps.length - 1)
const canGoBack = computed(() => !isFirstStep.value)
const canGoNext = computed(() => !isValidating.value)

const progressPercent = computed(() => {
  return Math.round((completedSteps.value.length / props.steps.length) * 100)
})

// Provide context to child steps
provide('workflowData', stepData)
provide('setStepData', (key: string, value: any) => {
  stepData.value[key] = value
})

// Navigation
async function goToStep(index: number) {
  if (index < 0 || index >= props.steps.length) return
  if (index === currentStep.value) return

  // Run onLeave for current step
  const current = props.steps[currentStep.value]
  if (current.onLeave) {
    await current.onLeave()
  }

  currentStep.value = index
  error.value = null

  // Run onEnter for new step
  const next = props.steps[index]
  if (next.onEnter) {
    await next.onEnter()
  }

  emit('step-change', index)
}

async function next() {
  if (isLastStep.value) {
    await complete()
    return
  }

  // Validate current step
  const step = currentStepConfig.value
  if (step.validate) {
    isValidating.value = true
    error.value = null

    try {
      const isValid = await step.validate()
      if (!isValid) {
        error.value = 'Please complete this step before continuing'
        isValidating.value = false
        return
      }
    } catch (e: any) {
      error.value = e.message || 'Validation failed'
      isValidating.value = false
      return
    }

    isValidating.value = false
  }

  // Mark step as completed
  if (!completedSteps.value.includes(currentStep.value)) {
    completedSteps.value.push(currentStep.value)
  }

  await goToStep(currentStep.value + 1)
}

function back() {
  if (canGoBack.value) {
    goToStep(currentStep.value - 1)
  }
}

async function complete() {
  // Validate final step
  const step = currentStepConfig.value
  if (step.validate) {
    isValidating.value = true
    try {
      const isValid = await step.validate()
      if (!isValid) {
        error.value = 'Please complete this step'
        isValidating.value = false
        return
      }
    } catch (e: any) {
      error.value = e.message || 'Validation failed'
      isValidating.value = false
      return
    }
    isValidating.value = false
  }

  // Mark final step completed
  if (!completedSteps.value.includes(currentStep.value)) {
    completedSteps.value.push(currentStep.value)
  }

  emit('complete', stepData.value)
}

function cancel() {
  emit('cancel')
}

function reset() {
  currentStep.value = 0
  completedSteps.value = []
  stepData.value = {}
  error.value = null
}

// Expose for parent control
defineExpose({
  currentStep,
  goToStep,
  next,
  back,
  reset,
  stepData,
})
</script>

<template>
  <div class="guided-workflow">
    <!-- Header -->
    <header v-if="title || subtitle" class="workflow-header">
      <h2 v-if="title" class="workflow-title">{{ title }}</h2>
      <p v-if="subtitle" class="workflow-subtitle">{{ subtitle }}</p>
    </header>

    <!-- Step Indicator -->
    <StepIndicator
      :steps="steps"
      :current-step="currentStep"
      :completed-steps="completedSteps"
      @step-click="goToStep"
    />

    <!-- Progress Bar -->
    <div class="progress-bar">
      <div class="progress-bar__fill" :style="{ width: `${progressPercent}%` }" />
    </div>

    <!-- Step Content -->
    <div class="step-content">
      <div class="step-header">
        <h3 class="step-title">
          Step {{ currentStep + 1 }}: {{ currentStepConfig.label }}
        </h3>
        <p v-if="currentStepConfig.description" class="step-description">
          {{ currentStepConfig.description }}
        </p>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error-banner">
        <span class="error-icon">!</span>
        <span>{{ error }}</span>
        <button class="error-dismiss" @click="error = null">Dismiss</button>
      </div>

      <!-- Dynamic Step Content -->
      <div class="step-body">
        <slot :name="`step-${currentStep}`" :data="stepData">
          <component
            v-if="currentStepConfig.component"
            :is="currentStepConfig.component"
            v-model:data="stepData"
          />
          <div v-else class="step-placeholder">
            <p>Step content for "{{ currentStepConfig.label }}"</p>
          </div>
        </slot>
      </div>
    </div>

    <!-- Navigation Buttons -->
    <footer class="workflow-footer">
      <button
        class="btn btn--secondary"
        @click="cancel"
      >
        Cancel
      </button>

      <div class="workflow-footer__right">
        <button
          v-if="canGoBack"
          class="btn btn--outline"
          @click="back"
        >
          Back
        </button>

        <button
          class="btn btn--primary"
          :disabled="!canGoNext"
          @click="next"
        >
          <span v-if="isValidating">Validating...</span>
          <span v-else-if="isLastStep">Complete</span>
          <span v-else>Next</span>
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.guided-workflow {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 800px;
  margin: 0 auto;
  padding: 1.5rem;
}

.workflow-header {
  text-align: center;
}

.workflow-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text, #1f2937);
  margin: 0;
}

.workflow-subtitle {
  font-size: 0.875rem;
  color: var(--color-text-muted, #6b7280);
  margin: 0.5rem 0 0 0;
}

.progress-bar {
  height: 4px;
  background: var(--color-surface-elevated, #f3f4f6);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background: var(--color-primary, #3b82f6);
  transition: width 0.3s ease;
}

.step-content {
  background: var(--color-surface, #ffffff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  padding: 1.5rem;
}

.step-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.step-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text, #1f2937);
  margin: 0;
}

.step-description {
  font-size: 0.875rem;
  color: var(--color-text-muted, #6b7280);
  margin: 0.5rem 0 0 0;
}

.step-body {
  min-height: 200px;
}

.step-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-muted, #6b7280);
  background: var(--color-surface-elevated, #f9fafb);
  border-radius: 4px;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #b91c1c;
  margin-bottom: 1rem;
}

.error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  background: #dc2626;
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: bold;
}

.error-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: #b91c1c;
  cursor: pointer;
  font-size: 0.75rem;
  text-decoration: underline;
}

.workflow-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.workflow-footer__right {
  display: flex;
  gap: 0.75rem;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn--primary {
  background: var(--color-primary, #3b82f6);
  color: white;
  border: none;
}

.btn--primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--secondary {
  background: transparent;
  color: var(--color-text-muted, #6b7280);
  border: 1px solid var(--color-border, #e5e7eb);
}

.btn--secondary:hover {
  background: var(--color-surface-elevated, #f3f4f6);
}

.btn--outline {
  background: transparent;
  color: var(--color-primary, #3b82f6);
  border: 1px solid var(--color-primary, #3b82f6);
}

.btn--outline:hover {
  background: rgba(59, 130, 246, 0.1);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .step-content {
    background: #1f2937;
    border-color: #374151;
  }

  .step-header {
    border-color: #374151;
  }

  .step-placeholder {
    background: #111827;
  }

  .workflow-footer {
    border-color: #374151;
  }

  .error-banner {
    background: #450a0a;
    border-color: #7f1d1d;
    color: #fca5a5;
  }
}
</style>
