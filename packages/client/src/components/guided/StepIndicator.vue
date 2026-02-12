<script setup lang="ts">
/**
 * StepIndicator - Visual progress indicator for multi-step workflows
 *
 * Shows numbered steps with active/completed/pending states.
 */

export interface Step {
  id: string
  label: string
  description?: string
}

const props = defineProps<{
  steps: Step[]
  currentStep: number
  completedSteps?: number[]
}>()

const emit = defineEmits<{
  (e: 'step-click', stepIndex: number): void
}>()

function getStepState(index: number): 'completed' | 'active' | 'pending' {
  if (props.completedSteps?.includes(index)) return 'completed'
  if (index === props.currentStep) return 'active'
  if (index < props.currentStep) return 'completed'
  return 'pending'
}

function canNavigateTo(index: number): boolean {
  // Can navigate to completed steps or current step
  return index <= props.currentStep || (props.completedSteps?.includes(index) ?? false)
}

function handleStepClick(index: number) {
  if (canNavigateTo(index)) {
    emit('step-click', index)
  }
}
</script>

<template>
  <div class="step-indicator">
    <div
      v-for="(step, index) in steps"
      :key="step.id"
      class="step"
      :class="[
        `step--${getStepState(index)}`,
        { 'step--clickable': canNavigateTo(index) }
      ]"
      @click="handleStepClick(index)"
    >
      <div class="step__number">
        <span v-if="getStepState(index) === 'completed'" class="step__check">✓</span>
        <span v-else>{{ index + 1 }}</span>
      </div>
      <div class="step__content">
        <div class="step__label">{{ step.label }}</div>
        <div v-if="step.description" class="step__description">
          {{ step.description }}
        </div>
      </div>
      <div v-if="index < steps.length - 1" class="step__connector" />
    </div>
  </div>
</template>

<style scoped>
.step-indicator {
  display: flex;
  align-items: flex-start;
  gap: 0;
  padding: 1rem 0;
}

.step {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  flex: 1;
}

.step--clickable {
  cursor: pointer;
}

.step--clickable:hover .step__number {
  transform: scale(1.1);
}

.step__number {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
  transition: transform 0.15s ease, background-color 0.2s ease;
}

.step--pending .step__number {
  background: var(--color-surface-elevated, #f3f4f6);
  color: var(--color-text-muted, #6b7280);
  border: 2px solid var(--color-border, #e5e7eb);
}

.step--active .step__number {
  background: var(--color-primary, #3b82f6);
  color: white;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
}

.step--completed .step__number {
  background: var(--color-success, #22c55e);
  color: white;
}

.step__check {
  font-size: 1rem;
}

.step__content {
  flex: 1;
  min-width: 0;
}

.step__label {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--color-text, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step--pending .step__label {
  color: var(--color-text-muted, #6b7280);
}

.step__description {
  font-size: 0.75rem;
  color: var(--color-text-muted, #6b7280);
  margin-top: 0.125rem;
}

.step__connector {
  position: absolute;
  top: 1rem;
  left: 2.5rem;
  right: 0;
  height: 2px;
  background: var(--color-border, #e5e7eb);
}

.step--completed .step__connector,
.step--active .step__connector {
  background: var(--color-success, #22c55e);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .step--pending .step__number {
    background: #374151;
    border-color: #4b5563;
  }

  .step__connector {
    background: #4b5563;
  }
}
</style>
