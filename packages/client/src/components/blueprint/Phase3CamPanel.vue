<template>
  <section class="workflow-section phase-3">
    <div class="section-header">
      <h2>
        <span class="step-number">3</span>
        Send to CAM Pipeline (GRBL)
      </h2>
    </div>

    <!-- CAM Parameters -->
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

    <!-- RMOS Result -->
    <div
      v-if="rmosResult"
      class="results-card"
    >
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-value">{{ rmosResult.decision?.risk_level || 'N/A' }}</span>
          <span class="stat-label">Risk Level</span>
        </div>
        <div class="stat-card">
          <span
            class="stat-value run-id"
          >{{ rmosResult.run_id || 'N/A' }}</span>
          <span class="stat-label">RMOS Run ID</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ rmosResult.rmos_persisted ? 'Y' : 'N' }}</span>
          <span class="stat-label">RMOS Persisted</span>
        </div>
      </div>

      <!-- Warnings -->
      <div
        v-if="rmosResult.decision?.warnings?.length"
        class="warning-list"
      >
        <strong>Warnings:</strong>
        <ul>
          <li
            v-for="(w, i) in rmosResult.decision.warnings"
            :key="i"
          >
            {{ w }}
          </li>
        </ul>
      </div>

      <!-- RMOS Error -->
      <div
        v-if="!rmosResult.rmos_persisted && rmosResult.rmos_error"
        class="rmos-error"
      >
        <strong>RMOS Error:</strong> {{ rmosResult.rmos_error }}
      </div>

      <!-- Download Button -->
      <div class="export-row">
        <button
          :disabled="!gcodeReady"
          class="btn-primary"
          @click="emit('download-gcode')"
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
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Download G-code (.nc)
        </button>
        <span
          v-if="rmosResult && !rmosResult.gcode?.inline"
          class="hint-small"
        >
          G-code too large for inline delivery. Use RMOS attachments.
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { CamParams, RmosResult } from '@/composables/useBlueprintWorkflow'

// Props
interface Props {
  camParams: CamParams
  rmosResult: RmosResult | null
  isSendingToCAM: boolean
  gcodeReady: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'send-to-cam': []
  'download-gcode': []
  'update:camParams': [params: CamParams]
}>()

// Helpers
function updateParam<K extends keyof CamParams>(key: K, value: CamParams[K]) {
  emit('update:camParams', { ...props.camParams, [key]: value })
}
</script>

<style scoped>
.workflow-section {
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  padding: 1.5rem;
  background: white;
}

.workflow-section.phase-3 {
  border-color: #f59e0b;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.25rem;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f59e0b;
  color: white;
  font-weight: bold;
  font-size: 1rem;
}

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

.results-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #f59e0b;
}

.stat-value.run-id {
  font-size: 0.75rem;
  word-break: break-all;
}

.stat-label {
  display: block;
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.warning-list {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.warning-list ul {
  margin: 0.5rem 0 0 1.25rem;
  padding: 0;
}

.warning-list li {
  color: #92400e;
  font-size: 0.875rem;
}

.rmos-error {
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
  color: #991b1b;
}

.export-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.hint-small {
  color: #9ca3af;
  font-size: 0.875rem;
}

/* Buttons */
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
