<script setup lang="ts">
/**
 * SliderRow — Labeled range input with unit display
 *
 * Used by SpiralSoundholeDesigner.vue for parameter controls.
 * Dev Order 6.1: Created to resolve missing component.
 */
import { computed } from 'vue'

const props = defineProps<{
  label: string
  id: string
  min: number
  max: number
  step: number
  modelValue: number
  unit?: string
  accent?: 'upper' | 'lower' | string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
}>()

const displayValue = computed(() => {
  const val = props.modelValue
  if (props.step < 1) {
    const decimals = props.step.toString().split('.')[1]?.length ?? 2
    return val.toFixed(decimals)
  }
  return val.toString()
})

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', parseFloat(target.value))
}
</script>

<template>
  <div class="slider-row" :class="accent">
    <label :for="id" class="slider-label">{{ label }}</label>
    <input
      type="range"
      :id="id"
      :min="min"
      :max="max"
      :step="step"
      :value="modelValue"
      class="slider-input"
      @input="onInput"
    />
    <span class="slider-value">{{ displayValue }}{{ unit }}</span>
  </div>
</template>

<style scoped>
.slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.slider-label {
  flex: 0 0 120px;
  font-size: 11px;
  color: var(--color-text-secondary, #9ca3af);
}

.slider-input {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-background-secondary, #374151);
  border-radius: 2px;
  cursor: pointer;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-text-primary, #f9fafb);
  cursor: pointer;
}

.slider-input::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-text-primary, #f9fafb);
  border: none;
  cursor: pointer;
}

.slider-value {
  flex: 0 0 60px;
  text-align: right;
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  color: var(--color-text-primary, #f9fafb);
}

/* Accent colors for upper/lower spirals */
.slider-row.upper .slider-input::-webkit-slider-thumb {
  background: #c8a050;
}
.slider-row.upper .slider-input::-moz-range-thumb {
  background: #c8a050;
}
.slider-row.upper .slider-value {
  color: #c8a050;
}

.slider-row.lower .slider-input::-webkit-slider-thumb {
  background: #50a8c8;
}
.slider-row.lower .slider-input::-moz-range-thumb {
  background: #50a8c8;
}
.slider-row.lower .slider-value {
  color: #50a8c8;
}
</style>
