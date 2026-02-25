<script setup lang="ts">
/**
 * BenchParamsPanel.vue - Parameter input panel
 * Extracted from AdaptiveBenchLab.vue
 */
import type { BenchParams } from './useAdaptiveBenchActions'

const props = defineProps<{
  params: BenchParams
  loading: boolean
}>()

const emit = defineEmits<{
  'update:params': [params: BenchParams]
  'generate-spiral': []
  'generate-trochoid': []
  'run-benchmark': []
}>()

function updateParam<K extends keyof BenchParams>(key: K, value: BenchParams[K]) {
  emit('update:params', { ...props.params, [key]: value })
}
</script>

<template>
  <div class="params-panel">
    <h3>Test Parameters</h3>

    <div class="param-group">
      <h4>Geometry</h4>
      <label>
        Width (mm):
        <input
          :value="params.width"
          type="number"
          step="10"
          min="10"
          @input="updateParam('width', +($event.target as HTMLInputElement).value)"
        >
      </label>
      <label>
        Height (mm):
        <input
          :value="params.height"
          type="number"
          step="10"
          min="10"
          @input="updateParam('height', +($event.target as HTMLInputElement).value)"
        >
      </label>
    </div>

    <div class="param-group">
      <h4>Tool</h4>
      <label>
        Tool Diameter (mm):
        <input
          :value="params.toolDia"
          type="number"
          step="0.5"
          min="1"
          @input="updateParam('toolDia', +($event.target as HTMLInputElement).value)"
        >
      </label>
      <label>
        Stepover (mm):
        <input
          :value="params.stepover"
          type="number"
          step="0.1"
          min="0.1"
          @input="updateParam('stepover', +($event.target as HTMLInputElement).value)"
        >
      </label>
    </div>

    <div class="param-group">
      <h4>Spiral Options</h4>
      <label>
        Corner Fillet (mm):
        <input
          :value="params.cornerFillet"
          type="number"
          step="0.1"
          min="0"
          @input="updateParam('cornerFillet', +($event.target as HTMLInputElement).value)"
        >
      </label>
    </div>

    <div class="param-group">
      <h4>Trochoid Options</h4>
      <label>
        Loop Pitch (mm):
        <input
          :value="params.loopPitch"
          type="number"
          step="0.1"
          min="0.1"
          @input="updateParam('loopPitch', +($event.target as HTMLInputElement).value)"
        >
      </label>
      <label>
        Amplitude (mm):
        <input
          :value="params.amplitude"
          type="number"
          step="0.1"
          min="0"
          @input="updateParam('amplitude', +($event.target as HTMLInputElement).value)"
        >
      </label>
    </div>

    <div class="param-group">
      <h4>Benchmark</h4>
      <label>
        Runs:
        <input
          :value="params.benchRuns"
          type="number"
          step="10"
          min="1"
          @input="updateParam('benchRuns', +($event.target as HTMLInputElement).value)"
        >
      </label>
    </div>

    <div class="actions">
      <button
        :disabled="loading"
        class="btn-primary"
        @click="emit('generate-spiral')"
      >
        {{ loading ? 'Generating...' : 'Generate Spiral' }}
      </button>
      <button
        :disabled="loading"
        class="btn-primary"
        @click="emit('generate-trochoid')"
      >
        {{ loading ? 'Generating...' : 'Generate Trochoid' }}
      </button>
      <button
        :disabled="loading"
        class="btn-secondary"
        @click="emit('run-benchmark')"
      >
        {{ loading ? 'Running...' : 'Run Benchmark' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.params-panel {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.param-group {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.param-group:last-of-type {
  border-bottom: none;
}

h3 {
  margin-top: 0;
  color: #333;
  font-size: 1.2rem;
}

h4 {
  margin: 0 0 0.5rem 0;
  color: #555;
  font-size: 0.95rem;
  font-weight: 600;
}

label {
  display: block;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  color: #555;
}

input[type="number"] {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-primary, .btn-secondary {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #64748b;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #475569;
}

.btn-primary:disabled, .btn-secondary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
</style>
