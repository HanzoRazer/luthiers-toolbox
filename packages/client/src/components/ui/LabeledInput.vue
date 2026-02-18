<script setup lang="ts">
/**
 * LabeledInput.vue - Reusable labeled input component
 *
 * Reduces repetitive input + label patterns across god objects.
 * Supports number, text, and select types.
 */
defineOptions({ name: 'LabeledInput' })

type InputType = 'number' | 'text' | 'select'

const props = withDefaults(defineProps<{
  modelValue: number | string
  label: string
  type?: InputType
  hint?: string
  min?: number
  max?: number
  step?: number
  options?: Array<{ value: string; label: string }>
  disabled?: boolean
  suffix?: string
}>(), {
  type: 'number',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: number | string]
}>()

function onInput(event: Event) {
  const target = event.target as HTMLInputElement | HTMLSelectElement
  const value = props.type === 'number' ? parseFloat(target.value) : target.value
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="labeled-input">
    <label class="label">
      {{ label }}
      <span v-if="suffix" class="suffix">{{ suffix }}</span>
    </label>

    <select
      v-if="type === 'select'"
      :value="modelValue"
      :disabled="disabled"
      class="input select"
      @change="onInput"
    >
      <option
        v-for="opt in options"
        :key="opt.value"
        :value="opt.value"
      >
        {{ opt.label }}
      </option>
    </select>

    <input
      v-else
      :type="type"
      :value="modelValue"
      :min="min"
      :max="max"
      :step="step"
      :disabled="disabled"
      class="input"
      @input="onInput"
    >

    <p v-if="hint" class="hint">{{ hint }}</p>
  </div>
</template>

<style scoped>
.labeled-input {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.suffix {
  font-weight: 400;
  color: #6b7280;
  font-size: 0.75rem;
}

.input {
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  width: 100%;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}

.select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
  padding-right: 2rem;
}

.hint {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
}
</style>
