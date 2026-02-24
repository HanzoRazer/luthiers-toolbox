<script setup lang="ts">
/**
 * CamParametersCard.vue - CAM parameter inputs and generate button
 * Extracted from Phase3CamPanel.vue
 */
import type { CamParams } from "@/composables/useBlueprintWorkflow";

const props = defineProps<{
  camParams: CamParams;
  isSendingToCAM: boolean;
}>();

const emit = defineEmits<{
  "send-to-cam": [];
  "update:camParams": [params: CamParams];
}>();

function updateParam<K extends keyof CamParams>(key: K, value: CamParams[K]) {
  emit("update:camParams", { ...props.camParams, [key]: value });
}
</script>

<template>
  <div class="action-card">
    <p class="hint">
      Generate G-code from vectorized DXF using adaptive pocketing
    </p>

    <div class="controls-grid">
      <div class="control-group">
        <label>Tool Diameter (mm):</label>
        <input
          :value="camParams.tool_d"
          type="number"
          step="0.5"
          min="0.5"
          max="25"
          @input="updateParam('tool_d', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Stepover (0-1):</label>
        <input
          :value="camParams.stepover"
          type="number"
          step="0.05"
          min="0.1"
          max="0.9"
          @input="updateParam('stepover', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Stepdown (mm):</label>
        <input
          :value="camParams.stepdown"
          type="number"
          step="0.5"
          min="0.5"
          max="10"
          @input="updateParam('stepdown', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Target Depth (mm):</label>
        <input
          :value="camParams.z_rough"
          type="number"
          step="0.5"
          max="0"
          @input="updateParam('z_rough', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Feed XY (mm/min):</label>
        <input
          :value="camParams.feed_xy"
          type="number"
          step="100"
          min="100"
          max="5000"
          @input="updateParam('feed_xy', parseInt(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Feed Z (mm/min):</label>
        <input
          :value="camParams.feed_z"
          type="number"
          step="50"
          min="50"
          max="1000"
          @input="updateParam('feed_z', parseInt(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <button
      :disabled="isSendingToCAM"
      class="btn-primary"
      @click="emit('send-to-cam')"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
      {{ isSendingToCAM ? 'Generating G-code...' : 'Generate G-code (GRBL)' }}
    </button>
  </div>
</template>

<style scoped>
.action-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.hint {
  color: #6b7280;
  margin-bottom: 1rem;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.control-group label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.control-group input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #f59e0b;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #d97706;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}
</style>
