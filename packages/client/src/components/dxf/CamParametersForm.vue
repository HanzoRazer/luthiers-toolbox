<script setup lang="ts">
/**
 * CamParametersForm - CAM parameters input form
 * Extracted from DxfToGcodeView.vue
 */

interface CamParams {
  tool_d: number
  stepover: number
  stepdown: number
  z_rough: number
  feed_xy: number
  feed_z: number
  rapid: number
  safe_z: number
  strategy: string
  layer_name: string
  climb: boolean
  smoothing: number
  margin: number
}

const props = defineProps<{
  modelValue: CamParams
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: CamParams]
}>()

function updateParam<K extends keyof CamParams>(key: K, value: CamParams[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <div class="params-section" :class="{ disabled }">
    <h2>CAM Parameters</h2>
    <div class="params-grid">
      <div class="param">
        <label>Tool Diameter (mm)</label>
        <input
          :value="modelValue.tool_d"
          type="number"
          step="0.5"
          min="0.5"
          max="25"
          :disabled="disabled"
          @input="updateParam('tool_d', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="param">
        <label>Stepover (0-1)</label>
        <input
          :value="modelValue.stepover"
          type="number"
          step="0.05"
          min="0.1"
          max="0.9"
          :disabled="disabled"
          @input="updateParam('stepover', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="param">
        <label>Stepdown (mm)</label>
        <input
          :value="modelValue.stepdown"
          type="number"
          step="0.5"
          min="0.5"
          max="10"
          :disabled="disabled"
          @input="updateParam('stepdown', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="param">
        <label>Target Depth (mm)</label>
        <input
          :value="modelValue.z_rough"
          type="number"
          step="0.5"
          max="0"
          :disabled="disabled"
          @input="updateParam('z_rough', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="param">
        <label>Feed XY (mm/min)</label>
        <input
          :value="modelValue.feed_xy"
          type="number"
          step="100"
          min="100"
          max="5000"
          :disabled="disabled"
          @input="updateParam('feed_xy', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="param">
        <label>Feed Z (mm/min)</label>
        <input
          :value="modelValue.feed_z"
          type="number"
          step="50"
          min="50"
          max="1000"
          :disabled="disabled"
          @input="updateParam('feed_z', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="param">
        <label>Safe Z (mm)</label>
        <input
          :value="modelValue.safe_z"
          type="number"
          step="1"
          min="1"
          max="50"
          :disabled="disabled"
          @input="updateParam('safe_z', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="param">
        <label>Layer Name</label>
        <input
          :value="modelValue.layer_name"
          type="text"
          :disabled="disabled"
          @input="updateParam('layer_name', ($event.target as HTMLInputElement).value)"
        >
      </div>
    </div>
  </div>
</template>

<style scoped>
.params-section {
  margin-bottom: 2rem;
}

.params-section.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.params-section h2 {
  font-size: 1.125rem;
  margin-bottom: 1rem;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.param {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.param label {
  font-size: 0.875rem;
  color: #374151;
  font-weight: 500;
}

.param input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
}

.param input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}
</style>
