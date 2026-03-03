<template>
  <div class="adaptive-panel">
    <h3>Adaptive Pocket Parameters</h3>

    <div class="param-grid">
      <div class="param-field">
        <label>Tool Diameter</label>
        <input
          :value="params.tool_d"
          type="number"
          step="0.1"
          @input="emitUpdate('tool_d', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">{{ params.units }}</span>
      </div>

      <div class="param-field">
        <label>Units</label>
        <select
          :value="params.units"
          @change="emitUpdate('units', ($event.target as HTMLSelectElement).value)"
        >
          <option value="mm">
            Millimeters
          </option>
          <option value="inch">
            Inches
          </option>
        </select>
      </div>

      <div class="param-field">
        <label>Geometry Layer</label>
        <input
          :value="params.geometry_layer"
          type="text"
          @input="emitUpdate('geometry_layer', ($event.target as HTMLInputElement).value)"
        >
      </div>

      <div class="param-field">
        <label>Stepover</label>
        <input
          :value="params.stepover"
          type="number"
          step="0.05"
          min="0.1"
          max="1.0"
          @input="emitUpdate('stepover', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">% of tool_d</span>
      </div>

      <div class="param-field">
        <label>Stepdown</label>
        <input
          :value="params.stepdown"
          type="number"
          step="0.1"
          @input="emitUpdate('stepdown', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">{{ params.units }}</span>
      </div>

      <div class="param-field">
        <label>Margin</label>
        <input
          :value="params.margin"
          type="number"
          step="0.1"
          @input="emitUpdate('margin', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">{{ params.units }}</span>
      </div>

      <div class="param-field">
        <label>Strategy</label>
        <select
          :value="params.strategy"
          @change="emitUpdate('strategy', ($event.target as HTMLSelectElement).value)"
        >
          <option value="Spiral">
            Spiral
          </option>
          <option value="Lanes">
            Lanes
          </option>
        </select>
      </div>

      <div class="param-field">
        <label>Feed XY</label>
        <input
          :value="params.feed_xy"
          type="number"
          step="100"
          @input="emitUpdate('feed_xy', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">{{ params.units }}/min</span>
      </div>

      <div class="param-field">
        <label>Safe Z</label>
        <input
          :value="params.safe_z"
          type="number"
          step="0.5"
          @input="emitUpdate('safe_z', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">{{ params.units }}</span>
      </div>

      <div class="param-field">
        <label>Z Rough</label>
        <input
          :value="params.z_rough"
          type="number"
          step="0.5"
          @input="emitUpdate('z_rough', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">{{ params.units }}</span>
      </div>
    </div>

    <button
      class="btn-primary"
      :disabled="!canGenerate || running"
      @click="$emit('generate')"
    >
      {{ running ? 'Generating Toolpath...' : '🔄 Generate Adaptive Toolpath' }}
    </button>

    <!-- Toolpath Results -->
    <ToolpathResultsPanel
      v-if="toolpathResult"
      :toolpath-result="toolpathResult"
      :units="params.units"
      :machine-limits="machineLimits"
    />
  </div>
</template>

<script setup lang="ts">
import ToolpathResultsPanel from './ToolpathResultsPanel.vue'
import type { AdaptiveParams, MachineLimits } from './composables/bridgeLabTypes'

const props = defineProps<{
  params: AdaptiveParams
  canGenerate: boolean
  running: boolean
  toolpathResult: unknown | null
  machineLimits: MachineLimits | null
}>()

const emit = defineEmits<{
  'update:params': [params: AdaptiveParams]
  generate: []
}>()

function emitUpdate(key: keyof AdaptiveParams, value: number | string) {
  emit('update:params', { ...props.params, [key]: value })
}
</script>

<style scoped>
.adaptive-panel {
  padding: 1.5rem;
}

.adaptive-panel h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.param-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.param-field label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.param-field input,
.param-field select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.param-field .unit {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: -0.25rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>
