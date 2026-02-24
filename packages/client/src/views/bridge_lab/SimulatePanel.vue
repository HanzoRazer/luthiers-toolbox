<template>
  <div class="simulate-panel">
    <h3>G-code Simulation</h3>

    <p class="help-text">
      Upload exported G-code file to verify toolpath
    </p>

    <div class="file-upload">
      <label class="upload-button">
        📁 Select G-code File
        <input
          type="file"
          accept=".nc,.gcode,.ngc"
          hidden
          @change="$emit('file-change', $event)"
        >
      </label>
      <span
        v-if="gcodeFile"
        class="file-name"
      >{{ gcodeFile.name }}</span>
    </div>

    <button
      class="btn-primary"
      :disabled="!gcodeFile || running"
      @click="$emit('simulate')"
    >
      {{ running ? 'Simulating...' : '▶️ Run Simulation' }}
    </button>

    <!-- Simulation Results -->
    <SimulationResultsPanel :sim-result="simResult" />
  </div>
</template>

<script setup lang="ts">
import SimulationResultsPanel, { type SimulationResult } from './SimulationResultsPanel.vue'

defineProps<{
  gcodeFile: File | null
  running: boolean
  simResult: SimulationResult | null
}>()

defineEmits<{
  'file-change': [event: Event]
  simulate: []
}>()
</script>

<style scoped>
.simulate-panel {
  padding: 1.5rem;
}

.simulate-panel h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.help-text {
  margin-bottom: 1rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.file-upload {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.upload-button {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #1f2937;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
  font-size: 0.875rem;
}

.upload-button:hover {
  background: #d1d5db;
}

.file-name {
  font-size: 0.875rem;
  color: #6b7280;
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
